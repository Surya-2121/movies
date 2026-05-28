"""
Auto-discover Peddi shows across all platforms and regenerate
booking.html + data/peddi_shows.json.

Flow:
  1. Hit Zineflix /othertheatre/{movieId} for the current theatre list.
  2. For each known cinema (in data/peddi_cinemas.json), call the
     platform-specific discovery function to fetch all current shows.
  3. For NEW Zineflix theatres not in the registry, try to auto-detect
     the platform from the URL pattern and add them; if the pattern is
     unknown, log and skip.
  4. Write the merged show list to data/peddi_shows.json.
  5. Regenerate the const movies = { ... } block in booking.html using
     the same brace-counting trick as update_shows.py.

Usage:  py scripts/discover_peddi_shows.py
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CINEMAS_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_cinemas.json")
SHOWS_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_shows.json")
BOOKING_HTML = os.path.join(PROJECT_ROOT, "booking.html")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def _berlin_offset_hours(dt_utc):
    """Berlin = UTC+2 from last Sun of March 01:00 UTC to last Sun of Oct 01:00 UTC,
    else UTC+1. Avoids the tzdata dependency on bare Windows installs."""
    year = dt_utc.year
    def last_sunday(month):
        d = datetime(year, month, 31, 1, 0, tzinfo=timezone.utc)
        while d.weekday() != 6:
            d -= timedelta(days=1)
        return d
    return 2 if last_sunday(3) <= dt_utc < last_sunday(10) else 1


def to_berlin(dt_utc):
    return dt_utc + timedelta(hours=_berlin_offset_hours(dt_utc))


def fetch_json(url, method="GET", data=None, extra_headers=None):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers, method=method,
                                 data=data.encode() if isinstance(data, str) else data)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def utc_to_local(iso_z):
    """Convert '2026-06-03T18:30:00Z' to ('2026-06-03', '20:30') in Berlin time."""
    dt = datetime.strptime(iso_z, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    local = to_berlin(dt)
    return local.strftime("%Y-%m-%d"), local.strftime("%H:%M")


def normalize_booking_url(url, kinotickets_slug=None, kinoheld_cinema=None):
    """Convert Cineamo-provided URLs to the user-facing booking URL we want."""
    if not url:
        return url
    # kinotickets: /booking/N -> /sale/seats/N
    m = re.match(r"(https://kinotickets\.express/[\w\-]+)/booking/(\d+)", url)
    if m:
        return f"{m.group(1)}/sale/seats/{m.group(2)}"
    # Cinemoon marsedv: pforzheim_cinemoon.marsedv/kinoheld/N -> kinoheld widget URL
    m = re.match(r"https?://([\w\-]+)\.marsedv/kinoheld/(\d+)", url)
    if m and kinoheld_cinema:
        return (f"https://www.kinoheld.de/kino/{kinoheld_cinema['city']}/"
                f"{kinoheld_cinema['slug']}?rb=0&mode=widget&appView=1"
                f"&showId={m.group(2)}#panel-seats")
    return url


def extract_kinotickets_show_id(booking_url):
    m = re.search(r"/(?:sale/seats|booking)/(\d+)", booking_url)
    return m.group(1) if m else None


def extract_kinoheld_show_id(booking_url):
    m = re.search(r"showId=(\d+)", booking_url)
    return m.group(1) if m else None


def extract_cinetixx_show_id(booking_url):
    m = re.search(r"showId=(\d+)", booking_url)
    return m.group(1) if m else None


# --------------------------------------------------------------------
# Discovery functions per platform
# --------------------------------------------------------------------

def discover_cineamo(cinema):
    """Cineamo: /cinemas/{cinemaId}/showings-future?contentId={programId}"""
    cinema_id = cinema["cineamoCinemaId"]
    content_id = cinema["cineamoContentId"]
    url = f"https://api.cineamo.com/cinemas/{cinema_id}/showings-future?contentId={content_id}"
    data = fetch_json(url)
    cinema_kh = None
    if "kinoheldWidget" in cinema:
        cinema_kh = cinema["kinoheldWidget"]
    shows = []
    for s in data.get("_embedded", {}).get("showings", []):
        booking_url = (s.get("bookingUrlExternal")
                       or (s.get("ticketUrls") or {}).get("default"))
        booking_url = normalize_booking_url(booking_url, kinoheld_cinema=cinema_kh)
        if not booking_url or not booking_url.startswith("http"):
            print(f"  [skip] {cinema['name']} show {s.get('id')} has no usable bookingUrl: {booking_url}")
            continue
        date, time = utc_to_local(s["startDatetime"])
        shows.append({"date": date, "time": time, "bookingUrl": booking_url,
                      "isPremiere": bool(s.get("isPremiere"))})
    return shows


def discover_capitol_cineweb(cinema):
    """Capitol's own film page: parse JSON-LD ScreeningEvents.

    Capitol no longer publishes the kinotickets seat URL on the film
    page, so we map (date, time) -> seat_id via the seatIdByDateTime
    table in the cinema config. Anything missing falls back to the
    cinema's film URL (works for users but not for seat scraping)."""
    html = fetch_text(cinema["filmUrl"])
    seat_map = cinema.get("seatIdByDateTime", {}) or {}
    cinema_slug = cinema.get("kinoticketsCinemaSlug") or "kornwestheim-capitol"
    shows = []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            data = json.loads(block.strip())
        except Exception:
            continue
        for it in (data if isinstance(data, list) else [data]):
            if not isinstance(it, dict) or it.get("@type") != "ScreeningEvent":
                continue
            if "Peddi" not in (it.get("name") or ""):
                continue
            start = it.get("startDate")
            if not start:
                continue
            dt = datetime.fromisoformat(start)
            date_s = dt.strftime("%Y-%m-%d")
            time_s = dt.strftime("%H:%M")
            seat_id = seat_map.get(f"{date_s} {time_s}")
            if seat_id:
                booking = f"https://kinotickets.express/{cinema_slug}/sale/seats/{seat_id}"
            else:
                booking = cinema["filmUrl"]
            shows.append({"date": date_s, "time": time_s,
                          "bookingUrl": booking, "isPremiere": False})
    return shows


