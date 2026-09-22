"""
Cinemaxx.de show-discovery agent.

For every movie in data/zineflix_movies.json that declares a
`cinemaxxSlug`, scan all Cinemaxx cities for future showtimes and merge
them into that movie's `data/<slug>_manual.json` overlay. The change
lands in booking.html via the same surgical patch used by the Zineflix
scraper.

Backend: `scripts/browser_fetch.py` (patchright driving Chrome/Chromium
in headed mode with a persistent user-data dir so cf_clearance cookies
survive between runs).

Flow per movie:
  1. For each Cinemaxx city (see CITIES below), navigate to
     /kinoprogramm/<city>/film/<cinemaxxSlug> in a single browser
     session (city loop reuses the same page — first city warms up
     the cf_clearance cookie, the rest are fast).
  2. Parse showtimes from Cinemaxx's `data-test="sessions-group-…"`
     structure.
  3. Merge into data/<slug>_manual.json, dedup by bookingUrl. New
     rows land as `Cinemaxx <City>` cinema entries with Telugu OmeU
     subtitle inferred from the session's `__lang` label.
  4. Write data/<slug>_cinemaxx.json (roster snapshot of scanned
     cities), append any per-run diff to data/cinemaxx_alerts.md.
  5. Delegate booking.html patching to the Zineflix scraper's
     `regenerate_booking_html` — same brace-count-safe rewrite of
     ONLY the movie's sub-entry.

Usage:
  py scripts/discover_cinemaxx_shows.py            # all registered movies
  py scripts/discover_cinemaxx_shows.py paradise   # one movie
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from patchright.sync_api import sync_playwright

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
REGISTRY_FILE = DATA_DIR / "zineflix_movies.json"
ALERTS_FILE = DATA_DIR / "cinemaxx_alerts.md"

sys.path.insert(0, str(SCRIPT_DIR))
from discover_zineflix_shows import regenerate_booking_html  # noqa: E402
from browser_fetch import USER_DATA, CONTACT_URL, CONTACT_EMAIL, _CHALLENGE_TITLE_RE  # noqa: E402

# Known Cinemaxx cinema slugs. Enumerated from
# https://www.cinemaxx.de/unsere-kinos (30 cinemas as of 2026-09-22).
# When Cinemaxx adds a new location, add its slug here — the scraper
# will pick it up on the next run.
CITIES = [
    "augsburg", "berlin", "bielefeld", "bremen", "dresden", "essen",
    "freiburg", "gottingen", "halle", "hamburg-dammtor", "hamburg-harburg",
    "hamburg-holi", "hamburg-wandsbek", "hannover", "heilbronn", "kiel",
    "krefeld", "magdeburg", "mulheim", "munchen", "offenbach", "oldenburg",
    "regensburg", "sindelfingen", "stuttgart-liederhalle",
    "stuttgart-si-centrum", "trier", "wolfsburg", "wuppertal", "wurzburg",
]

# Pretty-print labels for city slugs with special characters.
CITY_LABELS = {
    "hamburg-dammtor": "Hamburg (Dammtor)",
    "hamburg-harburg": "Hamburg (Harburg)",
    "hamburg-holi": "Hamburg (Holi)",
    "hamburg-wandsbek": "Hamburg (Wandsbek)",
    "stuttgart-liederhalle": "Stuttgart (Liederhalle)",
    "stuttgart-si-centrum": "Stuttgart (SI-Centrum)",
    "gottingen": "Göttingen",
    "mulheim": "Mülheim",
    "munchen": "München",
    "wurzburg": "Würzburg",
}

# For city fields on booking.html, collapse Hamburg/Stuttgart branches
# so users see one grouped Hamburg / Stuttgart accordion.
CITY_FIELD_OVERRIDES = {
    "hamburg-dammtor": "Hamburg", "hamburg-harburg": "Hamburg",
    "hamburg-holi": "Hamburg", "hamburg-wandsbek": "Hamburg",
    "stuttgart-liederhalle": "Stuttgart",
    "stuttgart-si-centrum": "Stuttgart",
}


def label(slug: str) -> str:
    return CITY_LABELS.get(slug, slug.capitalize())


# --------------------------------------------------------------------
# HTML -> sessions
# --------------------------------------------------------------------

def extract_sessions(html: str) -> list[dict]:
    """Return [{date, time, kino, lang, href}, ...] parsed from a rendered
    Cinemaxx film-page HTML dump."""
    anchors = list(re.finditer(r'<a class="session"[^>]*href="([^"]+)"', html))
    date_markers = list(re.finditer(
        r'data-test="sessions-group-(\d{4}-\d{2}-\d{2})', html))
    seen = set()
    out = []
    for a in anchors:
        prev_date = None
        for d in date_markers:
            if d.start() < a.start():
                prev_date = d.group(1)
            else:
                break
        if not prev_date:
            continue
        href = a.group(1)
        body = html[a.end():a.end() + 2500]
        t = re.search(r'datetime="(\d{2}:\d{2})"[^>]*>\d{2}:\d{2}</time>', body)
        k = re.search(r'screen-name">([^<]+)</span>', body)
        L = re.search(r'__lang">([^<]+)</span>', body)
        if not t:
            continue
        key = (prev_date, t.group(1), href)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "date": prev_date,
            "time": t.group(1),
            "kino": (k.group(1).strip() if k else ""),
            "lang": (L.group(1).strip() if L else ""),
            "href": f"https://www.cinemaxx.de{href}",
        })
    out.sort(key=lambda s: (s["date"], s["time"]))
    return out


# --------------------------------------------------------------------
# Registry + merge
# --------------------------------------------------------------------

def load_registry() -> list[dict]:
    with open(REGISTRY_FILE, encoding="utf-8") as f:
        return json.load(f).get("movies") or []


def load_manual(slug: str) -> dict:
    path = DATA_DIR / f"{slug}_manual.json"
    if path.exists():
        return json.load(open(path, encoding="utf-8"))
    return {"shows": []}


def save_manual(slug: str, data: dict):
    path = DATA_DIR / f"{slug}_manual.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_sessions_into_manual(slug: str, city_sessions: dict) -> int:
    """city_sessions: {city_slug: [session dicts]}. Merge into
    <slug>_manual.json (dedup by bookingUrl). Returns number of new rows."""
    data = load_manual(slug)
    shows = data.setdefault("shows", [])
    have_urls = {s.get("bookingUrl") for s in shows if s.get("bookingUrl")}
    added = 0
    for city_slug, sess_list in city_sessions.items():
        city = CITY_FIELD_OVERRIDES.get(city_slug, label(city_slug))
        cinema = f"Cinemaxx {label(city_slug)}"
        for s in sess_list:
            if s["href"] in have_urls:
                continue
            lang = s.get("lang", "")
            subtitle = (
                "Telugu (OmeU)" if re.search(r"engl|OmeU|OmU|UT", lang, re.I)
                else "Telugu"
            )
            shows.append({
                "city": city, "cinema": cinema,
                "date": s["date"], "time": s["time"],
                "subtitle": subtitle, "bookingUrl": s["href"],
            })
            have_urls.add(s["href"])
            added += 1
    if added:
        save_manual(slug, data)
    return added


# --------------------------------------------------------------------
# Alerts + snapshot
# --------------------------------------------------------------------

def load_prior_cities(slug: str) -> dict:
    path = DATA_DIR / f"{slug}_cinemaxx.json"
    if not path.exists():
        return {}
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return {}
    return d.get("cities") or {}


def write_snapshot(slug: str, city_sessions: dict):
    path = DATA_DIR / f"{slug}_cinemaxx.json"
    payload = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "movie": slug,
        "totalCities": len([c for c, s in city_sessions.items() if s]),
        "totalShows": sum(len(s) for s in city_sessions.values()),
        "cities": city_sessions,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def append_alerts(slug: str, movie_title: str, new_shows_count: int,
                   new_cities: list[str], removed_cities: list[str]):
    if new_shows_count == 0 and not new_cities and not removed_cities:
        return
    header_needed = not ALERTS_FILE.exists()
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("# Cinemaxx roster alerts\n\n")
            f.write("Auto-generated by `scripts/discover_cinemaxx_shows.py`.\n\n")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        f.write(f"## {ts} — {movie_title} ({slug})\n\n")
        if new_shows_count:
            f.write(f"**+{new_shows_count} new show(s) added to booking.html.**\n\n")
        if new_cities:
            f.write(f"**{len(new_cities)} new Cinemaxx city/cities scheduling this film:**\n")
            for c in new_cities:
                f.write(f"- {label(c)}\n")
            f.write("\n")
        if removed_cities:
            f.write(f"**{len(removed_cities)} Cinemaxx city/cities removed the film:**\n")
            for c in removed_cities:
                f.write(f"- {label(c)}\n")
            f.write("\n")


# --------------------------------------------------------------------
# Browser scan
# --------------------------------------------------------------------

def scan_movie_cinemaxx(movie: dict) -> dict:
    """Return {city_slug: [sessions]} for one movie."""
    cinemaxx_slug = movie["cinemaxxSlug"]
    print(f"\n=== {movie['title']} ({movie['slug']}) — Cinemaxx slug={cinemaxx_slug!r} ===")

    USER_DATA.mkdir(parents=True, exist_ok=True)
    channel = os.environ.get("BROWSER_FETCH_CHANNEL", "chrome")
    results = {}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA),
            channel=channel,
            headless=False,
            no_viewport=True,
            extra_http_headers={
                "X-Bot-Contact": f"{CONTACT_URL} <{CONTACT_EMAIL}>",
                "From": CONTACT_EMAIL,
            },
        )
        page = ctx.new_page()
        for slug in CITIES:
            url = f"https://www.cinemaxx.de/kinoprogramm/{slug}/film/{cinemaxx_slug}"
            print(f"  [{slug}] ", end="", flush=True)
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                # Wait for challenge (usually already cleared thanks to cookie).
                for _ in range(30):
                    t = page.title()
                    if t.strip() and not _CHALLENGE_TITLE_RE.search(t):
                        break
                    page.wait_for_timeout(1000)
                # Wait for the SPA to render either the schedule or a
                # "not in programm" marker.
                try:
                    page.wait_for_function(
                        "() => /sessions__list__item|nicht im Programm|derzeit keine|Aktuell nicht|Ticketwecker/.test(document.body.innerText)",
                        timeout=15000,
                    )
                except Exception:
                    pass
                page.wait_for_timeout(1500)
                sess = extract_sessions(page.content())
                if sess:
                    print(f"{len(sess)} show(s)")
                    for s in sess:
                        print(f"      {s['date']} {s['time']}  {s['kino']}  ({s['lang']})")
                    results[slug] = sess
                else:
                    print("0")
            except Exception as e:
                print(f"ERR {e}")
        ctx.close()
    return results


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def run_movie(movie: dict) -> tuple[int, list[str], list[str]]:
    slug = movie["slug"]
    current = scan_movie_cinemaxx(movie)
    prior = load_prior_cities(slug)
    prior_with_shows = {c for c, s in prior.items() if s}
    current_with_shows = {c for c, s in current.items() if s}
    new_cities = sorted(current_with_shows - prior_with_shows)
    removed_cities = sorted(prior_with_shows - current_with_shows)
    added_rows = merge_sessions_into_manual(slug, current)
    write_snapshot(slug, current)
    append_alerts(slug, movie["title"], added_rows, new_cities, removed_cities)
    print(f"\n[{slug}] {added_rows} new row(s) added to manual, "
          f"{sum(len(v) for v in current.values())} total Cinemaxx shows across "
          f"{len(current_with_shows)} city/cities.")
    # Regenerate booking.html surgically.
    if added_rows:
        manual = load_manual(slug)
        booking_shows = sorted(
            manual.get("shows") or [],
            key=lambda s: (s.get("date", ""), s.get("time", ""),
                           s.get("city", ""), s.get("cinema", "")),
        )
        if regenerate_booking_html(movie, booking_shows):
            print(f"[{slug}] Patched booking.html with {len(booking_shows)} real show(s).")
    return added_rows, new_cities, removed_cities


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    movies = load_registry()
    movies = [m for m in movies if m.get("cinemaxxSlug")]
    if argv:
        wanted = set(argv)
        movies = [m for m in movies if m["slug"] in wanted]
    if not movies:
        print("No movies to scan (none with `cinemaxxSlug` in the registry).")
        return
    print(f"Cinemaxx agent — scanning {len(movies)} movie(s) across "
          f"{len(CITIES)} Cinemaxx cities...")
    for m in movies:
        run_movie(m)


if __name__ == "__main__":
    main()
