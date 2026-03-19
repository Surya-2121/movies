// Show data for Ustaad Bhagat Singh

const showsData = [
  {
    id: 1,
    city: "Dusseldorf",
    cinema: "UFA Palast",
    date: "2026-03-18",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=169&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA==",
  },
  {
    id: 2,
    city: "Dusseldorf",
    cinema: "UFA Palast",
    date: "2026-03-22",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=171&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMg==",
  },
  {
    id: 3,
    city: "N\u00fcrnberg",
    cinema: "Cinecitta",
    date: "2026-03-18",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=168&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA==",
  },
  {
    id: 4,
    city: "Frankfurt (Karben)",
    cinema: "Frankfurt (Karben)",
    date: "2026-03-18",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=172&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA==",
  },
  {
    id: 5,
    city: "Frankfurt (Karben)",
    cinema: "Frankfurt (Karben)",
    date: "2026-03-21",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=173&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMQ==",
  },
  {
    id: 6,
    city: "Hamburg",
    cinema: "Hansa Filmstudios",
    date: "2026-03-20",
    time: "20:00",
    language: "Telugu",
    bookingUrl: "https://getmyticket.de/showbookings.php?id=175&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0yMA==",
  },
  {
    id: 7,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-18",
    time: "20:30",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133",
  },
  {
    id: 8,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-21",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534",
  },
  {
    id: 9,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
  },
  {
    id: 10,
    city: "Essen",
    cinema: "CinemaxX Essen",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh",
  },
  {
    id: 11,
    city: "M\u00fcnchen",
    cinema: "CinemaxX M\u00fcnchen",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh",
  },
  {
    id: 12,
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577",
  },
  {
    id: 13,
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-21",
    time: "21:15",
    language: "Telugu",
    bookingUrl: "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln",
  },
  {
    id: 14,
    city: "Berlin",
    cinema: "Cineplex Berlin",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf",
  },
  {
    id: 15,
    city: "M\u00fcnchen",
    cinema: "Cincinnati Kino",
    date: "2026-03-21",
    time: "11:00",
    language: "Telugu",
    bookingUrl: "https://www.cincinnati-muenchen.de/en/program/1655865",
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-19T05:52:16Z", "movie": "Ustaad Bhagat Singh", "totalShows": 15, "shows": [{"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-03-18", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=169&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA=="}, {"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-03-22", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=171&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMg=="}, {"city": "Nürnberg", "cinema": "Cinecitta", "date": "2026-03-18", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=168&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA=="}, {"city": "Frankfurt (Karben)", "cinema": "Frankfurt (Karben)", "date": "2026-03-18", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=172&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA=="}, {"city": "Frankfurt (Karben)", "cinema": "Frankfurt (Karben)", "date": "2026-03-21", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=173&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMQ=="}, {"city": "Hamburg", "cinema": "Hansa Filmstudios", "date": "2026-03-20", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=175&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0yMA=="}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-18", "time": "20:30", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133"}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-21", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534"}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-22", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535"}, {"city": "Essen", "cinema": "CinemaxX Essen", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh"}, {"city": "München", "cinema": "CinemaxX München", "date": "2026-03-18", "time": "19:20", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh"}, {"city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577"}, {"city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-21", "time": "21:15", "bookingUrl": "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln"}, {"city": "Berlin", "cinema": "Cineplex Berlin", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf"}, {"city": "München", "cinema": "Cincinnati Kino", "date": "2026-03-21", "time": "11:00", "bookingUrl": "https://www.cincinnati-muenchen.de/en/program/1655865"}]};
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
