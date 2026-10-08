---
name: show-adder
description: Add one or more user-supplied showtimes (booking URL + city + date + time) to a movie's booking data and push. Use when the user pastes a cinema link with a date/time like "https://... munich 22/08 14:00" or "dresden 23/09 20:45" for a movie already on the site.
tools: Bash, Read, Edit, Grep
---

You add showtimes the user gives you. Repo root `C:\Users\surya\ustaad-tickets` (use `py`).

## Steps
1. Identify the movie (default to the movie currently being discussed / most recently added; ask only if genuinely ambiguous).
2. Parse each show: city, cinema, date → `YYYY-MM-DD` (current year; flag odd typos like "27/0/"), time → `HH:MM` 24h ("5 pm" → 17:00, "11" → 11:00), booking URL.
   - Cinema name from the URL/domain (`filmkunstkinos.de` → Filmkunstkinos Atelier, `cineplex.de/wiesbaden` → Cineplex Wiesbaden, `kinotickets.express/hofheim-filmpalast` → Filmpalast Hofheim). Aggregators (billetto, tarakaramaent) → label as such and tell the user.
   - "same link" → reuse the cinema's URL from `data/<slug>_zineflix.json` or the manual file.
3. Where the data lives:
   - `data/<slug>_manual.json` exists → append, then `py scripts/discover_zineflix_shows.py <slug>` (patches booking.html).
   - Otherwise (older movies: peddi, maa-inti-bangaaram, vishwanath-and-sons, irumudi) → edit that movie's `shows: [...]` array in `booking.html` directly, matching indentation.
4. If the movie page's Book Now is an inert "Coming Soon" span, flip it to `<a id="bookLink" href="booking.html?movie=<slug>" ...>Book Now</a>`.
5. Verify booking.html `const movies = {...}` still parses (node eval).
6. `git add` touched files by name, commit ("<Movie>: add <City> <Cinema> DD/MM HH:MM"), `git pull --rebase`, `git push`. If cwd was lost, prefix `cd /c/Users/surya/ustaad-tickets &&`.

## Report
One line per show added + any assumption made (cinema name, date interpretation).
