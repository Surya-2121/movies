"""
Extract Paradise (or any film's) showtimes from a Cinemaxx.de cinema
page. Uses browser_fetch to punch through Cloudflare Turnstile.

Cinemaxx renders showtimes as:

  <div data-test="sessions-group-YYYY-MM-DDT00:00:00">
    ...
    <a class="session" href="/buchtickets/zusammenfassung/<c>/<f>/<sid>">
      <time class="session-time__start" datetime="HH:MM">HH:MM</time>
      <span class="session-special-attributes__screen-name">Kino NN</span>
      <span class="session-additional-attributes__lang">engl. UT - Telugu</span>
    </a>

Usage:
  py scripts/scrape_cinemaxx.py <film-page-url>
      -> prints every date+time+lang+booking URL

  py scripts/scrape_cinemaxx.py <film-page-url> \\
      --add-to <slug>_manual.json --city Offenbach --cinema "Cinemaxx Offenbach"
      -> also appends new entries to data/<slug>_manual.json (dedup by URL)
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from browser_fetch import fetch_rendered_html  # noqa: E402

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def extract_sessions(html: str) -> list[dict]:
    """Return [{date, time, kino, lang, href}, ...] parsed from a
    Cinemaxx film-page HTML dump. Deduplicates identical entries."""
    anchors = list(re.finditer(r'<a class="session"[^>]*href="([^"]+)"', html))
    date_markers = list(re.finditer(
        r'data-test="sessions-group-(\d{4}-\d{2}-\d{2})', html))

    seen = set()
    out = []
    for a in anchors:
        # Nearest preceding date marker.
        prev_date = None
        for d in date_markers:
            if d.start() < a.start():
                prev_date = d.group(1)
            else:
                break
        if not prev_date:
            continue
        href = a.group(1)
        body = html[a.end():a.end() + 2500]
        t = re.search(r'datetime="(\d{2}:\d{2})"[^>]*>\d{2}:\d{2}</time>', body)
        k = re.search(r'screen-name">([^<]+)</span>', body)
        L = re.search(r'__lang">([^<]+)</span>', body)
        if not t:
            continue
        key = (prev_date, t.group(1), href)
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "date": prev_date,
            "time": t.group(1),
            "kino": (k.group(1).strip() if k else ""),
            "lang": (L.group(1).strip() if L else ""),
            "href": f"https://www.cinemaxx.de{href}",
        })
    out.sort(key=lambda s: (s["date"], s["time"]))
    return out


def append_to_manual(slug: str, city: str, cinema: str, sessions: list[dict]) -> int:
    """Merge sessions into data/<slug>_manual.json, dedupe by URL. Returns
    the number of new rows added."""
    path = Path(DATA_DIR) / f"{slug}_manual.json"
    data = json.load(open(path, encoding="utf-8"))
    shows = data.setdefault("shows", [])
    have_urls = {s.get("bookingUrl") for s in shows}
    added = 0
    for sess in sessions:
        if sess["href"] in have_urls:
            continue
        subtitle = "Telugu"
        if "Telugu" in sess["lang"]:
            subtitle = (
                "Telugu (OmeU)" if re.search(r"engl|OmeU|OmU|UT", sess["lang"], re.I)
                else "Telugu"
            )
        shows.append({
            "city": city,
            "cinema": cinema,
            "date": sess["date"],
            "time": sess["time"],
            "subtitle": subtitle,
            "bookingUrl": sess["href"],
        })
        added += 1
    if added:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return added


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("url")
    p.add_argument("--add-to", metavar="<slug>",
                   help="Movie slug — appends to data/<slug>_manual.json")
    p.add_argument("--city", default="")
    p.add_argument("--cinema", default="")
    args = p.parse_args()

    print(f"[cinemaxx] fetching {args.url}")
    html = fetch_rendered_html(
        args.url,
        wait_for_regex=r"sessions__list__item|nicht im Programm",
        wait_ms=8000,
    )
    print(f"[cinemaxx] rendered {len(html)} bytes")

    sessions = extract_sessions(html)
    print(f"[cinemaxx] found {len(sessions)} session(s):")
    for s in sessions:
        print(f"  {s['date']} {s['time']}  {s['kino']:8}  ({s['lang']})")
        print(f"      -> {s['href']}")

    if args.add_to:
        if not args.city or not args.cinema:
            print("--add-to requires --city and --cinema")
            sys.exit(2)
        added = append_to_manual(args.add_to, args.city, args.cinema, sessions)
        print(f"[cinemaxx] appended {added} new row(s) to data/{args.add_to}_manual.json")


if __name__ == "__main__":
    main()
