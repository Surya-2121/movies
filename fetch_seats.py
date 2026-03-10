"""
Automated seat count fetcher for multiple ticketing platforms.
Discovers shows from getmyticket.de + 3realmsentertainment.com,
deduplicates, fetches seat availability from getmyticket.de and
kinotickets.express, injects data into dashboard.
"""
import json
import re
import time
import urllib.request
import urllib.parse
import base64
import sys
import os
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "seat_data.json")
APP_JS = os.path.join(SCRIPT_DIR, "app.js")
DASHBOARD_HTML = os.path.join(SCRIPT_DIR, "ustaad.html")

MOVIES_URL = "https://www.getmyticket.de/movies.php"
THREEALMS_URL = "https://3realmsentertainment.com/movie/39/"


def fetch_html(url):
    """Fetch HTML page."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    req.add_header("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
    req.add_header("Accept-Language", "en-US,en;q=0.5")
    req.add_header("Referer", "https://www.getmyticket.de/")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def discover_shows():
    """Auto-discover all shows from getmyticket.de movies page."""
    print("[1/2] Fetching movies page...")
    html = fetch_html(MOVIES_URL)
    if not html:
        print("  ERROR: Could not fetch movies page")
        return [], ""

    # Find movie title
    title_match = re.search(r"<h5[^>]*class=['\"]col_red['\"][^>]*>([^<]+)</h5>", html)
    movie_title = title_match.group(1).strip() if title_match else "Unknown Movie"
    print(f"  Movie: {movie_title}")

    # The page structure:
    # Each movie has a bookings div (id="bookings-NNN") containing:
    #   <span>CITY_NAME</span><br/>
    #   <a href='showbookings.php?id=ID&time=TIME&mdate=MDATE'>DATE - TIME</a>
    #   ...repeats for each city...

    # Find all bookings divs
    bookings_divs = re.findall(
        r"id=['\"]bookings-\d+['\"][^>]*>(.*?)</div>", html, re.DOTALL
    )

    shows = []
    for div_content in bookings_divs:
        # Split by city spans - each city section starts with a span containing city name
        # Pattern: <span style='...'>CITY</span><br/><a href='...'>DATE</a>
        city_blocks = re.split(
            r"<span\s+style='[^']*font-size[^']*'[^>]*>(?:<i[^>]*></i>)?\s*",
            div_content,
        )

        current_city = ""
        for block in city_blocks:
            if not block.strip():
                continue

            # Extract city name (first text before </span>)
            city_match = re.match(r"([^<]+)</span>", block)
            if city_match:
                current_city = city_match.group(1).strip()

            # Find all booking links in this block
            for link_match in re.finditer(
                r"href='showbookings\.php\?id=(\d+)&(?:amp;)?time=([^&]+)&(?:amp;)?mdate=([^'\"&]+)'[^>]*>([^<]+)</a>",
                block,
            ):
                show_id = int(link_match.group(1))
                time_param = link_match.group(2).replace("&amp;", "&")
                mdate = link_match.group(3)
                date_text = link_match.group(4).strip()

                # Decode mdate (base64 encoded date like "MjAyNi0wMy0xOA==" -> "2026-03-18")
                try:
                    decoded_date = base64.b64decode(mdate).decode("utf-8")
                except Exception:
                    decoded_date = ""

                # Convert 12h time to 24h
                time_24 = time_param
                tm = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", time_param, re.I)
                if tm:
                    h, m, ampm = int(tm.group(1)), tm.group(2), tm.group(3).upper()
                    if ampm == "PM" and h != 12:
                        h += 12
                    elif ampm == "AM" and h == 12:
                        h = 0
                    time_24 = f"{h:02d}:{m}"

                shows.append({
                    "showId": show_id,
                    "city": current_city,
                    "date": decoded_date,
                    "time": time_24,
                    "dateText": date_text,
                    "timeParam": time_param,
                    "mdate": mdate,
                })

    print(f"  Found {len(shows)} show(s) across {len(set(s['city'] for s in shows))} city/cities")
    for s in shows:
        print(f"    {s['city']}: {s['dateText']} (ID {s['showId']})")

    return shows, movie_title


def discover_capitol_shows():
    """Auto-discover Capitol Kornwestheim shows from kinotickets.express."""
    print("[Capitol] Discovering shows from kinotickets.express...")
    movies_url = "https://kinotickets.express/kornwestheim-capitol/movies"
    html = fetch_html(movies_url)
    if not html:
        print("  ERROR: Could not fetch kinotickets.express movies page")
        return []

    shows = []

    # Strategy: find "Ustaad" or "Bhagat Singh" in the page, then extract
    # booking links from a 5000-char window after the title.

    # Find the position of "ustaad" or "bhagat singh"
    ustaad_match = re.search(r'ustaad\s+bhagat\s+singh|bhagat\s+singh', html, re.IGNORECASE)
    if not ustaad_match:
        print("  No Ustaad section found on kinotickets.express")
        return []

    # Extract a window from the Ustaad title
    start_pos = ustaad_match.start()
    # The movie's own poster is right after the title (~300 chars).
    # Skip past it and look for the SECOND poster (next movie) as the end boundary.
    posters = list(re.finditer(r'assets/poster\?movieId=', html[start_pos:]))
    if len(posters) >= 2:
        end_pos = start_pos + posters[1].start()
    else:
        end_pos = min(start_pos + 5000, len(html))

    ustaad_chunk = html[start_pos:end_pos]

    # Extract booking links: pattern is DD.MM. ... booking/NNNNN ... HH:MM
    # Find all booking IDs in this chunk
    booking_ids = re.findall(r'/kornwestheim-capitol/booking/(\d+)', ustaad_chunk)

    if not booking_ids:
        print("  No booking IDs found in Ustaad section")
        return []

    # Extract dates (DD.MM.) and times that appear in booking link text
    # Each showtime has: day abbreviation, DD.MM., then time as link text
    # e.g., "Mi\n18.03.\n[19:30](/kornwestheim-capitol/booking/25577)"
    date_time_pairs = []
    for bid in booking_ids:
        # Look for DD.MM. before this booking ID
        pattern = re.compile(
            r'(\d{1,2})\.(\d{2})\.'  # DD.MM.
            r'.*?'                     # anything between
            r'/kornwestheim-capitol/booking/' + bid +
            r'[^>]*>.*?(\d{1,2}:\d{2})',  # time in link
            re.DOTALL
        )
        # Search backwards from booking link position
        bid_pos = ustaad_chunk.find(f'/kornwestheim-capitol/booking/{bid}')
        # Search in the 500 chars before the booking link
        search_start = max(0, bid_pos - 500)
        chunk_before = ustaad_chunk[search_start:bid_pos + 200]

        m = pattern.search(chunk_before)
        if m:
            date_time_pairs.append((m.group(1), m.group(2), m.group(3)))
        else:
            # Try just extracting time from the link
            time_match = re.search(
                r'/kornwestheim-capitol/booking/' + bid + r'[^>]*>\s*(\d{1,2}:\d{2})',
                ustaad_chunk
            )
            if time_match:
                date_time_pairs.append(("", "", time_match.group(1)))
            else:
                date_time_pairs.append(("", "", ""))

    year = "2026"
    for idx, bid in enumerate(booking_ids):
        day, month, show_time = date_time_pairs[idx] if idx < len(date_time_pairs) else ("", "", "")
        show_date = f"{year}-{month}-{int(day):02d}" if day and month else ""

        shows.append({
            "source": "kinotickets.express",
            "city": "Stuttgart",
            "cinema": "Capital Kornwestheim",
            "bookingId": int(bid),
            "date": show_date,
            "time": show_time,
            "bookingUrl": f"https://kinotickets.express/kornwestheim-capitol/sale/seats/{bid}",
        })

    if not shows:
        print("  No Capitol shows found")
    else:
        for s in shows:
            print(f"    Booking {s['bookingId']}: {s['date']} {s['time']}")

    return shows


def _extract_date_time(html, url, url_pos):
    """Extract date and time from context around a booking URL."""
    # Prefer text AFTER the URL (the <li> text), fall back to before
    after = html[url_pos:url_pos + 200]
    before = html[max(0, url_pos - 300):url_pos]

    # Search after first (date/time is usually in the link text)
    for context in [after, before]:
        date_match = re.search(r'March\s*(\d{1,2})', context, re.IGNORECASE)
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(p\.m\.|a\.m\.|PM|AM)', context, re.IGNORECASE)
        if date_match and time_match:
            show_date = f"2026-03-{int(date_match.group(1)):02d}"
            h = int(time_match.group(1))
            m = time_match.group(2) or "00"
            ampm = time_match.group(3).replace(".", "").upper()
            if ampm == "PM" and h != 12:
                h += 12
            elif ampm == "AM" and h == 12:
                h = 0
            return show_date, f"{h:02d}:{m}"

    # Partial matches
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
                if ampm == "PM" and h != 12:
                    h += 12
                elif ampm == "AM" and h == 12:
                    h = 0
                show_time = f"{h:02d}:{m}"

    return show_date, show_time


def discover_3realms_shows():
    """Discover extra shows from 3realmsentertainment.com."""
    print("[3Realms] Fetching shows page...")
    html = fetch_html(THREEALMS_URL)
    if not html:
        print("  ERROR: Could not fetch 3realms page")
        return []

    shows = []
    seen_urls = set()

    # CinemaxX city slug to display name
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

    # ─── 1. Luxor Heidelberg (ticket-cloud.de) ───
    for m in re.finditer(r'href="(https://ticket-cloud\.de/Luxor[^"]*?/Show/(\d+))"', html):
        url, show_id = m.group(1), m.group(2)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found Luxor Heidelberg: {show_date} {show_time} (Show {show_id})")
        shows.append({
            "source": "luxor",
            "city": "Heidelberg",
            "cinema": "LUXOR FILM PALAST",
            "date": show_date or "2026-03-18",
            "time": show_time or "20:30",
            "bookingUrl": url,
            "_showId": show_id,
        })

    # ─── 2. CinemaxX (cinemaxx.de) ───
    for m in re.finditer(r'href="(https?://(?:www\.)?cinemaxx\.de/kinoprogramm/([^"/]+)/[^"]*)"', html):
        url, city_slug = m.group(1), m.group(2)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        city_name = cinemaxx_city_map.get(city_slug, city_slug.replace("-", " ").title())
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        print(f"  Found CinemaxX {city_name}: {show_date} {show_time}")
        shows.append({
            "source": "cinemaxx",
            "city": city_name,
            "cinema": f"CinemaxX {city_name}",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
            "_slug": city_slug,
        })

    # ─── 3. Berlin Cineplex / ticketverz.com ───
    for m in re.finditer(r'href="(https?://(?:www\.)?ticketverz\.com/[^"]+)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        # Try to extract city from URL or nearby text
        context = html[max(0, url_pos - 300):url_pos + 300]
        city_match = re.search(r'Berlin|Neuköln|Neukölln|Neukoln', context, re.IGNORECASE)
        city_name = "Berlin" if city_match else "Berlin"
        cinema_match = re.search(r'Cineplex|Cinema', context, re.IGNORECASE)
        cinema_name = cinema_match.group(0) if cinema_match else "Cineplex"
        print(f"  Found {cinema_name} {city_name}: {show_date} {show_time}")
        shows.append({
            "source": "ticketverz",
            "city": city_name,
            "cinema": f"{cinema_name} {city_name}",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 4. Cincinnati Kino München (cincinnati-muenchen.de) ───
    # Same URL can appear multiple times for different dates
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
            "source": "cincinnati",
            "city": "München",
            "cinema": "Cincinnati Kino",
            "date": show_date or "2026-03-19",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    # ─── 5. Any other booking links (generic catch-all) ───
    # Catch kinoheld.de, kinopolis, UCI, etc. if they appear in future
    for m in re.finditer(r'href="(https?://(?:www\.)?kinoheld\.de/[^"]+)"', html):
        url = m.group(1)
        if url in seen_urls:
            continue
        seen_urls.add(url)
        url_pos = m.start()
        show_date, show_time = _extract_date_time(html, url, url_pos)
        context = html[max(0, url_pos - 300):url_pos + 300]
        print(f"  Found kinoheld show: {show_date} {show_time} — {url}")
        shows.append({
            "source": "kinoheld",
            "city": "Unknown",
            "cinema": "Unknown",
            "date": show_date or "2026-03-18",
            "time": show_time or "19:30",
            "bookingUrl": url,
        })

    print(f"  Found {len(shows)} extra show(s) from 3realms")
    return shows


# ─── CinemaxX API ──────────────────────────────────────


def fetch_json(url, headers=None):
    """Fetch JSON from URL."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode("utf-8")), resp
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None, None


