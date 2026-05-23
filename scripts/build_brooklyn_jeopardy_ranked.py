#!/usr/bin/env python3
"""Generate jeopardy-brooklyn-history.html: the single Brooklyn Borough History
Jeopardy game. Everyone who finishes gets a civic title (Community Associate up
through Mayor) and can post their score to a localStorage leaderboard, matching
the pattern used by quiz-leaderboard.html on the app."""
import json, os

ROOT = os.path.join(os.path.dirname(__file__), '..')
cats = json.load(open(os.path.join(os.path.dirname(__file__),'brooklyn_jeopardy_categories.json')))
CAT_JSON = json.dumps(cats, ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brooklyn Borough History Jeopardy, Brooklyn CB6</title>
<meta name="description" content="The ranked edition of the Brooklyn Borough History Jeopardy game. Climb from Community Associate to Mayor, and post your score to the local leaderboard. From Brooklyn Community Board 6.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://bkcb6.app/jeopardy-brooklyn-history.html">
<meta property="og:title" content="Brooklyn Borough History Jeopardy, Brooklyn CB6">
<meta property="og:description" content="Climb from Community Associate to Mayor and post your score to the leaderboard.">
<meta property="og:image" content="https://bkcb6.app/jeopardy-preview.png">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1080">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Brooklyn Borough History Jeopardy, Brooklyn CB6">
<meta name="twitter:description" content="Climb from Community Associate to Mayor and post your score to the leaderboard.">
<meta name="twitter:image" content="https://bkcb6.app/jeopardy-preview.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root {
    --navy: #0d1b4b; --orange: #f47920; --gold: #f47920; --blue: #16235e;
    --blue-hover: #1e2f78; --white: #fff; --gray: #ccc; --green: #2ecc71; --red: #e74c3c;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'DM Sans', sans-serif; background: var(--navy); color: var(--white); min-height: 100vh; }
  .topbar { background: var(--navy); border-bottom: 3px solid var(--orange); padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .topbar-brand { display: flex; align-items: center; gap: 10px; }
  .topbar-logo { width: 44px; height: 44px; flex-shrink: 0; border-radius: 4px; overflow: hidden; }
  .topbar-logo img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .topbar-title { font-size: 1.1rem; font-weight: 800; color: var(--white); letter-spacing: 0.5px; }
  .topbar-title span { color: var(--orange); }
  .topbar-right { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .score-display { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 4px 14px; font-size: 0.9rem; font-weight: bold; color: var(--gold); }
  .main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 40px; }
  .game-header { text-align: center; padding: 20px 0 10px; }
  .game-header h1 { font-size: 2rem; font-weight: 800; color: var(--orange); text-shadow: 2px 2px 8px rgba(0,0,0,0.4); letter-spacing: 0.5px; text-transform: uppercase; }
  .game-header p { color: rgba(255,255,255,0.7); font-size: 0.95rem; margin-top: 6px; font-style: italic; }
  .board { display: grid; grid-template-columns: repeat(var(--cols, 6), minmax(0, 1fr)); gap: 6px; margin-top: 20px; }
  .category-header { background: var(--blue); border: 1px solid rgba(255,255,255,0.12); border-top: 3px solid var(--orange); border-radius: 6px; padding: 12px 8px; text-align: center; font-size: 0.78rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; color: var(--white); min-height: 70px; display: flex; align-items: center; justify-content: center; line-height: 1.3; }
  .clue-cell { background: var(--blue); border: 1px solid rgba(255,255,255,0.12); border-radius: 6px; padding: 10px 6px; text-align: center; font-size: 1.4rem; font-weight: 800; color: var(--orange); cursor: pointer; min-height: 70px; display: flex; align-items: center; justify-content: center; transition: background 0.15s, transform 0.1s; user-select: none; }
  .clue-cell:hover:not(.used) { background: var(--blue-hover); transform: scale(1.03); }
  .clue-cell.used { background: #0a1336; color: #0a1336; cursor: default; pointer-events: none; }
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
  .modal-overlay.open { display: flex; }
  .modal-card { background: var(--navy); border: 3px solid var(--gold); border-radius: 16px; max-width: 640px; width: 100%; padding: 32px 28px; text-align: center; animation: popIn 0.2s ease; max-height: 90vh; overflow-y: auto; }
  @keyframes popIn { from { transform: scale(0.85); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  .modal-category { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: var(--gold); margin-bottom: 8px; }
  .modal-value { font-size: 1.1rem; color: rgba(255,255,255,0.6); margin-bottom: 20px; }
  .modal-clue { font-size: 1.3rem; line-height: 1.5; color: var(--white); margin-bottom: 28px; min-height: 80px; display: flex; align-items: center; justify-content: center; }
  .modal-input-row { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 16px; }
  .modal-input { font-size: 1.1rem; padding: 10px 16px; border-radius: 8px; border: 2px solid var(--gold); background: rgba(255,255,255,0.1); color: var(--white); width: 280px; text-align: center; font-family: 'DM Sans', sans-serif; }
  .modal-input::placeholder { color: rgba(255,255,255,0.4); }
  .modal-input:focus { outline: none; border-color: var(--orange); }
  .btn { padding: 10px 22px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.95rem; font-weight: 700; font-family: 'DM Sans', sans-serif; transition: opacity 0.15s; }
  .btn:hover { opacity: 0.85; }
  .btn-gold { background: var(--gold); color: var(--navy); }
  .btn-gray { background: rgba(255,255,255,0.15); color: var(--white); }
  .btn-orange { background: var(--orange); color: var(--white); }
  .modal-feedback { font-size: 1rem; min-height: 28px; margin-bottom: 10px; font-weight: bold; }
  .modal-feedback.correct { color: var(--green); }
  .modal-feedback.wrong { color: var(--red); }
  .reveal-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 16px 18px; margin: 4px 0 18px; text-align: left; }
  .reveal-card:empty { display: none; }
  .reveal-answer { font-size: 1.25rem; font-weight: bold; color: var(--gold); margin-bottom: 6px; }
  .reveal-context { font-size: 0.92rem; color: rgba(255,255,255,0.82); line-height: 1.55; margin-bottom: 14px; }
  .reveal-links { display: flex; flex-wrap: wrap; gap: 8px; }
  .reveal-link { display: inline-flex; align-items: center; gap: 6px; font-size: 0.78rem; font-weight: bold; text-decoration: none; padding: 7px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); color: var(--white); background: rgba(255,255,255,0.06); transition: background 0.15s, border-color 0.15s; }
  .reveal-link:hover { background: rgba(255,255,255,0.14); border-color: var(--gold); }
  .reveal-link .ic { font-size: 0.9rem; }
  #resultsScreen { display: none; text-align: center; padding: 30px 20px; }
  #resultsScreen.active { display: block; }
  .results-title { font-size: 2rem; color: var(--gold); margin-bottom: 8px; }
  .results-score { font-size: 3rem; font-weight: bold; color: var(--white); margin: 16px 0 4px; }
  .results-score.positive { color: var(--green); }
  .results-score.negative { color: var(--red); }
  .results-label { color: rgba(255,255,255,0.6); font-size: 1rem; margin-bottom: 12px; }
  .rank-badge { display: inline-block; background: rgba(245,197,24,0.12); border: 1.5px solid var(--gold); color: var(--gold); border-radius: 30px; padding: 8px 22px; font-size: 1.25rem; font-weight: bold; margin: 6px 0 4px; }
  .rank-sub { color: rgba(255,255,255,0.7); font-size: 0.9rem; font-style: italic; margin-bottom: 22px; }
  .results-btns { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
  /* Name entry */
  .name-entry { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; padding: 20px; max-width: 420px; margin: 0 auto 22px; }
  .name-entry label { display: block; font-size: 0.8rem; color: rgba(255,255,255,0.65); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
  .name-entry input { font-size: 1.4rem; letter-spacing: 4px; text-transform: uppercase; padding: 10px 16px; border-radius: 8px; border: 2px solid var(--gold); background: rgba(255,255,255,0.1); color: var(--white); width: 140px; text-align: center; font-family: 'DM Sans', sans-serif; }
  .name-entry input:focus { outline: none; border-color: var(--orange); }
  .name-entry .btn { margin-left: 8px; }
  .saved-note { font-size: 0.85rem; color: var(--green); min-height: 20px; margin-top: 8px; }
  /* Leaderboard */
  .lb { max-width: 520px; margin: 24px auto 0; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; overflow: hidden; text-align: left; }
  .lb-head { display: flex; gap: 10px; padding: 12px 16px; background: rgba(255,255,255,0.07); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.06em; color: rgba(255,255,255,0.55); font-weight: bold; }
  .lb-row { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.06); }
  .lb-row:last-child { border-bottom: none; }
  .lb-row.me { background: rgba(245,197,24,0.1); }
  .lb-rank { width: 28px; text-align: center; font-weight: bold; color: rgba(255,255,255,0.55); }
  .lb-rank.r1 { color: var(--gold); } .lb-rank.r2 { color: #c0c0c0; } .lb-rank.r3 { color: #cd7c4a; }
  .lb-initials { width: 52px; font-weight: bold; color: var(--white); }
  .lb-score { width: 72px; font-weight: bold; color: var(--orange); }
  .lb-role { flex: 1; font-size: 0.78rem; color: rgba(255,255,255,0.7); }
  .lb-empty { padding: 22px; text-align: center; font-style: italic; color: rgba(255,255,255,0.5); font-size: 0.9rem; }
  .lb-stats { display: flex; gap: 22px; justify-content: center; margin: 18px 0 0; font-size: 0.8rem; color: rgba(255,255,255,0.6); }
  .lb-stats strong { color: var(--white); }
  .signup-bar { background: var(--gold); text-align: center; padding: 14px 20px; margin-top: 30px; }
  .signup-bar a { color: var(--navy); font-weight: bold; text-decoration: none; font-size: 0.95rem; }
  .signup-bar a:hover { text-decoration: underline; }
  .footer { text-align: center; padding: 12px; font-size: 0.75rem; color: rgba(255,255,255,0.35); }
  .footer a { color: rgba(255,255,255,0.5); }
  .ladder-link { color: var(--gold); cursor: pointer; text-decoration: underline; font-size: 0.85rem; }
  .ladder { max-width: 420px; margin: 14px auto 0; text-align: left; font-size: 0.82rem; color: rgba(255,255,255,0.75); display: none; }
  .ladder.open { display: block; }
  .ladder div { padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.06); }
  @media (max-width: 600px) {
    #boardScreen { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .board { min-width: 560px; }
    .category-header { font-size: 0.6rem; min-height: 55px; }
    .clue-cell { font-size: 1rem; min-height: 55px; }
    .game-header h1 { font-size: 1.3rem; }
    .modal-clue { font-size: 1.05rem; }
  }
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-brand">
    <div class="topbar-logo"><img src="cb6-logo.png" alt="CB6 Logo"></div>
    <div class="topbar-title">Brooklyn Borough History <span>Jeopardy</span></div>
  </div>
  <div class="topbar-right">
    <div class="score-display" id="scoreDisplay">Score: $0</div>
  </div>
</div>

<div class="main">
  <div id="boardScreen">
    <div class="game-header">
      <h1>Brooklyn Borough History</h1>
      <p>Finish the game, find your rank.</p>
    </div>
    <div class="board" id="board"></div>
  </div>

  <div id="resultsScreen">
    <div class="results-title">&#127942; Game Over!</div>
    <div class="results-score" id="finalScore"></div>
    <div class="results-label">Final Score</div>
    <div class="rank-badge" id="rankBadge"></div>
    <div class="rank-sub" id="rankSub"></div>

    <div class="name-entry" id="nameEntry">
      <label for="initialsInput">Add your initials to the leaderboard</label>
      <input id="initialsInput" maxlength="3" placeholder="ABC" />
      <button class="btn btn-gold" onclick="saveScore()">Post</button>
      <div class="saved-note" id="savedNote"></div>
    </div>

    <div class="lb">
      <div class="lb-head">
        <div style="width:28px">#</div>
        <div style="width:52px">Name</div>
        <div style="width:72px">Score</div>
        <div style="flex:1">Title</div>
      </div>
      <div id="lbBody"><div class="lb-empty">No scores yet. Be the first.</div></div>
    </div>
    <div class="lb-stats">
      <div>Games played: <strong id="lbTotal">0</strong></div>
      <div>Top title: <strong id="lbTop">--</strong></div>
    </div>
    <div style="margin-top:14px"><span class="ladder-link" onclick="toggleLadder()">See the title ladder</span></div>
    <div class="ladder" id="ladder"></div>

    <div class="results-btns" style="margin-top:22px">
      <button class="btn btn-gold" onclick="resetGame()">&#128260; Play Again</button>
      <a href="crossword-brooklyn-history.html" class="btn btn-gray">&#129513; Crossword</a>
    </div>
  </div>
</div>

<div class="modal-overlay" id="clueModal">
  <div class="modal-card">
    <div class="modal-category" id="modalCategory"></div>
    <div class="modal-value" id="modalValue"></div>
    <div class="modal-clue" id="modalClue"></div>
    <div class="modal-input-row" id="modalInputRow">
      <input type="text" class="modal-input" id="modalInput" placeholder="What is...?" />
      <button class="btn btn-gold" onclick="checkAnswer()">Submit</button>
    </div>
    <div class="modal-feedback" id="modalFeedback"></div>
    <div class="reveal-card" id="revealCard"></div>
    <div id="modalNextRow" style="display:none;text-align:center;margin-top:8px;">
      <button class="btn btn-orange" onclick="closeModal()">Continue &#8594;</button>
    </div>
  </div>
</div>

<div class="signup-bar">
  <a href="https://docs.google.com/forms/d/1So02DHCINVIxHzq3ZKYe_wSdWGjO-9a34SJQyEEM4yU/viewform" target="_blank">
    &#9993;&#65039; Sign up to find out about more puzzles &amp; games
  </a>
</div>
<div class="footer">
  A civic history game from <a href="https://bkcb6.app" target="_blank">bkcb6.app</a> &middot; scores are saved on this device
  <div style="margin-top:6px;font-size:0.68rem;color:rgba(255,255,255,0.3)">Game designed by Mike Racioppo</div>
</div>

<script>
const CATEGORIES = __CAT_JSON__;

// Civic title ladder, low to high. minPct is the share of max score needed.
const TITLES = [
  { min: 0.00, name: 'Community Associate' },
  { min: 0.20, name: 'Board Member' },
  { min: 0.35, name: 'Committee Chair' },
  { min: 0.50, name: 'District Manager' },
  { min: 0.62, name: 'Community Board Chair' },
  { min: 0.74, name: 'Borough President' },
  { min: 0.84, name: 'City Council Member' },
  { min: 0.93, name: 'Deputy Mayor' },
  { min: 1.00, name: 'Mayor' }
];
const LB_KEY = 'bk_history_jeopardy_lb';
const STATS_KEY = 'bk_history_jeopardy_stats';
const MAX_SCORE = CATEGORIES.reduce((s, c) => s + c.clues.reduce((a, x) => a + x.value, 0), 0);

let score = 0;
let cluesAnswered = 0;
let totalClues = CATEGORIES.reduce((s, c) => s + c.clues.length, 0);
let currentClue = null;
let myEntryId = null;

function titleFor(sc) {
  const pct = MAX_SCORE > 0 ? sc / MAX_SCORE : 0;
  let t = TITLES[0].name;
  for (const tier of TITLES) { if (pct >= tier.min) t = tier.name; }
  return t;
}

function getStore(key, def) {
  try { var v = localStorage.getItem(key); return v ? JSON.parse(v) : def; } catch(e) { return def; }
}
function setStore(key, val) { try { localStorage.setItem(key, JSON.stringify(val)); } catch(e) {} }

function initBoard() {
  const board = document.getElementById('board');
  board.innerHTML = '';
  board.style.setProperty('--cols', CATEGORIES.length);
  CATEGORIES.forEach(cat => {
    const hdr = document.createElement('div');
    hdr.className = 'category-header';
    hdr.textContent = cat.name;
    board.appendChild(hdr);
  });
  const maxRows = Math.max(...CATEGORIES.map(c => c.clues.length));
  for (let row = 0; row < maxRows; row++) {
    CATEGORIES.forEach((cat, col) => {
      const clue = cat.clues[row];
      const cell = document.createElement('div');
      cell.className = 'clue-cell';
      if (clue) {
        cell.dataset.col = col;
        cell.dataset.row = row;
        cell.textContent = '$' + clue.value;
        cell.addEventListener('click', () => openClue(col, row, cell));
      } else {
        cell.classList.add('used');
        cell.textContent = '';
      }
      board.appendChild(cell);
    });
  }
  updateScore();
}

function openClue(col, row, cell) {
  const clue = CATEGORIES[col].clues[row];
  currentClue = { col, row, cell, clue };
  document.getElementById('modalFeedback').textContent = '';
  document.getElementById('modalFeedback').className = 'modal-feedback';
  document.getElementById('revealCard').innerHTML = '';
  document.getElementById('modalInput').value = '';
  document.getElementById('modalNextRow').style.display = 'none';
  document.getElementById('modalInputRow').style.display = 'flex';
  document.getElementById('modalCategory').textContent = CATEGORIES[col].name;
  document.getElementById('modalValue').textContent = '$' + clue.value;
  document.getElementById('modalClue').textContent = clue.clue;
  document.getElementById('clueModal').classList.add('open');
  setTimeout(() => document.getElementById('modalInput').focus(), 100);
}

document.getElementById('modalInput').addEventListener('keydown', e => {
  if (e.key === 'Enter') checkAnswer();
});

function checkAnswer() {
  const raw = document.getElementById('modalInput').value.trim().toLowerCase();
  const clue = currentClue.clue;
  const stripped = raw.replace(/^(what|who|where)\s+(is|are|was|were)\s+/i,'').replace(/[?!.,;]+$/,'').trim();
  const correct = clue.accept.some(a => {
    const norm = a.toLowerCase().trim();
    return raw === norm || stripped === norm;
  });
  if (correct) {
    score += clue.value;
    document.getElementById('modalFeedback').textContent = '\u2705 Correct! +$' + clue.value;
    document.getElementById('modalFeedback').className = 'modal-feedback correct';
  } else {
    score -= clue.value;
    document.getElementById('modalFeedback').textContent = '\u274c Incorrect! -$' + clue.value;
    document.getElementById('modalFeedback').className = 'modal-feedback wrong';
  }
  var card = '<div class="reveal-answer">' + clue.answer + '</div>';
  card += '<div class="reveal-context">' + clue.reveal + '</div>';
  card += '<div class="reveal-links">';
  card += '<a class="reveal-link" href="' + clue.src_url + '" target="_blank" rel="noopener"><span class="ic">\ud83d\udcd6</span> Source: ' + clue.src_title + '</a>';
  if (clue.app_url) {
    card += '<a class="reveal-link" href="' + clue.app_url + '" target="_blank" rel="noopener"><span class="ic">\ud83c\udfd9\ufe0f</span> ' + clue.app_title + '</a>';
  }
  card += '</div>';
  document.getElementById('revealCard').innerHTML = card;
  updateScore();
  currentClue.cell.classList.add('used');
  currentClue.cell.textContent = '';
  document.getElementById('modalInputRow').style.display = 'none';
  document.getElementById('modalNextRow').style.display = 'block';
  cluesAnswered++;
  if (cluesAnswered >= totalClues) setTimeout(showResults, 900);
}

function closeModal() {
  document.getElementById('clueModal').classList.remove('open');
  currentClue = null;
}

function showResults() {
  closeModal();
  document.getElementById('boardScreen').style.display = 'none';
  document.getElementById('resultsScreen').classList.add('active');
  const el = document.getElementById('finalScore');
  el.textContent = (score >= 0 ? '$' : '-$') + Math.abs(score).toLocaleString();
  el.className = 'results-score ' + (score >= 0 ? 'positive' : 'negative');
  const t = titleFor(Math.max(0, score));
  document.getElementById('rankBadge').textContent = t;
  document.getElementById('rankSub').textContent = (t === 'Mayor')
    ? 'A flawless run. You run the city.'
    : 'Score higher to climb toward Mayor.';
  // reset name entry for this round
  myEntryId = null;
  document.getElementById('nameEntry').style.display = 'block';
  document.getElementById('savedNote').textContent = '';
  document.getElementById('initialsInput').value = '';
  renderLeaderboard();
}

function saveScore() {
  var input = document.getElementById('initialsInput');
  var initials = (input.value || '').trim().toUpperCase().replace(/[^A-Z]/g, '').slice(0, 3);
  if (initials.length < 1) { input.focus(); return; }
  var lb = getStore(LB_KEY, []);
  var entry = { id: Date.now(), initials: initials, score: score, role: titleFor(Math.max(0, score)) };
  lb.push(entry);
  lb.sort(function(a, b) { return b.score - a.score; });
  lb = lb.slice(0, 20);
  setStore(LB_KEY, lb);
  myEntryId = entry.id;
  var stats = getStore(STATS_KEY, { total: 0 });
  stats.total = (stats.total || 0) + 1;
  setStore(STATS_KEY, stats);
  document.getElementById('nameEntry').style.display = 'none';
  document.getElementById('savedNote').textContent = 'Posted as ' + initials + '.';
  renderLeaderboard();
}

function renderLeaderboard() {
  var lb = getStore(LB_KEY, []);
  var stats = getStore(STATS_KEY, { total: 0 });
  var body = document.getElementById('lbBody');
  document.getElementById('lbTotal').textContent = stats.total || lb.length || 0;
  document.getElementById('lbTop').textContent = lb.length ? lb[0].role : '--';
  if (!lb.length) {
    body.innerHTML = '<div class="lb-empty">No scores yet. Be the first.</div>';
    return;
  }
  var rankClass = ['r1', 'r2', 'r3'];
  body.innerHTML = lb.map(function(e, i) {
    var me = (e.id === myEntryId) ? ' me' : '';
    var sc = (e.score >= 0 ? '$' : '-$') + Math.abs(e.score).toLocaleString();
    return '<div class="lb-row' + me + '">' +
      '<div class="lb-rank ' + (rankClass[i] || '') + '">' + (i + 1) + '</div>' +
      '<div class="lb-initials">' + e.initials + '</div>' +
      '<div class="lb-score">' + sc + '</div>' +
      '<div class="lb-role">' + e.role + '</div>' +
      '</div>';
  }).join('');
}

function toggleLadder() {
  var el = document.getElementById('ladder');
  if (!el.innerHTML) {
    el.innerHTML = TITLES.slice().reverse().map(function(t) {
      var pts = Math.ceil(t.min * MAX_SCORE);
      return '<div><strong style="color:var(--gold)">' + t.name + '</strong> &middot; $' + pts.toLocaleString() + '+</div>';
    }).join('');
  }
  el.classList.toggle('open');
}

function updateScore() {
  document.getElementById('scoreDisplay').textContent = 'Score: ' + (score >= 0 ? '$' : '-$') + Math.abs(score).toLocaleString();
}

function resetGame() {
  score = 0;
  cluesAnswered = 0;
  currentClue = null;
  myEntryId = null;
  document.getElementById('resultsScreen').classList.remove('active');
  document.getElementById('boardScreen').style.display = 'block';
  document.getElementById('ladder').classList.remove('open');
  initBoard();
}

initBoard();
</script>
</body>
</html>
'''

HTML = HTML.replace('__CAT_JSON__', CAT_JSON)
out = os.path.join(ROOT, 'jeopardy-brooklyn-history.html')
with open(out, 'w') as f:
    f.write(HTML)
print("Wrote", os.path.abspath(out), "(", len(HTML), "bytes )")
