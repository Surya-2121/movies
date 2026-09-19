"""
Scrape per-show seat counts for The Paradise and write data/paradise_seats.json.

Each Paradise show in data/paradise_manual.json is stamped with a booking
URL pointing at the cinema's public film page. Most of those pages actually
wrap a well-known backend (Kinoheld, Kinotickets.express, PremiumKino,
Ticket-Cloud, Cinetixx). This script does a small URL-preprocessing step
per cinema (fetch the page, extract the backend show id, rewrite the URL
into the canonical backend form) and then hands it to
`scripts.fetch_peddi_seats.scrape_show()` — the same seat counter Peddi's
revenue pipeline already uses.

Anything that doesn't map to a supported backend (Cineplex.de behind
OAuth, most custom "cineweb" sites, Filmkunstkinos SPA) is written with
`note: <reason>` and null counts — so the operator sees exactly which
shows still need a per-cinema handler.

Output: data/paradise_seats.json
   {
     "fetchedAt": "…UTC iso…",
     "shows": [
       { "date": "...", "time": "...", "city": "...", "cinema": "...",
         "bookingUrl": "...", "capacity": N, "booked": N, "free": N,
         "note": null | "reason" }
     ],
     "totals": { "shows": N, "capacity": N, "booked": N, "free": N,
                 "coverage_shows": N }
   }

Usage:  py scripts/fetch_paradise_seats.py [YYYY-MM-DD]

With a date arg, only shows on that date are scraped (useful for
day-of-show sanity checks).
"""
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from urllib.parse import unquote

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MANUAL_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_manual.json")
OUT_FILE = os.path.join(PROJECT_ROOT, "data", "paradise_seats.json")

sys.path.insert(0, SCRIPT_DIR)
from fetch_peddi_seats import (  # noqa: E402
    scrape_show, count_kinoheld_graphql, count_kinotickets, UA,
)


def fetch_html(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="replace")


# --------------------------------------------------------------------
# Per-cinema URL rewriting — normalize a public film-page URL into one
# of the canonical backend URLs that fetch_peddi_seats.scrape_show()
# understands. Returns the rewritten URL or None if unsupported.
# --------------------------------------------------------------------

def _rewrite_ufa_duesseldorf(url, show_date, show_time):
    """UFA Düsseldorf embeds kinotickets IDs on its film page."""
    html = fetch_html(url)
    ids = re.findall(
        r"kinotickets\.express/duesseldorf-ufa-filmpalast/(?:sale/seats|booking)/(\d+)",
        html,
    )
    if not ids:
        raise LookupError("no kinotickets id on UFA page")
    # Only one Paradise show at UFA (23/09 20:15); use first id.
    return f"https://kinotickets.express/duesseldorf-ufa-filmpalast/sale/seats/{ids[0]}"


def _rewrite_babylon_berlin(url, show_date, show_time):
    """Babylon Berlin exposes a kinoheld /show/<id> URL."""
    html = fetch_html(url)
    m = re.search(r"kinoheld\.de/kino-berlin/babylon-berlin/show/(\d+)", html)
    if not m:
        raise LookupError("no kinoheld show id on Babylon page")
    # Rewrite into the peddi-supported /vorstellung/<id> form.
    return f"https://www.kinoheld.de/kino/berlin/babylon-berlin/vorstellung/{m.group(1)}"


def _rewrite_cincinnati_muenchen(url, show_date, show_time):
    """Cincinnati München's film page embeds a kinoheld showId per screening.
    Match by ISO datetime (UTC = local - 2h CEST / -1h CET)."""
    html = fetch_html(url)
    # Every showtime block includes an ISO datetime and a showId — match by time.
    # HH:MM local -> HH:MM UTC (approximate: subtract 2h CEST for late September)
    hh, mm = show_time.split(":")
    utc_hour = (int(hh) - 2) % 24  # CEST offset
    want = f"{show_date}T{utc_hour:02d}:{mm}"
    # Find the closest showId to a datetime matching our target hour
    best_id = None
    for m in re.finditer(r"(20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}).{0,600}?showId=(\d+)", html, re.S):
        iso, sid = m.groups()
        if iso.startswith(want[:16]) or iso.startswith(f"{show_date}T{utc_hour:02d}"):
            best_id = sid
            break
    if not best_id:
        # Fallback: any Paradise-associated showId
        first = re.search(r"[Pp]aradise[\s\S]{0,2500}?showId=(\d+)", html)
        if first:
            best_id = first.group(1)
    if not best_id:
        raise LookupError("no Paradise showId on Cincinnati page")
    return f"https://www.kinoheld.de/kino/muenchen/cincinnati-muenchen/vorstellung/{best_id}"


def _rewrite_lux_heidelberg(url, show_date, show_time):
    """Luxor-kino Heidelberg runs on Cineamo (Next.js SPA). Seat data
    needs a per-show Cineamo query which isn't wired up yet."""
    raise LookupError("Lux Heidelberg uses Cineamo — handler TODO")


def _rewrite_premiumkino_frankfurt(url, show_date, show_time):
    """PremiumKino Frankfurt: find the show URL in the sitemap by date+time,
    then hand the canonical /vorstellung/<slug>/<yyyymmdd>/<hhmm>/<token>
    URL to peddi's premiumkino handler."""
    yyyymmdd = show_date.replace("-", "")
    hhmm = show_time.replace(":", "")
    sitemap = fetch_html("https://backend.premiumkino.de/v1/de/frankfurt/sitemap")
    pat = (rf"<loc>([^<]*vorstellung/the-paradise/{yyyymmdd}/{hhmm}/[^<]+)</loc>")
    m = re.search(pat, sitemap)
    if not m:
        raise LookupError(f"no PremiumKino show for {show_date} {show_time}")
    return m.group(1)