def discover_kinoheld_showgroup(cinema):
    """Kinoheld GraphQL: showGroup(uuid).shows.data with kinoheld vorstellung URL."""
    uuid = cinema["kinoheldShowGroupUuid"]
    query = '{ showGroup(uuid: "%s") { name shows { data { id urlSlug beginning isBookable cinema { id urlSlug } } } } }' % uuid
    body = json.dumps({"query": query}).encode()
    data = fetch_json("https://next-live.kinoheld.de/graphql", method="POST",
                      data=body, extra_headers={"Content-Type": "application/json"})
    sg = (data.get("data") or {}).get("showGroup") or {}
    shows_data = (sg.get("shows") or {}).get("data") or []
    cinema_filter = cinema.get("kinoheldCinemaId")
    out = []
    for s in shows_data:
        if cinema_filter and (s.get("cinema") or {}).get("id") != str(cinema_filter):
            continue
        dt = datetime.fromisoformat(s["beginning"])  # already local with tz offset
        cinema_slug = (s.get("cinema") or {}).get("urlSlug") or ""
        city = cinema.get("kinoheldCity") or ""
        url_slug = s["urlSlug"]
        booking_url = f"https://www.kinoheld.de/kino/{city}/{cinema_slug}/vorstellung/{url_slug}"
        out.append({"date": dt.strftime("%Y-%m-%d"), "time": dt.strftime("%H:%M"),
                    "bookingUrl": booking_url, "isPremiere": False})
    return out


def discover_premiumkino(cinema):
    """Premiumkino sitemap: parse vorstellung URLs for the movie slug."""
    cinema_slug = cinema["premiumkinoCinema"]
    movie_slug = cinema.get("movieSlug", "peddi")
    sitemap = fetch_text(f"https://backend.premiumkino.de/v1/de/{cinema_slug}/sitemap")
    shows = []
    pattern = rf"<loc>([^<]*vorstellung/{re.escape(movie_slug)}/(\d{{4}})(\d{{2}})(\d{{2}})/(\d{{2}})(\d{{2}})/[^<]+)</loc>"
    for m in re.finditer(pattern, sitemap):
        url, y, mo, d, hh, mm = m.groups()
        shows.append({"date": f"{y}-{mo}-{d}", "time": f"{hh}:{mm}",
                      "bookingUrl": url, "isPremiere": False})
    return shows


def discover_manual(cinema):
    """Click-through cinemas whose showtimes can't be scraped (locked
    booking backend). Shows are listed by hand in the cinema config's
    `manualShows` array: [{date, time, bookingUrl}]."""
    out = []
    for s in cinema.get("manualShows", []):
        out.append({"date": s["date"], "time": s["time"],
                    "bookingUrl": s["bookingUrl"], "isPremiere": False})
    return out


