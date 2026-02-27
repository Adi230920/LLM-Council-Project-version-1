// js/api.js
/**
 * Handles communication with the FastAPI backend.
 *
 * In production (Render backend + Vercel frontend):
 *   window.BOULE_BACKEND_URL is set in frontend/js/config.js to the
 *   full Render URL, e.g. "https://bouleai.onrender.com"
 *
 * In local development (uvicorn serving both on port 8000):
 *   window.BOULE_BACKEND_URL is "" → falls back to relative path.
 */
const _base = (window.BOULE_BACKEND_URL || "").replace(/\/$/, "");
const API_BASE = _base ? `${_base}/api/v1` : '/api/v1';


export async function consultCouncil(promptText) {
    try {
        const response = await fetch(`${API_BASE}/consult`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                prompt: promptText,
                temperature: 0.7,
                max_tokens: 512
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || `Server Error: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error("consultCouncil Error:", error);
        throw error;
    }
}
