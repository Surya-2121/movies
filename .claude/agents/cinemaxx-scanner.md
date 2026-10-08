---
name: cinemaxx-scanner
description: Scan all ~30 Cinemaxx.de cities for a movie's showtimes (bypasses Cloudflare Turnstile with patchright), merge new shows into data/<slug>_manual.json and booking.html, push. Use when the user pastes a cinemaxx.de link or says "check cinemaxx for X". Slow (several minutes) — good background task.
tools: Bash, Read, Edit
---

Repo root `C:\Users\surya\ustaad-tickets` (use `py`). Requires `patchright` + local Chrome (installed on this machine).

## Steps
1. Get the Cinemaxx film slug from the URL `/kinoprogramm/<city>/film/<cinemaxxSlug>`. Ensure the movie's entry in `data/zineflix_movies.json` has `"cinemaxxSlug"` (add if missing).
2. Single URL: `py scripts/scrape_cinemaxx.py "<url>" --add-to <slug> --city "<City>" --cinema "Cinemaxx <City>"`.
3. All cities: `py scripts/discover_cinemaxx_shows.py <slug>` (long timeout / background). Writes `data/<slug>_cinemaxx.json` + `data/cinemaxx_alerts.md`, merges into the manual file, patches booking.html.
4. Language scope: drop non-Telugu sessions if the user wants Telugu only (session lang e.g. `engl. UT - Telugu`).
5. Verify booking.html parses; commit + push the manual/cinemaxx/booking files.

## Notes
- First city takes ~5–10 s to clear Turnstile; the persistent cf_clearance cookie makes the rest fast.
- Keep the `X-Bot-Contact` header identifying germany-telugu-movies.com.
- If Turnstile stops clearing, report it — don't hammer the site.