def discover_cinestar(cinema):
    """CineStar: /api/show/<showId> returns showtimes with a
    'YYYY-MM-DD HH:MM CEST' datetime. Booking is the cinema's event
    page (detailLink). Seat data lives in the Vista system and isn't
    exposed, so seats stay unknown."""
    show_id = cinema["cinestarShowId"]
    data = fetch_json(f"https://www.cinestar.de/api/show/{show_id}")
    detail = data.get("detailLink", "")
    booking = ("https://www.cinestar.de" + detail) if detail.startswith("/") else (detail or cinema.get("filmUrl"))
    shows = []
    for st in data.get("showtimes", []):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})", st.get("datetime", ""))
        if m:
            shows.append({"date": m.group(1), "time": m.group(2),
                          "bookingUrl": booking, "isPremiere": False})
    return shows


def discover_kinopolis(cinema):
    """Kinopolis family (Kinopolis Hamburg/Viernheim/Aschaffenburg,
    Mathäser Munich): the film-detail page lists each show with
    data-performance-id and a /<code>/programm/vorstellung/<id> link.
    JSON-LD startDate gives the date; the page has only one date in
    this view at a time."""
    import json as _json
    html = fetch_text(cinema["filmUrl"])
    # Date from JSON-LD ScreeningEvent
    show_date = None
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            d = _json.loads(b.strip())
        except Exception:
            continue
        for it in (d if isinstance(d, list) else [d]):
            if isinstance(it, dict) and it.get("@type") == "ScreeningEvent" and it.get("startDate"):
                show_date = it["startDate"][:10]
                break
        if show_date:
            break
    if not show_date:
        return []
    pattern = (r'data-performance-id="([^"]+)".{0,2000}?'
               r'prog2__time\s+time__buy_btn"\s+href="([^"]+)"[^>]*>\s*'
               r'([\d:]+)\s*</a>')
    shows = []
    base = cinema.get("siteBase", "https://www.kinopolis.de")
    for pid, href, time in re.findall(pattern, html, re.S):
        booking = href if href.startswith("http") else base + href
        shows.append({"date": show_date, "time": time,
                      "bookingUrl": booking, "isPremiere": False})
    return shows


def discover_cineweb_termine(cinema):
    """Cineweb-style film page with embedded `termine` JS block, e.g.
    Cinefactory Mönchengladbach. Each termin entry has datum, zeit and
    a link_desktop pointing at the kinotickets booking URL."""
    html = fetch_text(cinema["filmUrl"])
    pattern = (r'"datum_(\d{4}-\d{2}-\d{2})":\{"datum":"([^"]+)","zeit":"([^"]+)",'
               r'"saal":"[^"]*","saal_bezeichnung":"([^"]+)","link_desktop":"([^"]+)"')
    shows = []
    for _, date, time, _saal, link in re.findall(pattern, html):
        link = link.replace("\\/", "/")
        # Normalize /booking/N -> /sale/seats/N
        m = re.match(r"(https://kinotickets\.express/[\w\-]+)/booking/(\d+)", link)
        if m:
            link = f"{m.group(1)}/sale/seats/{m.group(2)}"
        shows.append({"date": date, "time": time, "bookingUrl": link, "isPremiere": False})
    return shows


PLATFORM_DISCOVERY = {
    "cineamo": discover_cineamo,
    "capitol_cineweb": discover_capitol_cineweb,
    "cineweb_termine": discover_cineweb_termine,
    "kinoheld_showgroup": discover_kinoheld_showgroup,
    "premiumkino": discover_premiumkino,
    "kinopolis": discover_kinopolis,
    "cinestar": discover_cinestar,
    "manual": discover_manual,
}


# --------------------------------------------------------------------
# Auto-onboarding: detect platform from a new Zineflix theatre's URL
# --------------------------------------------------------------------

def _clean_theatre_name(name):
    """Strip parenthetical notes and excess whitespace from Zineflix names."""
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name or "").strip()
    return re.sub(r"\s+", " ", name)


def _city_from_theatre(name):
    """Heuristic: the last word of the cleaned name is usually the city."""
    parts = _clean_theatre_name(name).split()
    if not parts:
        return ""
    city = parts[-1]
    return city[:1].upper() + city[1:].lower()


def _auto_onboard_kinopolis(theatre, url):
    m = re.match(r"https?://(?:www\.)?(kinopolis\.de|mathaeser\.de)/(\w+)/filmdetail/[\w\-]+/\w+", url)
    if not m:
        return None
    domain, code = m.group(1), m.group(2)
    city = _city_from_theatre(theatre)
    if not city:
        city = code.upper()
    if domain == "mathaeser.de":
        name = "Mathäser"
        key = f"{city.lower()}-mathaeser"
    else:
        name = f"Kinopolis {city}"
        key = f"{city.lower()}-kinopolis"
    return {
        "key": key, "city": city, "name": name,
        "zineflixTheatreName": theatre, "platform": "kinopolis",
        "filmUrl": url, "siteBase": f"https://www.{domain}",
        "ticketPrice": 14.0, "premierePrice": 18.0,
    }


