// Show data for Ustaad Bhagat Singh

const showsData = [];

/* Shows ended 2026-03-23
const showsDataArchive = [
  {
    id: 1,
    city: "Dusseldorf",
    cinema: "UFA Palast",
    date: "2026-03-22",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=171&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMg==",
  },
  {
    id: 2,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
  },
];
*/
// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-23T00:00:00Z", "movie": "Ustaad Bhagat Singh", "totalShows": 0, "shows": []};
// SEAT_DATA_END

let shows = JSON.parse(JSON.stringify(showsData));

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}


function getSelectedDate() {
  const sel = document.getElementById('dateFilter');
  return sel ? sel.value : 'all';
}

function getFilteredShows() {
  const date = getSelectedDate();
  if (date === 'all') return shows;
  return shows.filter(s => s.date === date);
}

function populateDateFilter() {
  const sel = document.getElementById('dateFilter');
  const current = sel.value;
  const dates = [...new Set(shows.map(s => s.date))].sort();
  sel.innerHTML = '<option value="all">All Dates</option>';
  dates.forEach(d => {
    const label = new Date(d + 'T00:00:00').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    sel.innerHTML += `<option value="${d}"${d === current ? ' selected' : ''}>${label}</option>`;
  });
}

function render() {
  populateDateFilter();
  const filtered = getFilteredShows();

  const showList = document.getElementById('showList');
  showList.innerHTML = '';

  if (filtered.length === 0) {
    showList.innerHTML = '<div class="show-card" style="text-align:center;padding:2rem;"><h3>No shows currently available</h3><p style="color:#999;margin-top:0.5rem;">All shows for this movie have ended. Check back for future screenings!</p></div>';
    return;
  }

  filtered.forEach(show => {
    const card = document.createElement('div');
    card.className = 'show-card';
    card.innerHTML = `
      <div class="show-card-header">
        <div>
          <h3>${escapeHtml(show.city)}</h3>
          ${show.cinema && show.cinema !== show.city ? '<div class="cinema-name">' + escapeHtml(show.cinema) + '</div>' : ''}
        </div>
        <div class="show-time-badge">${show.time}</div>
      </div>
      <div style="font-size:0.75rem;color:#666;margin-top:4px;">${show.language} &bull; ${show.date}</div>
      ${show.bookingUrl ? `<a href="${show.bookingUrl}" target="_blank" rel="noopener" class="book-btn">Book Now</a>` : '<span class="book-btn book-btn-soon">Coming Soon</span>'}
    `;
    showList.appendChild(card);
  });
}

render();
document.getElementById('dateFilter').addEventListener('change', render);