def get_cinemaxx_token():
    """Get a microservices JWT token from CinemaxX."""
    req = urllib.request.Request("https://www.cinemaxx.de/", method="GET")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        for header in resp.headers.get_all("Set-Cookie") or []:
            if "microservicesToken=" in header:
                return header.split("microservicesToken=")[1].split(";")[0]
    except Exception:
        pass
    return None


def fetch_cinemaxx_shows(cinemaxx_cities):
    """Fetch seat data for CinemaxX shows via their API."""
    if not cinemaxx_cities:
        return []

    print(f"\n[CinemaxX API] Fetching seat data for {len(cinemaxx_cities)} city/cities...")
    token = get_cinemaxx_token()
    if not token:
        print("  ERROR: Could not get CinemaxX token")
        return []

    # Get all CinemaxX cinemas
    data, _ = fetch_json(
        "https://www.cinemaxx.de/api/microservice/showings/cinemas",
        headers={"Authorization": f"Bearer {token}"},
    )
    if not data:
        print("  ERROR: Could not get cinema list")
        return []

    # Build cinema lookup by city slug (normalized: no umlauts)
    def _norm_slug(s):
        return s.lower().replace(" ", "-").replace("ü", "u").replace("ö", "o").replace("ä", "a").replace("ß", "ss")

    cinema_lookup = {}
    for group in data.get("result", []):
        for c in group.get("cinemas", []):
            slug = _norm_slug(c.get("cinemaName", ""))
            cinema_lookup[slug] = {
                "cinemaId": c["cinemaId"],
                "name": c.get("fullName", ""),
                "city": c.get("cinemaName", ""),
            }

    # Find the Ustaad film ID by checking a cinema that has our show
    film_id = None
    # Use Bielefeld (known to have Ustaad) or first available cinemaxx city
    search_cinema = cinema_lookup.get("bielefeld") or cinema_lookup.get(
        cinemaxx_cities[0].get("_slug", "")) or next(iter(cinema_lookup.values()), None)

    if search_cinema:
        films_data, _ = fetch_json(
            f"https://www.cinemaxx.de/api/microservice/showings/cinemas/{search_cinema['cinemaId']}/films",
            headers={"Authorization": f"Bearer {token}"},
        )
        if films_data:
            for f in films_data.get("result", []):
                fid = f.get("filmId", "")
                try:
                    show_data, _ = fetch_json(
                        f"https://www.cinemaxx.de/api/microservice/showings/cinemas/{search_cinema['cinemaId']}/films/{fid}/showings",
                        headers={"Authorization": f"Bearer {token}"},
                    )
                    if show_data:
                        for s in show_data.get("result", []):
                            title = s.get("title", "") or f.get("title", "")
                            poster = s.get("posterUrl", "")
                            if ("ustaad" in title.lower() or "bhagat" in title.lower()
                                    or "ustaad" in poster.lower()):
                                film_id = fid
                                print(f"  Found film: {title or 'Ustaad'} (ID: {film_id})")
                                break
                    if film_id:
                        break
                except Exception:
                    continue
                time.sleep(0.2)

    if not film_id:
        print("  Could not find Ustaad film ID on CinemaxX")
        return []

    results = []
    for i, city_info in enumerate(cinemaxx_cities, 1):
        city_slug = city_info.get("_slug", "")
        cinema = cinema_lookup.get(city_slug)
        if not cinema:
            # Try fuzzy match
            for slug, c in cinema_lookup.items():
                if city_slug in slug or slug in city_slug:
                    cinema = c
                    break

        if not cinema:
            print(f"  [{i}/{len(cinemaxx_cities)}] {city_info['city']} - Cinema not found in API")
            continue

        # Get sessions
        show_data, _ = fetch_json(
            f"https://www.cinemaxx.de/api/microservice/showings/cinemas/{cinema['cinemaId']}/films/{film_id}/showings",
            headers={"Authorization": f"Bearer {token}"},
        )
        if not show_data or not show_data.get("result"):
            print(f"  [{i}/{len(cinemaxx_cities)}] {city_info['city']} - No sessions")
            continue

        for session in show_data.get("result", []):
            session_id = session["id"]
            show_time_raw = session.get("showTime", "")
            price_str = session.get("formattedPrice", "")
            screen = session.get("screenName", "")

            # Parse price (e.g., "14,99 €" -> 14.99)
            price_num = 0
            pm = re.search(r"(\d+)[,.](\d+)", price_str)
            if pm:
                price_num = float(f"{pm.group(1)}.{pm.group(2)}")

            # Parse datetime
            show_date = show_time_raw[:10] if len(show_time_raw) >= 10 else ""
            show_time = show_time_raw[11:16] if len(show_time_raw) >= 16 else ""

            # Get seat data
            seat_data, _ = fetch_json(
                f"https://www.cinemaxx.de/api/microservice/booking/session/{cinema['cinemaId']}/{session_id}/seats",
                headers={"Authorization": f"Bearer {token}"},
            )

            total_seats = 0
            sold = 0
            available = 0
            if seat_data:
                result_data = seat_data.get("result", {})
                for row in result_data.get("seatRows", []):
                    for col in row.get("columns", []):
                        if col is None:
                            continue
                        status = col.get("seatStatus", -1)
                        total_seats += 1
                        if status == 0:
                            available += 1
                        elif status == 1:
                            sold += 1

            revenue = round(sold * price_num)

            # Build dateText
            if show_date:
                from datetime import datetime as _dt
                try:
                    dt = _dt.strptime(show_date, "%Y-%m-%d")
                    h, m = show_time.split(":")
                    h = int(h)
                    ampm = "AM" if h < 12 else "PM"
                    h12 = h if h <= 12 else h - 12
                    if h12 == 0:
                        h12 = 12
                    date_text = f"{dt.strftime('%a')} {dt.day} {dt.strftime('%b')} {dt.year} - {h12:02d}:{m} {ampm}"
                except Exception:
                    date_text = f"{show_date} - {show_time}"
            else:
                date_text = ""

            pct = round(sold / total_seats * 100, 1) if total_seats > 0 else 0
            print(f"  [{i}/{len(cinemaxx_cities)}] {city_info['city']} - {screen}")
            print(f"           Seats: {total_seats} | Sold: {sold} | Available: {available} | {pct}% | €{price_num}/ticket")

            results.append({
                "showId": f"cinemaxx-{cinema['cinemaId']}-{session_id}",
                "city": city_info["city"],
                "cinema": f"CinemaxX {city_info['city']}",
                "date": show_date,
                "time": show_time,
                "dateText": date_text,
                "totalSeats": total_seats,
                "sold": sold,
                "available": available,
                "unavailable": 0,
                "revenue": revenue,
                "soldByPrice": {str(price_num): sold} if sold > 0 else {},
                "rowPrices": {},
                "source": "cinemaxx",
                "bookingUrl": city_info.get("bookingUrl", ""),
                "ticketPrice": price_num,
            })

        time.sleep(0.3)

    return results


