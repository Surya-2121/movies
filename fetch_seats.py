"""
Automated seat count fetcher for getmyticket.de movies.
Auto-discovers all shows from the movies page, fetches seat availability,
calculates revenue, injects data into dashboard, and opens browser.
"""
import json
import re
import time
import urllib.request
import base64
import sys
import os
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "seat_data.json")
APP_JS = os.path.join(SCRIPT_DIR, "app.js")
INDEX_HTML = os.path.join(SCRIPT_DIR, "index.html")

MOVIES_URL = "https://www.getmyticket.de/movies.php"


def fetch_html(url):
    """Fetch HTML page."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
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


def main():
    print("=" * 55)
    print("  getmyticket.de - Seat Count Fetcher")
    print("=" * 55)
    print()

    # Step 1: Auto-discover shows
    shows, movie_title = discover_shows()
    if not shows:
        print("  No shows found. Exiting.")
        return

    print()

    # Step 2: Fetch seat counts for each show
    print(f"[2/2] Fetching seat counts for {len(shows)} show(s)...")
    results = []
    total_seats = 0
    total_booked = 0

    for i, show in enumerate(shows, 1):
        url = (
            f"https://www.getmyticket.de/showbookings.php"
            f"?id={show['showId']}"
            f"&time={urllib.request.quote(show['timeParam'])}"
            f"&mdate={show['mdate']}"
        )

        sys.stdout.write(f"  [{i}/{len(shows)}] {show['city']}...")
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
        print(f"\r  [{i}/{len(shows)}] {show['city']}{' - ' + cinema if cinema else ''}")
        print(
            f"           Seats: {counts['totalSeats']} | Sold: {counts['sold']} "
            f"| Available: {counts['available']} | {pct}%"
        )
        print(f"           Revenue: €{counts['revenue']} | Breakdown: {counts['soldByPrice']}")

        time.sleep(0.5)

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
        import re as _re
        _m = _re.search(r"\]\s*;?\s*\n", code[shows_start:])
        shows_end = shows_start + _m.end() if _m else code.index("]", shows_start + 20) + 1
        shows_js = "const showsData = [\n"
        for r in results:
            prices_obj = ", ".join(
                f"'row{k}': {v}" for k, v in sorted(r["rowPrices"].items(), key=lambda x: int(x[0]))
            )
            shows_js += f"""  {{
    id: {r['showId']},
    city: {json.dumps(r['city'])},
    cinema: {json.dumps(r['cinema'])},
    date: {json.dumps(r['date'])},
    time: {json.dumps(r['time'])},
    language: "Telugu",
    totalSeats: {r['totalSeats']},
    ticketsBooked: {r['sold']},
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

    # Update HTML title
    try:
        with open(INDEX_HTML, "r", encoding="utf-8") as f:
            html_code = f.read()

        # Update the h1 title
        html_code = re.sub(
            r"<h1>[^<]+</h1>",
            f"<h1>{movie_title}</h1>",
            html_code,
        )
        # Update page title
        html_code = re.sub(
            r"<title>[^<]+</title>",
            f"<title>{movie_title} - Ticket Dashboard</title>",
            html_code,
        )

        with open(INDEX_HTML, "w", encoding="utf-8") as f:
            f.write(html_code)
    except Exception:
        pass

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

    # Open in browser
    webbrowser.open(f"file:///{INDEX_HTML}")
    print(f"\n  Opening dashboard in browser...")


if __name__ == "__main__":
    main()
