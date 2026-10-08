"""
Sunset ended movies — remove them from the site's Now Showing surfaces
once every one of their showtimes has passed.

Scans booking.html's `const movies = { ... }` block, finds every movie
whose latest show date < today (Berlin time), and strips it from:

  - index.html         : hm-card `<a href="<slug>-movie.html">...</a>`,
                         nowShowing Set, movies search array
  - coming-soon.html   : nowShowing Set
  - js/nav.js          : allMovies search array
  - scripts/send_notify.py : MOVIE_NAMES dict entry (optional, soft)

What we DO NOT touch (so bookmarked URLs don't 404):
  - `<slug>-movie.html`
  - booking.html's movies[<slug>] entry
  - images, Firebase data, data/<slug>_* overlays

Usage:
  py scripts/sunset_ended_movies.py              # dry-run, prints plan
  py scripts/sunset_ended_movies.py --apply      # actually edit the files
  py scripts/sunset_ended_movies.py --apply --slug toxic   # force one movie
  py scripts/sunset_ended_movies.py --today 2026-10-10     # override "today"

Protected slugs that NEVER sunset (always-on legacy pages):
  ustaad, peddi, maa-inti-bangaaram, vishwanath-and-sons, irumudi

These were already manually sunset in earlier commits — leaving them
alone to avoid double-removal attempts.
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = SCRIPT_DIR.parent
BOOKING_HTML = PROJECT_ROOT / "booking.html"
INDEX_HTML = PROJECT_ROOT / "index.html"
COMING_SOON_HTML = PROJECT_ROOT / "coming-soon.html"
NAV_JS = PROJECT_ROOT / "js" / "nav.js"
SEND_NOTIFY = PROJECT_ROOT / "scripts" / "send_notify.py"

PROTECTED = {
    "ustaad", "peddi", "maa-inti-bangaaram",
    "vishwanath-and-sons", "irumudi", "toxic",
}


# --------------------------------------------------------------------
# Berlin "today" without the tzdata dependency (same trick peddi uses)
# --------------------------------------------------------------------

def _berlin_offset_hours(dt_utc: datetime) -> int:
    year = dt_utc.year

    def last_sunday(month):
        d = datetime(year, month, 31, 1, 0, tzinfo=timezone.utc)
        while d.weekday() != 6:
            d -= timedelta(days=1)
        return d
    return 2 if last_sunday(3) <= dt_utc < last_sunday(10) else 1


def berlin_today() -> date:
    now_utc = datetime.now(timezone.utc)
    local = now_utc + timedelta(hours=_berlin_offset_hours(now_utc))
    return local.date()


# --------------------------------------------------------------------
# Parse booking.html's movies -> {slug: [date strings]}
# --------------------------------------------------------------------

def parse_booking_shows() -> dict[str, list[str]]:
    """Return {slug: [YYYY-MM-DD, ...]} per movie in booking.html."""
    html = BOOKING_HTML.read_text(encoding="utf-8")
    start = html.find("const movies = {")
    if start == -1:
        raise RuntimeError("Cannot find 'const movies = {' in booking.html")
    # Brace-count forward to find matching close.
    brace = html.index("{", start)
    depth = 0
    end = brace
    for i in range(brace, len(html)):
        if html[i] == "{":
            depth += 1
        elif html[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    movies_body = html[brace + 1:end]

    # Walk each top-level key: match a slug followed by `: {` at nesting depth 1.
    out = {}
    depth = 0
    i = 0
    key_re = re.compile(r'["\']?([a-zA-Z][a-zA-Z0-9_\-]*)["\']?\s*:\s*\{')
    while i < len(movies_body):
        c = movies_body[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif depth == 0:
            m = key_re.match(movies_body, i)
            if m:
                slug = m.group(1)
                # Find matching close of this movie's { ... } block
                sub_start = movies_body.index("{", i)
                sd = 0
                sub_end = sub_start
                for j in range(sub_start, len(movies_body)):
                    if movies_body[j] == "{":
                        sd += 1
                    elif movies_body[j] == "}":
                        sd -= 1
                        if sd == 0:
                            sub_end = j
                            break
                sub = movies_body[sub_start:sub_end + 1]
                dates = re.findall(r'"date"\s*:\s*"(\d{4}-\d{2}-\d{2})"', sub)
                out[slug] = sorted(set(dates))
                i = sub_end + 1
                continue
        i += 1
    return out


# --------------------------------------------------------------------
# Per-file surgical edits
# --------------------------------------------------------------------

def sunset_index_html(slug: str, html: str) -> tuple[str, list[str]]:
    """Remove hm-card + nowShowing entry + search-array entry for slug.
    Returns (new_html, list_of_change_descriptions)."""
    changes = []

    # 1. hm-card: full <a href="<slug>-movie.html" class="hm-card"> ... </a>
    card_re = re.compile(
        r'\s*<a href="' + re.escape(slug) + r'-movie\.html" class="hm-card">[\s\S]*?</a>',
    )
    new_html, n = card_re.subn("", html, count=1)
    if n:
        changes.append("home hm-card removed")
        html = new_html

    # 2. nowShowing Set — strip the slug + its separators
    for quote in ("'", '"'):
        pat_mid = re.compile(r"," + r"\s*" + re.escape(quote) + re.escape(slug) + re.escape(quote))
        new_html, n = pat_mid.subn("", html)
        if n:
            changes.append("nowShowing entry removed (mid)")
            html = new_html; continue
        pat_lead = re.compile(re.escape(quote) + re.escape(slug) + re.escape(quote) + r"\s*,\s*")
        new_html, n = pat_lead.subn("", html)
        if n:
            changes.append("nowShowing entry removed (lead)")
            html = new_html; continue
        pat_only = re.compile(r"new Set\(\[\s*" + re.escape(quote) + re.escape(slug) + re.escape(quote) + r"\s*\]\)")
        new_html, n = pat_only.subn("new Set([])", html)
        if n:
            changes.append("nowShowing entry removed (only)")
            html = new_html

    # 3. search `movies` array — line that includes url: '<slug>-movie.html'
    search_re = re.compile(
        r"[ \t]*\{\s*name:[^}]*url:\s*['\"]" + re.escape(slug) + r"-movie\.html['\"][^}]*\},?\s*\n",
    )
    new_html, n = search_re.subn("", html, count=1)
    if n:
        changes.append("search array entry removed")
        html = new_html

    return html, changes


def sunset_coming_soon_html(slug: str, html: str) -> tuple[str, list[str]]:
    """Remove slug from the nowShowing Set in coming-soon.html."""
    changes = []
    for quote in ("'", '"'):
        pat_mid = re.compile(r"," + r"\s*" + re.escape(quote) + re.escape(slug) + re.escape(quote))
        new_html, n = pat_mid.subn("", html)
        if n:
            changes.append("coming-soon nowShowing entry removed (mid)")
            return new_html, changes
        pat_lead = re.compile(re.escape(quote) + re.escape(slug) + re.escape(quote) + r"\s*,\s*")
        new_html, n = pat_lead.subn("", html)
        if n:
            changes.append("coming-soon nowShowing entry removed (lead)")
            return new_html, changes
    return html, changes


def sunset_nav_js(slug: str, js: str) -> tuple[str, list[str]]:
    """Remove the search entry for slug in js/nav.js."""
    changes = []
    search_re = re.compile(
        r"[ \t]*\{\s*name:[^}]*url:\s*['\"]" + re.escape(slug) + r"-movie\.html['\"][^}]*\},?\s*\n",
    )
    new_js, n = search_re.subn("", js, count=1)
    if n:
        changes.append("allMovies entry removed")
        return new_js, changes
    return js, changes


def sunset_send_notify(slug: str, src: str) -> tuple[str, list[str]]:
    """Remove the entry in MOVIE_NAMES — optional, keeps the dict tidy."""
    changes = []
    pat = re.compile(r"[ \t]*['\"]" + re.escape(slug) + r"['\"]\s*:\s*['\"][^'\"]*['\"]\s*,?\s*\n")
    new_src, n = pat.subn("", src, count=1)
    if n:
        changes.append("MOVIE_NAMES entry removed")
        return new_src, changes
    return src, changes


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser()
    p.add_argument("--apply", action="store_true",
                   help="Actually write the edits (default is dry-run).")
    p.add_argument("--slug", action="append", default=[],
                   help="Force-sunset this specific slug (repeatable). "
                        "Bypasses the date-based check.")
    p.add_argument("--today", help="Override today's date (YYYY-MM-DD).")
    args = p.parse_args()

    today = (date.fromisoformat(args.today) if args.today else berlin_today())
    print(f"Sunset check — cutoff date = {today.isoformat()} (Berlin)")

    shows_by_slug = parse_booking_shows()
    ended = []
    for slug, dates in shows_by_slug.items():
        if slug in PROTECTED:
            continue
        if slug in args.slug:
            ended.append((slug, "forced", dates[-1] if dates else "<no shows>"))
            continue
        if not dates:
            # No shows at all → treat as ended-at-registration (sunset).
            ended.append((slug, "empty", "<no shows>"))
            continue
        if dates[-1] < today.isoformat():
            ended.append((slug, "ended", dates[-1]))

    for slug in args.slug:
        if slug not in shows_by_slug:
            print(f"  [warn] --slug {slug} not found in booking.html; skipping")

    if not ended:
        print("No movies need sunsetting. ✓")
        return

    print(f"\n{len(ended)} movie(s) to sunset:")
    for slug, reason, last_date in ended:
        print(f"  - {slug:25}  (reason: {reason}, last show: {last_date})")

    if not args.apply:
        print("\n[dry-run] rerun with --apply to actually edit the files.")
        return

    for slug, _, _ in ended:
        print(f"\n→ Sunsetting {slug}:")
        for path, fn in [
            (INDEX_HTML, sunset_index_html),
            (COMING_SOON_HTML, sunset_coming_soon_html),
            (NAV_JS, sunset_nav_js),
            (SEND_NOTIFY, sunset_send_notify),
        ]:
            src = path.read_text(encoding="utf-8")
            new, changes = fn(slug, src)
            if new != src:
                path.write_text(new, encoding="utf-8")
                for c in changes:
                    print(f"    {path.name}: {c}")
            else:
                print(f"    {path.name}: no change")


if __name__ == "__main__":
    main()
