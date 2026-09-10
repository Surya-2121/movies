"""
Auto-discover The Paradise (movieId=77) cinemas from Zineflix.

Zineflix's `/movie/places/show-cities/Paradise/77` page reads
GET /othertheatre — a flat {theatreName, city (uuid), redirectLink}
list. Zineflix carries no dates/times for these external theatres, so
this scraper does NOT fabricate placeholder showtimes. Instead:

  - Every Zineflix cinema is written to data/paradise_zineflix.json
    (a reference roster of "cities where Paradise is playing"), plus
    printed to stdout so the operator knows which cinemas still need
    real showtimes.
  - Only entries in data/paradise_manual.json (real, dated, timed
    shows the operator has hand-curated) land in booking.html.

To surface a Zineflix-listed city on the booking page, add a real
showtime to data/paradise_manual.json with the same bookingUrl (or
any URL you prefer). The Zineflix roster is diff'd against the manual
list to flag cinemas still awaiting dates.

Flow:
  1. GET /cities  -> {uuid: cityName}
  2. GET /othertheatre  -> filter movieId=77
  3. Write data/paradise_zineflix.json (Zineflix roster).
  4. Load data/paradise_manual.json (real shows) into booking.html
     via a surgical patch of the `paradise:` sub-entry.
  5. Print which Zineflix cinemas still lack a manual showtime.

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
ZINEFLIX_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_zineflix.json")
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
    """Return the reference roster of Zineflix-listed Paradise cinemas.

    No dates/times — Zineflix doesn't carry them for external theatres.
    Each entry: {city, cinema, bookingUrl}.
    """
    theatres = fetch_json(f"{API_BASE}/othertheatre").get("data") or []
    paradise = [t for t in theatres if t.get("movieId") == MOVIE["zineflixMovieId"]]
    print(f"  Zineflix /othertheatre -> {len(theatres)} total, {len(paradise)} for Paradise")
    if not paradise:
        return []

    cities = get_cities()
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
    print("== Zineflix /othertheatre roster ==")
    try:
        zineflix_cinemas = fetch_zineflix_theatres()
    except Exception as e:
        print(f"  Zineflix scrape failed: {e}")
        zineflix_cinemas = []
    for c in zineflix_cinemas:
        print(f"    {c['city']:15} | {c['cinema']:45} | {c['bookingUrl']}")

    print("\n== Manual (real, dated/timed) shows ==")
    manual_shows = load_manual()

    # Persist the Zineflix roster for reference.
    os.makedirs(os.path.dirname(ZINEFLIX_FILE), exist_ok=True)
    with open(ZINEFLIX_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
            "movie": MOVIE["slug"],
            "totalCinemas": len(zineflix_cinemas),
            "cinemas": zineflix_cinemas,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {ZINEFLIX_FILE} ({len(zineflix_cinemas)} cinemas)")

    # Report which Zineflix cinemas still lack a manual (dated) show.
    manual_urls = {m.get("bookingUrl") for m in manual_shows if m.get("bookingUrl")}
    missing = [c for c in zineflix_cinemas if c["bookingUrl"] not in manual_urls]
    if missing:
        print(f"\n== {len(missing)} Zineflix cinema(s) awaiting real showtimes ==")
        for c in missing:
            print(f"    {c['city']:15} | {c['cinema']:45} | {c['bookingUrl']}")
        print("  Add each with real date/time to data/paradise_manual.json to publish.")

    # Only manual (real) shows go into booking.html.
    booking_shows = sorted(
        manual_shows,
        key=lambda s: (s.get("date", ""), s.get("time", ""), s.get("city", ""), s.get("cinema", ""))
    )
    if regenerate_booking_html(MOVIE, booking_shows):
        print(f"\nUpdated {BOOKING_HTML} with {len(booking_shows)} real show(s)")
    else:
        print(f"\n{BOOKING_HTML} unchanged ({len(booking_shows)} real show(s))")


if __name__ == "__main__":
    main()