def _auto_onboard_premiumkino(theatre, url):
    m = re.match(r"https?://([\w\-]+)\.premiumkino\.de/", url)
    if not m:
        return None
    cinema_slug = m.group(1)
    city = _city_from_theatre(theatre) or cinema_slug.capitalize()
    name_parts = _clean_theatre_name(theatre).split()
    name = " ".join(name_parts[:-1]) if len(name_parts) > 1 else "Astor"
    return {
        "key": f"{cinema_slug}-{name.lower().replace(' ', '-')}",
        "city": city, "name": name, "zineflixTheatreName": theatre,
        "platform": "premiumkino", "premiumkinoCinema": cinema_slug,
        "movieSlug": "peddi", "ticketPrice": 17.0, "premierePrice": 18.0,
    }


def _auto_onboard_cinefactory(theatre, url):
    """Cineweb-style cinemas with a film URL — Cinefactory pattern."""
    m = re.match(r"https?://(?:www\.)?([\w\-]+\.\w+)/detail/\d+/[\w%]+", url)
    if not m:
        return None
    host = m.group(1)
    # Need a kinoticketsCinemaSlug for the discovered URLs — leave blank
    # so users can fill in if needed; the show URLs themselves are
    # parsed from the termine block and used as-is.
    city = _city_from_theatre(theatre) or host.split(".")[0].capitalize()
    name = _clean_theatre_name(theatre).split()[0] if theatre else "Cinema"
    return {
        "key": f"{city.lower()}-{name.lower().replace(' ', '-')}",
        "city": city, "name": name, "zineflixTheatreName": theatre,
        "platform": "cineweb_termine", "filmUrl": url,
        "ticketPrice": 12.0, "premierePrice": 18.0,
    }


def _auto_onboard_cinestar(theatre, url):
    # Zineflix sometimes doubles the URL or mistypes the event slug
    # (e.g. ...-omum/veranstaltung...). Extract the cinema slug and
    # rebuild a clean event URL (the Peddi event slug is shared chain-wide).
    m = re.search(r"cinestar\.de/([\w\-]+?)/veranstaltung", url)
    if not m:
        return None
    cinema_slug = m.group(1)
    clean_url = f"https://www.cinestar.de/{cinema_slug}/veranstaltung-peddi-telugu-omu"
    try:
        html = fetch_text(clean_url)
    except Exception:
        return None
    sid = re.search(r'data-show-id="(\d+)"', html)
    if not sid:
        return None
    city = _city_from_theatre(theatre) or cinema_slug.replace("kino-", "").split("-")[0].capitalize()
    return {
        "key": f"{city.lower()}-cinestar", "city": city,
        "name": f"CineStar {city}", "zineflixTheatreName": theatre,
        "platform": "cinestar", "cinestarShowId": sid.group(1),
        "filmUrl": clean_url, "ticketPrice": 14.0, "premierePrice": 18.0,
    }


AUTO_ONBOARDERS = [
    _auto_onboard_kinopolis,
    _auto_onboard_premiumkino,
    _auto_onboard_cinestar,
    _auto_onboard_cinefactory,
]


def auto_onboard(theatre, url):
    for fn in AUTO_ONBOARDERS:
        cfg = fn(theatre, url)
        if cfg:
            return cfg
    return None


# --------------------------------------------------------------------
# Zineflix theatre list
# --------------------------------------------------------------------

def fetch_zineflix_theatres(movie_id):
    url = f"https://backendzineflex.teammatrixmantra.com/api/v1/othertheatre/{movie_id}"
    data = fetch_json(url)
    return data.get("data") or []


def normalize_name(name):
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


# --------------------------------------------------------------------
# booking.html regeneration
# --------------------------------------------------------------------