def get_cinema_name(html, city):
    """Extract cinema/theater name from the booking page title."""
    # Title format: "Get My Ticket - MovieName CityName TheaterName"
    m = re.search(r"<title>([^<]+)</title>", html)
    if m:
        title = m.group(1).strip()
        title = re.sub(r"^Get My Ticket\s*-\s*", "", title)
        city_idx = title.lower().find(city.lower())
        if city_idx >= 0:
            raw = title[city_idx + len(city):].strip()
            if raw:
                # Clean up: "cinecitta_kino6" -> "Cinecittà Kino 6"
                raw = raw.replace("_", " ")
                raw = re.sub(r"(?i)cinecitta", "Cinecittà", raw)
                # Add space before numbers: "kino6" -> "kino 6"
                raw = re.sub(r"([a-zA-Zà])(\d)", r"\1 \2", raw)
                # Title-case each word
                raw = " ".join(w.capitalize() if w.lower() in ("kino", "saal") else w for w in raw.split())
                return raw.strip()
    return ""


def count_seats(html):
    """Count available/sold seats and calculate revenue per row."""
    row_prices = {}
    for m in re.findall(r"id='gcharges(\d+)' value='(\d+)'", html):
        row_prices[int(m[0])] = int(m[1])

    row_sections = re.split(r"id='head(\d+)'", html)

    available = 0
    sold = 0
    unavailable = 0
    revenue = 0
    sold_by_price = {}

    for i in range(1, len(row_sections), 2):
        row_num = int(row_sections[i])
        section = row_sections[i + 1] if i + 1 < len(row_sections) else ""
        next_head = re.search(r"id='head\d+'", section)
        if next_head:
            section = section[: next_head.start()]

        price = row_prices.get(row_num, 0)
        # Count only seats in td.seat cells (available/bookable seats)
        row_avail = len(re.findall(r"class='seat'", section))
        # Count sold seats (sold.png images, these are in plain <td> without class='seat')
        row_sold = len(re.findall(r"sold\.png", section))

        available += row_avail
        sold += row_sold
        revenue += row_sold * price

        if row_sold > 0:
            sold_by_price[price] = sold_by_price.get(price, 0) + row_sold

    return {
        "available": available,
        "sold": sold,
        "unavailable": unavailable,
        "totalSeats": available + sold,
        "revenue": revenue,
        "soldByPrice": sold_by_price,
        "rowPrices": row_prices,
    }


