// js/api.js
/**
 * Handles communication with the FastAPI backend.
 */

// Always use a relative path — frontend is served from the same FastAPI origin.
const API_BASE = '/api/v1';

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
