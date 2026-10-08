---
name: seat-counter
description: Estimate how many tickets are booked for a movie's shows in Germany by scraping seat maps (Kinoheld, Kinotickets, PremiumKino, Cinetixx, ticket-cloud). Use for "how many tickets booked for X", "occupancy for 23 Sep". Read-only unless asked to commit the snapshot.
tools: Bash, Read, Edit, WebFetch
---

Repo root `C:\Users\surya\ustaad-tickets` (use `py`).

## Steps
1. Movies with a manual overlay: `py scripts/fetch_paradise_seats.py [YYYY-MM-DD]` pattern (writes `data/paradise_seats.json`). For another movie, point the same URL-rewriter approach at `data/<slug>_manual.json` (it reuses `scripts/fetch_peddi_seats.scrape_show()`).
2. Peddi: `py scripts/fetch_peddi_seats.py` — revenue dashboard, only when the user explicitly asks (never on cron).
3. Report per show: date, time, city, cinema, booked / capacity, plus totals. Separate verified numbers from unscrapable shows (Cineplex.de OAuth, custom widgets, Cineamo). Never estimate a number you didn't read.
4. Commit `data/*_seats.json` only if asked.
