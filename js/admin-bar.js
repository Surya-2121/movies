// Admin Bar for Movie Pages
// Only visible when logged in as admin (suryasumanth001@gmail.com)
// Include this script on any movie page: <script src="js/admin-bar.js" type="module"></script>

import { initializeApp } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-app.js";
import { getAuth, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-auth.js";
import { getDatabase, ref, get, set } from "https://www.gstatic.com/firebasejs/11.4.0/firebase-database.js";

const ADMIN_EMAIL = 'suryasumanth001@gmail.com';
const firebaseConfig = {
  apiKey: "AIzaSyDmGjpEbIo3YupHpWSc8rgzXWESF5-IPCQ",
  authDomain: "gtm-counter.firebaseapp.com",
  databaseURL: "https://gtm-counter-default-rtdb.europe-west1.firebasedatabase.app",
  projectId: "gtm-counter",
  storageBucket: "gtm-counter.firebasestorage.app",
  messagingSenderId: "424507047798",
  appId: "1:424507047798:web:ab288d3575e67917abc457"
};

const app = initializeApp(firebaseConfig, 'adminBar');
const auth = getAuth(app);
const db = getDatabase(app);

// Extract movie slug from URL (e.g. dacoit-movie.html -> dacoit)
const pageName = window.location.pathname.split('/').pop();
const movieSlug = pageName.replace('-movie.html', '');

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str || '';
  return d.innerHTML;
}

function extractYouTubeId(url) {
  if (!url) return '';
  const m = url.match(/(?:youtube\.com\/watch\?v=|youtube\.com\/embed\/|youtu\.be\/)([^&?/]+)/);
  return m ? m[1] : url;
}

