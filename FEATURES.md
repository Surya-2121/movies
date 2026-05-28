# Germany Telugu Movies — Features & Architecture

This document describes how the site is built, how the **Peddi** booking +
revenue system works end-to-end, and **how to replicate it for any future
movie**. Peddi is the reference implementation; everything here generalises.

Live site: <https://germany-telugu-movies.com> (GitHub Pages, repo `Surya-2121/movies`, deploys on push to `main`).

---

## 1. Pages — what each one is and how it's built

All pages are hand-authored static HTML + vanilla JS + one shared stylesheet
(`css/style.css`). No build step, no bundler. Firebase (client SDK) provides
auth, the interested/notify counters, ratings, and admin-edited movie metadata.

| Page | Purpose | How it's built |
|---|---|---|
| `index.html` | Landing page | Top-left `site-header` logo; a full-screen **hero** with a dimmed poster-grid background (`hero-poster-grid`, opacity 0.45, uniform 2:3 posters) and the **Movies + Coming Soon** cards overlaid on top (`hero-foreground`, z-index 2). The Movies column shows the current now-playing card; Coming Soon is an auto-sliding carousel. Both are seeded with static cards, then **overridden by live Firebase data** when present. Has its own search (`handleHomeSearch`). |
| `booking.html` | Showtimes + ticket links for one movie | Reads `?movie=<slug>` and looks it up in an in-file `const movies = { <slug>: { title, genre, language, page, shows:[...] } }`. Renders a **date-tab bar** + a **2-column city accordion**: each city is a collapsible card; clicking it reveals the cinemas in that city with their showtime pills. City names + grouping mirror Zineflix. The `shows` block is **auto-regenerated** by `scripts/discover_peddi_shows.py`. |
| `<slug>-movie.html` | Movie landing page (e.g. `peddi-movie.html`, `dragon-movie.html`) | Backdrop banner + poster, title/meta, **Interested / Notify Me** bar (pre-release) that switches to **Rate + Book Now** after the release date. Sections: About, Cast & Crew, Songs, Trailer/Teaser/Glimpse. "Book Now" links to `booking.html?movie=<slug>`. Includes `js/admin-bar.js` for live Firebase editing by the admin. |
| `coming-soon.html` | Grid of upcoming movies | Firebase-driven (`movies/<slug>.status === 'Coming Soon'`), plus a `staticAdditions` list for movies not yet in Firebase, minus a `hidden`/`nowShowing` filter. |
| `admin-revenue-peddi.html` | **Admin-only** revenue dashboard | Firebase-Auth gated (only `suryasumanth001@gmail.com`). Reads `data/peddi_seats.json` and renders a **Premiere-day table** + an **All-shows table** with Seats / Booked / Free / Occupancy % / Price / Gross, summary cards, a premiere countdown, and "Export as JPG" (html2canvas) on each table. |
| `movie.html` | Generic fallback movie page | Driven by `?id=<slug>` + Firebase, for movies without a dedicated page. |
| `login.html` | Email/password auth | Firebase Auth; sets the session used by the admin bar + admin dashboard. |
| `boxoffice.html`, `about.html`, `contact.html`, `reviews.html`, `predict.html` | Supporting pages | Static content + small Firebase widgets. |
| `ustaad.html` | Legacy per-movie dashboard | Driven by `js/app.js`; predates the Peddi system. |

**Theme:** light (bright) mode is the **default** site-wide. Dark mode is a
toggle in the nav menu, persisted in `localStorage['theme']`. `js/nav.js`
applies `localStorage.getItem('theme') || 'light'`; every styled block has a
`.light-theme` override in `css/style.css`.

---

## 2. Data files (the single source of truth)

