// Show data for Ustaad Bhagat Singh
// Admin mode: add ?admin=true to URL to see revenue section
const isAdmin = new URLSearchParams(window.location.search).get('admin') === 'true';

const showsData = [
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
    totalSeats: 145,
    ticketsBooked: 0,
    bookingUrl: "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582",
    prices: {  },
  },
]// Embedded real seat data (auto-injected by fetch_seats.py)
// SEAT_DATA_START
const seatData = {"fetchedAt": "2026-03-09T15:03:02Z", "movie": "Ustaad Bhagat Singh - Telugu", "totalShows": 2, "totalSeats": 290, "totalBooked": 0, "totalAvailable": 290, "overallBookingPercent": 0.0, "totalRevenue": 0, "shows": [{"showId": "capitol-25577", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-18", "time": "19:30", "dateText": "Wed 18 Mar 2026 - 07:30 PM", "totalSeats": 145, "sold": 0, "available": 145, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25577"}, {"showId": "capitol-25582", "city": "Stuttgart", "cinema": "Capital Kornwestheim", "date": "2026-03-21", "time": "21:15", "dateText": "Sat 21 Mar 2026 - 09:15 PM", "totalSeats": 145, "sold": 0, "available": 145, "unavailable": 0, "revenue": 0, "soldByPrice": {}, "rowPrices": {}, "source": "kinotickets.express", "bookingUrl": "https://kinotickets.express/kornwestheim-capitol/sale/seats/25582"}]};
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