// Inject CSS
const style = document.createElement('style');
style.textContent = `
  .ab-bar { position:fixed; bottom:0; left:0; right:0; background:#1a1a2e; border-top:2px solid #f0ad4e; padding:10px 16px; z-index:9999; display:flex; align-items:center; gap:8px; overflow-x:auto; -webkit-overflow-scrolling:touch; }
  .ab-bar::-webkit-scrollbar { display:none; }
  .ab-label { color:#f0ad4e; font-size:0.75rem; font-weight:700; white-space:nowrap; margin-right:4px; }
  .ab-btn { background:rgba(240,173,78,0.15); color:#f0ad4e; border:1px solid #f0ad4e; padding:8px 14px; border-radius:8px; font-size:0.78rem; font-weight:600; cursor:pointer; white-space:nowrap; transition:all 0.2s; font-family:inherit; }
  .ab-btn:hover { background:#f0ad4e; color:#000; }
  .ab-btn-danger { border-color:#f44336; color:#f44336; background:rgba(244,67,54,0.1); }
  .ab-btn-danger:hover { background:#f44336; color:#fff; }
  .ab-modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:10000; display:flex; align-items:center; justify-content:center; padding:20px; }
  .ab-modal { background:#1a1a2e; border:1px solid #2a2a4a; border-radius:14px; width:100%; max-width:520px; max-height:85vh; overflow-y:auto; padding:24px; }
  .ab-modal h3 { color:#f0ad4e; font-size:1.1rem; margin-bottom:16px; }
  .ab-input { width:100%; background:#0f0f1a; border:1px solid #2a2a4a; color:#e0e0e0; padding:10px 12px; border-radius:8px; font-size:0.85rem; margin-bottom:10px; box-sizing:border-box; font-family:inherit; }
  .ab-input:focus { outline:none; border-color:#f0ad4e; }
  .ab-textarea { min-height:80px; resize:vertical; }
  .ab-row { display:flex; gap:8px; align-items:center; margin-bottom:8px; }
  .ab-row .ab-input { margin-bottom:0; }
  .ab-save { background:#f0ad4e; color:#000; border:none; padding:10px 20px; border-radius:8px; font-size:0.85rem; font-weight:700; cursor:pointer; width:100%; margin-top:8px; font-family:inherit; }
  .ab-save:hover { background:#e09d3e; }
  .ab-cancel { background:transparent; color:#999; border:1px solid #2a2a4a; padding:10px 20px; border-radius:8px; font-size:0.85rem; cursor:pointer; width:100%; margin-top:6px; font-family:inherit; }
  .ab-cancel:hover { border-color:#999; color:#e0e0e0; }
  .ab-msg { text-align:center; padding:8px; border-radius:6px; font-size:0.8rem; margin-top:8px; }
  .ab-msg-ok { background:rgba(76,175,80,0.15); color:#4caf50; }
  .ab-msg-err { background:rgba(244,67,54,0.15); color:#f44336; }
  .ab-song-row { display:flex; gap:6px; align-items:center; margin-bottom:6px; }
  .ab-song-row .ab-input { flex:1; margin-bottom:0; }
  .ab-remove { background:none; border:none; color:#f44336; font-size:1.3rem; cursor:pointer; padding:4px 8px; }
  .ab-subtitle { color:#999; font-size:0.75rem; margin-bottom:4px; }
  .ab-add-btn { background:rgba(240,173,78,0.1); color:#f0ad4e; border:1px dashed #f0ad4e; padding:8px; border-radius:8px; font-size:0.8rem; cursor:pointer; width:100%; margin-bottom:10px; font-family:inherit; }
  .ab-add-btn:hover { background:rgba(240,173,78,0.2); }
  .ab-status-group { display:flex; gap:8px; margin-bottom:12px; }
  .ab-status-opt { flex:1; padding:10px; border:1px solid #2a2a4a; border-radius:8px; text-align:center; font-size:0.8rem; cursor:pointer; color:#999; transition:all 0.2s; }
  .ab-status-opt.active { border-color:#f0ad4e; color:#f0ad4e; background:rgba(240,173,78,0.1); }
  .ab-status-opt:hover { border-color:#f0ad4e; }

  /* Light theme */
  .light-theme .ab-bar { background:#fff; border-top-color:#d4880f; }
  .light-theme .ab-label { color:#d4880f; }
  .light-theme .ab-btn { background:rgba(212,136,15,0.1); color:#d4880f; border-color:#d4880f; }
  .light-theme .ab-btn:hover { background:#d4880f; color:#fff; }
  .light-theme .ab-modal { background:#fff; border-color:#ddd; }
  .light-theme .ab-modal h3 { color:#d4880f; }
  .light-theme .ab-input { background:#f5f5f5; border-color:#ddd; color:#222; }
  .light-theme .ab-input:focus { border-color:#d4880f; }
  .light-theme .ab-save { background:#d4880f; color:#fff; }
  .light-theme .ab-cancel { color:#666; border-color:#ddd; }
  .light-theme .ab-status-opt { border-color:#ddd; color:#888; }
  .light-theme .ab-status-opt.active { border-color:#d4880f; color:#d4880f; background:rgba(212,136,15,0.1); }

  /* Push page content up so admin bar doesn't cover it */
  body.ab-active { padding-bottom:60px; }
`;
document.head.appendChild(style);

