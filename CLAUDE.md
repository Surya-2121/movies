# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Static website for **Germany Telugu Movies** (germany-telugu-movies.com) — discovery, showtimes, and booking links for Telugu film premieres across Germany. Hosted on GitHub Pages (CNAME points to custom domain). Deploys via `git push` to `main` on the `Surya-2121/movies` repo.

## Common commands

Run from the repo root. Most day-to-day actions are bundled in `ustaad-tickets.cmd` (Windows batch menu), but the underlying commands are:

```bash
# Local preview (serves on http://localhost:8000)
python -m http.server 8000

# Scrape 3 Realms for current showtimes, update booking.html
python scripts/update_shows.py

# Legacy seat-data scraper (updates js/app.js + data/seat_data.json for ustaad.html dashboard)
python scripts/fetch_seats.py

# Send ticket-live notification emails (requires SMTP_USER, SMTP_PASS, firebase-key.json)
python scripts/send_notify.py <movie_key> <booking_url>
python scripts/send_notify.py welcome <email> [name]
python scripts/send_notify.py welcome-all
```

Python dependencies for the scrapers: `pip install requests beautifulsoup4`. For `send_notify.py` also: `pip install firebase-admin`.

No build step, no bundler, no test suite — pages are hand-authored HTML + vanilla JS + one shared CSS file.

## Architecture

### Page model
Each movie has a dedicated landing page (`<slug>-movie.html`, e.g. `dacoit-movie.html`, `peddi-movie.html`) with hero, cast, trailer, songs, and a "Book Tickets" CTA that links to `booking.html?movie=<slug>`. `booking.html` is a single BookMyShow-style UI that reads showtimes from an in-file `const movies = { ... }` object and filters by date + cinema search. `movie.html` is a generic fallback driven by `?id=<slug>` + Firebase data for movies that don't have a dedicated page yet.

`index.html` is the landing page and self-contains its own search + coming-soon carousel (which it overrides with live Firebase data when available). `ustaad.html` is a legacy per-movie dashboard driven by `js/app.js` and the `// SEAT_DATA_START ... // SEAT_DATA_END` markers that `fetch_seats.py` rewrites.

### Shared JS (`js/`)
- **`nav.js`** — site-wide nav menu toggle, theme toggle (persisted in `localStorage`), Firebase auth-aware login link, and a movie-search helper. **Do not redefine `toggleSearch` / `handleSearchInput` in page-local scripts** (see `feedback_navjs` memory) — nav.js guards against overwriting these via `if (!window.toggleSearch)`, but a clashing earlier-loaded definition will break the nav search. Use different function names for per-page search (see `index.html`'s `handleHomeSearch`).
- **`admin-bar.js`** — fixed bottom bar that only renders when the logged-in user is `suryasumanth001@gmail.com` (the `ADMIN_EMAIL` constant). Provides inline edit controls on `*-movie.html` pages. It calls `getApp()` first to reuse the page's existing default Firebase app so auth state is shared; only initializes its own app as a fallback. Include via `<script src="js/admin-bar.js" type="module"></script>`.
- **`app.js`** — only used by `ustaad.html`. Renders shows from the `showsData` array and `seatData` blob; both are rewritten in-place by `scripts/fetch_seats.py`.

### Firebase backend (client-side SDK, no server)
All pages use the same Firebase Realtime Database project: `gtm-counter` (`https://gtm-counter-default-rtdb.europe-west1.firebasedatabase.app`). The config is duplicated inline across pages and in `js/admin-bar.js` / `js/nav.js` — when editing it, update every copy. Firebase provides:
- **Auth** (email/password) — login/register on `login.html`; user profile node at `users/<uid>`.
- **Realtime DB** — `movies/<slug>` (metadata, posters, trailers, songs edited via admin bar), `notify/<movie_key>` (per-movie email subscribers), `users/<uid>.notifyAll` (registered users opted into all notifications).
- **Storage** — movie poster uploads.

Security rules live in the Firebase console (not in repo) and **expire periodically** — renew them via the console when users report write failures (see `feedback_firebase` memory).

### Scrapers and CI
Two GitHub Actions workflows in `.github/workflows/` run on cron against the scraper scripts, commit changes as `github-actions[bot]`, and push back to `main`:

| Workflow | Cron | Script | Target |
|---|---|---|---|
| `update-shows.yml` | `0 */6 * * *` | `scripts/update_shows.py` | `booking.html` `const movies = { ... }` |
| `update-seats.yml` | `0 * * * *` | `scripts/fetch_seats.py` | `js/app.js` + `data/seat_data.json` + `ustaad.html` |

`update_shows.py` scrapes `https://3realmsentertainment.com/movie/<id>/` pages discovered from `/latest-movies`, `/up-movies`, and `/`. It only rewrites entries for movies listed in its `MOVIE_MAP` dict. **To onboard a new movie to the auto-scraper, add a key (matching a case-insensitive substring of the 3 Realms title) to `MOVIE_MAP` with `slug`, `title`, `genre`, `language`, `page`.** Movies not in the map are logged and skipped. The script rewrites `booking.html` by brace-counting from `const movies = {` — preserve that literal prefix when editing.

`fetch_seats.py` is regex-based and specific to the Ustaad Bhagat Singh page on 3 Realms (hard-coded `THREEALMS_URL`, hard-coded `2026-03-<dd>` year/month in `_extract_date_time`). It injects JSON into `js/app.js` between the `// SEAT_DATA_START` / `// SEAT_DATA_END` markers — preserve those markers when editing `app.js`.

### New-movie checklist
When adding a new Telugu film to the site:
1. Create `<slug>-movie.html` (copy an existing movie page as a template).
2. Add poster + card to `index.html` (home grid) and `coming-soon.html`.
3. Add the movie to the `movies` array in `index.html` and `allMovies` in `js/nav.js` (search index).
4. Add an entry to `MOVIE_MAP` in `scripts/update_shows.py` once shows appear on 3 Realms.
5. Add the movie key + display name to `MOVIE_NAMES` in `scripts/send_notify.py` for notification emails.
6. Ensure the movie page includes `<script src="js/admin-bar.js" type="module"></script>` so the admin can edit Firebase metadata live.

## Style conventions

**Booking page** (`booking.html`): keep the BookMyShow-style layout (sticky header, horizontal date tabs, grouped cinema cards). Use the site's orange accent `#f0ad4e` on dark `#0f0f1a` (dark theme) and `#d4880f` on `#f5f5f5` (light theme). Do **not** display 3 Realms branding, "powered by" credits, or external-source attribution anywhere in the booking UI (see `feedback_booking_style` memory).

**Theme**: every page supports a dark/light toggle driven by `document.body.classList.toggle('light-theme', ...)` with preference in `localStorage['theme']`. When adding new styled sections, always author a `.light-theme` override.

**Home "Movies" column** (`index.html`): the card slot has a **fixed height** (`210px` desktop / `160px` ≤768px / `130px` ≤480px) shared between `.now-playing-card` (an actual movie) and `.no-shows-card` (the "No shows available" placeholder). Keep any new variant you add within this fixed footprint so swapping a movie in/out doesn't shift the layout against the Coming Soon column next to it.

## Admin

The admin-bar scripts gate on email equality against `suryasumanth001@gmail.com`. This is the site owner's account and also the contact point for SMTP notification emails (`FROM_EMAIL` defaults to `SMTP_USER`).
