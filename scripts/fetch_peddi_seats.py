"""
Scrape kinotickets.express seat layouts for Peddi shows to count
capacity and booked seats per show. Writes data/peddi_seats.json
consumed by admin-revenue-peddi.html.

Cinetixx (Munich Cincinnati) and Kinoheld (Dresden) shows cannot be
scraped this way, so they're included with null counts and rendered
as "n/a" in the dashboard.

Usage:
    py scripts/fetch_peddi_seats.py
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "data", "peddi_seats.json")

# All Peddi shows. For kinotickets.express we scrape seat data; the
# other three sources lack a usable public seat layout.
SHOWS = [
    # Munich - Cincinnati (cinetixx)
    {"city": "Munich", "cinema": "Cincinnati", "date": "2026-06-03", "time": "20:30",
     "url": "https://booking.cinetixx.de/frontend/index.html?cinemaId=296551098&showId=3540551659&bgswitch=false&resize=false",
     "scrape": "cinetixx", "cinetixx_show_id": "3540551659"},

    # Frankfurt - Filmpalast Hofheim (kinotickets.express)
    {"city": "Frankfurt", "cinema": "Filmpalast Hofheim", "date": "2026-06-03", "time": "20:45",
     "url": "https://kinotickets.express/hofheim-filmpalast/sale/seats/14678", "scrape": "kinotickets"},
    {"city": "Frankfurt", "cinema": "Filmpalast Hofheim", "date": "2026-06-04", "time": "14:30",
     "url": "https://kinotickets.express/hofheim-filmpalast/sale/seats/14719", "scrape": "kinotickets"},
    {"city": "Frankfurt", "cinema": "Filmpalast Hofheim", "date": "2026-06-06", "time": "14:00",
     "url": "https://kinotickets.express/hofheim-filmpalast/sale/seats/14720", "scrape": "kinotickets"},

    # Stuttgart - Capitol Kornwestheim (kinotickets.express)
    {"city": "Stuttgart", "cinema": "Capitol Kornwestheim", "date": "2026-06-03", "time": "21:00",
     "url": "https://kinotickets.express/kornwestheim-capitol/sale/seats/26314", "scrape": "kinotickets"},
    {"city": "Stuttgart", "cinema": "Capitol Kornwestheim", "date": "2026-06-05", "time": "21:00",
     "url": "https://kinotickets.express/kornwestheim-capitol/sale/seats/26315", "scrape": "kinotickets"},

    # Dusseldorf - UFA Palast (kinotickets.express)
    {"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-06-03", "time": "20:30",
     "url": "https://kinotickets.express/duesseldorf-ufa-filmpalast/sale/seats/80776", "scrape": "kinotickets"},
    {"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-06-05", "time": "19:40",
     "url": "https://kinotickets.express/duesseldorf-ufa-filmpalast/sale/seats/80777", "scrape": "kinotickets"},
    {"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-06-06", "time": "13:30",
     "url": "https://kinotickets.express/duesseldorf-ufa-filmpalast/sale/seats/80778", "scrape": "kinotickets"},

    # Dresden - Zentralkino (kinoheld frontend, cinetixx backend)
    {"city": "Dresden", "cinema": "Zentralkino", "date": "2026-06-05", "time": "19:30",
     "url": "https://www.kinoheld.de/kino/dresden/zentralkino-dresden/vorstellung/3541829399",
     "scrape": "cinetixx", "cinetixx_show_id": "3541829399"},
    {"city": "Dresden", "cinema": "Zentralkino", "date": "2026-06-07", "time": "12:30",
     "url": "https://www.kinoheld.de/kino/dresden/zentralkino-dresden/vorstellung/3541829434",
     "scrape": "cinetixx", "cinetixx_show_id": "3541829434"},

    # Pforzheim - Cinemoon (kinoheld, Mars backend - seats via GraphQL)
    {"city": "Pforzheim", "cinema": "Cinemoon", "date": "2026-06-03", "time": "20:30",
     "url": "https://www.kinoheld.de/kino/pforzheim/cinemoon-pforzheim?rb=0&mode=widget&appView=1&showId=31784#panel-seats",
     "scrape": "kinoheld_graphql", "kinoheld_show_id": "125569539"},
    {"city": "Pforzheim", "cinema": "Cinemoon", "date": "2026-06-07", "time": "13:15",
     "url": "https://www.kinoheld.de/kino/pforzheim/cinemoon-pforzheim?rb=0&mode=widget&appView=1&showId=31785#panel-seats",
     "scrape": "kinoheld_graphql", "kinoheld_show_id": "125569541"},
]

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# Ticket prices (EUR). PREMIERE_PRICES override PRICES on PREMIERE_DATE.
# Dresden Zentralkino is reservation-only (no money at booking) => 0.
PREMIERE_DATE = "2026-06-03"
PRICES = {
    "Cincinnati":           14.00,
    "Capitol Kornwestheim": 14.00,
    "Filmpalast Hofheim":   14.00,
    "UFA Palast":           14.00,
    "Cinemoon":             14.00,
    "Zentralkino":           0.00,
}
PREMIERE_PRICES = {
    "Cincinnati":           18.00,
    "Capitol Kornwestheim": 18.00,
    "Filmpalast Hofheim":   18.00,
    "UFA Palast":           18.00,
    "Cinemoon":             19.00,
    "Zentralkino":           0.00,
}


def price_for(cinema, date):
    table = PREMIERE_PRICES if date == PREMIERE_DATE else PRICES
    return table.get(cinema, PRICES.get(cinema, 0.0))


# Per-cinema capacity override. Use when the cinema's published seat
# count differs from what the booking system exposes (e.g. wheelchair
# seats sold offline, or admin-blocked cells that physically exist).
CAPACITY_OVERRIDE = {
    "Cincinnati": 401,
}


def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def count_cinetixx_seats(show_id):
    """Capacity and booked from the cinetixx sector endpoint.

    Cinetixx returns seat-grid cells including layout gaps (isGap=true).
    Those gaps must be excluded from the real seat count. A booked seat
    is one with isSold=true (or state="S"); state="B" without isGap is
    an admin-blocked seat (broken / reserved off-sale).
    """
    sectors = fetch_json(f"https://booking.cinetixx.de/api/shows/{show_id}/sectors")
    capacity = sold = blocked = free = 0
    for sec in sectors:
        sec_id = sec["id"]
        full = fetch_json(
            f"https://booking.cinetixx.de/api/shows/{show_id}/sector/{sec_id}"
        )
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


def count_kinoheld_graphql_seats(show_id):
    """Capacity and booked via kinoheld GraphQL (for Mars-source shows)."""
    query = ('{ show(id: "' + show_id + '") '
             '{ auditorium { seatCount } seats { status } } }')
    req = urllib.request.Request(
        "https://next-live.kinoheld.de/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Content-Type": "application/json",
                 "User-Agent": UA, "Accept": "application/json"},
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
        if st == "SOLD" or st == "RESERVED" or st == "NOTED":
            counts["booked"] += 1
        elif st == "BLOCKED" or st == "SOCIAL_DISTANCE":
            counts["blocked"] += 1
        elif st == "FREE":
            counts["free"] += 1
    return counts


def count_kinotickets_seats(html):
    """Count capacity and booked from a kinotickets.express seat page.

    Each seat position is its own element with class seat-dim-1x1:
      <button> = free (bookable), <div> = sold/blocked.
    Both halves of a dual/couple seat (leftdualseat + rightdualseat)
    have their own seat number, price and toggle action, so they
    count as 2 separate seats. The page also has 3 legend icons at
    the bottom inside <div class="h-8 w-8 mr-1"> — those are NOT seats.
    """
    free = sold = 0
    for m in re.finditer(
        r'<(button|div)[^>]*class="seat-dim-1x1[^"]*"[^>]*>',
        html,
    ):
        if m.group(1) == "button":
            free += 1
        else:
            sold += 1
    return {"capacity": free + sold, "booked": sold, "free": free}


def main():
    out_shows = []
    for s in SHOWS:
        rec = {"city": s["city"], "cinema": s["cinema"], "date": s["date"],
               "time": s["time"], "url": s["url"]}
        try:
            if s["scrape"] == "kinotickets":
                html = fetch_html(s["url"])
                counts = count_kinotickets_seats(html)
            elif s["scrape"] == "kinoheld_graphql":
                counts = count_kinoheld_graphql_seats(s["kinoheld_show_id"])
            elif s["scrape"] == "cinetixx":
                counts = count_cinetixx_seats(s["cinetixx_show_id"])
            else:
                counts = None

            if counts is None:
                rec.update({"capacity": None, "booked": None, "free": None,
                            "ticketPrice": None, "gross": None,
                            "note": "seat data not available for this booking system"})
                print(f"  --  {s['city']:11} {s['cinema']:22} {s['date']} {s['time']}  (no seat scrape)")
            else:
                # Apply cinema-level capacity override if set; adjust free accordingly.
                if s["cinema"] in CAPACITY_OVERRIDE:
                    counts["capacity"] = CAPACITY_OVERRIDE[s["cinema"]]
                    counts["free"] = max(0, counts["capacity"] - counts["booked"]
                                         - counts.get("blocked", 0))
                price = price_for(s["cinema"], s["date"])
                counts["ticketPrice"] = price
                counts["gross"] = round(counts["booked"] * price, 2)
                rec.update(counts)
                tag = " (PREMIERE)" if s["date"] == PREMIERE_DATE else ""
                blocked_tag = f" (blocked={counts.get('blocked',0)})" if counts.get('blocked') else ''
                print(f"  OK  {s['city']:11} {s['cinema']:22} {s['date']} {s['time']}  "
                      f"cap={counts['capacity']:3d} booked={counts['booked']:3d} "
                      f"@ EUR {price:5.2f} -> gross EUR {counts['gross']:7.2f}"
                      f"{tag}{blocked_tag}")
        except Exception as e:
            print(f"  ERR {s['city']} {s['date']} {s['time']}: {e}")
            rec.update({"capacity": None, "booked": None, "free": None,
                        "ticketPrice": None, "gross": None, "error": str(e)})
        out_shows.append(rec)

    payload = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "movie": "Peddi",
        "totalShows": len(out_shows),
        "shows": out_shows,
    }
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