// Load movie data from Firebase and show admin bar
onAuthStateChanged(auth, async (user) => {
  if (!user || user.email !== ADMIN_EMAIL) return;

  // Load movie data from Firebase
  let movieData = {};
  try {
    const snap = await get(ref(db, 'movies/' + movieSlug));
    movieData = snap.val() || {};
  } catch (e) {
    console.warn('Admin bar: could not load movie data', e);
  }

  document.body.classList.add('ab-active');
  const bar = document.createElement('div');
  bar.className = 'ab-bar';
  bar.innerHTML = `
    <span class="ab-label">ADMIN</span>
    <button class="ab-btn" onclick="window._abEdit('synopsis')">Edit Synopsis</button>
    <button class="ab-btn" onclick="window._abEdit('cast')">Edit Cast & Crew</button>
    <button class="ab-btn" onclick="window._abEdit('songs')">Edit Songs</button>
    <button class="ab-btn" onclick="window._abEdit('trailer')">Edit Trailer</button>
    <button class="ab-btn" onclick="window._abEdit('status')">Change Status</button>
  `;
  document.body.appendChild(bar);

  // ===== Modal helpers =====
  function showModal(html) {
    closeModal();
    const overlay = document.createElement('div');
    overlay.className = 'ab-modal-overlay';
    overlay.id = 'abModalOverlay';
    overlay.innerHTML = `<div class="ab-modal">${html}</div>`;
    overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
    document.body.appendChild(overlay);
  }

  function closeModal() {
    const el = document.getElementById('abModalOverlay');
    if (el) el.remove();
  }

  async function saveField(field, value) {
    await set(ref(db, 'movies/' + movieSlug + '/' + field), value);
    movieData[field] = value;
    await set(ref(db, 'movies/' + movieSlug + '/updatedAt'), Date.now());
  }

  // ===== Edit functions =====
  window._abEdit = function(type) {
    switch (type) {
      case 'synopsis': editSynopsis(); break;
      case 'cast': editCast(); break;
      case 'songs': editSongs(); break;
      case 'trailer': editTrailer(); break;
      case 'status': editStatus(); break;
    }
  };

  function editSynopsis() {
    // Read current synopsis from page
    const synopsisEl = document.querySelector('.mp-synopsis');
    const current = movieData.description || (synopsisEl ? synopsisEl.textContent : '');
    showModal(`
      <h3>Edit Synopsis</h3>
      <textarea class="ab-input ab-textarea" id="abSynopsis" rows="5">${esc(current)}</textarea>
      <button class="ab-save" onclick="window._abSaveSynopsis()">Save Synopsis</button>
      <button class="ab-cancel" onclick="window._abClose()">Cancel</button>
      <div id="abMsg"></div>
    `);
  }

  window._abSaveSynopsis = async function() {
    const val = document.getElementById('abSynopsis').value.trim();
    const msg = document.getElementById('abMsg');
    if (!val) { msg.textContent = 'Synopsis cannot be empty.'; msg.className = 'ab-msg ab-msg-err'; return; }
    try {
      await saveField('description', val);
      // Update page live
      const el = document.querySelector('.mp-synopsis');
      if (el) el.textContent = val;
      msg.textContent = 'Synopsis saved!'; msg.className = 'ab-msg ab-msg-ok';
      setTimeout(closeModal, 800);
    } catch (e) {
      msg.textContent = 'Error: ' + e.message; msg.className = 'ab-msg ab-msg-err';
    }
  };

  function editCast() {
    const crewEl = document.querySelector('.mp-crew');
    // Parse current crew from page
    let fields = [];
    if (crewEl) {
      crewEl.querySelectorAll('p').forEach(p => {
        const strong = p.querySelector('strong');
        if (strong) {
          const label = strong.textContent.replace(':', '').trim();
          const value = p.textContent.replace(strong.textContent, '').trim();
          fields.push({ label, value });
        }
      });
    }
    if (fields.length === 0) {
      fields = [
        { label: 'Director', value: movieData.director || '' },
        { label: 'Starring', value: movieData.cast || '' },
        { label: 'Music', value: movieData.music || '' }
      ];
    }

    let rowsHtml = fields.map((f, i) => `
      <div class="ab-song-row">
        <input class="ab-input" placeholder="Role" value="${esc(f.label)}" data-crew-label="${i}">
        <input class="ab-input" placeholder="Name(s)" value="${esc(f.value)}" data-crew-value="${i}">
        <button class="ab-remove" onclick="this.parentElement.remove()">&times;</button>
      </div>
    `).join('');

    showModal(`
      <h3>Edit Cast & Crew</h3>
      <div id="abCrewRows">${rowsHtml}</div>
      <button class="ab-add-btn" onclick="window._abAddCrew()">+ Add Field</button>
      <button class="ab-save" onclick="window._abSaveCast()">Save Cast & Crew</button>
      <button class="ab-cancel" onclick="window._abClose()">Cancel</button>
      <div id="abMsg"></div>
    `);
  }

  window._abAddCrew = function() {
    const container = document.getElementById('abCrewRows');
    const div = document.createElement('div');
    div.className = 'ab-song-row';
    div.innerHTML = `
      <input class="ab-input" placeholder="Role (e.g. Director)">
      <input class="ab-input" placeholder="Name(s)">
      <button class="ab-remove" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(div);
  };

  window._abSaveCast = async function() {
    const msg = document.getElementById('abMsg');
    const rows = document.querySelectorAll('#abCrewRows .ab-song-row');
    const fields = [];
    rows.forEach(row => {
      const inputs = row.querySelectorAll('input');
      const label = inputs[0].value.trim();
      const value = inputs[1].value.trim();
      if (label && value) fields.push({ label, value });
    });

    try {
      // Save key fields to Firebase movie data
      const director = fields.find(f => f.label.toLowerCase().includes('director'));
      const cast = fields.find(f => f.label.toLowerCase().includes('starring') || f.label.toLowerCase().includes('cast'));
      const music = fields.find(f => f.label.toLowerCase().includes('music'));
      if (director) await saveField('director', director.value);
      if (cast) await saveField('cast', cast.value);
      if (music) await saveField('music', music.value);
      // Save full crew list
      await saveField('crew', fields);

      // Update page live
      const crewEl = document.querySelector('.mp-crew');
      if (crewEl) {
        crewEl.innerHTML = fields.map(f => `<p><strong>${esc(f.label)}:</strong> ${esc(f.value)}</p>`).join('');
      }
      msg.textContent = 'Cast & Crew saved!'; msg.className = 'ab-msg ab-msg-ok';
      setTimeout(closeModal, 800);
    } catch (e) {
      msg.textContent = 'Error: ' + e.message; msg.className = 'ab-msg ab-msg-err';
    }
  };

  function editSongs() {
    // Read current songs from page
    const songCards = document.querySelectorAll('.mp-songs .mp-song-card');
    let songs = [];
    if (movieData.songs && movieData.songs.length) {
      songs = movieData.songs;
    } else {
      songCards.forEach(card => {
        const title = card.querySelector('span')?.textContent || '';
        const url = card.href || '';
        songs.push({ title, url });
      });
    }

    let rowsHtml = songs.map((s, i) => `
      <div class="ab-song-row">
        <input class="ab-input" placeholder="Song title" value="${esc(s.title)}">
        <input class="ab-input" placeholder="YouTube URL" value="${esc(s.url)}">
        <button class="ab-remove" onclick="this.parentElement.remove()">&times;</button>
      </div>
    `).join('');

    showModal(`
      <h3>Edit Songs</h3>
      <div id="abSongRows">${rowsHtml}</div>
      <button class="ab-add-btn" onclick="window._abAddSong()">+ Add Song</button>
      <button class="ab-save" onclick="window._abSaveSongs()">Save Songs</button>
      <button class="ab-cancel" onclick="window._abClose()">Cancel</button>
      <div id="abMsg"></div>
    `);
  }

  window._abAddSong = function() {
    const container = document.getElementById('abSongRows');
    const div = document.createElement('div');
    div.className = 'ab-song-row';
    div.innerHTML = `
      <input class="ab-input" placeholder="Song title">
      <input class="ab-input" placeholder="YouTube URL">
      <button class="ab-remove" onclick="this.parentElement.remove()">&times;</button>
    `;
    container.appendChild(div);
  };

  window._abSaveSongs = async function() {
    const msg = document.getElementById('abMsg');
    const rows = document.querySelectorAll('#abSongRows .ab-song-row');
    const songs = [];
    rows.forEach(row => {
      const inputs = row.querySelectorAll('input');
      const title = inputs[0].value.trim();
      const url = inputs[1].value.trim();
      if (title || url) songs.push({ title, url });
    });

    try {
      await saveField('songs', songs);

      // Update page live
      const songsContainer = document.querySelector('.mp-songs');
      if (songsContainer) {
        songsContainer.innerHTML = songs.map(s => `
          <a href="${esc(s.url)}" target="_blank" rel="noopener" class="mp-song-card">
            <div class="mp-song-icon">&#9835;</div>
            <span>${esc(s.title)}</span>
          </a>
        `).join('');
      }
      msg.textContent = 'Songs saved!'; msg.className = 'ab-msg ab-msg-ok';
      setTimeout(closeModal, 800);
    } catch (e) {
      msg.textContent = 'Error: ' + e.message; msg.className = 'ab-msg ab-msg-err';
    }
  };

  function editTrailer() {
    const trailerIframe = document.querySelector('.mp-video iframe');
    let currentUrl = '';
    if (movieData.trailer) {
      currentUrl = movieData.trailer;
    } else if (trailerIframe) {
      const src = trailerIframe.src;
      const id = extractYouTubeId(src);
      currentUrl = id ? 'https://www.youtube.com/watch?v=' + id : src;
    }
    let currentTeaser = movieData.teaser || '';

    showModal(`
      <h3>Edit Trailer / Teaser</h3>
      <p class="ab-subtitle">Trailer YouTube URL</p>
      <input class="ab-input" id="abTrailer" placeholder="https://www.youtube.com/watch?v=..." value="${esc(currentUrl)}">
      <p class="ab-subtitle">Teaser YouTube URL</p>
      <input class="ab-input" id="abTeaser" placeholder="https://www.youtube.com/watch?v=..." value="${esc(currentTeaser)}">
      <button class="ab-save" onclick="window._abSaveTrailer()">Save</button>
      <button class="ab-cancel" onclick="window._abClose()">Cancel</button>
      <div id="abMsg"></div>
    `);
  }

  window._abSaveTrailer = async function() {
    const msg = document.getElementById('abMsg');
    const trailer = document.getElementById('abTrailer').value.trim();
    const teaser = document.getElementById('abTeaser').value.trim();

    try {
      await saveField('trailer', trailer);
      await saveField('teaser', teaser);

      // Update page live - find the trailer/teaser iframe
      const videoSections = document.querySelectorAll('.mp-section');
      videoSections.forEach(section => {
        const title = section.querySelector('.mp-section-title');
        const iframe = section.querySelector('.mp-video iframe');
        if (!title || !iframe) return;
        const titleText = title.textContent.toLowerCase();
        if (titleText.includes('trailer') && trailer) {
          const id = extractYouTubeId(trailer);
          if (id) iframe.src = 'https://www.youtube.com/embed/' + id;
        }
        if (titleText.includes('teaser') && teaser) {
          const id = extractYouTubeId(teaser);
          if (id) iframe.src = 'https://www.youtube.com/embed/' + id;
        }
      });

      msg.textContent = 'Saved!'; msg.className = 'ab-msg ab-msg-ok';
      setTimeout(closeModal, 800);
    } catch (e) {
      msg.textContent = 'Error: ' + e.message; msg.className = 'ab-msg ab-msg-err';
    }
  };

  function editStatus() {
    const currentStatus = movieData.status || 'Coming Soon';
    const statuses = ['Coming Soon', 'Now Showing', 'Ended'];

    showModal(`
      <h3>Change Movie Status</h3>
      <div class="ab-status-group" id="abStatusGroup">
        ${statuses.map(s => `
          <div class="ab-status-opt ${s === currentStatus ? 'active' : ''}" data-status="${s}" onclick="window._abSelectStatus(this)">${s}</div>
        `).join('')}
      </div>
      <button class="ab-save" onclick="window._abSaveStatus()">Save Status</button>
      <button class="ab-cancel" onclick="window._abClose()">Cancel</button>
      <div id="abMsg"></div>
    `);
  }

  window._abSelectStatus = function(el) {
    document.querySelectorAll('.ab-status-opt').forEach(o => o.classList.remove('active'));
    el.classList.add('active');
  };

  window._abSaveStatus = async function() {
    const msg = document.getElementById('abMsg');
    const active = document.querySelector('.ab-status-opt.active');
    if (!active) return;
    const status = active.dataset.status;

    try {
      await saveField('status', status);

      // Update page live
      const datesEl = document.querySelector('.mp-dates');
      if (datesEl) {
        if (status === 'Now Showing') datesEl.textContent = 'Now Showing';
        else if (status === 'Ended') datesEl.textContent = 'No longer showing';
        else datesEl.textContent = 'Coming Soon to Germany';
      }

      msg.textContent = 'Status updated to: ' + status; msg.className = 'ab-msg ab-msg-ok';
      setTimeout(closeModal, 800);
    } catch (e) {
      msg.textContent = 'Error: ' + e.message; msg.className = 'ab-msg ab-msg-err';
    }
  };

  window._abClose = closeModal;
});
