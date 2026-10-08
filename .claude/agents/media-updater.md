---
name: media-updater
description: Add or replace trailers, teasers, glimpses, songs, posters, backdrops, synopsis or cast details on an existing movie page. Use for "add trailer <youtube link> to X", "add songs", "change poster", "update synopsis".
tools: Bash, Read, Edit, Grep
---

Repo root `C:\Users\surya\ustaad-tickets`.

## Patterns (match existing markup in `<slug>-movie.html`)
- Video section (Trailer / Teaser / Glimpse):
  ```html
  <section class="mp-section">
    <h2 class="mp-section-title">Trailer</h2>
    <div class="mp-video">
      <iframe src="https://www.youtube.com/embed/<ID>" title="<Movie> Trailer" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
    </div>
  </section>
  ```
  Order: Trailer above Teaser above Glimpse.
- Songs: inside `<div class="mp-songs">` add
  `<a href="https://www.youtube.com/watch?v=<ID>" target="_blank" rel="noopener" class="mp-song-card"><div class="mp-song-icon">&#9835;</div><span><Song Title></span></a>`
- Extract the YouTube ID from any URL form (`watch?v=ID&list=...`, `youtu.be/ID`) — strip playlist/start_radio params.
- Poster/backdrop: copy the file into `images/`, update `src` in the movie page AND the home-page hm-card (`index.html`) AND any `staticAdditions` poster in index/coming-soon.

## Finish
Commit the touched files by name + push. Tell the user to Ctrl+F5 if they don't see it (GitHub Pages cache ~1–2 min).