| File | Written by | Read by | Contents |
|---|---|---|---|
| `data/peddi_cinemas.json` | hand + auto-onboarder | both scripts | Per-cinema **config**: city, name, Zineflix theatre name, `platform`, platform IDs, `ticketPrice`, `premierePrice`, optional `capacityOverride`, optional `seatIdByDateTime`/`manualShows`. Also the `movie` block (slug, title, genre, premiereDate, `zineflixMovieId`) and `ignoredCinemas`. |
| `data/peddi_shows.json` | `discover_peddi_shows.py` | `fetch_peddi_seats.py`, dashboards | The flat list of discovered shows: `{city, cinema, date, time, subtitle, bookingUrl}`. |
| `data/peddi_seats.json` | `fetch_peddi_seats.py` | `admin-revenue-peddi.html` | Per-show seat counts: `{…show…, capacity, booked, free, blocked, ticketPrice, gross}` + `fetchedAt`. |
| `booking.html` `const movies` block | `discover_peddi_shows.py` | the public booking page | Same shows, embedded so the page is self-contained (no extra fetch). |

---

## 3. Show discovery (Zineflix + per-cinema platforms)

Script: **`scripts/discover_peddi_shows.py`**. Flow each run:

1. **Zineflix check** — GET `https://backendzineflex.teammatrixmantra.com/api/v1/othertheatre/<zineflixMovieId>` for the current theatre list, and `/cities` for the uuid→city-name map. Each theatre is matched against the registry by `zineflixTheatreName`.
2. **New theatres** → tried against the **auto-onboarders** (see §5). Matched ones are appended to `data/peddi_cinemas.json` and used immediately; unmatched ones are logged as `NEW: …` for a manual add.
3. **Per-cinema discovery** — for every cinema in the registry, the handler for its `platform` is called to fetch current dates/times + booking URLs.
4. **Write** `data/peddi_shows.json` and **regenerate** the `const movies = {…}` block in `booking.html` (brace-counting replace, same trick as `update_shows.py`).

City names come from the cinema config's `city` field, set to match Zineflix's
grouping (e.g. Aschaffenburg → Frankfurt, Viernheim → Mannheim, Braunschweig →
"Wolfsburg (Braunschweig)").

### Discovery handlers (`platform` → function)

| `platform` | Source | How shows are found |
|---|---|---|
| `cineamo` | Cineamo API | `GET api.cineamo.com/cinemas/<cineamoCinemaId>/showings-future?contentId=<cineamoContentId>` → `startDatetime` (UTC→Berlin) + `bookingUrlExternal`/`ticketUrls.default`. Covers Cincinnati, Lux, UFA, Filmpalast, Cinemoon. |
| `cineamo_to_kinotickets` | Cineamo API | Same as `cineamo`; booking URL is a `kinotickets.express/.../booking/N` link (normalised to `/sale/seats/N`). |
| `cinetixx` | Cineamo API | Same as `cineamo` (Cincinnati books via cinetixx). |
| `kinoheld_graphql` | Cineamo API | Cinemoon Pforzheim — Cineamo lists the show; booking is a kinoheld widget URL. |
| `kinoheld_cinetixx` / `kinoheld_showgroup` | Kinoheld GraphQL | `next-live.kinoheld.de/graphql` `showGroup(uuid).shows.data` (Dresden). Note the showGroup **uuid rotates** and must be refreshed when discovery returns 0. |
| `capitol_cineweb` | Cinema film page | Parse JSON-LD `ScreeningEvent`s on `capitol-kornwestheim.de/film/peddi`; map (date,time)→kinotickets seat id via `seatIdByDateTime`. |
| `cineweb_termine` | Cinema film page | Parse the embedded `termine` JS block (Cinefactory Mönchengladbach) → kinotickets booking links. |
| `premiumkino` | Premiumkino sitemap | `backend.premiumkino.de/v1/de/<cinema>/sitemap` → `vorstellung/<slug>/YYYYMMDD/HHMM/...` (Astor). |
| `kinopolis` | Cinema film page | Parse `data-performance-id` blocks on `kinopolis.de`/`mathaeser.de` film page → showtime + `/programm/vorstellung/<id>` link. |
| `cinestar` | CineStar API | `GET cinestar.de/api/show/<cinestarShowId>` → `showtimes[].datetime`. Booking is the cinema event page. |
| `manual` | hand-entered | Returns the cinema config's `manualShows: [{date, time, bookingUrl}]` (used for cinemas whose backend is locked, e.g. Apollo Aachen). |

