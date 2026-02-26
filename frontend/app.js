/**
 * BouleAI — Frontend Controller (v2)
 */

'use strict';

/* ── Constants ──────────────────────────────────────────────── */
const API_ENDPOINT = '/api/v1/consult';
const MAX_CHARS = 4096;

/* ── DOM References ─────────────────────────────────────────── */
const promptInput = document.getElementById('prompt-input');
const submitBtn = document.getElementById('submit-btn');
const charCount = document.getElementById('char-count');
const statusBar = document.getElementById('status-bar');
const statusText = document.getElementById('status-text');
const elapsedTimer = document.getElementById('elapsed-timer');
const errorBanner = document.getElementById('error-banner');
const errorText = document.getElementById('error-text');
const errorCloseBtn = document.getElementById('error-close-btn');
const resultsSection = document.getElementById('results-section');
const verdictText = document.getElementById('verdict-text');
const stage1Tabs = document.getElementById('stage1-tabs');
const stage1Content = document.getElementById('stage1-content');
const reviewGrid = document.getElementById('review-grid');

/* ── State ──────────────────────────────────────────────────── */
let elapsedInterval = null;
let msgTimerInterval = null;

/* ── Character Counter ──────────────────────────────────────── */
promptInput.addEventListener('input', () => {
  const len = promptInput.value.length;
  charCount.textContent = `${len} / ${MAX_CHARS}`;
  charCount.style.color = len > MAX_CHARS * 0.9 ? 'var(--danger)' : '';
});

/* ── Submit ─────────────────────────────────────────────────── */
submitBtn.addEventListener('click', handleSubmit);

async function handleSubmit() {
  const prompt = promptInput.value.trim();
  if (!prompt) return showError('Please enter a question.');

  setLoadingState(true);
  hideError();
  resultsSection.hidden = true;

  try {
    const res = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });

    if (!res.ok) throw new Error(await res.text() || 'Server error');

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    showError(err.message);
  } finally {
    setLoadingState(false);
  }
}

/* ── Rendering ──────────────────────────────────────────────── */
function renderResults(data) {
  // 1. Render Verdict (Stage 3)
  verdictText.innerHTML = markdownToHTML(data.verdict);

  // 2. Render Stage 1 (Tabs)
  stage1Tabs.innerHTML = '';
  stage1Content.innerHTML = '';
  data.stage1_opinions.forEach((op, idx) => {
    const btn = document.createElement('button');
    btn.className = `tab-btn ${idx === 0 ? 'active' : ''}`;
    btn.textContent = `Response #${op.response_id} (${op.short_name})`;
    btn.onclick = () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      stage1Content.innerHTML = markdownToHTML(op.response);
    };
    stage1Tabs.appendChild(btn);
    if (idx === 0) stage1Content.innerHTML = markdownToHTML(op.response);
  });

  // 3. Render Stage 2 (Reviews)
  reviewGrid.innerHTML = '';
  data.stage2_reviews.forEach((rev) => {
    if (!rev.succeeded) return;
    rev.detailed_scores.forEach(score => {
      const card = document.createElement('div');
      card.className = 'review-card';
      card.innerHTML = `
        <div class="review-header">
          <span>Peer Review of #${score.response_id}</span>
          <span class="member-badge ok">Analysed</span>
        </div>
        <div class="score-strip">
          <span class="score-tag">Acc: <strong>${score.accuracy}</strong></span>
          <span class="score-tag">Ins: <strong>${score.insight}</strong></span>
          <span class="score-tag">Log: <strong>${score.logic}</strong></span>
        </div>
        <div class="critique-text">"${score.critique}"</div>
      `;
      reviewGrid.appendChild(card);
    });
  });

  resultsSection.hidden = false;
  resultsSection.scrollIntoView({ behavior: 'smooth' });
}

/* ── UI Helpers ─────────────────────────────────────────────── */
function setLoadingState(isLoading) {
  submitBtn.disabled = isLoading;
  statusBar.hidden = !isLoading;
  if (isLoading) {
    startElapsedTimer();
    const msgs = ['Deliberating...', 'Cross-reviewing...', 'Synthesizing...'];
    let i = 0;
    msgTimerInterval = setInterval(() => { statusText.textContent = msgs[++i % msgs.length]; }, 6000);
  } else {
    stopElapsedTimer();
    clearInterval(msgTimerInterval);
  }
}

function startElapsedTimer() {
  const start = Date.now();
  elapsedInterval = setInterval(() => {
    elapsedTimer.textContent = `${Math.floor((Date.now() - start) / 1000)}s`;
  }, 1000);
}

function stopElapsedTimer() {
  clearInterval(elapsedInterval);
}

function showError(msg) {
  errorText.textContent = msg;
  errorBanner.hidden = false;
}

function hideError() {
  errorBanner.hidden = true;
}

errorCloseBtn.onclick = hideError;

function markdownToHTML(text) {
  let html = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\n/g, '<br>');
  return html;
}
