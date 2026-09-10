"""
Auto-discover The Paradise (movieId=77) shows from Zineflix.

Zineflix's SPA at zineflix.com is powered by
`https://backendzineflex.teammatrixmantra.com/api/v1`. This script:

  1. GET /shows                       -> every show record
  2. Filter to movieId == 77 (Paradise)
  3. For each unique cinemaId, GET /cinemas/getcinema/{id}
     (cached in-process) to get name + city (via cinema.location =
     "uuid-N" -> cities[uuid].name).
  4. Merge in any hand-added shows from data/paradise_manual.json.
  5. Dedupe by (date, time, city, cinema).
  6. Write data/paradise_shows.json.
  7. Patch ONLY the `paradise:` sub-entry inside `const movies = {...}`
     in booking.html — never the whole movies object.

Usage:  py scripts/discover_paradise_shows.py
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MANUAL_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_manual.json")
SHOWS_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_shows.json")
BOOKING_HTML = os.path.join(PROJECT_ROOT, "booking.html")

API_BASE = "https://backendzineflex.teammatrixmantra.com/api/v1"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

MOVIE = {
    "slug": "paradise",
    "title": "The Paradise",
    "genre": "Period Action-Drama",
    "language": "Telugu",
    "page": "paradise-movie.html",
    "zineflixMovieId": 77,
    "zineflixSlug": "Paradise",
    "subtitle": "Telugu",
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
    """Return {uuid: name} map."""
    data = fetch_json(f"{API_BASE}/cities").get("data") or []
    out = {}
    for c in data:
        u = c.get("uuid")
        n = (c.get("name") or "").strip()
        if u and n:
            out[u] = n
    return out


def get_cinema(cinema_id, cache):
    if cinema_id in cache:
        return cache[cinema_id]
    try:
        data = fetch_json(f"{API_BASE}/cinemas/getcinema/{cinema_id}").get("data") or {}
    except Exception as e:
        print(f"  [warn] cinema {cinema_id} lookup failed: {e}")
        data = {}
    cache[cinema_id] = data
    return data


def zineflix_booking_url(city_name):
    """Deep-link back to Zineflix's city booking page."""
    slug = MOVIE["zineflixSlug"]
    mid = MOVIE["zineflixMovieId"]
    # Zineflix uses the city name verbatim in the route.
    from urllib.parse import quote
    return f"https://zineflix.com/movie/booking/{slug}/{mid}/{quote(city_name)}"


def fetch_zineflix_shows():
    payload = fetch_json(f"{API_BASE}/shows")
    all_shows = payload.get("data") or []
    paradise = [s for s in all_shows if s.get("movieId") == MOVIE["zineflixMovieId"]]
    print(f"  Zineflix /shows -> {len(all_shows)} total, {len(paradise)} for Paradise")
    if not paradise:
        return []

    cities = get_cities()
    cinema_cache = {}
    out = []
    for s in paradise:
        cinema_id = s.get("cinemaId")
        start_date = s.get("startDate")
        start_time = (s.get("startTime") or "")[:5]  # "HH:MM"
        if not (cinema_id and start_date and start_time):
            print(f"  [skip] show {s.get('id')} missing fields")
            continue
        cinema = get_cinema(cinema_id, cinema_cache)
        cinema_name = (cinema.get("name") or f"Cinema {cinema_id}").strip()
        city_name = (cities.get(cinema.get("location")) or "").strip()
        if not city_name:
            # Fall back: try to lift city from the cinema name (e.g.
            # "Cinestar Frankfurt Metropolis kino 9" -> "Frankfurt").
            m = re.search(r"\b([A-ZÄÖÜ][a-zäöüß]+)\b", cinema_name)
            city_name = m.group(1) if m else "Unknown"
            print(f"  [warn] cinema {cinema_id} has no city uuid; guessed '{city_name}'")
        out.append({
            "city": city_name,
            "cinema": cinema_name,
            "date": start_date,
            "time": start_time,
            "subtitle": MOVIE["subtitle"],
            "bookingUrl": zineflix_booking_url(city_name),
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


def dedupe(shows):
    seen = set()
    out = []
    for s in shows:
        key = (s.get("date"), s.get("time"), s.get("city"), s.get("cinema"))
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


# --------------------------------------------------------------------
# booking.html regeneration — patch ONLY paradise: sub-entry
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
    print("== Zineflix scrape ==")
    try:
        zineflix_shows = fetch_zineflix_shows()
    except Exception as e:
        print(f"  Zineflix scrape failed: {e}")
        zineflix_shows = []

    print("\n== Manual overrides ==")
    manual_shows = load_manual()

    all_shows = dedupe(zineflix_shows + manual_shows)
    all_shows.sort(key=lambda s: (s["date"], s["time"], s["city"], s["cinema"]))
    print(f"\nTotal Paradise shows after merge+dedupe: {len(all_shows)}")

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
