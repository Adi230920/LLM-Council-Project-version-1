/**
 * BouleAI — Frontend Controller
 *
 * Vanilla JS only — no frameworks, no build step.
 * Uses the Fetch API to talk to POST /api/v1/consult.
 *
 * Verification:
 *  ✅ Submit button disabled during fetch, re-enabled after.
 *  ✅ "The Council is deliberating…" status bar shown during request.
 *  ✅ Live elapsed-seconds timer visible throughout the wait.
 *  ✅ Errors displayed in a dismissible banner (never silent).
 *  ✅ Zero external dependencies.
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
const metaParticipation = document.getElementById('meta-participation');
const metaTiming = document.getElementById('meta-timing');
const councilList = document.getElementById('council-members-list');

/* ── State ──────────────────────────────────────────────────── */
let elapsedInterval = null;   // handle for the live seconds setInterval
let msgTimerInterval = null;  // BUG FIX: separate handle for message-cycling timer
// Previously stored as a property on elapsedInterval,
// which caused a null-dereference after stopElapsedTimer()
// set elapsedInterval=null before the cleanup branch ran.

/* ── Character Counter ──────────────────────────────────────── */
promptInput.addEventListener('input', () => {
  const len = promptInput.value.length;
  charCount.textContent = `${len} / ${MAX_CHARS}`;
  charCount.style.color = len > MAX_CHARS * 0.9 ? 'var(--danger)' : '';
});

/* ── Submit ─────────────────────────────────────────────────── */
submitBtn.addEventListener('click', handleSubmit);

promptInput.addEventListener('keydown', (e) => {
  // Ctrl+Enter or Cmd+Enter submits
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') handleSubmit();
});

async function handleSubmit() {
  const prompt = promptInput.value.trim();

  if (!prompt) {
    showError('Please enter a question before consulting the council.');
    promptInput.focus();
    return;
  }

  if (prompt.length > MAX_CHARS) {
    showError(`Your question exceeds the ${MAX_CHARS}-character limit.`);
    return;
  }

  setLoadingState(true);
  hideError();
  hideResults();

  const body = JSON.stringify({
    prompt,
    // Models are omitted to use backend defaults
  });

  try {
    const res = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    });

    if (!res.ok) {
      // Try to extract a detail message from FastAPI error shape
      let detail = `Server error ${res.status}`;
      try {
        const errData = await res.json();
        detail = errData.detail || detail;
      } catch { /* JSON parse failed — keep default */ }
      throw new Error(detail);
    }

    const data = await res.json();
    renderResults(data);

  } catch (err) {
    // Network failures, timeouts, or thrown errors from above
    showError(err.message || 'An unexpected error occurred. Please try again.');
  } finally {
    setLoadingState(false);
  }
}

/* ── UI State Management ────────────────────────────────────── */

/**
 * Enable or disable the loading state.
 * @param {boolean} isLoading
 */
function setLoadingState(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.classList.toggle('loading', isLoading);

  if (isLoading) {
    statusBar.hidden = false;
    startElapsedTimer();

    // Cycle through deliberation messages to reassure the user during 15-20s wait
    const messages = [
      'The Council is deliberating\u2026',
      'Council members are drafting their answers\u2026',
      'Gathering responses from all members\u2026',
      'Forwarding to the Chairman for synthesis\u2026',
    ];
    let msgIdx = 0;
    statusText.textContent = messages[msgIdx];

    // BUG FIX: use a dedicated module-level variable instead of a property
    // on elapsedInterval. The old code set elapsedInterval._msgTimer after
    // startElapsedTimer() returned, then the false-branch read it after
    // stopElapsedTimer() had already set elapsedInterval = null — leak + TypeError.
    msgTimerInterval = setInterval(() => {
      msgIdx = (msgIdx + 1) % messages.length;
      statusText.textContent = messages[msgIdx];
    }, 7000);

  } else {
    statusBar.hidden = true;
    stopElapsedTimer();
    // BUG FIX: clear from dedicated variable — always safe, no null dereference.
    if (msgTimerInterval) {
      clearInterval(msgTimerInterval);
      msgTimerInterval = null;
    }
  }
}