---

## 4. Revenue / seat tracking — number of tickets booked

Script: **`scripts/fetch_peddi_seats.py`**. It reads the show list from
`data/peddi_shows.json`, picks each cinema's `ticketPrice`/`premierePrice` from
`data/peddi_cinemas.json`, scrapes seat counts per show, and writes
`data/peddi_seats.json` with:

```
booked  = seats sold for that show
free    = available seats
blocked = admin-blocked / not-for-sale
capacity = booked + free + blocked   (or cinema "capacityOverride")
gross   = booked × (premierePrice if date == premiereDate else ticketPrice)
```

The handler is chosen from the **booking URL pattern**:

| Platform (URL) | Seat-count method |
|---|---|
| **cinetixx** (`booking.cinetixx.de`, and Dresden `kinoheld.de/.../vorstellung/<cinetixxId>`) | `GET /api/shows/<id>/sectors` then `/sector/<sectorId>`. Each seat has a `state`: `F`=free, `S`=sold, `B`=blocked; rows with `isGap:true` are skipped (aisles). |
| **kinotickets.express** (Capitol, UFA, Filmpalast, Mönchengladbach) | Scrape the seat page: each seat is a `seat-dim-1x1` element — `<button>` = free, `<div>` = sold. |
| **kinoheld GraphQL** (Cinemoon Pforzheim) | GraphQL `show(id).seats { status }`; SOLD/RESERVED/NOTED = booked, BLOCKED/SOCIAL_DISTANCE = blocked, FREE = free. The widget's public showId is resolved to the internal id via GraphQL first. |
| **premiumkino** (Astor) | `GET backend.premiumkino.de/v1/de/<cinema>/performance/<id>` → `occupation.occupiedSeats` length = booked. Capacity not exposed → `capacityOverride`. |
| **ticket-cloud.de** (Lux Heidelberg) | Stateful: load the show page for `informationString` + session cookie → POST `Method=Show` to `systemConnector.php` → read the `#Plain` field (ShowID,AudiID,SeatVariantID,SiteID) → POST `Method=PlainSeatPlan` → count `Seat_*.png` images (`_Sold`=sold, `_UnAvailable`=blocked, else free). Has retry/backoff. |
| **kinopolis** (`kinopolis.de`, `mathaeser.de`) | The film page lists each show with `prog2__seats` (capacity) + `prog2__scale … P% frei`; `booked = capacity × (100−P)/100`. |
| **cinestar** (`cinestar.de`) | **Click-through only** — Vista backend doesn't expose seats; returns `booked=null` (dashboard shows "—"). |
| **manual / apollo / unmapped Capitol** | Returns `booked=null` (no seat data; click-through). |

Prices live in `PRICES` (regular) and `PREMIERE_PRICES` (premiere day) dicts in
the script, keyed by cinema **name**; `CAPACITY_OVERRIDE` handles cinemas whose
API doesn't expose total seats (e.g. Munich Cincinnati = 401, Astor = 200).
Shows with `booked=null` are skipped in the gross totals.

---

## 5. Auto-onboarding new cinemas

When Zineflix lists a theatre we don't have, `discover_peddi_shows.py` tries
each function in `AUTO_ONBOARDERS` against the redirect URL. A match writes a
new entry into `data/peddi_cinemas.json` automatically:

