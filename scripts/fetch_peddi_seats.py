"""
Scrape per-show seat counts for Peddi and write data/peddi_seats.json
consumed by admin-revenue-peddi.html.

Reads the show list from data/peddi_shows.json (produced by
discover_peddi_shows.py) and the per-cinema config (prices, capacity
overrides, scrape platform IDs) from data/peddi_cinemas.json.

Per platform:
  cinetixx (Cincinnati, Dresden via kinoheld) -> Cinetixx sector API
  kinotickets URL  -> Capitol/UFA/Filmpalast seat-plan HTML scrape
  kinoheld widget URL -> Pforzheim via kinoheld GraphQL by show id
  premiumkino vorstellung URL -> Astor performance API

Usage:  py scripts/fetch_peddi_seats.py
"""
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
CINEMAS_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_cinemas.json")
SHOWS_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_shows.json")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_seats.json")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


# --------------------------------------------------------------------
# Platform-specific seat counters
# --------------------------------------------------------------------

def count_cinetixx(show_id):
    sectors = fetch_json(f"https://booking.cinetixx.de/api/shows/{show_id}/sectors")
    capacity = sold = blocked = free = 0
    for sec in sectors:
        full = fetch_json(f"https://booking.cinetixx.de/api/shows/{show_id}/sector/{sec['id']}")
        for s in full.get("seats", []):
            if s.get("isGap"):
                continue
            capacity += 1
            if s.get("isSold") or s.get("state") == "S":
                sold += 1
            elif s.get("state") == "B":
                blocked += 1
            elif s.get("state") == "F":
                free += 1
    return {"capacity": capacity, "booked": sold, "free": free, "blocked": blocked}


def count_kinotickets(seats_url):
    html = fetch_html(seats_url)
    free = sold = 0
    for m in re.finditer(r'<(button|div)[^>]*class="seat-dim-1x1[^"]*"[^>]*>', html):
        if m.group(1) == "button":
            free += 1
        else:
            sold += 1
    return {"capacity": free + sold, "booked": sold, "free": free, "blocked": 0}


def count_kinoheld_graphql(kinoheld_show_id):
    query = '{ show(id: "%s") { auditorium { seatCount } seats { status } } }' % kinoheld_show_id
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://next-live.kinoheld.de/graphql",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        d = json.loads(resp.read().decode())
    show = (d.get("data") or {}).get("show") or {}
    seats = show.get("seats") or []
    counts = {"capacity": 0, "booked": 0, "free": 0, "blocked": 0}
    for s in seats:
        st = s.get("status")
        counts["capacity"] += 1
        if st in ("SOLD", "RESERVED", "NOTED"):
            counts["booked"] += 1
        elif st in ("BLOCKED", "SOCIAL_DISTANCE"):
            counts["blocked"] += 1
        elif st == "FREE":
            counts["free"] += 1
    return counts


def count_premiumkino(cinema_slug, perf_id):
    url = f"https://backend.premiumkino.de/v1/de/{cinema_slug}/performance/{perf_id}"
    data = fetch_json(url)
    occupied = len(data.get("occupation", {}).get("occupiedSeats", []))
    return {"capacity": 0, "booked": occupied, "free": 0, "blocked": 0}


def count_kinopolis(perf_id, cinema_slug, site_base):
    """Kinopolis film-detail page lists the show with its capacity in
    `<div class="prog2__seats">N</div>` and the percentage free in
    `<div class="prog2__scale...">P% frei</div>`. Booked is derived as
    capacity * (100 - P) / 100."""
    # Re-fetch the film page for this cinema to get the per-show stats
    # We don't know the film URL from the booking URL alone, so look up
    # the cinema config; if not provided, derive from booking_url base.
    # The caller (scrape_show) passes the booking URL; we re-fetch the
    # film page via the kinopolis cinema mapping below.
    raise NotImplementedError  # handled inline in scrape_show via film page cache


# In-process cache so we don't fetch each cinema's film page multiple times.
_KINOPOLIS_PAGE_CACHE = {}