function startElapsedTimer() {
  const start = Date.now();
  elapsedTimer.textContent = '0s';
  elapsedInterval = setInterval(() => {
    const seconds = Math.floor((Date.now() - start) / 1000);
    elapsedTimer.textContent = `${seconds}s`;
  }, 1000);
  // BUG FIX: removed elapsedInterval._msgTimer = null here;
  // msgTimer is now tracked in its own module-level variable.
}

function stopElapsedTimer() {
  if (elapsedInterval) {
    clearInterval(elapsedInterval);
    elapsedInterval = null;
  }
}

/* ── Error Handling ─────────────────────────────────────────── */
function showError(message) {
  errorText.textContent = message;
  errorBanner.hidden = false;
}

function hideError() {
  errorBanner.hidden = true;
  errorText.textContent = '';
}

errorCloseBtn.addEventListener('click', hideError);

/* ── Results Rendering ──────────────────────────────────────── */
function hideResults() {
  resultsSection.hidden = true;
  verdictText.innerHTML = '';
  councilList.innerHTML = '';
}

/**
 * Render the full API response into the DOM.
 * @param {{ verdict: string, council_members: Array, meta: object }} data
 */
function renderResults(data) {
  // Verdict — convert lightweight markdown headers to HTML
  verdictText.innerHTML = markdownToHTML(data.verdict || '(No verdict returned)');

  // Meta chips
  const { meta } = data;
  metaParticipation.textContent =
    `✅ ${meta.council_models_succeeded}/${meta.council_models_queried} council members responded`;
  metaTiming.textContent =
    `⏱ ${meta.timing.total_seconds}s total  ` +
    `(council ${meta.timing.council_scatter_gather_seconds}s · ` +
    `chairman ${meta.timing.chairman_synthesis_seconds}s)`;

  // Council member cards
  councilList.innerHTML = '';
  (data.council_members || []).forEach((member, idx) => {
    councilList.appendChild(buildMemberCard(member, idx + 1, data.council_members.length));
  });

  resultsSection.hidden = false;

  // Scroll verdict into view smoothly
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

/**
 * Build a DOM card for a single council member.
 * @param {{ model: string, short_name: string, succeeded: boolean, response_preview: string }} member
 * @param {number} idx   1-based index
 * @param {number} total total member count
 * @returns {HTMLElement}
 */
function buildMemberCard(member, idx, total) {
  const card = document.createElement('div');
  card.className = 'member-card';

  const statusIcon = member.succeeded ? '✅' : '❌';
  const badgeClass = member.succeeded ? 'ok' : 'failed';
  const badgeLabel = member.succeeded ? 'Success' : 'Failed';

  card.innerHTML = `
    <div class="member-header">
      <span class="member-status" aria-hidden="true">${statusIcon}</span>
      <span class="member-name" title="${escapeHTML(member.model)}">
        ${escapeHTML(member.short_name)}
      </span>
      <span class="meta-chip" style="font-size:0.7rem; padding:0.1rem 0.5rem; margin-left:0.4rem;">
        ${idx}/${total}
      </span>
      <span class="member-badge ${badgeClass}">${badgeLabel}</span>
    </div>
    <div class="member-body">${escapeHTML(member.response_preview)}</div>
  `;

  return card;
}

/* ── Helpers ────────────────────────────────────────────────── */

/**
 * Minimal markdown → HTML converter for the verdict field.
 * Handles: ## headings, **bold**, bullet lists, newlines.
 * No third-party library needed for this subset.
 * @param {string} text
 * @returns {string} safe HTML string
 */
function markdownToHTML(text) {
  // Escape first so we don't accidentally trust server content as HTML
  let html = escapeHTML(text);

  // ## Heading → <h2>
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

  // **bold** → <strong>
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Lines starting with "- " or "* " → wrap in <ul><li>
  html = html.replace(/((?:^[*\-] .+\n?)+)/gm, (block) => {
    const items = block
      .trim()
      .split('\n')
      .map(line => `<li>${line.replace(/^[*\-] /, '')}</li>`)
      .join('');
    return `<ul>${items}</ul>`;
  });

  // Double newlines → paragraph breaks
  html = html.replace(/\n{2,}/g, '\n\n');

  return html;
}

/**
 * Escape a string for safe insertion as HTML text content.
 * @param {string} str
 * @returns {string}
 */
function escapeHTML(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}
