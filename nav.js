// Menu toggle
function toggleMenu() {
  const menu = document.getElementById('navMenu');
  const overlay = document.getElementById('navOverlay');
  menu.classList.toggle('nav-open');
  overlay.classList.toggle('nav-overlay-show');
}

// Theme toggle
function applyTheme(theme) {
  document.body.classList.toggle('light-theme', theme === 'light');
  const icon = document.getElementById('themeIcon');
  const text = document.getElementById('themeText');
  if (icon) icon.textContent = theme === 'light' ? '\u263E' : '\u2606';
  if (text) text.textContent = theme === 'light' ? 'Dark Mode' : 'Light Mode';
}

function toggleTheme() {
  const current = localStorage.getItem('theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', next);
  applyTheme(next);
}

// Apply saved theme on load
applyTheme(localStorage.getItem('theme') || 'dark');

// Search
const allMovies = [
  { name: 'Ustaad Bhagat Singh', url: 'ustaad-movie.html', cast: 'Pawan Kalyan, Sreeleela, Raashii Khanna', status: 'Now Showing' },
  { name: 'Peddi', url: 'peddi-movie.html', cast: 'Ram Charan, Janhvi Kapoor', status: 'Coming Soon' },
  { name: 'The Paradise', url: 'paradise-movie.html', cast: 'Nani', status: 'Coming Soon' },
  { name: 'Vishwambhara', url: 'vishwambhara-movie.html', cast: 'Chiranjeevi', status: 'Coming Soon' },
  { name: 'Varanasi', url: 'varanasi-movie.html', cast: 'Mahesh Babu', status: 'Coming Soon' },
  { name: 'Spirit', url: 'spirit-movie.html', cast: 'Prabhas, Triptii Dimri', status: 'Coming Soon' },
];

function toggleSearch() {
  const overlay = document.getElementById('searchOverlay');
  if (!overlay) return;
  const isOpen = overlay.classList.toggle('search-overlay-open');
  if (isOpen) {
    const input = overlay.querySelector('.search-overlay-input');
    if (input) input.focus();
  }
}

function handleSearchInput(e) {
  const q = e.target.value.trim().toLowerCase();
  const results = document.getElementById('searchOverlayResults');
  if (!results) return;
  if (!q) { results.innerHTML = ''; return; }
  const matches = allMovies.filter(m => m.name.toLowerCase().includes(q) || m.cast.toLowerCase().includes(q));
  if (matches.length === 0) {
    results.innerHTML = '<div class="search-item search-empty">No movies found</div>';
  } else {
    results.innerHTML = matches.map(m =>
      `<a href="${m.url}" class="search-item"><div class="search-item-name">${m.name}</div><div class="search-item-meta">${m.cast} &bull; ${m.status}</div></a>`
    ).join('');
  }
}

window.toggleMenu = toggleMenu;
window.toggleTheme = toggleTheme;
window.toggleSearch = toggleSearch;
window.handleSearchInput = handleSearchInput;
