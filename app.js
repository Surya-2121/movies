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
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-18",
    time: "20:30",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133",
  },
  {
    id: 5,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-21",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534",
  },
  {
    id: 6,
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
  },
  {
    id: 7,
    city: "Bielefeld",
    cinema: "CinemaxX Bielefeld",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh",
  },
  {
    id: 8,
    city: "Bremen",
    cinema: "CinemaxX Bremen",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh",
  },
  {
    id: 9,
    city: "Essen",
    cinema: "CinemaxX Essen",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh",
  },
  {
    id: 10,
    city: "Hamburg-Harburg",
    cinema: "CinemaxX Hamburg-Harburg",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh",
  },
  {
    id: 11,
    city: "Hannover",
    cinema: "CinemaxX Hannover",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh",
  },
  {
    id: 12,
    city: "Magdeburg",
    cinema: "CinemaxX Magdeburg",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh",
  },
  {
    id: 13,
    city: "Frankfurt (Offenbach)",
    cinema: "CinemaxX Frankfurt (Offenbach)",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh",
  },
  {
    id: 14,
    city: "Regensburg",
    cinema: "CinemaxX Regensburg",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh",
  },
  {
    id: 15,
    city: "Trier",
    cinema: "CinemaxX Trier",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh",
  },
  {
    id: 16,
    city: "M\u00fcnchen",
    cinema: "CinemaxX M\u00fcnchen",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh",
  },
  {
    id: 17,
    city: "Dresden",
    cinema: "CinemaxX Dresden",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh",
  },
  {
    id: 18,
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln",
  },
  {
    id: 19,
    city: "Berlin",
    cinema: "Cineplex Berlin",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf",
  },
  {
    id: 20,
    city: "M\u00fcnchen",
    cinema: "Cincinnati Kino",
    date: "2026-03-19",
    time: "19:30",
    language: "Telugu",
    bookingUrl: "https://www.cincinnati-muenchen.de/en/program/1655865",
  },
  {
    id: 21,
    city: "M\u00fcnchen",
    cinema: "Cincinnati Kino",
    date: "2026-03-21",
    time: "11:00",
    language: "Telugu",
    bookingUrl: "https://www.cincinnati-muenchen.de/en/program/1655865",
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-13T19:24:48Z", "movie": "Ustaad Bhagat Singh", "totalShows": 21, "shows": [{"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-03-18", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=169&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA=="}, {"city": "Dusseldorf", "cinema": "UFA Palast", "date": "2026-03-22", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=171&amp;time=11:30%20AM&amp;mdate=MjAyNi0wMy0yMg=="}, {"city": "Nürnberg", "cinema": "Cinecitta", "date": "2026-03-18", "time": "20:00", "bookingUrl": "https://getmyticket.de/showbookings.php?id=168&amp;time=07:30%20PM&amp;mdate=MjAyNi0wMy0xOA=="}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-18", "time": "20:30", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133"}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-21", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534"}, {"city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-22", "time": "16:00", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535"}, {"city": "Bielefeld", "cinema": "CinemaxX Bielefeld", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh"}, {"city": "Bremen", "cinema": "CinemaxX Bremen", "date": "2026-03-18", "time": "19:00", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh"}, {"city": "Essen", "cinema": "CinemaxX Essen", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh"}, {"city": "Hamburg-Harburg", "cinema": "CinemaxX Hamburg-Harburg", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh"}, {"city": "Hannover", "cinema": "CinemaxX Hannover", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh"}, {"city": "Magdeburg", "cinema": "CinemaxX Magdeburg", "date": "2026-03-18", "time": "19:20", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh"}, {"city": "Frankfurt (Offenbach)", "cinema": "CinemaxX Frankfurt (Offenbach)", "date": "2026-03-18", "time": "19:00", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh"}, {"city": "Regensburg", "cinema": "CinemaxX Regensburg", "date": "2026-03-18", "time": "19:00", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh"}, {"city": "Trier", "cinema": "CinemaxX Trier", "date": "2026-03-18", "time": "19:15", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh"}, {"city": "München", "cinema": "CinemaxX München", "date": "2026-03-18", "time": "19:20", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh"}, {"city": "Dresden", "cinema": "CinemaxX Dresden", "date": "2026-03-18", "time": "19:15", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh"}, {"city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://capitol-kornwestheim.de/film/ustaad-bhagat-singh-malayalam-mit-englischen-untertiteln"}, {"city": "Berlin", "cinema": "Cineplex Berlin", "date": "2026-03-18", "time": "19:30", "bookingUrl": "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf"}, {"city": "München", "cinema": "Cincinnati Kino", "date": "2026-03-19", "time": "19:30", "bookingUrl": "https://www.cincinnati-muenchen.de/en/program/1655865"}, {"city": "München", "cinema": "Cincinnati Kino", "date": "2026-03-21", "time": "11:00", "bookingUrl": "https://www.cincinnati-muenchen.de/en/program/1655865"}]};
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