def _kinopolis_count_from_film_page(film_url, perf_id):
    if film_url not in _KINOPOLIS_PAGE_CACHE:
        _KINOPOLIS_PAGE_CACHE[film_url] = fetch_html(film_url)
    html = _KINOPOLIS_PAGE_CACHE[film_url]
    block_match = re.search(
        rf'data-performance-id="{re.escape(perf_id)}".{{0,3000}}?'
        r'<div class="prog2__seats">\s*(\d+)\s*</div>'
        r'.{0,2000}?<div class="prog2__scale[^"]*">\s*(\d+)\s*%\s*frei',
        html, re.S,
    )
    if not block_match:
        raise ValueError(f"kinopolis perf {perf_id} not found on film page")
    capacity = int(block_match.group(1))
    pct_free = int(block_match.group(2))
    free = round(capacity * pct_free / 100)
    sold = capacity - free
    return {"capacity": capacity, "booked": sold, "free": free, "blocked": 0}


def count_ticketcloud(cinema_slug, show_id):
    """ticket-cloud.de (Lux Heidelberg etc): requires a session, then
    Method=Show to get IDs, then Method=PlainSeatPlan for the seat grid.
    Each seat is a <div ...><img src=".../Seat_<state>.png">."""
    base = f"https://ticket-cloud.de/{cinema_slug}/Show/{show_id}"
    connector = "https://ticket-cloud.de/modules/system/systemConnector.php"
    jar = urllib.request.HTTPCookieProcessor()
    opener = urllib.request.build_opener(jar)
    # 1) load the show page to set session cookie + get informationString
    req = urllib.request.Request(base, headers={"User-Agent": UA})
    with opener.open(req, timeout=20) as resp:
        page = resp.read().decode("utf-8", errors="replace")
    m = re.search(r"informationString\s*=\s*'([^']+)'", page)
    if not m:
        raise RuntimeError("informationString not found")
    info = m.group(1)
    common_headers = {
        "User-Agent": UA,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": base,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    def post(fields):
        data = urllib.parse.urlencode(fields).encode()
        r = urllib.request.Request(connector, data=data, headers=common_headers, method="POST")
        with opener.open(r, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")

    # 2) Method=Show -> returns header HTML + <input id="Plain" value="ShowID,AudiID,SeatVariantID,SiteID">
    # ticket-cloud occasionally responds "@-@#ERROR|System starting" on
    # the first request after a cold session; retry a few times.
    import time as _t
    show_resp = ""
    for attempt in range(4):
        show_resp = post({
            "Method": "Show", "ShowID": show_id, "information": info,
            "PlanWidth": "800", "PlanHeight": "700",
        })
        if "System starting" not in show_resp and "Plain" in show_resp:
            break
        _t.sleep(2 + attempt * 2)
    pm = re.search(r'id="Plain"[^>]*value="([^"]+)"', show_resp)
    if not pm:
        raise RuntimeError("Plain field not found in Show response")
    parts = pm.group(1).split(",")
    if len(parts) < 4:
        raise RuntimeError(f"Plain field has {len(parts)} parts, need >=4")
    _, audi_id, seat_var_id, site_id = parts[:4]

    # 3) Method=PlainSeatPlan -> seat grid
    plan_resp = post({
        "Method": "PlainSeatPlan",
        "AudiID": audi_id, "Center": site_id, "SeatVariantID": seat_var_id,
        "Width": "800", "Height": "700",
        "GetBlock": "0", "GetCategory": "0", "DeviceInfo": "desktop",
        "information": info, "ShowID": show_id,
    })
    # Each seat is one img tag with Seat_<state>.png in the src.
    free = sold = blocked = 0
    for src in re.findall(r"SeatplanImages/([\w_\-]+)\.png", plan_resp):
        if src.endswith("_Sold"):
            sold += 1
        elif src.endswith("_UnAvailable"):
            blocked += 1
        else:
            free += 1
    return {"capacity": free + sold + blocked, "booked": sold,
            "free": free, "blocked": blocked}


# --------------------------------------------------------------------
# Booking-URL -> platform handler
# --------------------------------------------------------------------

def scrape_show(booking_url):
    """Pick the right seat counter based on URL pattern."""
    m = re.search(r"booking\.cinetixx\.de/.*[?&]showId=(\d+)", booking_url)
    if m:
        return count_cinetixx(m.group(1))
    m = re.search(r"kinotickets\.express/[\w\-]+/(?:sale/seats|booking)/(\d+)", booking_url)
    if m:
        # normalize to /sale/seats/N regardless of source
        seats_url = re.sub(r"/booking/(\d+)", r"/sale/seats/\1", booking_url)
        return count_kinotickets(seats_url)
    # Dresden cinetixx via kinoheld (vorstellung/<cinetixxId>)
    m = re.search(r"kinoheld\.de/kino/[\w\-]+/[\w\-]+/vorstellung/(\d+)", booking_url)
    if m:
        return count_cinetixx(m.group(1))
    # Pforzheim cinemoon via kinoheld widget (showId in query)
    m = re.search(r"kinoheld\.de/kino/[\w\-]+/[\w\-]+\?.*showId=(\d+)", booking_url)
    if m:
        # need the internal kinoheld show id; fall through to GraphQL by url slug
        return _count_kinoheld_widget(m.group(1))
    m = re.search(r"premiumkino\.de/vorstellung/([\w\-]+)/(\d{8})/(\d{4})/([\w~_\-]+)", booking_url)
    if m:
        cinema = re.search(r"https?://([\w\-]+)\.premiumkino\.de", booking_url).group(1)
        return count_premiumkino(cinema, m.group(4))
    m = re.search(r"ticket-cloud\.de/([\w\-]+)/Show/(\d+)", booking_url)
    if m:
        return count_ticketcloud(m.group(1), m.group(2))
    # Kinopolis family (kinopolis.de or mathaeser.de): /<code>/programm/vorstellung/<perfId>
    m = re.search(r"(https?://(?:www\.)?(?:kinopolis\.de|mathaeser\.de))/(\w+)/programm/vorstellung/(\w+)", booking_url)
    if m:
        site_base, code, perf_id = m.group(1), m.group(2), m.group(3)
        # Reconstruct the film page URL — known slug is peddi-telugu/<id> from config
        film_url = f"{site_base}/{code}/filmdetail/peddi-telugu/42A74000012PLXMQDD"
        return _kinopolis_count_from_film_page(film_url, perf_id)
    raise ValueError(f"unknown booking URL pattern: {booking_url}")


def _count_kinoheld_widget(public_show_id):
    """Pforzheim Cinemoon: widget URL has the public showId (urlSlug);
    look up the internal kinoheld id via GraphQL, then count seats."""
    query = ('{ show(urlSlug: "%s", cinemaId: "292") { id } }' % public_show_id)
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request(
        "https://next-live.kinoheld.de/graphql",
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": UA},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        d = json.loads(resp.read().decode())
    show = (d.get("data") or {}).get("show") or {}
    show_id = show.get("id")
    if not show_id:
        raise ValueError(f"kinoheld widget show {public_show_id} not found")
    return count_kinoheld_graphql(show_id)


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def main():
    cfg = json.load(open(CINEMAS_FILE, encoding="utf-8"))
    shows_data = json.load(open(SHOWS_FILE, encoding="utf-8"))

    cinema_by_name = {c["name"]: c for c in cfg["cinemas"]}
    premiere_date = cfg["movie"].get("premiereDate")

    out_shows = []
    for s in shows_data["shows"]:
        cinema = cinema_by_name.get(s["cinema"]) or {}
        is_premiere = (s["date"] == premiere_date)
        price = cinema.get("premierePrice") if is_premiere else cinema.get("ticketPrice")
        price = float(price or 0.0)
        rec = dict(s)
        try:
            counts = scrape_show(s["bookingUrl"])
        except Exception as e:
            print(f"  ERR {s['city']:11} {s['cinema']:23} {s['date']} {s['time']}: {e}")
            rec.update({"capacity": None, "booked": None, "free": None,
                        "ticketPrice": price, "gross": None, "error": str(e)})
            out_shows.append(rec)
            continue
        # Cinema-level capacity override (when API doesn't expose total)
        cap_override = cinema.get("capacityOverride")
        if cap_override:
            counts["capacity"] = cap_override
            counts["free"] = max(0, cap_override - counts["booked"] - counts.get("blocked", 0))
        counts["ticketPrice"] = price
        counts["gross"] = round(counts["booked"] * price, 2)
        rec.update(counts)
        out_shows.append(rec)
        tag = " (PREMIERE)" if is_premiere else ""
        blocked_tag = (f" (blocked={counts.get('blocked', 0)})"
                       if counts.get("blocked") else "")
        print(f"  OK  {s['city']:11} {s['cinema']:23} {s['date']} {s['time']}  "
              f"cap={counts['capacity']:4d} booked={counts['booked']:3d} "
              f"@ EUR {price:5.2f} -> gross EUR {counts['gross']:7.2f}"
              f"{tag}{blocked_tag}")

    payload = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "movie": cfg["movie"]["slug"],
        "totalShows": len(out_shows),
        "shows": out_shows,
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
