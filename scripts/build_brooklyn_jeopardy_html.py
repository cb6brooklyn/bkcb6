#!/usr/bin/env python3
"""Generate jeopardy-brooklyn-history.html from brooklyn_jeopardy_categories.json."""
import json, os

cats = json.load(open(os.path.join(os.path.dirname(__file__),'brooklyn_jeopardy_categories.json')))
CAT_JSON = json.dumps(cats, ensure_ascii=False)

HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brooklyn Borough History Jeopardy, Brooklyn CB6</title>
<meta name="description" content="A Jeopardy-style game covering the history of all 18 Brooklyn community board districts, with a source link for every clue. From Brooklyn Community Board 6.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://bkcb6.app/jeopardy-brooklyn-history.html">
<meta property="og:title" content="Brooklyn Borough History Jeopardy, Brooklyn CB6">
<meta property="og:description" content="A Jeopardy-style game covering the history of all 18 Brooklyn community board districts, with a source link for every clue.">
<meta property="og:image" content="https://bkcb6.app/jeopardy-preview.png">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1080">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Brooklyn Borough History Jeopardy, Brooklyn CB6">
<meta name="twitter:description" content="A Jeopardy-style game covering the history of all 18 Brooklyn community board districts, with a source link for every clue.">
<meta name="twitter:image" content="https://bkcb6.app/jeopardy-preview.png">
<style>
  :root {
    --navy: #0d1b4b; --orange: #f47920; --gold: #f5c518; --blue: #060ce9;
    --light-blue: #1a1aff; --white: #fff; --gray: #ccc; --green: #2ecc71; --red: #e74c3c;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Georgia', serif; background: var(--navy); color: var(--white); min-height: 100vh; }
  .topbar { background: var(--navy); border-bottom: 3px solid var(--orange); padding: 10px 20px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }
  .topbar-brand { display: flex; align-items: center; gap: 10px; }
  .topbar-logo { width: 44px; height: 44px; flex-shrink: 0; border-radius: 4px; overflow: hidden; }
  .topbar-logo img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .topbar-title { font-size: 1.1rem; font-weight: bold; color: var(--white); letter-spacing: 0.5px; }
  .topbar-title span { color: var(--orange); }
  .topbar-right { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .score-display { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 4px 14px; font-size: 0.9rem; font-weight: bold; color: var(--gold); }
  .main { max-width: 1100px; margin: 0 auto; padding: 20px 16px 40px; }
  .game-header { text-align: center; padding: 20px 0 10px; }
  .game-header h1 { font-size: 2.2rem; color: var(--gold); text-shadow: 2px 2px 8px rgba(0,0,0,0.5); letter-spacing: 1.5px; text-transform: uppercase; }
  .game-header p { color: rgba(255,255,255,0.7); font-size: 0.95rem; margin-top: 6px; font-style: italic; }
  .board { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; margin-top: 20px; }
  .category-header { background: var(--blue); border: 2px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 12px 8px; text-align: center; font-size: 0.78rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; color: var(--white); min-height: 70px; display: flex; align-items: center; justify-content: center; line-height: 1.3; }
  .clue-cell { background: var(--blue); border: 2px solid rgba(255,255,255,0.15); border-radius: 6px; padding: 10px 6px; text-align: center; font-size: 1.4rem; font-weight: bold; color: var(--gold); cursor: pointer; min-height: 70px; display: flex; align-items: center; justify-content: center; transition: background 0.15s, transform 0.1s; user-select: none; }
  .clue-cell:hover:not(.used) { background: #2222cc; transform: scale(1.03); }
  .clue-cell.used { background: #0a0a5a; color: #0a0a5a; cursor: default; pointer-events: none; }
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
  .modal-overlay.open { display: flex; }
  .modal-card { background: var(--navy); border: 3px solid var(--gold); border-radius: 16px; max-width: 640px; width: 100%; padding: 32px 28px; text-align: center; animation: popIn 0.2s ease; }
  @keyframes popIn { from { transform: scale(0.85); opacity: 0; } to { transform: scale(1); opacity: 1; } }
  .modal-category { font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px; color: var(--gold); margin-bottom: 8px; }
  .modal-value { font-size: 1.1rem; color: rgba(255,255,255,0.6); margin-bottom: 20px; }
  .modal-clue { font-size: 1.3rem; line-height: 1.5; color: var(--white); margin-bottom: 28px; min-height: 80px; display: flex; align-items: center; justify-content: center; }
  .modal-input-row { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 16px; }
  .modal-input { font-size: 1.1rem; padding: 10px 16px; border-radius: 8px; border: 2px solid var(--gold); background: rgba(255,255,255,0.1); color: var(--white); width: 280px; text-align: center; font-family: 'Georgia', serif; }
  .modal-input::placeholder { color: rgba(255,255,255,0.4); }
  .modal-input:focus { outline: none; border-color: var(--orange); }
  .btn { padding: 10px 22px; border-radius: 8px; border: none; cursor: pointer; font-size: 0.95rem; font-weight: bold; font-family: 'Georgia', serif; transition: opacity 0.15s; }
  .btn:hover { opacity: 0.85; }
  .btn-gold { background: var(--gold); color: var(--navy); }
  .btn-gray { background: rgba(255,255,255,0.15); color: var(--white); }
  .btn-orange { background: var(--orange); color: var(--white); }
  .modal-feedback { font-size: 1rem; min-height: 28px; margin-bottom: 10px; font-weight: bold; }
  .modal-feedback.correct { color: var(--green); }
  .modal-feedback.wrong { color: var(--red); }
  .modal-answer-reveal { font-size: 1rem; color: var(--white); margin-bottom: 10px; min-height: 20px; line-height: 1.5; }
  .modal-answer-reveal strong { color: var(--gold); font-size: 1.1rem; }
  .reveal-context { font-size: 0.9rem; color: rgba(255,255,255,0.75); }
  .modal-source { font-size: 0.85rem; margin-bottom: 16px; min-height: 18px; }
  .modal-source a { color: var(--gold); text-decoration: none; }
  .modal-source a:hover { text-decoration: underline; }
  #resultsScreen { display: none; text-align: center; padding: 30px 20px; }
  #resultsScreen.active { display: block; }
  .results-title { font-size: 2rem; color: var(--gold); margin-bottom: 8px; }
  .results-score { font-size: 3rem; font-weight: bold; color: var(--white); margin: 16px 0 4px; }
  .results-score.positive { color: var(--green); }
  .results-score.negative { color: var(--red); }
  .results-label { color: rgba(255,255,255,0.6); font-size: 1rem; margin-bottom: 24px; }
  .results-rating { font-size: 1.2rem; color: var(--orange); margin-bottom: 28px; font-style: italic; }
  .results-btns { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; }
  .signup-bar { background: var(--gold); text-align: center; padding: 14px 20px; margin-top: 30px; }
  .signup-bar a { color: var(--navy); font-weight: bold; text-decoration: none; font-size: 0.95rem; }
  .signup-bar a:hover { text-decoration: underline; }
  .footer { text-align: center; padding: 12px; font-size: 0.75rem; color: rgba(255,255,255,0.35); }
  .footer a { color: rgba(255,255,255,0.5); }
  @media (max-width: 600px) {
    .board { grid-template-columns: repeat(3, 1fr); }
    .category-header { font-size: 0.6rem; min-height: 55px; }
    .clue-cell { font-size: 1rem; min-height: 55px; }
    .game-header h1 { font-size: 1.4rem; }
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
      <p>One clue for every one of Brooklyn's 18 community board districts. Pick a value, then answer in the form of a question. Each clue includes a source link.</p>
    </div>
    <div class="board" id="board"></div>
  </div>

  <div id="resultsScreen">
    <div class="results-title">&#127942; Game Over!</div>
    <div class="results-score" id="finalScore"></div>
    <div class="results-label">Final Score</div>
    <div class="results-rating" id="resultsRating"></div>
    <div class="results-btns">
      <button class="btn btn-gold" onclick="resetGame()">&#128260; Play Again</button>
      <a href="crossword-brooklyn-history.html" class="btn btn-gray">&#129513; Try the Crossword</a>
      <a href="https://bkcb6.app" target="_blank" class="btn btn-gray">&#127963; bkcb6.app</a>
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
    <div class="modal-answer-reveal" id="modalAnswerReveal"></div>
    <div class="modal-source" id="modalSource"></div>
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
  A civic history game from <a href="https://bkcb6.app" target="_blank">bkcb6.app</a> &middot; covering all 18 Brooklyn community board districts
</div>

<script>
const CATEGORIES = __CAT_JSON__;

let score = 0;
let cluesAnswered = 0;
let totalClues = CATEGORIES.reduce((s, c) => s + c.clues.length, 0);
let currentClue = null;

function initBoard() {
  const board = document.getElementById('board');
  board.innerHTML = '';
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
  document.getElementById('modalAnswerReveal').textContent = '';
  document.getElementById('modalSource').innerHTML = '';
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
  document.getElementById('modalAnswerReveal').innerHTML =
    '<strong>' + clue.answer + '</strong><br><span class="reveal-context">' + clue.reveal + '</span>';
  const src = document.getElementById('modalSource');
  src.innerHTML = 'Source: <a href="' + clue.src_url + '" target="_blank" rel="noopener">' + clue.src_title + '</a>';
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
  const maxScore = CATEGORIES.reduce((s, c) => s + c.clues.reduce((a, x) => a + x.value, 0), 0);
  let rating = '';
  if (score === maxScore) rating = '\ud83c\udfc6 A perfect run through all 18 districts!';
  else if (score >= maxScore * 0.7) rating = '\u2b50 Strong Brooklyn knowledge!';
  else if (score >= maxScore * 0.3) rating = '\ud83d\udcda Good effort, keep exploring bkcb6.app!';
  else rating = '\ud83d\udd0d Brush up on your borough history and try again!';
  document.getElementById('resultsRating').textContent = rating;
}

function updateScore() {
  document.getElementById('scoreDisplay').textContent = 'Score: ' + (score >= 0 ? '$' : '-$') + Math.abs(score).toLocaleString();
}

function resetGame() {
  score = 0;
  cluesAnswered = 0;
  currentClue = null;
  document.getElementById('resultsScreen').classList.remove('active');
  document.getElementById('boardScreen').style.display = 'block';
  initBoard();
}

initBoard();
</script>
</body>
</html>
'''

HTML = HTML.replace('__CAT_JSON__', CAT_JSON)
out = os.path.join(os.path.dirname(__file__), '..', 'jeopardy-brooklyn-history.html')
with open(out, 'w') as f:
    f.write(HTML)
print("Wrote", os.path.abspath(out), "(", len(HTML), "bytes )")
