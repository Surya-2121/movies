// Show data for Ustaad Bhagat Singh

const showsData = [
  {
    id: 168,
    city: "N\u00fcrnberg",
    cinema: "Cinecitt\u00e0 Kino 6",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 103,
    bookingUrl: "https://www.getmyticket.de/showbookings.php?id=168&time=07%3A30%20PM&mdate=MjAyNi0wMy0xOA==",
  },
  {
    id: 169,
    city: "Dusseldorf",
    cinema: "UFA Palast Kino 9",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 222,
    bookingUrl: "https://www.getmyticket.de/showbookings.php?id=169&time=07%3A30%20PM&mdate=MjAyNi0wMy0xOA==",
  },
  {
    id: 171,
    city: "Dusseldorf",
    cinema: "UFA-Palast Dus Kino 2",
    date: "2026-03-22",
    time: "11:30",
    language: "Telugu",
    totalSeats: 127,
    bookingUrl: "https://www.getmyticket.de/showbookings.php?id=171&time=11%3A30%20AM&mdate=MjAyNi0wMy0yMg==",
  },
  {
    id: 170,
    city: "Erlangen",
    cinema: "Erlangen LammKino Screen 1",
    date: "2026-03-22",
    time: "11 AM",
    language: "Telugu",
    totalSeats: 112,
    bookingUrl: "https://www.getmyticket.de/showbookings.php?id=170&time=11%20AM&mdate=MjAyNi0wMy0yMg==",
  },
  {
    id: "capitol-25577",
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 145,
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577",
  },
  {
    id: "capitol-25582",
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-21",
    time: "21:15",
    language: "Telugu",
    totalSeats: 144,
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582",
  },
  {
    id: "cinemaxx-1336-22915",
    city: "Bielefeld",
    cinema: "CinemaxX Bielefeld",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 110,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1281-20458",
    city: "Bremen",
    cinema: "CinemaxX Bremen",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 145,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1431-39339",
    city: "Essen",
    cinema: "CinemaxX Essen",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 453,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1207-15805",
    city: "Hamburg-Harburg",
    cinema: "CinemaxX Hamburg-Harburg",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 65,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1304-25011",
    city: "Hannover",
    cinema: "CinemaxX Hannover",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 224,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1391-33511",
    city: "Magdeburg",
    cinema: "CinemaxX Magdeburg",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    totalSeats: 112,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1631-16303",
    city: "Frankfurt (Offenbach)",
    cinema: "CinemaxX Frankfurt (Offenbach)",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 171,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1931-15538",
    city: "Regensburg",
    cinema: "CinemaxX Regensburg",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 131,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1531-13492",
    city: "Trier",
    cinema: "CinemaxX Trier",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    totalSeats: 182,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1801-15523",
    city: "M\u00fcnchen",
    cinema: "CinemaxX M\u00fcnchen",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    totalSeats: 121,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh",
  },
  {
    id: "cinemaxx-1011-17641",
    city: "Dresden",
    cinema: "CinemaxX Dresden",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    totalSeats: 262,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh",
  },
  {
    id: "luxor-2331133",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-18",
    time: "20:30",
    language: "Telugu",
    totalSeats: 125,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133",
  },
  {
    id: "luxor-2334534",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-21",
    time: "16:00",
    language: "Telugu",
    totalSeats: 123,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534",
  },
  {
    id: "luxor-2334535",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    totalSeats: 123,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
  },
  {
    id: "ticketverz-8bae530abf",
    city: "Berlin",
    cinema: "Cineplex Berlin",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 550,
    bookingUrl: "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf",
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-13T09:39:04Z", "movie": "Ustaad Bhagat Singh - Telugu", "totalShows": 21, "totalSeats": 3750, "shows": [{"showId": 168, "city": "Nürnberg", "cinema": "Cinecittà Kino 6", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 103}, {"showId": 169, "city": "Dusseldorf", "cinema": "UFA Palast Kino 9", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 222}, {"showId": 171, "city": "Dusseldorf", "cinema": "UFA-Palast Dus Kino 2", "date": "2026-03-22", "time": "11:30", "dateText": "Sun 22 Mar 2026 - 11:30 AM", "totalSeats": 127}, {"showId": 170, "city": "Erlangen", "cinema": "Erlangen LammKino Screen 1", "date": "2026-03-22", "time": "11 AM", "dateText": "Sun 22 Mar 2026 - 11 AM", "totalSeats": 112}, {"showId": "capitol-25577", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 145, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577"}, {"showId": "capitol-25582", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-21", "time": "21:15", "dateText": "Sat 21 Mar 2026 - 09:15 PM", "totalSeats": 144, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582"}, {"showId": "cinemaxx-1336-22915", "city": "Bielefeld", "cinema": "CinemaxX Bielefeld", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 110, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1281-20458", "city": "Bremen", "cinema": "CinemaxX Bremen", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 145, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1431-39339", "city": "Essen", "cinema": "CinemaxX Essen", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 453, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1207-15805", "city": "Hamburg-Harburg", "cinema": "CinemaxX Hamburg-Harburg", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 65, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1304-25011", "city": "Hannover", "cinema": "CinemaxX Hannover", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 224, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1391-33511", "city": "Magdeburg", "cinema": "CinemaxX Magdeburg", "date": "2026-03-18", "time": "19:20", "dateText": "Wed 18 Mar 2026 - 07:20 PM", "totalSeats": 112, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1631-16303", "city": "Frankfurt (Offenbach)", "cinema": "CinemaxX Frankfurt (Offenbach)", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 171, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1931-15538", "city": "Regensburg", "cinema": "CinemaxX Regensburg", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 131, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1531-13492", "city": "Trier", "cinema": "CinemaxX Trier", "date": "2026-03-18", "time": "19:15", "dateText": "Wed 18 Mar 2026 - 07:15 PM", "totalSeats": 182, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1801-15523", "city": "München", "cinema": "CinemaxX München", "date": "2026-03-18", "time": "19:20", "dateText": "Wed 18 Mar 2026 - 07:20 PM", "totalSeats": 121, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh"}, {"showId": "cinemaxx-1011-17641", "city": "Dresden", "cinema": "CinemaxX Dresden", "date": "2026-03-18", "time": "19:15", "dateText": "Wed 18 Mar 2026 - 07:15 PM", "totalSeats": 262, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh"}, {"showId": "luxor-2331133", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-18", "time": "20:30", "dateText": "Wed 18 Mar 2026 - 08:30 PM", "totalSeats": 125, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133"}, {"showId": "luxor-2334534", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-21", "time": "16:00", "dateText": "Sat 21 Mar 2026 - 04:00 PM", "totalSeats": 123, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534"}, {"showId": "luxor-2334535", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-22", "time": "16:00", "dateText": "Sun 22 Mar 2026 - 04:00 PM", "totalSeats": 123, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535"}, {"showId": "ticketverz-8bae530abf", "city": "Berlin", "cinema": "Cineplex Berlin", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 550, "source": "ticketverz", "bookingUrl": "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf"}]};
// SEAT_DATA_END

function loadShows() {
  const shows = JSON.parse(JSON.stringify(showsData));

  if (seatData) {
    for (const real of seatData.shows) {
      for (const show of shows) {
        if (show.id === real.showId) {
          show.totalSeats = real.totalSeats;
          break;
        }
      }
    }
  }
  return shows;
}

let shows = loadShows();

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