# ─── kinotickets.express (Capitol Kornwestheim) ─────────


def fetch_capitol_seats(booking_id):
    """Fetch seat data from kinotickets.express booking page."""
    url = f"https://kinotickets.express/kornwestheim-capitol/booking/{booking_id}"
    html = fetch_html(url)
    if not html:
        return None

    # Seats are <button id="seat-..."> with SVG <use href="#bg-...-free-N"/> or <use href="#bg-...-sold-N"/>
    seat_refs = re.findall(r'id="seat-[^"]*"[^>]*>.*?href="#([^"]*)"', html, re.DOTALL)

    total = len(seat_refs)
    sold = sum(1 for ref in seat_refs if "sold" in ref or "occupied" in ref or "reserved" in ref)
    available = total - sold

    # Try to extract date/time from booking page if not already known
    date_str = ""
    time_str = ""
    # Look for date like "18.03.2026" or "Mittwoch, 18. März 2026"
    dm = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', html)
    if dm:
        date_str = f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}"
    # Look for time like "19:30"
    tm = re.search(r'(\d{2}:\d{2})\s*(?:Uhr|$)', html)
    if tm:
        time_str = tm.group(1)

    return {
        "totalSeats": total,
        "sold": sold,
        "available": available,
        "date": date_str,
        "time": time_str,
    }


