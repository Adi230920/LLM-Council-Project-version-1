// js/ui.js

/**
 * Configure DOMPurify to allow details/summary for the trace accordion.
 */
const purifyConfig = {
    ADD_TAGS: ['details', 'summary'],
};

/**
 * Create a unique ID for dynamic elements.
 */
function generateId() {
    return 'msg-' + Math.random().toString(36).substring(2, 9);
}

/**
 * Render user's message into the chat history.
 */
export function renderUserMessage(text) {
    const history = document.getElementById('chatHistory');

    // Remove welcome banner if present
    const banner = document.getElementById('welcomeBanner');
    if (banner) banner.remove();

    const row = document.createElement('div');
    row.className = 'message-row message-user';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text; // Safe from XSS because we use textContent

    row.appendChild(bubble);
    history.appendChild(row);
    scrollToBottom();
}

/**
 * Render the animated skeleton loader while waiting for backend.
 */
export function renderCouncilSkeleton() {
    const history = document.getElementById('chatHistory');
    const skeletonId = generateId();

    const row = document.createElement('div');
    row.className = 'message-row message-council';
    row.id = skeletonId;

    row.innerHTML = `
    <div class="bubble thinking-container">
      <div class="pulse-text">
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        Council Deliberating...
      </div>
      <div class="stage-tracker">
        <span id="${skeletonId}-stage1" class="active">Stage 1: Opinions</span>
        <span id="${skeletonId}-stage2">Stage 2: Review</span>
        <span id="${skeletonId}-stage3">Stage 3: Synthesis</span>
      </div>
    </div>
  `;

    history.appendChild(row);
    scrollToBottom();

    return skeletonId;
}

/**
 * Update the skeleton to show progress visually.
 */
export function updateSkeletonStage(skeletonId, activeStageIndex) {
    const stages = [
        document.getElementById(`${skeletonId}-stage1`),
        document.getElementById(`${skeletonId}-stage2`),
        document.getElementById(`${skeletonId}-stage3`)
    ];

    stages.forEach((el, index) => {
        if (!el) return;
        if (index < activeStageIndex - 1) {
            el.className = 'done';
            el.textContent = el.textContent.replace('...', ' ✓');
        } else if (index === activeStageIndex - 1) {
            el.className = 'active';
            if (!el.textContent.includes('...')) el.textContent += '...';
        } else {
            el.className = '';
        }
    });
}

/**
 * Helper to generate the Trace Accordion HTML from the trace object.
 */
function buildTraceHTML(traceData) {
    if (!traceData || !traceData.stage1_opinions) return '';

    // 1. Build Stage 1 Grid
    const opinionsHtml = traceData.stage1_opinions.map(op => {
        const isSuccess = op.succeeded;
        return `
      <div class="opinion-card">
        <div class="model-name">
          ${DOMPurify.sanitize(op.short_name)}
          <span class="status-pill ${isSuccess ? '' : 'error'}">
            ${isSuccess ? 'Success' : 'Failed'}
          </span>
        </div>
        <div class="opinion-text">
          ${isSuccess ? marked.parse(op.response) : '<i>Failed to generate opinion.</i>'}
        </div>
      </div>
    `;
    }).join('');

    // 2. Build Stage 2 Matrix
    let reviewsHtml = '<p class="text-secondary">No cross-reviews generated.</p>';
    if (traceData.stage2_reviews && traceData.stage2_reviews.length > 0) {
        reviewsHtml = traceData.stage2_reviews.map(rev => {
            if (!rev.succeeded || !rev.detailed_scores) return '';
            const scoresHtml = rev.detailed_scores.map(score => `
        <div class="score-row">
          <strong>Reviewing Response #${score.response_id}:</strong>
          <span class="score-badge">Acc: ${score.accuracy}/10</span>
          <span class="score-badge">Ins: ${score.insight}/10</span>
          <span class="score-badge">Log: ${score.logic}/10</span>
        </div>
        <div class="critique-text">${DOMPurify.sanitize(score.critique)}</div>
      `).join('<br/>');

            return `
        <div class="review-item">
          <div class="review-header">Reviewer: ${DOMPurify.sanitize(rev.reviewer_provider)}</div>
          ${scoresHtml}
        </div>
      `;
        }).join('');
    }

    // Combine into Details/Summary
    return `
    <details class="trace-dropdown">
      <summary>View Council Deliberation Trace (Stages 1 & 2)</summary>
      <div class="trace-content">
        <div class="stage-section stage-reveal">
          <h4>Stage 1: Independent Opinions</h4>
          <div class="opinion-grid">
            ${opinionsHtml}
          </div>
        </div>
        <div class="stage-section stage-reveal">
          <h4>Stage 2: Peer Review & Scoring</h4>
          <div class="review-matrix">
            ${reviewsHtml}
          </div>
        </div>
      </div>
    </details>
  `;
}

/**
 * Animates the staging and renders the final verdict with the trace.
 */
export async function renderFinalVerdict(data, skeletonId) {
    // Simulate the stages passing visually (even if request happened fast)
    // In a real streaming app, these would be driven by socket events.
    const timing = data.meta?.timing || { stage1_seconds: 1, stage2_seconds: 1, stage3_seconds: 1 };

    // Calculate relative delays (min 800ms to feel the transition)
    const s1Delay = Math.max(800, Math.min(2000, timing.stage1_seconds * 1000));
    const s2Delay = Math.max(800, Math.min(2000, timing.stage2_seconds * 1000));

    updateSkeletonStage(skeletonId, 1);
    await new Promise(r => setTimeout(r, s1Delay));

    updateSkeletonStage(skeletonId, 2);
    await new Promise(r => setTimeout(r, s2Delay));

    updateSkeletonStage(skeletonId, 3);
    await new Promise(r => setTimeout(r, 600)); // Short final lock

    // Now replace the skeleton with the real verdict
    const skeletonRow = document.getElementById(skeletonId);
    const verdictHtml = marked.parse(data.verdict);
    const cleanVerdictHtml = DOMPurify.sanitize(verdictHtml);

    const traceHtml = buildTraceHTML(data);
    const cleanTraceHtml = DOMPurify.sanitize(traceHtml, purifyConfig);

    skeletonRow.innerHTML = `
    <div class="bubble council-message-block w-full">
      <div class="markdown-body">
        ${cleanVerdictHtml}
      </div>
      ${cleanTraceHtml}
    </div>
  `;

    // Attach intersection observer to stagger internal elements inside the trace
    const detailsEl = skeletonRow.querySelector('details');
    if (detailsEl) {
        detailsEl.addEventListener('toggle', (e) => {
            if (detailsEl.open) {
                const reveals = detailsEl.querySelectorAll('.stage-reveal');
                reveals.forEach((el, i) => {
                    setTimeout(() => el.classList.add('show'), i * 200 + 100);
                });
            }
        });
    }

    scrollToBottom();
}

/**
 * Renders an error block if the API fails.
 */
export function renderError(message, skeletonId) {
    const skeletonRow = document.getElementById(skeletonId);
    if (skeletonRow) {
        skeletonRow.innerHTML = `
      <div class="bubble markdown-body" style="border-left: 4px solid #ef4444;">
        <p style="color: #ef4444; margin: 0;"><strong>Deliberation Failed</strong></p>
        <p style="margin: 0; font-size: 0.9em;">${DOMPurify.sanitize(message)}</p>
      </div>
    `;
        scrollToBottom();
    }
}

/**
 * Utility to keep scroll anchored to bottom
 */
function scrollToBottom() {
    const history = document.getElementById('chatHistory');
    history.scrollTop = history.scrollHeight;
}
