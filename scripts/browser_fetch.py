"""
Headless-browser HTML fetcher that clears Cloudflare Turnstile /
similar bot-challenge pages.

Used as a fallback when a plain `urllib` / `curl` fetch returns a
challenge page (Cinemaxx.de, some Cineplex-family sites, etc.).

Backend: **patchright** (a Playwright fork with anti-detection
patches), driving the local Chrome installation in headed mode.
Headed + persistent user-data-dir is what actually clears Turnstile —
plain headless Chromium fails almost every time.

Public API (single function):

    fetch_rendered_html(url, *, wait_for_selector=None,
                        wait_for_regex=None, wait_ms=6000,
                        challenge_timeout_s=60) -> str

Returns the fully-rendered page HTML after any bot challenge has
cleared and the SPA has had a chance to render. Callers can optionally
wait for a specific CSS selector or a text/regex pattern to appear in
the DOM before returning.

CI note: this file works locally with a real Chrome install. On GitHub
Actions, install patchright + a Chrome build (or run under `xvfb-run`
so headed mode still has a display) — see docs/browser_fetch_ci.md.
"""
import os
import re
import sys
from pathlib import Path
from typing import Optional

try:
    from patchright.sync_api import sync_playwright
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "browser_fetch requires patchright. Install with:\n"
        "    py -m pip install patchright && py -m patchright install chromium"
    ) from e


# Persistent user-data dir so cf_clearance cookies survive between runs —
# subsequent fetches of the same site skip the challenge entirely.
USER_DATA = Path(os.environ.get(
    "BROWSER_FETCH_USER_DATA",
    Path.home() / ".cache" / "gtm_browser_fetch",
))

_CHALLENGE_TITLE_RE = re.compile(
    r"Just a moment|Nur einen Moment|Attention Required|Un momento",
    re.I,
)


def fetch_rendered_html(
    url: str,
    *,
    wait_for_selector: Optional[str] = None,
    wait_for_regex: Optional[str] = None,
    wait_ms: int = 6000,
    challenge_timeout_s: int = 60,
    headless: bool = False,
) -> str:
    """Return the fully-rendered HTML for `url`.

    - Passes through Cloudflare Turnstile / "Just a moment..." by waiting
      up to `challenge_timeout_s` seconds for the page title to leave
      the known challenge phrases.
    - Then waits `wait_ms` ms for the SPA to hydrate. If
      `wait_for_selector` or `wait_for_regex` is given, waits for that
      instead (bounded to 30s).
    - Uses a persistent user-data dir so the cf_clearance cookie is
      reused on subsequent calls — the second fetch of a given host is
      typically instant.

    Headless is off by default because Turnstile detects headless
    Chromium. Under CI, run this script under `xvfb-run` so the "headed"
    browser still runs invisibly.
    """
    USER_DATA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA),
            channel="chrome",
            headless=headless,
            no_viewport=True,
        )
        try:
            page = ctx.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=90000)

            # 1. Clear any bot challenge.
            for _ in range(challenge_timeout_s):
                title = page.title()
                if title.strip() and not _CHALLENGE_TITLE_RE.search(title):
                    break
                page.wait_for_timeout(1000)

            # 2. Wait for the page to actually render.
            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=30000)
                except Exception:
                    pass
            elif wait_for_regex:
                escaped = wait_for_regex.replace("\\", "\\\\").replace('"', '\\"')
                try:
                    page.wait_for_function(
                        f"() => new RegExp(\"{escaped}\").test(document.body.textContent)",
                        timeout=30000,
                    )
                except Exception:
                    pass
            else:
                page.wait_for_timeout(wait_ms)

            return page.content()
        finally:
            ctx.close()


# --------------------------------------------------------------------
# CLI entry point — quick sanity check:
#   py scripts/browser_fetch.py <url>
# --------------------------------------------------------------------
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("Usage: py scripts/browser_fetch.py <url>")
        sys.exit(2)
    html = fetch_rendered_html(sys.argv[1])
    print(f"[browser_fetch] rendered {len(html)} bytes")
    if len(sys.argv) >= 3:
        out = Path(sys.argv[2])
        out.write_text(html, encoding="utf-8")
        print(f"[browser_fetch] wrote {out}")
