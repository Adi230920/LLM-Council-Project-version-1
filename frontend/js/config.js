/**
 * BouleAI — Runtime Configuration
 * ──────────────────────────────────────────────────────────────────────────────
 * This file is loaded BEFORE any ES module and exposes the backend URL globally.
 *
 * HOW TO SET YOUR BACKEND URL (Render deployment):
 *
 *   1. Deploy your FastAPI backend to Render (see DEPLOYMENT_GUIDE.md)
 *   2. Copy your Render public URL  (e.g. https://bouleai.onrender.com)
 *   3. Replace the placeholder below with that URL — NO trailing slash.
 *   4. Commit and push.  Vercel will auto-redeploy the frontend.
 *
 * For LOCAL DEVELOPMENT leave this as an empty string — api.js will fall
 * back to relative paths, which works when frontend + backend are on the
 * same origin (uvicorn main:app --port 8000).
 * ──────────────────────────────────────────────────────────────────────────────
 */
window.BOULE_BACKEND_URL = ""; // ← paste your Render URL here, e.g. "https://bouleai.onrender.com"
