// Show data for Ustaad Bhagat Singh

const showsData = [
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
    city: "Frankfurt (Karben)",
    cinema: "Frankfurt (Karben)",
    date: "2026-03-21",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=173&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMQ==",
  },
  {
    id: 3,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-21",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534",
  },
  {
    id: 4,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
  },
  {
    id: 5,
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-21",
    time: "21:15",
    language: "Telugu",
    bookingUrl: "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln",
  },
  {
    id: 6,
    city: "M\u00fcnchen",
    cinema: "Cincinnati Kino",
    date: "2026-03-21",
    time: "11:00",
    language: "Telugu",
    bookingUrl: "https://www.cincinnati-muenchen.de/en/program/1655865",
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-21T09:22:54Z", "movie": "Ustaad Bhagat Singh", "totalShows": 6, "shows": [{"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-03-22", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=171&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMg=="}, {"city": "Frankfurt (Karben)", "cinema": "Frankfurt (Karben)", "date": "2026-03-21", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=173&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMQ=="}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-21", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534"}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-22", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535"}, {"city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-21", "time": "21:15", "bookingUrl": "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln"}, {"city": "München", "cinema": "Cincinnati Kino", "date": "2026-03-21", "time": "11:00", "bookingUrl": "https://www.cincinnati-muenchen.de/en/program/1655865"}]};
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
