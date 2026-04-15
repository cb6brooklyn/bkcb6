const RACE_META = {
  MAYOR: {
    file: 'data/mayor_cb_winner_margin.json',
    title: 'Mayor General ’25',
    subtitle: 'Ranking boards most pro Mamdani or most pro Cuomo by vote share.',
    sideA: { slug: 'mamdani', label: 'Mamdani', key: 'mamdani_pct', winnerValue: 'mamdani', color: '#0d1b4b' },
    sideB: { slug: 'cuomo', label: 'Cuomo', key: 'cuomo_pct', winnerValue: 'cuomo', color: '#f47920' }
  },
  Q2: {
    file: 'data/ballot_q2_cb_winner_margin.json',
    title: 'Q2 — Fast Track Affordable Housing',
    subtitle: 'Ranking boards most pro Yes / Approve or most pro No / Disapprove.',
    sideA: { slug: 'yes', label: 'Yes / Approve', key: 'yes_pct', winnerValue: 'yes', color: '#0d1b4b' },
    sideB: { slug: 'no', label: 'No / Disapprove', key: 'no_pct', winnerValue: 'no', color: '#f47920' }
  },
  Q3: {
    file: 'data/ballot_q3_cb_winner_margin.json',
    title: 'Q3 — Project Review',
    subtitle: 'Ranking boards most pro Yes / Approve or most pro No / Disapprove.',
    sideA: { slug: 'yes', label: 'Yes / Approve', key: 'yes_pct', winnerValue: 'yes', color: '#0d1b4b' },
    sideB: { slug: 'no', label: 'No / Disapprove', key: 'no_pct', winnerValue: 'no', color: '#f47920' }
  },
  Q4: {
    file: 'data/ballot_q4_cb_winner_margin.json',
    title: 'Q4 — Appeals Board',
    subtitle: 'Ranking boards most pro Yes / Approve or most pro No / Disapprove.',
    sideA: { slug: 'yes', label: 'Yes / Approve', key: 'yes_pct', winnerValue: 'yes', color: '#0d1b4b' },
    sideB: { slug: 'no', label: 'No / Disapprove', key: 'no_pct', winnerValue: 'no', color: '#f47920' }
  }
};

const GEOGRAPHIES = [
  { slug: 'citywide', label: 'Citywide', countLabel: '1–59' },
  { slug: 'brooklyn', label: 'Brooklyn', countLabel: '1–18' },
  { slug: 'queens', label: 'Queens', countLabel: '1–14' },
  { slug: 'manhattan', label: 'Manhattan', countLabel: '1–12' },
  { slug: 'bronx', label: 'Bronx', countLabel: '1–12' },
  { slug: 'statenisland', label: 'Staten Island', countLabel: '1–3' }
];

function pct(value) {
  return `${Number(value).toFixed(1)}%`;
}

function winnerChip(row, meta) {
  const isA = row.winner === meta.sideA.winnerValue;
  const label = isA ? meta.sideA.label : meta.sideB.label;
  const color = isA ? meta.sideA.color : meta.sideB.color;
  return `<span class="winner-chip"><span class="swatch" style="background:${color}"></span>${label}</span>`;
}

function isBkcb6(row) {
  return String(row.district_label || '').trim().toUpperCase() === 'BKCB6';
}

function boardLabel(row) {
  const label = `${row.district_label} <span style="color:#64748b">· ${row.district_name.replace(' Community Board', '')}</span>`;
  return isBkcb6(row) ? `<strong>${label}</strong>` : label;
}

function bkcb6Summary(sorted, selectedSide, geography) {
  const index = sorted.findIndex((row) => isBkcb6(row));
  if (index === -1) {
    return `<div class="rank-note"><strong>BKCB6</strong> is not part of the <strong>${geography.label}</strong> ranking view.</div>`;
  }
  const row = sorted[index];
  return `<div class="rank-note"><strong>BKCB6</strong> ranks <strong>#${index + 1}</strong> in <strong>${geography.label}</strong> when ordered by <strong>${selectedSide.label}</strong> vote share. Its ${selectedSide.label} share is <strong>${pct(row[selectedSide.key])}</strong>, with a winning margin of <strong>${pct(row.margin_pct)}</strong>.</div>`;
}

function rowClass(row) {
  return isBkcb6(row) ? ' class="bkcb6-row" style="background:rgba(13,27,75,.08);font-weight:700;"' : '';
}

function getRowsForGeography(data, geography) {
  if (geography === 'citywide') {
    return Object.values(data.boroughs).flat();
  }
  return data.boroughs[geography] || [];
}

function sortRows(rows, sideKey) {
  return [...rows].sort((a, b) => {
    const diff = Number(b[sideKey]) - Number(a[sideKey]);
    if (diff !== 0) return diff;
    return Number(b.margin_pct) - Number(a.margin_pct);
  });
}

function buildDonutCard(rows, meta, geography) {
  const winsA = rows.filter((row) => row.winner === meta.sideA.winnerValue).length;
  const winsB = rows.length - winsA;
  const total = rows.length || 1;
  const angle = (winsA / total) * 360;
  const pctA = (winsA / total) * 100;
  const pctB = (winsB / total) * 100;
  const donutStyle = `background:conic-gradient(${meta.sideA.color} 0deg, ${meta.sideA.color} ${angle}deg, ${meta.sideB.color} ${angle}deg, ${meta.sideB.color} 360deg)`;
  return `
    <article class="donut-card">
      <h4>${geography.label}</h4>
      <div class="donut-visual" style="${donutStyle}">
        <div class="donut-center"><strong>${rows.length}</strong><span>boards</span></div>
      </div>
      <div class="donut-stats">
        <div class="stat-pill">
          <small>${meta.sideA.label}</small>
          <strong>${winsA}</strong>
          <span>${pctA.toFixed(0)}% of boards</span>
        </div>
        <div class="stat-pill">
          <small>${meta.sideB.label}</small>
          <strong>${winsB}</strong>
          <span>${pctB.toFixed(0)}% of boards</span>
        </div>
      </div>
    </article>`;
}

