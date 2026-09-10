"""
Generalized Zineflix cinema-roster scraper.

Tracks any movie listed in data/zineflix_movies.json. For each movie:

  1. GET /othertheatre  ->  filter by movieId
  2. Resolve each cinema's city via /cities (uuid -> name)
  3. Write data/<slug>_zineflix.json           (roster snapshot)
  4. Diff against the prior snapshot           (detect NEW cinemas)
  5. Log any new cinemas to data/zineflix_alerts.md (append-only)
  6. Merge in data/<slug>_manual.json          (real dated/timed shows)
  7. Patch ONLY the `<slug>:` sub-entry in booking.html

The scraper never fabricates dates. Only entries in
data/<slug>_manual.json land on the booking page. Zineflix cinemas
without a manual counterpart appear in the alert log so the operator
knows what still needs real showtimes.

Usage:
  # Run for every movie in the registry (default, used by the cron)
  py scripts/discover_zineflix_shows.py

  # Run for one movie only
  py scripts/discover_zineflix_shows.py <slug>

  # Add a new movie to the registry (does NOT run the scrape)
  py scripts/discover_zineflix_shows.py add <slug> <zineflixMovieId> \\
      "<title>" "<genre>" "<language>" "<page>"

  Example:
  py scripts/discover_zineflix_shows.py add spirit 89 "Spirit" \\
      "Action / Drama" "Telugu" "spirit-movie.html"
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
REGISTRY_FILE = os.path.join(DATA_DIR, "zineflix_movies.json")
ALERTS_FILE = os.path.join(DATA_DIR, "zineflix_alerts.md")
BOOKING_HTML = os.path.join(PROJECT_ROOT, "booking.html")

API_BASE = "https://backendzineflex.teammatrixmantra.com/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


# --------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/json",
        "Origin": "https://zineflix.com",
        "Referer": "https://zineflix.com/",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_cities():
    """Return {uuid: cleaned city name}."""
    data = fetch_json(f"{API_BASE}/cities").get("data") or []
    out = {}
    for c in data:
        u = c.get("uuid")
        n = (c.get("name") or "").strip()
        if u and n:
            out[u] = n
    return out


def get_all_theatres():
    """Return the raw /othertheatre records (pre-filter)."""
    return fetch_json(f"{API_BASE}/othertheatre").get("data") or []


def clean_theatre_name(raw):
    """Zineflix names come in ALL CAPS with trailing city tokens and
    stray encoding artefacts. Return a legible label."""
    if not raw:
        return ""
    name = raw.strip().replace("ï¿½", "").replace("�", "")
    return re.sub(r"\s+", " ", name)


# --------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------

def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {"movies": []}
    with open(REGISTRY_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg):
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)


def register_movie(slug, zineflix_movie_id, title, genre, language, page):
    reg = load_registry()
    movies = reg.setdefault("movies", [])
    if any(m.get("slug") == slug for m in movies):
        print(f"[warn] '{slug}' already in registry; not adding again.")
        return
    movies.append({
        "slug": slug,
        "zineflixMovieId": int(zineflix_movie_id),
        "title": title,
        "genre": genre,
        "language": language,
        "page": page,
    })
    save_registry(reg)
    print(f"[ok] Registered '{slug}' (zineflixMovieId={zineflix_movie_id}). "
          f"Run the scraper to pick up shows.")


# --------------------------------------------------------------------
# Per-movie discovery
# --------------------------------------------------------------------

def fetch_zineflix_roster(movie, all_theatres, cities):
    """Return [{city, cinema, bookingUrl, zineflixId}] for this movie."""
    mid = movie["zineflixMovieId"]
    matches = [t for t in all_theatres if t.get("movieId") == mid]
    out = []
    for t in matches:
        raw_name = t.get("theatreName") or ""
        redirect = t.get("redirectLink") or ""
        city_uuid = t.get("city") or ""
        city_name = cities.get(city_uuid) or "Unknown"
        cinema_name = clean_theatre_name(raw_name) or f"Zineflix theatre {t.get('id')}"
        if not redirect:
            continue
        out.append({
            "city": city_name,
            "cinema": cinema_name,
            "bookingUrl": redirect,
            "zineflixId": t.get("id"),
        })
    return out


def load_prior_roster(slug):
    path = os.path.join(DATA_DIR, f"{slug}_zineflix.json")
    if not os.path.exists(path):
        return []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception:
        return []
    return d.get("cinemas") or []


def write_roster(slug, cinemas):
    path = os.path.join(DATA_DIR, f"{slug}_zineflix.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "movie": slug,
            "totalCinemas": len(cinemas),
            "cinemas": cinemas,
        }, f, indent=2, ensure_ascii=False)


def load_manual_shows(slug):
    path = os.path.join(DATA_DIR, f"{slug}_manual.json")
    if not os.path.exists(path):
        return []
    try:
        return json.load(open(path, encoding="utf-8")).get("shows") or []
    except Exception as e:
        print(f"  [warn] {path} unreadable: {e}")
        return []


def diff_rosters(prior, current):
    """Return (new_cinemas, removed_cinemas). Match by bookingUrl."""
    prior_urls = {c.get("bookingUrl") for c in prior}
    curr_urls = {c.get("bookingUrl") for c in current}
    new = [c for c in current if c.get("bookingUrl") not in prior_urls]
    removed = [c for c in prior if c.get("bookingUrl") not in curr_urls]
    return new, removed


def append_alerts(movie, new_cinemas, removed_cinemas):
    if not new_cinemas and not removed_cinemas:
        return
    header_needed = not os.path.exists(ALERTS_FILE)
    with open(ALERTS_FILE, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("# Zineflix roster alerts\n\n")
            f.write("Auto-generated by `scripts/discover_zineflix_shows.py`. "
                    "Each entry lists cinemas that appeared on (or disappeared "
                    "from) a movie's Zineflix roster since the previous scrape.\n\n")
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        f.write(f"## {ts} — {movie['title']} ({movie['slug']})\n\n")
        if new_cinemas:
            f.write(f"**{len(new_cinemas)} new cinema(s):**\n")
            for c in new_cinemas:
                f.write(f"- {c['city']} — {c['cinema']} — {c['bookingUrl']}\n")
            f.write("\n")
        if removed_cinemas:
            f.write(f"**{len(removed_cinemas)} cinema(s) removed:**\n")
            for c in removed_cinemas:
                f.write(f"- {c['city']} — {c['cinema']} — {c.get('bookingUrl','')}\n")
            f.write("\n")


# --------------------------------------------------------------------
# booking.html regeneration — patch ONLY <slug>: sub-entry
# --------------------------------------------------------------------

def regenerate_booking_html(movie, shows):
    """Rewrite ONLY the `<slug>: { ... }` sub-entry inside `const movies = {...}`,
    preserving every other movie key. If the slug isn't present yet, insert it
    just before the closing `}` of the movies object."""
    with open(BOOKING_HTML, "r", encoding="utf-8") as f:
        html = f.read()

    entries_json = json.dumps(shows, indent=10, ensure_ascii=False)
    entries_json = entries_json.replace("\n          ", "\n            ")

    slug = movie["slug"]
    body = (
        '{\n'
        '        title: "' + movie["title"] + '",\n'
        '        genre: "' + movie["genre"] + '",\n'
        '        language: "' + movie["language"] + '",\n'
        '        page: "' + movie["page"] + '",\n'
        '        shows: ' + entries_json + "\n"
        "      }"
    )

    movies_start = html.find("const movies = {")
    if movies_start == -1:
        raise RuntimeError("Cannot find 'const movies = {' in booking.html")

    slug_keys = [slug + ":", '"' + slug + '":', "'" + slug + "':"]
    slug_pos = -1
    for sk in slug_keys:
        p = html.find(sk, movies_start)
        while p != -1:
            prev = html[p - 1] if p > 0 else "\n"
            if prev in " \t\n{,":
                slug_pos = p
                break
            p = html.find(sk, p + 1)
        if slug_pos != -1:
            break

    if slug_pos == -1:
        brace_start = html.index("{", movies_start)
        depth = 0
        end = brace_start
        for i in range(brace_start, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        existing = html[brace_start + 1:end].strip()
        prefix = "," if existing else ""
        insert = f'{prefix}\n      {slug}: {body}\n    '
        new_html = html[:end] + insert + html[end:]
    else:
        brace_open = html.index("{", slug_pos)
        depth = 0
        brace_close = brace_open
        for i in range(brace_open, len(html)):
            if html[i] == "{":
                depth += 1
            elif html[i] == "}":
                depth -= 1
                if depth == 0:
                    brace_close = i
                    break
        new_html = html[:brace_open] + body + html[brace_close + 1:]

    if new_html != html:
        with open(BOOKING_HTML, "w", encoding="utf-8") as f:
            f.write(new_html)
        return True
    return False


# --------------------------------------------------------------------
# Per-movie run
# --------------------------------------------------------------------

def run_movie(movie, all_theatres, cities):
    slug = movie["slug"]
    print(f"\n=== {movie['title']} ({slug}, zineflixMovieId={movie['zineflixMovieId']}) ===")
    current = fetch_zineflix_roster(movie, all_theatres, cities)
    print(f"  Zineflix roster: {len(current)} cinema(s)")
    for c in current:
        print(f"    {c['city']:15} | {c['cinema']:45} | {c['bookingUrl']}")

    prior = load_prior_roster(slug)
    new, removed = diff_rosters(prior, current)
    if new:
        print(f"\n  NEW cinemas ({len(new)}):")
        for c in new:
            print(f"    + {c['city']} | {c['cinema']} | {c['bookingUrl']}")
    if removed:
        print(f"\n  REMOVED cinemas ({len(removed)}):")
        for c in removed:
            print(f"    - {c['city']} | {c['cinema']} | {c.get('bookingUrl','')}")

    write_roster(slug, current)
    append_alerts(movie, new, removed)

    manual_shows = load_manual_shows(slug)
    print(f"\n  Manual shows: {len(manual_shows)}")
    booking_shows = sorted(
        manual_shows,
        key=lambda s: (s.get("date", ""), s.get("time", ""),
                       s.get("city", ""), s.get("cinema", ""))
    )
    if regenerate_booking_html(movie, booking_shows):
        print(f"  Patched booking.html with {len(booking_shows)} real show(s)")
    else:
        print(f"  booking.html unchanged ({len(booking_shows)} real show(s))")

    # Also report Zineflix cinemas still waiting for a manual showtime.
    manual_urls = {m.get("bookingUrl") for m in manual_shows if m.get("bookingUrl")}
    pending = [c for c in current if c["bookingUrl"] not in manual_urls]
    if pending:
        print(f"\n  {len(pending)} Zineflix cinema(s) awaiting real showtimes:")
        for c in pending:
            print(f"    ? {c['city']:15} | {c['cinema']:45} | {c['bookingUrl']}")

    return {"new": new, "removed": removed, "pending": pending}


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def main():
    argv = sys.argv[1:]

    # `add` subcommand
    if argv and argv[0] == "add":
        if len(argv) != 7:
            print(__doc__)
            sys.exit(2)
        _, slug, mid, title, genre, language, page = argv
        register_movie(slug, mid, title, genre, language, page)
        return

    reg = load_registry()
    movies = reg.get("movies") or []
    if argv:
        wanted = set(argv)
        movies = [m for m in movies if m["slug"] in wanted]
        missing = wanted - {m["slug"] for m in movies}
        for slug in missing:
            print(f"[warn] slug '{slug}' not in registry; skipping.")

    if not movies:
        print("No movies to scrape.")
        return

    print(f"Scraping Zineflix for {len(movies)} movie(s)...")
    all_theatres = get_all_theatres()
    cities = get_cities()

    summary = {}
    for m in movies:
        summary[m["slug"]] = run_movie(m, all_theatres, cities)

    print("\n== Summary ==")
    for slug, s in summary.items():
        print(f"  {slug}: {len(s['new'])} new, {len(s['removed'])} removed, "
              f"{len(s['pending'])} pending real dates")


if __name__ == "__main__":
    main()