def regenerate_booking_html(movie, shows):
    with open(BOOKING_HTML, "r", encoding="utf-8") as f:
        html = f.read()
    # Build the new movies object
    entries_json = json.dumps(shows, indent=10, ensure_ascii=False)
    # Cosmetic indent fix to match existing style
    entries_json = entries_json.replace("\n          ", "\n            ")
    block = (
        "{\n"
        "      " + movie["slug"] + ": {\n"
        '        title: "' + movie["title"] + '",\n'
        '        genre: "' + movie["genre"] + '",\n'
        '        language: "' + movie["language"] + '",\n'
        '        page: "' + movie["page"] + '",\n'
        '        shows: ' + entries_json + "\n"
        "      }\n"
        "    }"
    )
    start = html.find("const movies = {")
    if start == -1:
        raise RuntimeError("Cannot find 'const movies = {' in booking.html")
    brace_start = html.index("{", start)
    depth = 0
    end = brace_start
    for i in range(brace_start, len(html)):
        if html[i] == "{": depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                end = i; break
    new_html = html[:start] + "const movies = " + block + html[end + 1:]
    if new_html != html:
        with open(BOOKING_HTML, "w", encoding="utf-8") as f:
            f.write(new_html)
        return True
    return False


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def main():
    cfg = json.load(open(CINEMAS_FILE, encoding="utf-8"))
    movie = cfg["movie"]
    cinemas = cfg["cinemas"]

    # 1. Zineflix theatre check (informational + new-cinema detection +
    #    auto-onboarding for URL patterns we already know).
    print("== Zineflix theatre check ==")
    newly_onboarded = []
    try:
        theatres = fetch_zineflix_theatres(movie["zineflixMovieId"])
        known = {normalize_name(c.get("zineflixTheatreName")) for c in cinemas}
        ignored = {normalize_name(n) for n in cfg.get("ignoredCinemas", [])}
        unknown = []
        for t in theatres:
            n = normalize_name(t.get("theatreName"))
            if n in known or n in ignored:
                continue
            unknown.append(t)
        print(f"  Zineflix lists {len(theatres)} theatres; {len(known)} known, "
              f"{len(ignored)} ignored, {len(unknown)} NEW unknown.")
        for t in unknown:
            name = t.get("theatreName")
            url = t.get("redirectLink")
            new_cfg = auto_onboard(name, url)
            if new_cfg:
                print(f"  AUTO-ONBOARDED: '{name}' -> {new_cfg['platform']} ({new_cfg['key']})")
                cinemas.append(new_cfg)
                newly_onboarded.append(new_cfg)
            else:
                print(f"  NEW: '{name}' -> {url}")
                print(f"       (no URL pattern match; add to data/peddi_cinemas.json manually)")
        if newly_onboarded:
            with open(CINEMAS_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            print(f"  Wrote {len(newly_onboarded)} new cinema(s) to {CINEMAS_FILE}")
    except Exception as e:
        print(f"  Zineflix check failed: {e}")

    # 2. Per-cinema discovery
    print("\n== Per-cinema show discovery ==")
    all_shows = []
    subtitle = movie.get("subtitle", "English Subtitles")
    for c in cinemas:
        platform = c["platform"]
        # Map composite platforms to their concrete discovery function.
        # cinetixx -> cineamo, cineamo_to_kinotickets -> cineamo,
        # kinoheld_cinetixx -> kinoheld_showgroup, kinoheld_graphql -> cineamo or kinoheld_showgroup
        func_key = {
            "cinetixx": "cineamo",
            "cineamo_to_kinotickets": "cineamo",
            "kinoheld_cinetixx": "kinoheld_showgroup",
            "kinoheld_graphql": "cineamo",
        }.get(platform, platform)
        func = PLATFORM_DISCOVERY.get(func_key)
        if not func:
            print(f"  [skip] {c['name']} ({c['city']}): unknown platform '{platform}'")
            continue
        try:
            shows = func(c)
        except Exception as e:
            print(f"  [err]  {c['name']} ({c['city']}): {e}")
            continue
        for s in shows:
            s["city"] = c["city"]
            s["cinema"] = c["name"]
            s["subtitle"] = subtitle
            all_shows.append(s)
        print(f"  [ok]   {c['name']:22} ({c['city']:11}) -> {len(shows)} shows")

    # Sort shows by date+time+city for stable output
    all_shows.sort(key=lambda s: (s["date"], s["time"], s["city"], s["cinema"]))

    # 3. Write data/peddi_shows.json
    os.makedirs(os.path.dirname(SHOWS_FILE), exist_ok=True)
    out = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "movie": movie["slug"],
        "totalShows": len(all_shows),
        "shows": [{k: s[k] for k in ("city", "cinema", "date", "time", "subtitle",
                                       "bookingUrl") if k in s} for s in all_shows],
    }
    with open(SHOWS_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {SHOWS_FILE} ({len(all_shows)} shows)")

    # 4. Regenerate booking.html
    booking_shows = [{"city": s["city"], "cinema": s["cinema"], "date": s["date"],
                      "time": s["time"], "subtitle": s["subtitle"],
                      "bookingUrl": s["bookingUrl"]} for s in all_shows]
    if regenerate_booking_html(movie, booking_shows):
        print(f"Updated {BOOKING_HTML}")
    else:
        print(f"{BOOKING_HTML} unchanged")


if __name__ == "__main__":
    main()