def _rewrite_colosseum_berlin(url, show_date, show_time):
    """Colosseum Berlin's tickets URL wraps a kinoheld vorstellung URL in
    a query param."""
    m = re.search(r"[?&]showUrl=([^&]+)", url)
    if not m:
        raise LookupError("no showUrl param in Colosseum URL")
    inner = unquote(m.group(1))
    # Peddi supports /vorstellung/<id> already; use it directly.
    return inner


# --------------------------------------------------------------------
# Dispatcher: pick a rewriter based on URL hostname
# --------------------------------------------------------------------

REWRITERS = [
    (r"ufa-duesseldorf\.de", _rewrite_ufa_duesseldorf),
    (r"babylonberlin\.eu", _rewrite_babylon_berlin),
    (r"cincinnati-muenchen\.de", _rewrite_cincinnati_muenchen),
    (r"heidelberg\.luxor-kino\.de", _rewrite_lux_heidelberg),
    (r"frankfurt\.premiumkino\.de", _rewrite_premiumkino_frankfurt),
    (r"kino\.colosseumberlin\.com", _rewrite_colosseum_berlin),
]

BLOCKED = [
    (r"cineplex\.de", "Cineplex.de BFF requires OAuth (WAF-blocked)"),
    (r"zeise\.de", "Zeise Hamburg custom widget — no public seat API"),
    (r"filmwerk-gt\.de", "Filmwerk Gütersloh custom booking — not scrapable"),
    (r"universum-city\.de", "Universum Karlsruhe custom widget — not mapped"),
    (r"kinoneuwied\.de", "Kino Neuwied custom widget — not mapped"),
    (r"cinefactorymg\.de", "Cinefactory Mönchengladbach — not mapped"),
    (r"filmkunstkinos\.de", "Filmkunstkinos Atelier custom widget — not mapped"),
    (r"capitol-kornwestheim\.de", "Capitol Kornwestheim — kinotickets id per show needs manual map"),
]


def scrape_paradise_show(show):
    url = show["bookingUrl"]
    date = show["date"]
    time = show["time"]

    # 1. Try peddi's scrape_show on the URL as-is (covers Kinoheld
    #    vorstellung URLs, Kinotickets, ticket-cloud, kinopolis, etc.)
    try:
        counts = scrape_show(url)
        rewritten = url
    except ValueError:
        # 2. Fall through to per-host rewriter.
        rewritten = None
        for pat, fn in REWRITERS:
            if re.search(pat, url):
                try:
                    rewritten = fn(url, date, time)
                except Exception as e:
                    return {**show, "capacity": None, "booked": None,
                            "free": None, "note": f"rewrite failed: {e}"}
                break
        if rewritten is None:
            for pat, reason in BLOCKED:
                if re.search(pat, url):
                    return {**show, "capacity": None, "booked": None,
                            "free": None, "note": reason}
            return {**show, "capacity": None, "booked": None, "free": None,
                    "note": "no scraper for this URL"}
        try:
            counts = scrape_show(rewritten)
        except Exception as e:
            return {**show, "capacity": None, "booked": None, "free": None,
                    "rewrittenUrl": rewritten if rewritten != url else None,
                    "note": f"scrape failed: {e}"}
    except Exception as e:
        return {**show, "capacity": None, "booked": None, "free": None,
                "note": f"scrape failed: {e}"}

    out = dict(show)
    out["capacity"] = counts.get("capacity")
    out["booked"] = counts.get("booked")
    out["free"] = counts.get("free")
    out["blocked"] = counts.get("blocked", 0)
    if counts.get("note"):
        out["note"] = counts["note"]
    else:
        out["note"] = None
    if rewritten != url:
        out["rewrittenUrl"] = rewritten
    return out


def main():
    only_date = sys.argv[1] if len(sys.argv) > 1 else None
    shows = json.load(open(MANUAL_FILE, encoding="utf-8"))["shows"]
    if only_date:
        shows = [s for s in shows if s["date"] == only_date]
    shows.sort(key=lambda s: (s["date"], s["time"], s["city"], s["cinema"]))

    results = []
    total_capacity = total_booked = total_free = 0
    coverage = 0
    for s in shows:
        res = scrape_paradise_show(s)
        results.append(res)
        sold = res.get("booked")
        cap = res.get("capacity")
        free = res.get("free")
        if isinstance(sold, int):
            coverage += 1
            total_booked += sold
        if isinstance(cap, int):
            total_capacity += cap
        if isinstance(free, int):
            total_free += free
        cap_s = str(cap) if cap is not None else "-"
        sold_s = str(sold) if sold is not None else "-"
        free_s = str(free) if free is not None else "-"
        print(f"  {s['date']} {s['time']}  {s['city'][:12]:<12} "
              f"{s['cinema'][:35]:<35} sold={sold_s:>4} free={free_s:>4} "
              f"cap={cap_s:>4}  {res.get('note') or ''}")

    out = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "filterDate": only_date,
        "shows": results,
        "totals": {
            "shows": len(results),
            "coverageShows": coverage,
            "capacity": total_capacity,
            "booked": total_booked,
            "free": total_free,
        },
    }
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_FILE}")
    print(f"Coverage: {coverage}/{len(results)} shows scraped, "
          f"booked={total_booked}, free={total_free}, capacity={total_capacity}")


if __name__ == "__main__":
    main()
