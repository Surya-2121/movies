"""
Show discovery from 3realmsentertainment.com.
Discovers shows and booking links, injects into dashboard.
No seat counts, prices, or revenue data.
"""
import json
import re
import time
import urllib.request
import sys
import os
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "seat_data.json")
APP_JS = os.path.join(PROJECT_ROOT, "js", "app.js")
DASHBOARD_HTML = os.path.join(PROJECT_ROOT, "ustaad.html")

THREEALMS_URL = "https://3realmsentertainment.com/movie/39/"


def fetch_html(url):
    """Fetch HTML page."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "en-US,en;q=0.5")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def _extract_date_time(html, url, url_pos):
    """Extract date and time from context around a booking URL."""
    after = html[url_pos:url_pos + 200]
    before = html[max(0, url_pos - 300):url_pos]

    for context in [after, before]:
        date_match = re.search(r'March\s*(\d{1,2})', context, re.IGNORECASE)
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(p\.m\.|a\.m\.|PM|AM)', context, re.IGNORECASE)
        if date_match and time_match:
            show_date = f"2026-03-{int(date_match.group(1)):02d}"
            h = int(time_match.group(1))
            m = time_match.group(2) or "00"
            ampm = time_match.group(3).replace(".", "").upper()
            if ampm == "PM" and h < 12:
                h += 12
            elif ampm == "AM" and h == 12:
                h = 0
            return show_date, f"{h:02d}:{m}"

    show_date = ""
    show_time = ""
    for context in [after, before]:
        if not show_date:
            dm = re.search(r'March\s*(\d{1,2})', context, re.IGNORECASE)
            if dm:
                show_date = f"2026-03-{int(dm.group(1)):02d}"
        if not show_time:
            tm = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(p\.m\.|a\.m\.|PM|AM)', context, re.IGNORECASE)
            if tm:
                h = int(tm.group(1))
                m = tm.group(2) or "00"
                ampm = tm.group(3).replace(".", "").upper()
                if ampm == "PM" and h < 12:
                    h += 12
                elif ampm == "AM" and h == 12:
                    h = 0
                show_time = f"{h:02d}:{m}"

    return show_date, show_time


def discover_shows():
    """Discover all shows from 3realmsentertainment.com."""
    print("[3Realms] Fetching shows page...")
    html = fetch_html(THREEALMS_URL)
    if not html:
        print("  ERROR: Could not fetch 3realms page")
        return [], "Ustaad Bhagat Singh - Telugu"

    # Try to extract movie title
    title_match = re.search(r'<h[12][^>]*>([^<]*Ustaad[^<]*)</h', html, re.IGNORECASE)
    movie_title = title_match.group(1).strip() if title_match else "Ustaad Bhagat Singh - Telugu"

    shows = []
    seen_urls = set()

    cinemaxx_city_map = {
        "bielefeld": "Bielefeld", "bremen": "Bremen", "essen": "Essen",
        "hamburg-harburg": "Hamburg-Harburg", "hannover": "Hannover",
        "magdeburg": "Magdeburg", "offenbach": "Frankfurt (Offenbach)",
        "regensburg": "Regensburg", "trier": "Trier",
        "munchen": "München", "dresden": "Dresden",
        "berlin": "Berlin", "dortmund": "Dortmund",
        "freiburg": "Freiburg", "halle": "Halle",
        "krefeld": "Krefeld", "muelheim": "Mülheim",
        "oldenburg": "Oldenburg", "wuppertal": "Wuppertal",
    }

    # ─── 1. getmyticket.de ───
    for m in re.finditer(r'href="(https?://(?:www\.)?getmyticket\.de/showbookings[^"]+)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        context = html[max(0, url_pos - 500):url_pos + 300]
        # Extract city from nearby text
        city = "Unknown"
        for c in ["Düsseldorf", "Dusseldorf", "Nürnberg", "Erlangen", "Frankfurt", "Karben", "Hamburg"]:
            if c.lower() in context.lower():
                city = c
                break
        # Map city to cinema name
        city_cinema_map = {
            "Düsseldorf": "UFA Palast",
            "Dusseldorf": "UFA Palast",
            "Nürnberg": "Cinecitta",
            "Erlangen": "LammKino",
            "Frankfurt": "Frankfurt (Karben)",
            "Karben": "Frankfurt (Karben)",
            "Hamburg": "Hansa Filmstudios",
        }
        # Normalize Karben/Frankfurt to Frankfurt (Karben)
        if city in ("Karben", "Frankfurt"):
            city = "Frankfurt (Karben)"
        cinema = city_cinema_map.get(city, city)
        print(f"  Found {city} ({cinema}): {show_date} {show_time}")
        shows.append({
            "city": city,
            "cinema": cinema,
            "date": show_date,
            "time": show_time,
            "bookingUrl": url,
        })

    # ─── 2. Luxor Heidelberg (ticket-cloud.de) ───
    for m in re.finditer(r'href="(https://ticket-cloud\.de/Luxor[^"]*?/Show/(\d+))"', html):
        url, show_id = m.group(1), m.group(2)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found Luxor Heidelberg: {show_date} {show_time}")
        shows.append({
            "city": "Heidelberg",
            "cinema": "LUXOR FILM PALAST",
            "date": show_date or "2026-03-18",
            "time": show_time or "20:30",
            "bookingUrl": url,
        })

    # ─── 3. CinemaxX (cinemaxx.de) — only allow Essen, München, Berlin ───
    cinemaxx_allowed = {"essen", "munchen", "berlin", "dresden", "magdeburg", "regensburg"}
    for m in re.finditer(r'href="(https?://(?:www\.)?cinemaxx\.de/kinoprogramm/([^"/]+)/[^"]*)"', html):
        url, city_slug = m.group(1), m.group(2)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        if city_slug not in cinemaxx_allowed:
            continue
        city_name = cinemaxx_city_map.get(city_slug, city_slug.replace("-", " ").title())
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found CinemaxX {city_name}: {show_date} {show_time}")
        shows.append({
            "city": city_name,
            "cinema": f"CinemaxX {city_name}",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 4. Capitol Kornwestheim / Stuttgart ───
    for m in re.finditer(r'href="(https?://(?:www\.)?(?:capitol-kornwestheim\.de|kinotickets\.express/kornwestheim)[^"]*)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found Capitol Stuttgart: {show_date} {show_time}")
        shows.append({
            "city": "Stuttgart",
            "cinema": "Capital Kornwestheim",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 5. Berlin Cineplex / ticketverz.com ───
    for m in re.finditer(r'href="(https?://(?:www\.)?ticketverz\.com/[^"]+)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found Cineplex Berlin: {show_date} {show_time}")
        shows.append({
            "city": "Berlin",
            "cinema": "Cineplex Berlin",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 6. Cincinnati Kino München ───
    seen_cincinnati = set()
    for m in re.finditer(r'href="(https?://(?:www\.)?cincinnati-muenchen\.de/[^"]+)"', html):
        url = m.group(1)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        dedup = f"{show_date}|{show_time}"
        if dedup in seen_cincinnati:
            continue
        seen_cincinnati.add(dedup)
        print(f"  Found Cincinnati Kino München: {show_date} {show_time}")
        shows.append({
            "city": "München",
            "cinema": "Cincinnati Kino",
            "date": show_date or "2026-03-19",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 7. Generic catch-all (kinoheld etc.) ───
    for m in re.finditer(r'href="(https?://(?:www\.)?kinoheld\.de/[^"]+)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found kinoheld show: {show_date} {show_time}")
        shows.append({
            "city": "Unknown",
            "cinema": "Unknown",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    print(f"\n  Total: {len(shows)} show(s) from 3realms")
    return shows, movie_title


def main():
    print("=" * 55)
    print("  Show Discovery (3Realms Entertainment)")
    print("=" * 55)
    print()

    shows, movie_title = discover_shows()

    # Filter out past dates
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    shows = [s for s in shows if s.get("date", "") >= today]
    print(f"  After filtering past dates: {len(shows)} show(s)")

    if not shows:
        print("  No shows found!")
        return

    # Save JSON
    output = {
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "movie": movie_title,
        "totalShows": len(shows),
        "shows": shows,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Inject into app.js
    try:
        with open(APP_JS, "r", encoding="utf-8") as f:
            code = f.read()

        marker_start = "// SEAT_DATA_START"
        marker_end = "// SEAT_DATA_END"
        s = code.index(marker_start)
        e = code.index(marker_end) + len(marker_end)
        seat_json = json.dumps(output, ensure_ascii=False)
        code = (
            code[:s]
            + f"{marker_start}\nconst seatData = {seat_json};\n{marker_end}"
            + code[e:]
        )

        # Update showsData array
        shows_start = code.index("const showsData = [")
        _m = re.search(r"\]\s*;?\s*\n", code[shows_start:])
        shows_end = shows_start + _m.end() if _m else code.index("]", shows_start + 20) + 1
        shows_js = "const showsData = [\n"
        for i, s in enumerate(shows):
            shows_js += f"""  {{
    id: {i + 1},
    city: {json.dumps(s['city'])},
    cinema: {json.dumps(s['cinema'])},
    date: {json.dumps(s['date'])},
    time: {json.dumps(s['time'])},
    language: "Telugu",
    bookingUrl: {json.dumps(s['bookingUrl'])},
  }},