def fetch_all_capitol_seats(capitol_shows):
    """Fetch seat data for all discovered Capitol shows."""
    if not capitol_shows:
        return []

    print(f"\n[Capitol] Fetching seat counts for {len(capitol_shows)} show(s)...")
    results = []

    for i, show in enumerate(capitol_shows, 1):
        bid = show["bookingId"]
        sys.stdout.write(f"  [{i}/{len(capitol_shows)}] Booking {bid}...")
        sys.stdout.flush()

        counts = fetch_capitol_seats(bid)

        if counts and counts["totalSeats"] > 0:
            # Use date/time from discovery, fallback to booking page
            show_date = show.get("date") or counts.get("date", "")
            show_time = show.get("time") or counts.get("time", "")

            # Build dateText
            if show_date:
                from datetime import datetime
                try:
                    dt = datetime.strptime(show_date, "%Y-%m-%d")
                    day_name = dt.strftime("%a")
                    day_num = dt.day
                    month_name = dt.strftime("%b")
                    year = dt.year
                    # Convert 24h time to 12h for dateText
                    display_time = show_time
                    if show_time and ":" in show_time:
                        h, m = show_time.split(":")
                        h = int(h)
                        ampm = "AM" if h < 12 else "PM"
                        h12 = h if h <= 12 else h - 12
                        if h12 == 0:
                            h12 = 12
                        display_time = f"{h12:02d}:{m} {ampm}"
                    date_text = f"{day_name} {day_num} {month_name} {year} - {display_time}"
                except Exception:
                    date_text = f"{show_date} - {show_time}"
            else:
                date_text = ""

            pct = round(counts["sold"] / counts["totalSeats"] * 100, 1)
            print(f"\r  [{i}/{len(capitol_shows)}] {show['city']} - {show['cinema']}")
            print(f"           Date: {show_date} {show_time} | Seats: {counts['totalSeats']} | Sold: {counts['sold']} | {pct}%")

            results.append({
                "showId": f"capitol-{bid}",
                "city": show["city"],
                "cinema": show["cinema"],
                "date": show_date,
                "time": show_time,
                "dateText": date_text,
                "totalSeats": counts["totalSeats"],
                "sold": counts["sold"],
                "available": counts["available"],
                "unavailable": 0,
                "revenue": 0,
                "soldByPrice": {},
                "rowPrices": {},
                "source": "kinotickets.express",
                "bookingUrl": show["bookingUrl"],
            })
        else:
            print(f"\r  [{i}/{len(capitol_shows)}] Booking {bid} - Failed or no seats")

        time.sleep(0.5)

    return results


# ─── Luxor Heidelberg (ticket-cloud.de) ────────────────


def fetch_luxor_seats(show_id="2331133"):
    """Fetch seat data from ticket-cloud.de PlainSeatPlan for Luxor Heidelberg."""
    print(f"\n[Luxor] Fetching seat data from ticket-cloud.de (Show {show_id})...")
    connector_url = "https://ticket-cloud.de/modules/system/systemConnector.php"

    # Step 1: Get the informationString and Plain params from the show page
    page_url = f"https://ticket-cloud.de/Luxor-Heidelberg/Show/{show_id}"
    req = urllib.request.Request(page_url)
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        page_html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching Luxor show page: {e}")
        return None

    # Extract informationString
    info_match = re.search(r"var informationString\s*=\s*'([^']+)'", page_html)
    if not info_match:
        print("  ERROR: Could not find informationString")
        return None
    info_str = info_match.group(1)

    # Step 2: First call to get block plan (extracts Plain params + SiteID)
    data = urllib.parse.urlencode({"information": info_str}).encode("utf-8")
    req = urllib.request.Request(connector_url, data=data, method="POST")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Origin", "https://ticket-cloud.de")
    req.add_header("Referer", page_url)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        block_html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching block plan: {e}")
        return None

    # Extract Plain value: "ShowID,AudiID,SeatVariantID,SiteID"
    plain_match = re.search(r'id="Plain"\s+value="([^"]+)"', block_html)
    site_match = re.search(r'id="SiteID"\s+value="([^"]+)"', block_html)
    if not plain_match:
        print("  ERROR: Could not find Plain params")
        return None

    plain_parts = plain_match.group(1).split(",")
    if len(plain_parts) < 4:
        print(f"  ERROR: Plain has unexpected format: {plain_match.group(1)}")
        return None

    show_id_p, audi_id, variant_id, site_id = plain_parts[0], plain_parts[1], plain_parts[2], plain_parts[3]

    # Step 3: Fetch PlainSeatPlan
    params = {
        "information": info_str,
        "PHPSESSIONID": "",
        "ShowID": show_id_p,
        "Method": "PlainSeatPlan",
        "AudiID": audi_id,
        "Center": site_id,
        "SeatVariantID": variant_id,
        "Width": "800",
        "Height": "600",
        "GetBlock": "",
        "GetCategory": "",
        "DeviceInfo": "Desktop",
    }
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(connector_url, data=data, method="POST")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Origin", "https://ticket-cloud.de")
    req.add_header("Referer", page_url)

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching PlainSeatPlan: {e}")
        return None

    if len(html) < 100:
        print(f"  ERROR: Response too short ({len(html)} chars)")
        return None

    # Parse seats: count by image type
    # Seat_Sold.png = sold, Seat_Loge/Parkett/Lounge.png = available
    # data-blocked="1" = blocked/unavailable, Seat_UnAvailable = not for sale
    from collections import Counter
    seat_types = Counter(re.findall(r'Seat_(\w+)\.png', html))

    sold = seat_types.get("Sold", 0)
    # Available = all seat types except Sold, UnAvailable, Wheelchair variants
    available_types = {k: v for k, v in seat_types.items()
                       if k not in ("Sold", "UnAvailable") and "Wheelchair" not in k}
    available = sum(available_types.values())
    total = sold + available

    # Also check data-blocked="1" for seats that aren't Seat_Sold but are blocked
    blocked_1 = len(re.findall(r'data-blocked="1"', html))
    # If blocked_1 > 0 and we didn't already count them as sold
    # blocked seats with non-sold images might be reserved
    if blocked_1 > 0 and blocked_1 > sold:
        # Some blocked seats might be counted in available — adjust
        pass  # The Seat_Sold image is the reliable indicator

    # Extract prices from tooltips
    prices = {}
    for pm in re.finditer(r"(\d+),(\d{2})&nbsp;", html):
        price = float(f"{pm.group(1)}.{pm.group(2)}")
        prices[price] = prices.get(price, 0) + 1

    # Calculate revenue: we need price per sold seat
    # Since we can't tell which price a sold seat had, use average price
    avg_price = sum(p * c for p, c in prices.items()) / sum(prices.values()) if prices else 0
    revenue = round(sold * avg_price) if avg_price > 0 else 0

    if total > 0:
        pct = round(sold / total * 100, 1)
        print(f"  Seats: {total} | Sold: {sold} | Available: {available} | {pct}%")
        print(f"  Seat types: {dict(seat_types)}")
        print(f"  Prices: {prices} | Revenue: ~€{revenue}")
        return {
            "totalSeats": total,
            "sold": sold,
            "available": available,
            "revenue": revenue,
            "prices": prices,
        }

    print("  ERROR: Could not parse any seats from seatplan")
    return None


