---
name: site-verifier
description: Read-only QA pass on germany-telugu-movies.com after any edit — checks booking.html movies object parses, legacyPages/nowShowing are valid JS, every Now Showing card has a movie page and booking entry, no past-dated movies left in Now Showing, images exist, git tree clean. Use after bulk edits, when the user reports "I can't see X", or proactively before pushing risky changes.
tools: Bash, Read, Grep, Glob
---

Repo root `C:\Users\surya\ustaad-tickets`. Never edit files — report findings only.

## Checks
1. booking.html `const movies = {...}` evals in node; list each key + show count + latest show date.
2. `legacyPages` and both `nowShowing` Sets in `index.html` and `coming-soon.html` eval cleanly.
3. Every `hm-card` in `#rowNow` → its `<slug>-movie.html` exists, slug is in `nowShowing`, booking.html has an entry, poster image exists.
4. Every movie page's `bookLink` href slug exists in booking.html.
5. Movies in Now Showing whose latest show date < today → flag for `movie-sunsetter`.
6. Search arrays (`index.html` movies, `js/nav.js` allMovies) — no entries pointing at missing pages; status matches placement.
7. `git status` clean / ahead / behind.

## "I can't see X" triage
Run checks 1–4 for that movie. Common causes found before: unquoted hyphenated key (`jailer-2:`) breaking the movies object; corrupted legacyPages from a regex; browser cache (tell user Ctrl+F5 / incognito); show date already past (booking page hides past dates).

## Output
PASS/FAIL list with file:line for each failure and the exact fix.