function buildTable(rows, meta, selectedSide, geography) {
  const sorted = sortRows(rows, selectedSide.key);
  return `
    ${bkcb6Summary(sorted, selectedSide, geography)}
    <div class="rank-note">Showing ${sorted.length} community boards for <strong>${geography.label}</strong>. Rankings are ordered by <strong>${selectedSide.label}</strong> vote share, so the citywide view runs 1–59 and each borough view resets to its own board count.</div>
    <div class="rank-table-wrap">
      <table class="rank-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Community board</th>
            <th>Borough</th>
            <th>${selectedSide.label}</th>
            <th>Margin</th>
            <th>Winning side</th>
            <th>EDs carried</th>
          </tr>
        </thead>
        <tbody>
          ${sorted.map((row, index) => `
            <tr${rowClass(row)}>
              <td><span class="rank-badge">${index + 1}</span></td>
              <td>${boardLabel(row)}</td>
              <td>${row.borough_name}</td>
              <td><strong>${pct(row[selectedSide.key])}</strong></td>
              <td>${pct(row.margin_pct)}</td>
              <td>${winnerChip(row, meta)}</td>
              <td>${row.winner_ed_count} / ${row.total_eds}</td>
            </tr>`).join('')}
        </tbody>
      </table>
    </div>`;
}

function buildRaceSection(raceKey, data) {
  const meta = RACE_META[raceKey];
  const section = document.createElement('section');
  section.className = 'section-card';
  section.id = `ranking-${raceKey.toLowerCase()}`;

  const defaultSide = meta.sideA;
  const defaultGeography = GEOGRAPHIES[0];

  section.innerHTML = `
    <div class="section-label">${meta.title}</div>
    <div class="ranking-head">
      <h3>${meta.title}</h3>
      <p>${meta.subtitle}</p>
    </div>
    <div class="ranking-shell">
      <div class="ranking-controls">
        <div class="control-group" data-side-controls></div>
        <div class="control-group" data-geo-controls></div>
      </div>
      <div class="donut-grid" data-donut-grid></div>
      <div data-table-root></div>
    </div>`;

  const sideControls = section.querySelector('[data-side-controls]');
  const geoControls = section.querySelector('[data-geo-controls]');
  const donutGrid = section.querySelector('[data-donut-grid]');
  const tableRoot = section.querySelector('[data-table-root]');

  let activeSide = defaultSide;
  let activeGeography = defaultGeography;

  function renderControls() {
    sideControls.innerHTML = `<span class="chip-label">Side</span>` + [meta.sideA, meta.sideB].map((side, index) => `
      <button class="control-btn ${side.slug === activeSide.slug ? `active ${index === 1 ? 'orange' : ''}` : ''}" type="button" data-side="${side.slug}">${side.label}</button>`).join('');

    geoControls.innerHTML = `<span class="chip-label">Ranking scope</span>` + GEOGRAPHIES.map((geo) => `
      <button class="control-btn ${geo.slug === activeGeography.slug ? 'active' : ''}" type="button" data-geo="${geo.slug}">${geo.label} <span style="opacity:.65">${geo.countLabel}</span></button>`).join('');

    sideControls.querySelectorAll('[data-side]').forEach((btn) => {
      btn.addEventListener('click', () => {
        activeSide = btn.dataset.side === meta.sideA.slug ? meta.sideA : meta.sideB;
        render();
      });
    });

    geoControls.querySelectorAll('[data-geo]').forEach((btn) => {
      btn.addEventListener('click', () => {
        activeGeography = GEOGRAPHIES.find((geo) => geo.slug === btn.dataset.geo) || defaultGeography;
        render();
      });
    });
  }

  function render() {
    renderControls();
    donutGrid.innerHTML = GEOGRAPHIES.map((geo) => buildDonutCard(getRowsForGeography(data, geo.slug), meta, geo)).join('');
    tableRoot.innerHTML = buildTable(getRowsForGeography(data, activeGeography.slug), meta, activeSide, activeGeography);
  }

  render();
  return section;
}

async function initBallotMapRankings() {
  const root = document.getElementById('ranking-root');
  if (!root) return;

  try {
    const entries = await Promise.all(Object.entries(RACE_META).map(async ([raceKey, meta]) => {
      const response = await fetch(meta.file, { cache: 'no-store' });
      if (!response.ok) {
        throw new Error(`Failed to load ${meta.file}`);
      }
      return [raceKey, await response.json()];
    }));

    root.removeAttribute('data-loading');
    root.innerHTML = '';
    entries.forEach(([raceKey, data]) => {
      root.appendChild(buildRaceSection(raceKey, data));
    });
  } catch (error) {
    root.removeAttribute('data-loading');
    root.innerHTML = `<div class="rank-note">The ranking view could not load right now. Please refresh the page.</div>`;
    console.error(error);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initBallotMapRankings);
} else {
  initBallotMapRankings();
}
