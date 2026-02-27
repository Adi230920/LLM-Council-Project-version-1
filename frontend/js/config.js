/**
 * BouleAI — Runtime Configuration
 * ──────────────────────────────────────────────────────────────────────────────
 * This file is loaded BEFORE any ES module and exposes the backend URL globally.
 *
 * HOW TO SET YOUR BACKEND URL:
 *
 *   LOCAL DEVELOPMENT:
 *     Leave this as an empty string "". The frontend will use relative paths,
 *     which works when uvicorn serves both frontend and API on the same origin
 *     (e.g. http://localhost:8000).
 *
 *   PRODUCTION (Render backend + Vercel frontend):
 *     1. Deploy your FastAPI backend to Render (see DEPLOYMENT_GUIDE.md)
 *     2. Copy your Render public URL (e.g. https://bouleai.onrender.com)
 *     3. Replace the empty string below with that URL — NO trailing slash.
 *     4. Commit and push. Vercel will auto-redeploy the frontend.
 *
 *   Example:
 *     window.BOULE_BACKEND_URL = "https://bouleai.onrender.com";
 * ──────────────────────────────────────────────────────────────────────────────
 */
window.BOULE_BACKEND_URL = ""; // ← Leave "" for local dev. Set Render URL for production.
