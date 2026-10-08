---
name: movie-sunsetter
description: Remove a movie from Now Showing surfaces (home card, nowShowing sets, search indexes, notify list) — because all its shows have passed or because the user asked. Keeps the movie page and booking entry so links still work. Use for "remove X from now showing", "X is done", "why is X still showing".
tools: Bash, Read, Edit, Grep
---

Repo root `C:\Users\surya\ustaad-tickets` (use `py`).

## Steps
1. Dry run: `py scripts/sunset_ended_movies.py` — lists movies whose last booking.html show date < today (Berlin).
2. Apply:
   - Ended movies: `py scripts/sunset_ended_movies.py --apply`
   - Force one movie: `py scripts/sunset_ended_movies.py --apply --slug <slug>`
   - Slugs in the script's `PROTECTED` set are skipped — edit by hand if the user insists.
3. Verify (mandatory — a regex slip here has broken the site before):
   ```
   node -e "const fs=require('fs');for(const f of ['index.html','coming-soon.html']){const h=fs.readFileSync(f,'utf-8');const m=h.match(/legacyPages\s*=\s*(\{[\s\S]*?\})/);try{eval('('+m[1]+')');console.log(f,'OK')}catch(e){console.log(f,'FAIL',e.message)}}"
   ```
   Confirm the hm-card is gone from `#rowNow` and the slug is gone from both `nowShowing` Sets, the index.html `movies` array, and `js/nav.js` `allMovies`.
4. Commit + push `index.html coming-soon.html js/nav.js scripts/send_notify.py`.

## Never touch
`<slug>-movie.html`, the booking.html entry, images, Firebase data, `data/<slug>_*` files.