| Auto-onboarder | Matches URL like |
|---|---|
| `_auto_onboard_kinopolis` | `kinopolis.de/<code>/filmdetail/…` or `mathaeser.de/…` |
| `_auto_onboard_premiumkino` | `<cinema>.premiumkino.de/…` |
| `_auto_onboard_cinestar` | `cinestar.de/<slug>/veranstaltung-…` (tolerates Zineflix's doubled/mistyped URLs; reads `data-show-id` from the page) |
| `_auto_onboard_cinefactory` | `<cinema-domain>/detail/<id>/<slug>` (cineweb termine) |

Platforms that need extra lookups (Cineamo cinemaId, Kinoheld showGroup uuid)
or a locked backend (ticket-cloud, Apollo) are **logged** for a one-time manual
add instead of auto-onboarded.

---

## 6. GitHub Actions workflows

| Workflow | Trigger | Runs | Commits |
|---|---|---|---|
| **Discover Peddi Shows (daily)** `discover-peddi-shows.yml` | cron `0 6,11,13,16 * * *` + `30 21 * * *` = **08:00, 13:00, 15:00, 18:00, 23:30 Berlin**, plus manual | `discover_peddi_shows.py` | `booking.html`, `data/peddi_shows.json` |
| **Update Peddi Revenue Board** `update-peddi-seats.yml` | **manual only** (`workflow_dispatch`) | discovery **+** `fetch_peddi_seats.py` | `booking.html`, `data/peddi_shows.json`, `data/peddi_seats.json` |

So **new shows appear automatically** (5×/day), but the **revenue board only
refreshes when triggered** (by request).

> The legacy `update-shows.yml` (3 Realms scraper) has an **empty `MOVIE_MAP`**
> so it no longer rewrites `booking.html`.

---

## 7. How to operate it (recipes)

**Refresh the revenue board**
- GitHub: Actions → "Update Peddi Revenue Board" → Run workflow, **or**
- Local: `py scripts/fetch_peddi_seats.py` then commit `data/peddi_seats.json`.

**Pick up new shows / cinemas now (instead of waiting for cron)**
- GitHub: Actions → "Discover Peddi Shows" → Run workflow, **or**
- Local: `py scripts/discover_peddi_shows.py` then commit `booking.html` + `data/peddi_shows.json`.

**Add a new cinema by hand** (when auto-onboard logs `NEW:`): add an entry to
`data/peddi_cinemas.json` `cinemas[]` with the right `platform` + IDs + prices,
then run discovery.

**View the dashboard**: sign in at `/login.html` as the admin email, then open
`/admin-revenue-peddi.html`.

---

## 8. Replicating this for a NEW movie

Peddi is the template. To stand up the same system for movie `<X>`:

1. **Movie page** — copy `peddi-movie.html` → `<X>-movie.html`; update title,
   poster (`images/<X>.jpg`), backdrop, cast, songs, trailer, Firebase keys
   (`interested/<X>`, `notify/<X>`, `ratings/<X>`), and the release date.
2. **Home + Coming Soon** — add the card to `index.html` and `coming-soon.html`
   (and `js/nav.js` search index). Use the `staticAdditions`/`nowShowing`
   filters to move it between Coming Soon and Now Showing.
3. **Find the Zineflix movie id** — `…/api/v1/othertheatre/<id>`; put it in a
   new `data/<X>_cinemas.json` `movie.zineflixMovieId`, plus the movie's
   premiere date and the Cineamo `contentId` if applicable.
4. **Copy the scripts** — `discover_peddi_shows.py` and `fetch_peddi_seats.py`
   are movie-agnostic except for the data-file paths and a couple of hardcoded
   slugs (Cinemoon kinoheld `cinemaId`, Kinopolis `peddi-telugu/<id>` film-URL
   pattern). Parameterise those per movie, or fork the scripts to `<X>_*`.
5. **Add the booking entry** — `booking.html?movie=<X>` works once the
   `const movies` block has an `<X>` key (discovery regenerates it).
6. **Admin dashboard** — copy `admin-revenue-peddi.html` → `admin-revenue-<X>.html`
   pointing at `data/<X>_seats.json`.
7. **Workflows** — clone the two workflow YAMLs for `<X>` (discovery on cron,
   revenue on manual dispatch).

The cinema platform handlers (cinetixx, kinopolis, kinotickets, premiumkino,
kinoheld, ticket-cloud, cinestar, cineweb, manual) are **reusable as-is** —
only the per-cinema IDs in the registry change between movies.