"""
        shows_js += "]"
        code = code[:shows_start] + shows_js + code[shows_end:]

        with open(APP_JS, "w", encoding="utf-8") as f:
            f.write(code)
        print("  Data injected into app.js")
    except Exception as ex:
        print(f"\n  WARNING: Could not inject into app.js: {ex}")

    # Update dashboard HTML
    try:
        with open(DASHBOARD_HTML, "r", encoding="utf-8") as f:
            html_code = f.read()

        html_code = re.sub(
            r"<h1[^>]*>[^<]+</h1>",
            f'<h1 class="movie-title">{movie_title}</h1>',
            html_code,
        )
        html_code = re.sub(
            r"<title>[^<]+</title>",
            f"<title>{movie_title} - Ticket Dashboard</title>",
            html_code,
        )

        # Clear extraShows since all shows now come from 3realms
        html_code = re.sub(
            r"const extraShows = \[.*?\];",
            "const extraShows = [];",
            html_code,
            flags=re.DOTALL,
        )

        with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
            f.write(html_code)
        print("  Dashboard HTML updated")
    except Exception as ex:
        print(f"  WARNING: Could not update dashboard HTML: {ex}")

    print()
    print("=" * 55)
    print(f"  Movie: {movie_title}")
    print(f"  Total Shows: {len(shows)}")
    print("=" * 55)

    # Open in browser (skip in CI)
    if not os.environ.get("CI"):
        webbrowser.open(f"file:///{DASHBOARD_HTML}")
        print(f"\n  Opening dashboard in browser...")


if __name__ == "__main__":
    main()
