// js/app.js
import { AppState, setTheme, setOnboarded, setRequesting } from './state.js';
import { consultCouncil } from './api.js';
import { renderUserMessage, renderCouncilSkeleton, renderFinalVerdict, renderError } from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const themeToggle = document.getElementById('themeToggle');
    const modal = document.getElementById('onboardingModal');
    const startExploreBtn = document.getElementById('startExploreBtn');
    const promptInput = document.getElementById('promptInput');
    const sendBtn = document.getElementById('sendBtn');

    // Initialize Theme
    if (AppState.theme === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
    }

    // Initial Onboarding Check
    if (!AppState.hasSeenOnboarding) {
        setTimeout(() => {
            modal.classList.add('active');
        }, 500); // slight delay for smooth entry
    }

    // Event Listeners
    themeToggle.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        setTheme(newTheme);
    });

    startExploreBtn.addEventListener('click', () => {
        modal.classList.remove('active');
        setOnboarded();
        promptInput.focus();
    });

    // Auto-resize textarea
    promptInput.addEventListener('input', function () {
        this.style.height = 'auto'; // Reset height
        this.style.height = Math.min(this.scrollHeight, 200) + 'px'; // Max height capped at 200px
        sendBtn.disabled = this.value.trim().length === 0;
    });

    // Enter key to send (Shift+Enter for newline)
    promptInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    sendBtn.addEventListener('click', handleSend);

    // Core Request Flow
    async function handleSend() {
        const text = promptInput.value.trim();
        if (!text || AppState.isRequesting) return;

        // Lock UI
        setRequesting(true);
        promptInput.value = '';
        promptInput.style.height = 'auto';
        sendBtn.disabled = true;
        promptInput.disabled = true;

        // Render User Message & Loader
        renderUserMessage(text);
        const skeletonId = renderCouncilSkeleton();

        try {
            // Fetch from API
            const result = await consultCouncil(text);
            // Wait for transitions and render
            await renderFinalVerdict(result, skeletonId);
        } catch (err) {
            renderError(err.message, skeletonId);
        } finally {
            // Unlock UI
            setRequesting(false);
            promptInput.disabled = false;
            promptInput.focus();
            // Re-evaluate button state
            sendBtn.disabled = promptInput.value.trim().length === 0;
        }
    }
});
