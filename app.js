// Show data for Ustaad Bhagat Singh
// Admin mode: add ?admin=true to URL to see revenue section
const isAdmin = new URLSearchParams(window.location.search).get('admin') === 'true';

const showsData = [
  {
    id: 170,
    city: "Erlangen",
    cinema: "Erlangen LammKino Screen 1",
    date: "2026-03-22",
    time: "11 AM",
    language: "Telugu",
    totalSeats: 112,
    ticketsBooked: 0,
    bookingUrl: "",
    prices: { 'row1': 15, 'row2': 15, 'row3': 15, 'row4': 16, 'row5': 16, 'row6': 16, 'row7': 16, 'row8': 16, 'row9': 18, 'row10': 18, 'row11': 18, 'row12': 18, 'row13': 18, 'row14': 18, 'row15': 18, 'row16': 18 },
  },
  {
    id: 169,
    city: "Dusseldorf",
    cinema: "UFA Palast Kino 9",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 222,
    ticketsBooked: 54,
    bookingUrl: "",
    prices: { 'row1': 19, 'row2': 19, 'row3': 19, 'row4': 21, 'row5': 21, 'row6': 21, 'row7': 21, 'row8': 21, 'row9': 21, 'row10': 21, 'row11': 21, 'row12': 21, 'row13': 21, 'row14': 21, 'row15': 21 },
  },
  {
    id: 168,
    city: "N\u00fcrnberg",
    cinema: "Cinecitt\u00e0 Kino 6",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 103,
    ticketsBooked: 19,
    bookingUrl: "",
    prices: { 'row1': 18, 'row2': 18, 'row3': 18, 'row4': 22, 'row5': 22, 'row6': 22, 'row7': 22, 'row8': 22, 'row9': 22, 'row10': 22 },
  },
  {
    id: "capitol-25577",
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 145,
    ticketsBooked: 0,
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577",
    prices: {  },
  },
  {
    id: "capitol-25582",
    city: "Stuttgart",
    cinema: "Capital Kornwestheim",
    date: "2026-03-21",
    time: "21:15",
    language: "Telugu",
    totalSeats: 144,
    ticketsBooked: 0,
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582",
    prices: {  },
  },
  {
    id: "cinemaxx-1336-22915",
    city: "Bielefeld",
    cinema: "CinemaxX Bielefeld",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 110,
    ticketsBooked: 0,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1281-20458",
    city: "Bremen",
    cinema: "CinemaxX Bremen",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 145,
    ticketsBooked: 0,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1431-39339",
    city: "Essen",
    cinema: "CinemaxX Essen",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 453,
    ticketsBooked: 1,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1207-15805",
    city: "Hamburg-Harburg",
    cinema: "CinemaxX Hamburg-Harburg",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 65,
    ticketsBooked: 4,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1304-25011",
    city: "Hannover",
    cinema: "CinemaxX Hannover",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 224,
    ticketsBooked: 5,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1391-33511",
    city: "Magdeburg",
    cinema: "CinemaxX Magdeburg",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    totalSeats: 112,
    ticketsBooked: 2,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1631-16303",
    city: "Frankfurt (Offenbach)",
    cinema: "CinemaxX Frankfurt (Offenbach)",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 171,
    ticketsBooked: 1,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1931-15538",
    city: "Regensburg",
    cinema: "CinemaxX Regensburg",
    date: "2026-03-18",
    time: "19:00",
    language: "Telugu",
    totalSeats: 131,
    ticketsBooked: 5,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1531-13492",
    city: "Trier",
    cinema: "CinemaxX Trier",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    totalSeats: 182,
    ticketsBooked: 0,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1801-15523",
    city: "M\u00fcnchen",
    cinema: "CinemaxX M\u00fcnchen",
    date: "2026-03-18",
    time: "19:20",
    language: "Telugu",
    totalSeats: 121,
    ticketsBooked: 30,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "cinemaxx-1011-17641",
    city: "Dresden",
    cinema: "CinemaxX Dresden",
    date: "2026-03-18",
    time: "19:15",
    language: "Telugu",
    totalSeats: 262,
    ticketsBooked: 7,
    bookingUrl: "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh",
    prices: {  },
  },
  {
    id: "luxor-2331133",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-18",
    time: "20:30",
    language: "Telugu",
    totalSeats: 125,
    ticketsBooked: 4,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133",
    prices: { 'row0': 22.0, 'row1': 29.0 },
  },
  {
    id: "luxor-2334534",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-21",
    time: "16:00",
    language: "Telugu",
    totalSeats: 123,
    ticketsBooked: 0,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534",
    prices: { 'row0': 18.0, 'row1': 23.0 },
  },
  {
    id: "luxor-2334535",
    city: "Heidelberg",
    cinema: "LUXOR FILM PALAST",
    date: "2026-03-22",
    time: "16:00",
    language: "Telugu",
    totalSeats: 123,
    ticketsBooked: 0,
    bookingUrl: "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535",
    prices: { 'row0': 18.0, 'row1': 23.0 },
  },
  {
    id: "ticketverz-8bae530abf",
    city: "Berlin",
    cinema: "Cineplex Berlin",
    date: "2026-03-18",
    time: "19:30",
    language: "Telugu",
    totalSeats: 550,
    ticketsBooked: 9,
    bookingUrl: "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf",
    prices: { 'row0': 20.99, 'row1': 24 },
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-12T13:57:55Z", "movie": "Ustaad Bhagat Singh - Telugu", "totalShows": 20, "totalSeats": 3623, "totalBooked": 141, "totalAvailable": 3482, "overallBookingPercent": 3.9, "totalRevenue": 2734, "shows": [{"showId": 170, "city": "Erlangen", "cinema": "Erlangen LammKino Screen 1", "date": "2026-03-22", "time": "11 AM", "dateText": "Sun 22 Mar 2026 - 11 AM", "totalSeats": 112, "sold": 0, "available": 112, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {"1": 15, "2": 15, "3": 15, "4": 16, "5": 16, "6": 16, "7": 16, "8": 16, "9": 18, "10": 18, "11": 18, "12": 18, "13": 18, "14": 18, "15": 18, "16": 18}}, {"showId": 169, "city": "Dusseldorf", "cinema": "UFA Palast Kino 9", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 222, "sold": 54, "available": 168, "unavailable": 0, "revenue": 1134, "soldByPrice": {"21": 54}, "rowPrices": {"1": 19, "2": 19, "3": 19, "4": 21, "5": 21, "6": 21, "7": 21, "8": 21, "9": 21, "10": 21, "11": 21, "12": 21, "13": 21, "14": 21, "15": 21}}, {"showId": 168, "city": "Nürnberg", "cinema": "Cinecittà Kino 6", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 103, "sold": 19, "available": 84, "unavailable": 0, "revenue": 418, "soldByPrice": {"22": 19}, "rowPrices": {"1": 18, "2": 18, "3": 18, "4": 22, "5": 22, "6": 22, "7": 22, "8": 22, "9": 22, "10": 22}}, {"showId": "capitol-25577", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 145, "sold": 0, "available": 145, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577"}, {"showId": "capitol-25582", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-21", "time": "21:15", "dateText": "Sat 21 Mar 2026 - 09:15 PM", "totalSeats": 144, "sold": 0, "available": 144, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582"}, {"showId": "cinemaxx-1336-22915", "city": "Bielefeld", "cinema": "CinemaxX Bielefeld", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 110, "sold": 0, "available": 106, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bielefeld/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1281-20458", "city": "Bremen", "cinema": "CinemaxX Bremen", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 145, "sold": 0, "available": 141, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/bremen/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1431-39339", "city": "Essen", "cinema": "CinemaxX Essen", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 453, "sold": 1, "available": 448, "unavailable": 0, "revenue": 16, "soldByPrice": {"15.99": 1}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/essen/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1207-15805", "city": "Hamburg-Harburg", "cinema": "CinemaxX Hamburg-Harburg", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 65, "sold": 4, "available": 57, "unavailable": 0, "revenue": 64, "soldByPrice": {"15.99": 4}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hamburg-harburg/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1304-25011", "city": "Hannover", "cinema": "CinemaxX Hannover", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 224, "sold": 5, "available": 215, "unavailable": 0, "revenue": 75, "soldByPrice": {"14.99": 5}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/hannover/film/ustaad-bhagat-singh", "ticketPrice": 14.99}, {"showId": "cinemaxx-1391-33511", "city": "Magdeburg", "cinema": "CinemaxX Magdeburg", "date": "2026-03-18", "time": "19:20", "dateText": "Wed 18 Mar 2026 - 07:20 PM", "totalSeats": 112, "sold": 2, "available": 106, "unavailable": 0, "revenue": 32, "soldByPrice": {"15.99": 2}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/magdeburg/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1631-16303", "city": "Frankfurt (Offenbach)", "cinema": "CinemaxX Frankfurt (Offenbach)", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 171, "sold": 1, "available": 166, "unavailable": 0, "revenue": 16, "soldByPrice": {"15.99": 1}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/offenbach/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1931-15538", "city": "Regensburg", "cinema": "CinemaxX Regensburg", "date": "2026-03-18", "time": "19:00", "dateText": "Wed 18 Mar 2026 - 07:00 PM", "totalSeats": 131, "sold": 5, "available": 122, "unavailable": 0, "revenue": 80, "soldByPrice": {"15.99": 5}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/regensburg/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1531-13492", "city": "Trier", "cinema": "CinemaxX Trier", "date": "2026-03-18", "time": "19:15", "dateText": "Wed 18 Mar 2026 - 07:15 PM", "totalSeats": 182, "sold": 0, "available": 178, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/trier/film/ustaad-bhagat-singh", "ticketPrice": 14.99}, {"showId": "cinemaxx-1801-15523", "city": "München", "cinema": "CinemaxX München", "date": "2026-03-18", "time": "19:20", "dateText": "Wed 18 Mar 2026 - 07:20 PM", "totalSeats": 121, "sold": 30, "available": 87, "unavailable": 0, "revenue": 480, "soldByPrice": {"15.99": 30}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/munchen/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "cinemaxx-1011-17641", "city": "Dresden", "cinema": "CinemaxX Dresden", "date": "2026-03-18", "time": "19:15", "dateText": "Wed 18 Mar 2026 - 07:15 PM", "totalSeats": 262, "sold": 7, "available": 251, "unavailable": 0, "revenue": 112, "soldByPrice": {"15.99": 7}, "rowPrices": {}, "source": "cinemaxx", "bookingUrl": "https://www.cinemaxx.de/kinoprogramm/dresden/film/ustaad-bhagat-singh", "ticketPrice": 15.99}, {"showId": "luxor-2331133", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-18", "time": "20:30", "dateText": "Wed 18 Mar 2026 - 08:30 PM", "totalSeats": 125, "sold": 4, "available": 121, "unavailable": 0, "revenue": 91, "soldByPrice": {"22.782608695652176": 4}, "rowPrices": {"0": 22.0, "1": 29.0}, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2331133"}, {"showId": "luxor-2334534", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-21", "time": "16:00", "dateText": "Sat 21 Mar 2026 - 04:00 PM", "totalSeats": 123, "sold": 0, "available": 123, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {"0": 18.0, "1": 23.0}, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334534"}, {"showId": "luxor-2334535", "city": "Heidelberg", "cinema": "LUXOR FILM PALAST", "date": "2026-03-22", "time": "16:00", "dateText": "Sun 22 Mar 2026 - 04:00 PM", "totalSeats": 123, "sold": 0, "available": 123, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {"0": 18.0, "1": 23.0}, "source": "luxor", "bookingUrl": "https://ticket-cloud.de/Luxor-Heidelberg/Show/2334535"}, {"showId": "ticketverz-8bae530abf", "city": "Berlin", "cinema": "Cineplex Berlin", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 550, "sold": 9, "available": 541, "unavailable": 0, "revenue": 216, "soldByPrice": {"24": 9}, "rowPrices": {"0": 20.99, "1": 24}, "source": "ticketverz", "bookingUrl": "https://ticketverz.com/movieselection/ustaad-bhagat-singh-berlin/8bae530abf"}]};
// SEAT_DATA_END

function loadShows() {
  const shows = JSON.parse(JSON.stringify(showsData));

  if (seatData) {
    for (const real of seatData.shows) {
      for (const show of shows) {
        if (show.id === real.showId) {
          show.totalSeats = real.totalSeats;
          show.ticketsBooked = real.sold;
          show.realData = true;
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

function getStatus(percent) {
  if (percent >= 100) return { text: 'Sold Out', cls: 'status-sold-out' };
  if (percent >= 75) return { text: 'Almost Full', cls: 'status-almost-full' };
  if (percent >= 30) return { text: 'Filling Up', cls: 'status-filling' };
  return { text: 'Available', cls: 'status-available' };
}

function getBarClass(percent) {
  if (percent >= 100) return 'progress-full';
  if (percent >= 75) return 'progress-high';
  if (percent >= 30) return 'progress-mid';
  return 'progress-low';
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

  const totalSeats = filtered.reduce((a, s) => a + s.totalSeats, 0);
  const totalBooked = filtered.reduce((a, s) => a + s.ticketsBooked, 0);
  const totalAvailable = totalSeats - totalBooked;
  const overallPercent = totalSeats > 0 ? Math.round((totalBooked / totalSeats) * 100) : 0;


  // Countdown to premiere (18 March 2026)
  const premiere = new Date('2026-03-18T00:00:00');
  const now = new Date();
  const diffMs = premiere - now;
  let countdownHtml = '';
  if (diffMs <= 0) {
    countdownHtml = '<div class="summary-card countdown-card"><div class="value">NOW</div><div class="label">Premiered!</div></div>';
  } else {
    const days = Math.ceil(diffMs / 86400000);
    countdownHtml = `<div class="summary-card countdown-card"><div class="value">${days}</div><div class="label">Days to Premiere</div></div>`;
  }

  const summaryBar = document.getElementById('summaryBar');
  if (summaryBar && isAdmin) {
    const movieName = seatData ? seatData.movie : 'Ustaad Bhagat Singh - Telugu';
    summaryBar.innerHTML = `
      <div class="summary-row-top">
        <div class="top-movie-name">${escapeHtml(movieName)}</div>
        ${countdownHtml}
      </div>
      <div class="summary-row-stats">
        <div class="summary-card"><div class="value">${filtered.length}</div><div class="label">Shows</div></div>
        <div class="summary-card"><div class="value">${totalSeats}</div><div class="label">Total Seats</div></div>
        <div class="summary-card highlight"><div class="value">${totalBooked}</div><div class="label">Booked</div></div>
        <div class="summary-card"><div class="value">${totalAvailable}</div><div class="label">Available</div></div>
        <div class="summary-card highlight"><div class="value">${overallPercent}%</div><div class="label">Booking %</div></div>
      </div>
    `;
  }

  const showList = document.getElementById('showList');
  showList.innerHTML = '';

  filtered.forEach(show => {
    const percent = show.totalSeats > 0 ? Math.round((show.ticketsBooked / show.totalSeats) * 100) : 0;
    const available = show.totalSeats - show.ticketsBooked;
    const status = getStatus(percent);

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
      <span class="status-badge ${status.cls}">${status.text}</span>
      ${isAdmin && show.realData ? '<span style="font-size:0.65rem;background:#0f3460;color:#4fc3f7;padding:2px 8px;border-radius:8px;margin-left:6px;">LIVE DATA</span>' : ''}
      <div style="font-size:0.75rem;color:#666;margin-top:4px;">${show.language} &bull; ${show.date}</div>
      ${isAdmin ? `<div class="stats">
        <div class="stat-row">
          <span class="stat-label">Total Seats</span>
          <span class="stat-value">${show.totalSeats}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Booked</span>
          <span class="stat-value">${show.ticketsBooked}</span>
        </div>
        <div class="stat-row">
          <span class="stat-label">Available</span>
          <span class="stat-value">${available}</span>
        </div>
        <div>
          <div class="progress-bar-container">
            <div class="progress-bar ${getBarClass(percent)}" style="width: ${Math.min(percent, 100)}%"></div>
          </div>
          <div class="percentage-text" style="color: ${percent >= 100 ? '#ff6b81' : '#aaa'}">${percent}% Booked</div>
        </div>
      </div>` : ''}
      ${show.bookingUrl ? `<a href="${show.bookingUrl}" target="_blank" rel="noopener" class="book-btn">Book Now</a>` : '<span class="book-btn book-btn-soon">Coming Soon</span>'}
    `;
    showList.appendChild(card);
  });

  if (isAdmin) {
    renderRevenueTable();
  } else {
    const rp = document.querySelector('.right-panel');
    if (rp) rp.style.display = 'none';
  }
}

function renderRevenueTable() {
  const section = document.getElementById('revenueSection');
  const filtered = getFilteredShows();

  // Build per-show revenue rows
  let rows = '';
  let grandTotalSeats = 0;
  let grandTotalSold = 0;
  let grandTotalRevenue = 0;

  filtered.forEach(show => {
    let revenue = 0;
    let soldByPrice = {};
    let rowPrices = show.prices || {};

    if (seatData) {
      const real = seatData.shows.find(s => s.showId === show.id);
      if (real) {
        revenue = real.revenue || 0;
        soldByPrice = real.soldByPrice || {};
        rowPrices = real.rowPrices || {};
      }
    }

    const prices = Object.values(rowPrices);
    const uniquePrices = [...new Set(prices)].sort((a, b) => a - b).map(p => `€${p}`).join(' / ');

    grandTotalSeats += show.totalSeats;
    grandTotalSold += show.ticketsBooked;
    grandTotalRevenue += revenue > 0 ? revenue : show.ticketsBooked * 21;

    rows += `
      <tr>
        <td>${escapeHtml(show.city)}</td>
        <td>${escapeHtml(show.cinema)}</td>
        <td>${show.totalSeats}</td>
        <td>${show.ticketsBooked}</td>
        <td>${uniquePrices || '-'}</td>
        <td class="amount">€${(revenue > 0 ? revenue : show.ticketsBooked * 21).toLocaleString()}</td>
      </tr>
    `;
  });

  section.innerHTML = `
    <div class="revenue-section-title">Revenue Summary</div>
    <div class="revenue-section-sub">Ticket prices and gross collection${seatData ? ' &bull; Updated: ' + new Date(seatData.fetchedAt).toLocaleDateString('en-GB', {day: 'numeric', month: 'long', year: 'numeric'}) : ''}</div>
    <table class="revenue-table">
      <thead>
        <tr>
          <th>City</th>
          <th>Cinema</th>
          <th>Seats</th>
          <th>Sold</th>
          <th>Ticket Prices</th>
          <th>Gross Collection</th>
        </tr>
      </thead>
      <tbody>
        ${rows}
        <tr class="total-row">
          <td colspan="2">TOTAL</td>
          <td>${grandTotalSeats}</td>
          <td>${grandTotalSold}</td>
          <td></td>
          <td class="amount">€${grandTotalRevenue.toLocaleString()}</td>
        </tr>
      </tbody>
    </table>
  `;
}

render();
document.getElementById('dateFilter').addEventListener('change', render);
