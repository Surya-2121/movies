"""
Auto-discover The Paradise (movieId=77) shows from Zineflix.

Zineflix's SPA at zineflix.com is powered by
`https://backendzineflex.teammatrixmantra.com/api/v1`.

The `/movie/places/show-cities/Paradise/77` page reads from
GET /othertheatre — a flat list of {theatreName, city (uuid), redirectLink}
records. Zineflix stores no dates/times for these external theatres, so
each listing surfaces the cinema as an "external booking" card that
deep-links back to the actual cinema's own booking page.

Any real, hand-curated showtime lives in data/paradise_manual.json and
takes precedence: if a manual entry shares the same bookingUrl as a
Zineflix-discovered theatre, the Zineflix placeholder is dropped in
favor of the manual (dated, timed) entry.

Flow:
  1. GET /cities  -> {uuid: cityName}
  2. GET /othertheatre  -> filter movieId=77
  3. Build one placeholder show per theatre (today's date, "External"
     time), with city resolved via /cities.
  4. Load data/paradise_manual.json.
  5. Drop Zineflix placeholders whose bookingUrl already appears in
     the manual list; keep everything else.
  6. Write data/paradise_shows.json.
  7. Patch ONLY the `paradise:` sub-entry inside `const movies = {...}`
     in booking.html — never touch other movies.

Usage:  py scripts/discover_paradise_shows.py
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, date, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MANUAL_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_manual.json")
SHOWS_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_shows.json")
BOOKING_HTML = os.path.join(PROJECT_ROOT, "booking.html")

API_BASE = "https://backendzineflex.teammatrixmantra.com/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Placeholder time for Zineflix theatres that carry no showtime data.
# Users see "See cinema" in the subtitle and click through to the real
# booking backend for exact dates/times.
PLACEHOLDER_TIME = "20:00"
PLACEHOLDER_SUBTITLE = "See cinema for showtimes"

MOVIE = {
    "slug": "paradise",
    "title": "The Paradise",
    "genre": "Period Action-Drama",
    "language": "Telugu",
    "page": "paradise-movie.html",
    "zineflixMovieId": 77,
}


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


def clean_theatre_name(raw):
    """Zineflix names come in ALL CAPS with trailing city tokens and stray
    encoding artefacts. Return a legible label."""
    if not raw:
        return ""
    name = raw.strip()
    # Drop encoding replacement chars, collapse whitespace.
    name = name.replace("�", "").replace("  ", " ").strip()
    return re.sub(r"\s+", " ", name)


def fetch_zineflix_theatres():
    """One placeholder show per Zineflix theatre entry for Paradise."""
    theatres = fetch_json(f"{API_BASE}/othertheatre").get("data") or []
    paradise = [t for t in theatres if t.get("movieId") == MOVIE["zineflixMovieId"]]
    print(f"  Zineflix /othertheatre -> {len(theatres)} total, {len(paradise)} for Paradise")
    if not paradise:
        return []

    cities = get_cities()
    placeholder_date = date.today().isoformat()
    out = []
    for t in paradise:
        raw_name = t.get("theatreName") or ""
        redirect = t.get("redirectLink") or ""
        city_uuid = t.get("city") or ""
        city_name = cities.get(city_uuid) or "Unknown"
        cinema_name = clean_theatre_name(raw_name) or f"Zineflix theatre {t.get('id')}"
        if not redirect:
            print(f"  [skip] {cinema_name}: no redirectLink")
            continue
        out.append({
            "city": city_name,
            "cinema": cinema_name,
            "date": placeholder_date,
            "time": PLACEHOLDER_TIME,
            "subtitle": PLACEHOLDER_SUBTITLE,
            "bookingUrl": redirect,
        })
    return out


def load_manual():
    if not os.path.exists(MANUAL_FILE):
        return []
    try:
        data = json.load(open(MANUAL_FILE, encoding="utf-8"))
    except Exception as e:
        print(f"  [warn] {MANUAL_FILE} unreadable: {e}")
        return []
    shows = data.get("shows") or []
    print(f"  {MANUAL_FILE} -> {len(shows)} manual show(s)")
    return shows


def merge_prefer_manual(zineflix, manual):
    """Manual entries always win. If a Zineflix placeholder points at the
    same bookingUrl as any manual entry, drop the placeholder."""
    manual_urls = {m.get("bookingUrl") for m in manual if m.get("bookingUrl")}
    filtered = [z for z in zineflix if z.get("bookingUrl") not in manual_urls]
    return filtered + manual


# --------------------------------------------------------------------
# booking.html regeneration — patch ONLY the paradise: sub-entry
# --------------------------------------------------------------------

def regenerate_booking_html(movie, shows):
    """Rewrite ONLY the `<slug>: { ... }` sub-entry inside `const movies = {...}`,
    preserving every other movie key. Mirrors the peddi discovery script's
    regenerate_booking_html so we never touch unrelated movies."""
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
# Main
# --------------------------------------------------------------------

def main():
    print("== Zineflix /othertheatre scrape ==")
    try:
        zineflix_shows = fetch_zineflix_theatres()
    except Exception as e:
        print(f"  Zineflix scrape failed: {e}")
        zineflix_shows = []
    for s in zineflix_shows:
        print(f"    {s['city']:15} | {s['cinema']:40} | {s['bookingUrl']}")

    print("\n== Manual overrides ==")
    manual_shows = load_manual()

    all_shows = merge_prefer_manual(zineflix_shows, manual_shows)
    all_shows.sort(key=lambda s: (s["date"], s["time"], s["city"], s["cinema"]))
    print(f"\nTotal Paradise shows: {len(all_shows)} "
          f"({len(zineflix_shows) - (len(zineflix_shows + manual_shows) - len(all_shows))} zineflix + "
          f"{len(manual_shows)} manual)")

    os.makedirs(os.path.dirname(SHOWS_FILE), exist_ok=True)
    out = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "movie": MOVIE["slug"],
        "totalShows": len(all_shows),
        "shows": all_shows,
    }
    with open(SHOWS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {SHOWS_FILE}")

    if regenerate_booking_html(MOVIE, all_shows):
        print(f"Updated {BOOKING_HTML}")
    else:
        print(f"{BOOKING_HTML} unchanged")


if __name__ == "__main__":
    main()
