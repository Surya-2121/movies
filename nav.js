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

window.toggleMenu = toggleMenu;
window.toggleTheme = toggleTheme;