def dedup_key(city, date, time_str):
    """Generate deduplication key from city+date+approximate time."""
    # Normalize city name
    city_norm = city.lower().strip()
    city_norm = city_norm.replace("ü", "u").replace("ö", "o").replace("ä", "a")
    city_norm = re.sub(r'[^a-z0-9]', '', city_norm)
    # Normalize time to HH:MM 24h
    time_norm = time_str.strip()
    tm = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', time_norm, re.I)
    if tm:
        h, m, ampm = int(tm.group(1)), tm.group(2), tm.group(3).upper()
        if ampm == "PM" and h != 12:
            h += 12
        elif ampm == "AM" and h == 12:
            h = 0
        time_norm = f"{h:02d}:{m}"
    return f"{city_norm}|{date}|{time_norm}"


def main():
    print("=" * 55)
    print("  Seat Count Fetcher (Multi-Source Auto-Discovery)")
    print("=" * 55)
    print()

    # Step 1: Auto-discover shows from getmyticket.de
    gmt_shows, movie_title = discover_shows()
    if not gmt_shows:
        print("  No getmyticket shows found.")
        gmt_shows = []
        movie_title = "Ustaad Bhagat Singh - Telugu"

    print()

    # Step 2: Auto-discover Capitol shows from kinotickets.express
    capitol_shows = discover_capitol_shows()

    print()

    # Step 3: Discover extra shows from 3realmsentertainment.com (Luxor etc.)
    extra_shows = discover_3realms_shows()

    print()

    # ─── Deduplication ─────────────────────────────────────
    # Priority: getmyticket > kinotickets.express > showtime-only
    # Key: normalized city + date + time
    seen_keys = set()

    # Track which Capitol shows are NOT duplicates of getmyticket
    for s in gmt_shows:
        key = dedup_key(s["city"], s["date"], s["time"])
        seen_keys.add(key)

    unique_capitol = []
    for s in capitol_shows:
        key = dedup_key(s["city"], s.get("date", ""), s.get("time", ""))
        if key not in seen_keys:
            unique_capitol.append(s)
            seen_keys.add(key)
        else:
            print(f"  [Dedup] Skipping Capitol {s['bookingId']} ({s['city']} {s.get('date','')}) — already in getmyticket")

    unique_extra = []
    for s in extra_shows:
        key = dedup_key(s["city"], s.get("date", ""), s.get("time", ""))
        if key not in seen_keys:
            unique_extra.append(s)
            seen_keys.add(key)
        else:
            print(f"  [Dedup] Skipping {s['source']} {s['city']} — already covered")

    print(f"\n  After dedup: {len(gmt_shows)} getmyticket + {len(unique_capitol)} Capitol + {len(unique_extra)} extra")
    print()

    # ─── Fetch seat data ───────────────────────────────────

    # Step 4: Fetch getmyticket seat counts
    print(f"[Seats] Fetching getmyticket seat counts for {len(gmt_shows)} show(s)...")
    results = []
    total_seats = 0
    total_booked = 0

    for i, show in enumerate(gmt_shows, 1):
        url = (
            f"https://www.getmyticket.de/showbookings.php"
            f"?id={show['showId']}"
            f"&time={urllib.request.quote(show['timeParam'])}"
            f"&mdate={show['mdate']}"
        )

        sys.stdout.write(f"  [{i}/{len(gmt_shows)}] {show['city']}...")
        sys.stdout.flush()

        html = fetch_html(url)
        if not html:
            print(" Failed")
            continue

        cinema = get_cinema_name(html, show["city"])
        counts = count_seats(html)

        entry = {
            "showId": show["showId"],
            "city": show["city"],
            "cinema": cinema or show["city"],
            "date": show["date"],
            "time": show["time"],
            "dateText": show["dateText"],
            "totalSeats": counts["totalSeats"],
            "sold": counts["sold"],
            "available": counts["available"],
            "unavailable": counts["unavailable"],
            "revenue": counts["revenue"],
            "soldByPrice": counts["soldByPrice"],
            "rowPrices": counts["rowPrices"],
        }
        results.append(entry)

        total_seats += counts["totalSeats"]
        total_booked += counts["sold"]

        pct = (
            round(counts["sold"] / counts["totalSeats"] * 100, 1)
            if counts["totalSeats"] > 0
            else 0
        )
        print(f"\r  [{i}/{len(gmt_shows)}] {show['city']}{' - ' + cinema if cinema else ''}")
        print(
            f"           Seats: {counts['totalSeats']} | Sold: {counts['sold']} "
            f"| Available: {counts['available']} | {pct}%"
        )
        print(f"           Revenue: €{counts['revenue']} | Breakdown: {counts['soldByPrice']}")

        time.sleep(0.5)

    # Step 5: Fetch Capitol seat counts
    capitol_results = fetch_all_capitol_seats(unique_capitol)
    for r in capitol_results:
        results.append(r)
        total_seats += r["totalSeats"]
        total_booked += r["sold"]

    # Step 6: Fetch CinemaxX seat data via API
    cinemaxx_entries = [s for s in unique_extra if s.get("source") == "cinemaxx"]
    other_extra = [s for s in unique_extra if s.get("source") != "cinemaxx"]

    if cinemaxx_entries:
        # Add city slug for API lookup (use _slug from discovery if available)
        for s in cinemaxx_entries:
            if "_slug" not in s:
                slug_map = {
                    "Frankfurt (Offenbach)": "offenbach",
                    "München": "munchen",
                }
                s["_slug"] = slug_map.get(s["city"], s["city"].lower().replace(" ", "-").replace("ü", "u").replace("ö", "o").replace("ä", "a"))

        cinemaxx_results = fetch_cinemaxx_shows(cinemaxx_entries)
        for r in cinemaxx_results:
            results.append(r)
            total_seats += r["totalSeats"]
            total_booked += r["sold"]

    # Step 7: Fetch Luxor Heidelberg seat data
    luxor_entries = [s for s in other_extra if s.get("source") == "luxor"]
    remaining_extra = [s for s in other_extra if s.get("source") != "luxor"]

    for s in luxor_entries:
        show_id = s.get("_showId", "2331133")
        luxor_data = fetch_luxor_seats(show_id)
        if luxor_data and luxor_data["totalSeats"] > 0:
            # Build dateText
            show_date = s.get("date", "")
            show_time = s.get("time", "")
            if show_date:
                from datetime import datetime as _dt2
                try:
                    dt = _dt2.strptime(show_date, "%Y-%m-%d")
                    h, m = show_time.split(":") if show_time else ("0", "00")
                    h = int(h)
                    ampm = "AM" if h < 12 else "PM"
                    h12 = h if h <= 12 else h - 12
                    if h12 == 0:
                        h12 = 12
                    date_text = f"{dt.strftime('%a')} {dt.day} {dt.strftime('%b')} {dt.year} - {h12:02d}:{m} {ampm}"
                except Exception:
                    date_text = f"{show_date} - {show_time}"
            else:
                date_text = ""

            # Build row prices from Luxor price data
            row_prices = {}
            sold_by_price = {}
            if luxor_data.get("prices"):
                for i, (price, count) in enumerate(sorted(luxor_data["prices"].items())):
                    row_prices[str(i)] = price
                # For sold_by_price we need per-price sold counts — approximate with avg
                avg_price = sum(p * c for p, c in luxor_data["prices"].items()) / sum(luxor_data["prices"].values())
                if luxor_data["sold"] > 0:
                    sold_by_price[str(avg_price)] = luxor_data["sold"]

            results.append({
                "showId": f"luxor-{show_id}",
                "city": s["city"],
                "cinema": s["cinema"],
                "date": show_date,
                "time": show_time,
                "dateText": date_text,
                "totalSeats": luxor_data["totalSeats"],
                "sold": luxor_data["sold"],
                "available": luxor_data["available"],
                "unavailable": 0,
                "revenue": luxor_data["revenue"],
                "soldByPrice": sold_by_price,
                "rowPrices": row_prices,
                "source": "luxor",
                "bookingUrl": s.get("bookingUrl", ""),
            })
            total_seats += luxor_data["totalSeats"]
            total_booked += luxor_data["sold"]
        else:
            # Failed — keep as showtime-only
            remaining_extra.append(s)
            print(f"  [Luxor] Failed to get seat data, keeping as showtime-only")

    # Remaining showtime-only entries
    for s in remaining_extra:
        print(f"  [Showtime-only] {s['city']} - {s['cinema']} ({s.get('date','')}) — no seat data")

    # Update other_extra to remaining_extra for extraShows in HTML
    other_extra = remaining_extra

    # If getmyticket failed, preserve previous getmyticket shows from existing data
    if not gmt_shows:
        try:
            with open(APP_JS, "r", encoding="utf-8") as f:
                code = f.read()
            m = re.search(r'const seatData = ({.*?});', code, re.DOTALL)
            if m:
                prev_data = json.loads(m.group(1))
                prev_shows = [s for s in prev_data.get("shows", []) if not str(s.get("showId", "")).startswith("capitol-")]
                if prev_shows:
                    print(f"\n  [Fallback] Preserving {len(prev_shows)} previous getmyticket show(s)")
                    for ps in prev_shows:
                        # Check not already in results
                        if not any(r["showId"] == ps["showId"] for r in results):
                            results.insert(0, ps)
                            total_seats += ps.get("totalSeats", 0)
                            total_booked += ps.get("sold", 0)
        except Exception as ex:
            print(f"  [Fallback] Could not load previous data: {ex}")

    # If 3realms failed, preserve Luxor from existing extraShows in HTML
    if not unique_extra and not other_extra:
        try:
            with open(DASHBOARD_HTML, "r", encoding="utf-8") as f:
                html_code = f.read()
            m = re.search(r'const extraShows = (\[.*?\]);', html_code, re.DOTALL)
            if m:
                prev_extra = json.loads(m.group(1))
                if prev_extra:
                    unique_extra = prev_extra
                    print(f"  [Fallback] Preserving {len(prev_extra)} previous extra show(s)")
        except Exception:
            pass

    # Save JSON
    total_revenue = sum(r.get("revenue", 0) for r in results)
    output = {
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "movie": movie_title,
        "totalShows": len(results),
        "totalSeats": total_seats,
        "totalBooked": total_booked,
        "totalAvailable": total_seats - total_booked,
        "overallBookingPercent": (
            round(total_booked / total_seats * 100, 1) if total_seats > 0 else 0
        ),
        "totalRevenue": total_revenue,
        "shows": results,
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

        # Also update showsData array with discovered shows
        shows_start = code.index("const showsData = [")
        # Find end: look for ] followed by optional whitespace and newline
        _m = re.search(r"\]\s*;?\s*\n", code[shows_start:])
        shows_end = shows_start + _m.end() if _m else code.index("]", shows_start + 20) + 1
        shows_js = "const showsData = [\n"
        for r in results:
            prices_obj = ", ".join(
                f"'row{k}': {v}" for k, v in sorted(r["rowPrices"].items(), key=lambda x: int(x[0]))
            )
            # Find matching show to get booking URL
            booking_url = r.get("bookingUrl", "")
            if not booking_url:
                matching = [s for s in gmt_shows if s['showId'] == r['showId']]
                if matching:
                    ms = matching[0]
                    booking_url = f"https://www.getmyticket.de/showbookings.php?id={ms['showId']}&time={urllib.request.quote(ms['timeParam'])}&mdate={ms['mdate']}"
            show_id = json.dumps(r['showId']) if isinstance(r['showId'], str) else str(r['showId'])
            shows_js += f"""  {{
    id: {show_id},
    city: {json.dumps(r['city'])},
    cinema: {json.dumps(r['cinema'])},
    date: {json.dumps(r['date'])},
    time: {json.dumps(r['time'])},
    language: "Telugu",
    totalSeats: {r['totalSeats']},
    ticketsBooked: {r['sold']},
    bookingUrl: {json.dumps(booking_url)},
    prices: {{ {prices_obj} }},
  }},
"""
        shows_js += "]"
        code = code[:shows_start] + shows_js + code[shows_end:]

        # Update movie title in header
        code = code.replace(
            "movie: \"Ustaad Bhagat Singh\"",
            f"movie: {json.dumps(movie_title)}",
        )

        with open(APP_JS, "w", encoding="utf-8") as f:
            f.write(code)
        print("\n  Data injected into app.js")
    except Exception as ex:
        print(f"\n  WARNING: Could not inject into app.js: {ex}")

    # Update dashboard HTML: title + extraShows
    try:
        with open(DASHBOARD_HTML, "r", encoding="utf-8") as f:
            html_code = f.read()

        # Update the h1 title
        html_code = re.sub(
            r"<h1[^>]*>[^<]+</h1>",
            f'<h1 class="movie-title">{movie_title}</h1>',
            html_code,
        )
        # Update page title
        html_code = re.sub(
            r"<title>[^<]+</title>",
            f"<title>{movie_title} - Ticket Dashboard</title>",
            html_code,
        )

        # Update extraShows array with showtime-only entries (those without seat data)
        extra_js_entries = []
        for s in other_extra:
            extra_js_entries.append(
                f"      {{ city: {json.dumps(s['city'], ensure_ascii=False)}, cinema: {json.dumps(s['cinema'], ensure_ascii=False)}, "
                f"date: {json.dumps(s.get('date', ''))}, time: {json.dumps(s.get('time', ''))}, "
                f"prices: '', url: {json.dumps(s.get('bookingUrl', ''))} }}"
            )
        extra_js = "[\n" + ",\n".join(extra_js_entries) + "\n    ]" if extra_js_entries else "[]"

        # Replace the extraShows array
        html_code = re.sub(
            r"const extraShows = \[.*?\];",
            f"const extraShows = {extra_js};",
            html_code,
            flags=re.DOTALL,
        )

        with open(DASHBOARD_HTML, "w", encoding="utf-8") as f:
            f.write(html_code)
        print("  Dashboard HTML updated (title + extraShows)")
    except Exception as ex:
        print(f"  WARNING: Could not update dashboard HTML: {ex}")

    print()
    print("=" * 55)
    print(f"  Movie: {movie_title}")
    print(f"  Total Shows: {len(results)}")
    print(f"  Total Seats: {total_seats}")
    print(f"  Total Booked: {total_booked}")
    print(f"  Total Available: {total_seats - total_booked}")
    print(f"  Total Revenue: €{total_revenue}")
    if total_seats > 0:
        print(
            f"  Overall Booking: {round(total_booked / total_seats * 100, 1)}%"
        )
    print("=" * 55)

    # Open in browser (skip in CI)
    if not os.environ.get("CI"):
        webbrowser.open(f"file:///{DASHBOARD_HTML}")
        print(f"\n  Opening dashboard in browser...")


if __name__ == "__main__":
    main()
