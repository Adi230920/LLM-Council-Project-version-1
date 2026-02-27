<div align="center">

# BouleAI — LLM Advisory Council

### *Four minds. Three stages. One verdict.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Render](https://img.shields.io/badge/Backend-Render%20Free-46E3B7?style=flat-square)](https://render.com/)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel%20Free-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## 📖 What is BouleAI?

Most AI chatbots give you **one opinion from one model**. BouleAI is different.

Inspired by ancient Athenian democratic councils (*Boule* — βουλή), BouleAI routes every query through a **rigorous 3-stage deliberation pipeline** powered by multiple independent LLM models. Instead of trusting a single AI's answer, you get a synthesized consensus — the product of independent reasoning, anonymous peer critique, and chairman synthesis.

---

## ☁️ Deployment Architecture (100% Free)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER'S BROWSER                              │
└──────────────────┬──────────────────────┬───────────────────────────┘
                   │  Page Load           │  API Call (fetch)
                   ▼                      ▼
┌──────────────────────────┐   ┌──────────────────────────────────────┐
│   VERCEL FREE (CDN)      │   │   RENDER FREE (Web Service)          │
│   frontend/index.html    │──▶│   FastAPI — main.py                  │
│   frontend/css/*.css     │   │   POST /api/v1/consult               │
│   frontend/js/*.js       │   │   No timeout limit                   │
│                          │   │   OpenRouter + Groq LLM calls        │
│  (served globally from   │   │  (runs uvicorn, stays alive)         │
│   Vercel Edge CDN)       │   │                                      │
└──────────────────────────┘   └──────────────────────────────────────┘
        FREE                              FREE
   Next-day deploy                  ~50s cold start on
   Instant CDN                      first req after idle
```

**Why this split?** Vercel Free has a 10-second function timeout — far too short for the 3-stage LLM pipeline (30–90 s). Render Free has **no timeout** on web services. Vercel Free is ideal for the static frontend. Zero cost, no compromises.

---

## ✨ Features

- **3-Stage Deliberation Pipeline** — Opinions → Peer Review → Chairman Synthesis
- **Multi-Provider Support** — OpenRouter (free models) + Groq (fast inference)
- **Fully Async** — Zero blocking calls; built on `aiohttp` + FastAPI ASGI
- **Graceful Degradation** — Pipeline continues if individual models fail
- **Rate Limited** — 5 req/min/IP on `/consult`, 20/min global
- **Zero Frontend Dependencies** — Pure HTML5 / CSS3 / ES6 (no build step, no npm)
- **100% Free Hosting** — Render Free backend + Vercel Free frontend

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI 0.111+ (Python 3.12, ASGI) |
| **LLM Providers** | OpenRouter (free-tier models) + Groq (ultra-fast) |
| **HTTP Client** | `aiohttp` (fully async, connection-pooled) |
| **Rate Limiting** | `slowapi` (in-memory, per-IP) |
| **Frontend** | Vanilla HTML5 + CSS3 + ES6 JS |
| **Backend Hosting** | [Render](https://render.com) Free Web Service |
| **Frontend Hosting** | [Vercel](https://vercel.com) Free Static CDN |

---

## 📁 Project Structure

```
LLM-Council-Project-version-1/
│
├── frontend/                 # ← Deployed to Vercel Free (static CDN)
│   ├── index.html
│   ├── css/
│   │   ├── variables.css
│   │   ├── layout.css
│   │   └── components.css
│   └── js/
│       ├── config.js         # ← SET YOUR RENDER URL HERE before Vercel deploy
│       ├── api.js            # Reads config.js, calls Render backend
│       ├── app.js
│       ├── state.js
│       └── ui.js
│
├── routers/
│   └── api.py                # POST /api/v1/consult, GET /api/v1/config
│
├── services/                 # ← Deployed to Render Free (backend)
│   ├── orchestrator.py       # 3-stage pipeline coordinator
│   ├── council_service.py
│   ├── review_service.py
│   ├── chairman_service.py
│   ├── provider_manager.py   # Lazy-loaded client routing
│   ├── openrouter_client.py
│   └── groq_client.py
│
├── models/
│   └── schemas.py            # Pydantic models
│
├── main.py                   # FastAPI app factory + CORS + middleware
├── requirements.txt          # Python dependencies
├── Procfile                  # Render start command
├── runtime.txt               # python-3.12
├── vercel.json               # Vercel static frontend config
├── .env.example              # Env var template (safe to commit)
└── .gitignore
```

---

## ⚡ The 3-Stage Pipeline

| Stage | Activity | Description |
|:---|:---|:---|
| **Stage 1** | **Opinions** | 4 LLM models respond independently in parallel |
| **Stage 2** | **Peer Review** | Council members anonymously score each other's reasoning |
| **Stage 3** | **Synthesis** | Chairman model reads all opinions + scores → final verdict |

---

## 🚀 Local Development

### Prerequisites
- Python 3.12+
- Free API keys from [OpenRouter](https://openrouter.ai/keys) and [Groq](https://console.groq.com/keys)

```bash
# 1. Clone
git clone https://github.com/Adi230920/LLM-Council-Project-version-1.git
cd LLM-Council-Project-version-1

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # macOS/Linux
# → Edit .env with your real API keys. Set ENVIRONMENT=development

# 5. Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** — FastAPI serves both the backend API and the static frontend from one process.

> **Note:** `frontend/js/config.js` has `window.BOULE_BACKEND_URL = ""` by default, which makes `api.js` use relative paths (correct for local dev). Don't change this until you deploy to Render.

---

## 🔐 Environment Variables

Set these in **Render Dashboard → Environment** (not Vercel — Vercel only hosts static files):

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ | [openrouter.ai/keys](https://openrouter.ai/keys) — free account |
| `GROQ_API_KEY` | ✅ | [console.groq.com/keys](https://console.groq.com/keys) — free account |
| `ENVIRONMENT` | ✅ | Always `production` on Render |
| `ALLOWED_ORIGINS` | ✅ | Your Vercel frontend URL, e.g. `https://bouleai.vercel.app` |

---

## ☁️ Production Deployment (100% Free)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for the complete step-by-step walkthrough.

**Two-step summary:**
1. **Deploy backend → Render Free** (no timeout, long-running FastAPI process)
2. **Deploy frontend → Vercel Free** (instant CDN, global edge)

---

## 🛡️ Security

| Feature | Details |
|---|---|
| Rate Limiting | 5 req/min/IP on `/consult`, 20/min global |
| Security Headers | Nosniff, Frame-Options DENY, Referrer-Policy |
| CORS | Restricted to `ALLOWED_ORIGINS` env var |
| Prompt Cap | 800 chars max |
| Token Cap | 512 tokens max per model |

---

## 🔧 Troubleshooting

**`[Error: OPENROUTER_API_KEY is not configured]` in the response**
→ API keys not set on Render. Go to Render Dashboard → Your Service → Environment → add the keys.

**"Consult the Council" button does nothing / network error in browser console**
→ `BOULE_BACKEND_URL` in `frontend/js/config.js` is empty or wrong. Update it with your Render URL and redeploy to Vercel.

**CORS error in browser console**
→ `ALLOWED_ORIGINS` on Render does not match your Vercel URL. Update it in Render Environment and redeploy.

**Council takes 40–90 seconds to respond**
→ Normal. The 3-stage pipeline calls 4+ LLM APIs. If the first request after a long idle takes longer, that's Render's free-tier cold start (~50 s). Subsequent requests are fast.

**`uvicorn: command not found` on Render build**
→ Render must be running from the repo root. Check that `requirements.txt` is in the root directory.

---

## 🗺️ Future Improvements

- [ ] Streaming Stage 1 opinions to frontend as they arrive
- [ ] Persistent deliberation history (PostgreSQL)
- [ ] Model selection UI (let users pick council members)
- [ ] Export full trace as JSON / PDF
- [ ] User authentication

---

<div align="center">
Built with ⚡ FastAPI · 🧠 OpenRouter + Groq · ☁️ Render + Vercel (100% Free)
</div>
