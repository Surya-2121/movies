"""
Scrape 3 Realms Entertainment for current Telugu movie shows in Germany.
Updates booking.html with the latest show data.

Usage: py scripts/update_shows.py
"""

import re
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime

BASE_URL = "https://3realmsentertainment.com"

# Map 3 Realms movie slugs/IDs to our site's movie slugs and info.
# Add new movies here as they appear on 3 Realms.
# NOTE: Dacoit has ended; Peddi shows are not on 3 Realms (booked via
# Zineflix/cinetixx/kinotickets directly). MOVIE_MAP is intentionally
# empty so this scraper does not overwrite the hand-maintained
# booking.html — see fetch_peddi_seats.py for the current movie.
# Add a new entry here only when a future movie appears on 3 Realms.
MOVIE_MAP = {
    # Example:
    # "moviename": { "slug": "moviename", "title": "...", "genre": "...", "language": "Telugu", "page": "...-movie.html" }
}


def find_movie_pages():
    """Discover all movie pages from 3 Realms."""
    movie_urls = set()
    for path in ["/latest-movies", "/up-movies", "/"]:
        try:
            resp = requests.get(BASE_URL + path, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if re.match(r"^/movie/\d+/?$", href):
                    movie_urls.add(href.rstrip("/") + "/")
        except Exception as e:
            print(f"  Warning: could not fetch {path}: {e}")
    return sorted(movie_urls)


def parse_showtime_text(text):
    """Parse '​April 11, 2026, 4:50 p.m.' into date and time strings."""
    text = text.strip()
    # Try parsing various formats
    for fmt in [
        "%B %d, %Y, %I:%M %p.",
        "%B %d, %Y, %I:%M %p",
        "%B %d, %Y, %I:%M%p.",
        "%B %d, %Y, %I:%M%p",
        "%B %d, %Y, %I %p.",
        "%B %d, %Y, %I %p",
    ]:
        cleaned = text.replace("a.m.", "AM").replace("p.m.", "PM").replace("a.m", "AM").replace("p.m", "PM")
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            continue

    # Fallback: try regex with minutes
    m = re.search(r"(\w+ \d+, \d{4}),?\s*(\d+:\d+)\s*(a\.?m\.?|p\.?m\.?)", text, re.I)
    if m:
        date_str, time_str, ampm = m.groups()
        ampm_clean = ampm.replace(".", "").upper()
        try:
            dt = datetime.strptime(f"{date_str} {time_str} {ampm_clean}", "%B %d, %Y %I:%M %p")
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            pass

    # Fallback: try regex without minutes (e.g. "5 p.m.")
    m = re.search(r"(\w+ \d+, \d{4}),?\s*(\d+)\s*(a\.?m\.?|p\.?m\.?)", text, re.I)
    if m:
        date_str, hour_str, ampm = m.groups()
        ampm_clean = ampm.replace(".", "").upper()
        try:
            dt = datetime.strptime(f"{date_str} {hour_str} {ampm_clean}", "%B %d, %Y %I %p")
            return dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M")
        except ValueError:
            pass

    print(f"  Warning: could not parse showtime '{text}'")
    return None, None


def scrape_movie_page(url):
    """Scrape a single movie page for title and shows."""
    resp = requests.get(BASE_URL + url, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Get movie title
    title_el = soup.find("h1") or soup.find("h2")
    title = title_el.get_text(strip=True) if title_el else "Unknown"

    shows = []
    for theatre in soup.find_all("div", class_="theatre-column"):
        cinema_el = theatre.find("h4")
        cinema = cinema_el.get_text(strip=True) if cinema_el else "Unknown"

        # Get city from "Location: CityName"
        city = ""
        for p in theatre.find_all("p"):
            text = p.get_text(strip=True)
            if text.lower().startswith("location:"):
                city = text.split(":", 1)[1].strip()
                break

        # Get showtimes — <a> wraps <li> on 3 Realms
        showtimes_div = theatre.find("div", class_="showtimes")
        if showtimes_div:
            for a in showtimes_div.find_all("a", href=True):
                date, time = parse_showtime_text(a.get_text())
                if date and time:
                    shows.append({
                        "city": city,
                        "cinema": cinema,
                        "date": date,
                        "time": time,
                        "subtitle": "English Subtitles",
                        "bookingUrl": a["href"]
                    })

    return title, shows


def match_movie(title):
    """Match a 3 Realms movie title to our MOVIE_MAP."""
    title_lower = title.lower()
    for key, info in MOVIE_MAP.items():
        if key in title_lower:
            return info
    return None


def update_booking_html(all_movies):
    """Update the movies object in booking.html."""
    booking_path = "booking.html"
    with open(booking_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Build the new movies JS object
    entries = []
    for movie in all_movies:
        shows_json = json.dumps(movie["shows"], indent=10, ensure_ascii=False)
        # Clean up indentation
        shows_json = shows_json.replace("\n          ", "\n            ")
        entry = f"""      {movie["slug"]}: {{
        title: "{movie["title"]}",
        genre: "{movie["genre"]}",
        language: "{movie["language"]}",
        page: "{movie["page"]}",
        shows: {shows_json}
      }}"""
        entries.append(entry)

    movies_block = "{\n" + ",\n".join(entries) + "\n    }"

    # Replace the movies object in the HTML
    pattern = r"(const movies = ){[\s\S]*?}(\s*;)"
    # More robust: find from 'const movies = {' to the matching '};'
    start_marker = "const movies = {"
    start_idx = html.find(start_marker)
    if start_idx == -1:
        print("Error: could not find 'const movies = {' in booking.html")
        return False

    # Find the matching closing brace by counting braces
    brace_start = html.index("{", start_idx)
    depth = 0
    end_idx = brace_start
    for i in range(brace_start, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    new_html = html[:start_idx] + "const movies = " + movies_block + html[end_idx + 1:]

    with open(booking_path, "w", encoding="utf-8") as f:
        f.write(new_html)

    return True


def main():
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

    print("Discovering movies from 3 Realms Entertainment...")
    movie_urls = find_movie_pages()
    print(f"  Found {len(movie_urls)} movie page(s): {movie_urls}")

    all_movies = []
    for url in movie_urls:
        print(f"\nScraping {BASE_URL}{url}...")
        title, shows = scrape_movie_page(url)
        print(f"  Title: {title}")
        print(f"  Shows: {len(shows)}")

        movie_info = match_movie(title)
        if movie_info:
            movie_info = dict(movie_info)  # copy
            movie_info["shows"] = shows
            all_movies.append(movie_info)
            print(f"  Matched to: {movie_info['slug']}")
        else:
            print(f"  No match in MOVIE_MAP for '{title}' — skipping.")
            print(f"  To add it, add an entry to MOVIE_MAP in this script.")

    if not all_movies:
        print("\nNo movies matched. Nothing to update.")
        return

    print(f"\nUpdating booking.html with {len(all_movies)} movie(s)...")
    if update_booking_html(all_movies):
        print("Done! booking.html updated successfully.")
        print("\nShows summary:")
        for m in all_movies:
            print(f"  {m['title']}: {len(m['shows'])} show(s)")
            for s in m["shows"]:
                print(f"    {s['date']} {s['time']} — {s['cinema']}, {s['city']}")
    else:
        print("Failed to update booking.html.")


if __name__ == "__main__":
    main()
