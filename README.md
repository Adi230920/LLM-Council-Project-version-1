<div align="center">

# BouleAI — LLM Advisory Council

### *Four minds. Three stages. One verdict.*

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-Free%20Tier-FF6B35?style=flat-square)](https://openrouter.ai/)
[![Groq](https://img.shields.io/badge/Groq-Ultra--Fast%20LLM-F55036?style=flat-square)](https://groq.com/)
[![Vercel](https://img.shields.io/badge/Vercel-Ready-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

## 📖 What is BouleAI?

Most AI chatbots give you **one opinion from one model**. BouleAI is different.

Inspired by ancient Athenian democratic councils (*Boule* — βουλή), BouleAI routes every query through a **rigorous 3-stage deliberation pipeline** powered by multiple independent LLM models. Instead of trusting a single AI's answer, you get a synthesized consensus — the product of independent reasoning, anonymous peer critique, and a final chairman synthesis.

Think of it as a **peer-reviewed answer**, produced in real time.

---

## ✨ Features

- **3-Stage Deliberation Pipeline** — Opinions → Peer Review → Chairman Synthesis
- **Multi-Provider Support** — Routes requests to both OpenRouter and Groq simultaneously
- **Fully Async** — Zero blocking calls; built on `aiohttp` and FastAPI's ASGI runtime
- **Graceful Degradation** — If any model fails, the pipeline continues with the remaining results
- **Production-Hardened** — Rate limiting (5 req/min/IP), CSP headers, anonymized peer reviews
- **Zero Frontend Dependencies** — Pure HTML5 / CSS3 / ES6 (no build step, no npm)
- **Vercel-Ready** — Serverless-compatible Python entrypoint with correct routing configuration

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | FastAPI 0.111+ (Python 3.12, ASGI) |
| **LLM Providers** | OpenRouter (free-tier models) + Groq (ultra-fast inference) |
| **HTTP Client** | `aiohttp` (fully async, connection-pooled) |
| **Rate Limiting** | `slowapi` (in-memory, per-IP, no Redis required) |
| **Frontend** | Vanilla HTML5 + CSS3 + ES6 JavaScript |
| **Deployment** | Vercel (serverless Python runtime) |
| **Environment** | `python-dotenv` for local secrets management |

---

## 📁 Project Structure

```
LLM-Council-Project-version-1/
│
├── api/
│   └── index.py              # ← Vercel serverless entrypoint (re-exports FastAPI app)
│
├── frontend/                 # ← Static files served directly by Vercel CDN
│   ├── index.html
│   ├── css/
│   │   ├── variables.css     # Design tokens (colors, spacing, typography)
│   │   ├── layout.css        # Page structure & responsive grid
│   │   └── components.css    # UI components (chat bubbles, cards, buttons)
│   └── js/
│       ├── api.js            # Fetch calls to /api/v1/consult
│       ├── app.js            # Application bootstrap & event wiring
│       ├── state.js          # Lightweight state management
│       └── ui.js             # DOM rendering (chat messages, stage visualizer)
│
├── routers/
│   └── api.py                # FastAPI Router — POST /api/v1/consult, GET /api/v1/config
│
├── services/
│   ├── orchestrator.py       # 3-stage pipeline coordinator
│   ├── council_service.py    # Stage 1: parallel opinion generation
│   ├── review_service.py     # Stage 2: anonymous peer review
│   ├── chairman_service.py   # Stage 3: synthesis & verdict
│   ├── provider_manager.py   # Routes requests to OpenRouter or Groq
│   ├── openrouter_client.py  # Async OpenRouter API client (retry + backoff)
│   └── groq_client.py        # Async Groq API client (retry + backoff)
│
├── models/
│   └── schemas.py            # Pydantic request/response models
│
├── utils/
│   └── (anonymization & security helpers)
│
├── main.py                   # FastAPI app factory, middleware, static file mount
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel build + routing configuration
├── runtime.txt               # Python version declaration (python-3.12)
├── Procfile                  # Render/Railway deployment command
├── .env.example              # Environment variable template (safe to commit)
└── .gitignore                # Excludes .env, __pycache__, venv, etc.
```

---

## ⚡ The 3-Stage Pipeline

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 1 — Independent Opinions                             │
│  4 LLM models (OpenRouter free-tier) respond in parallel   │
│  Each model sees only the original prompt, not each other  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 2 — Anonymous Peer Review                            │
│  Council members cross-review each other's responses       │
│  Responses are anonymized (Response #1, #2...) to reduce   │
│  model-identity bias in scoring                             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  STAGE 3 — Chairman Synthesis                               │
│  A designated "Chairman" model reads all opinions +        │
│  reviews, resolves contradictions, and synthesizes a       │
│  final consensus verdict                                    │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
Structured JSON Response (DeliberationTrace)
```

---

## 🚀 Installation & Local Development

### Prerequisites

- Python 3.12+
- API keys for [OpenRouter](https://openrouter.ai/keys) (free) and optionally [Groq](https://console.groq.com/keys) (free)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Adi230920/LLM-Council-Project-version-1.git
cd LLM-Council-Project-version-1
```

### Step 2 — Create a Virtual Environment

```bash
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure Environment Variables

```bash
# Copy the example file
cp .env.example .env   # macOS/Linux
copy .env.example .env  # Windows
```

Then open `.env` and fill in your real API keys:

```toml
OPENROUTER_API_KEY=sk-or-v1-your-real-key-here
GROQ_API_KEY=gsk_your-real-key-here
ENVIRONMENT=development
ALLOWED_ORIGINS=http://localhost:8000
```

### Step 5 — Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open **[http://localhost:8000](http://localhost:8000)** in your browser to consult the council.

> **Tip:** With `ENVIRONMENT=development`, the FastAPI docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🔐 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Yes | OpenRouter API key — get one free at [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | ✅ Yes | Groq API key — get one free at [console.groq.com/keys](https://console.groq.com/keys) |
| `ENVIRONMENT` | ✅ Yes | `development` (enables `/docs`) or `production` (disables docs) |
| `ALLOWED_ORIGINS` | ✅ Yes | Comma-separated list of allowed CORS origins (e.g. `https://myapp.vercel.app`) |

---

## 🏗️ Build Instructions

**This project has no build step.** The frontend is pure HTML/CSS/JS served directly as static files.

```bash
# Verify all dependencies install cleanly
pip install -r requirements.txt

# Verify the application imports correctly
python -c "from main import app; print('✅ App import OK')"

# Run in production mode (single worker for serverless)
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## ☁️ Production Deployment

### Deploying to Vercel (Full-Stack Serverless)

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for the complete step-by-step walkthrough.

**Quick summary:**

1. Push this repo to GitHub
2. Go to [vercel.com/new](https://vercel.com/new) and import the repo
3. Add your 4 environment variables in Vercel Dashboard → Settings → Environment Variables
4. Click **Deploy**

The `vercel.json` file in this repo handles all build + routing configuration automatically.

> ⚠️ **Timeout Note:** The 3-stage LLM pipeline can take 30–90 seconds. Vercel's `maxDuration: 60` setting (used in this project's `vercel.json`) requires the **Pro plan**. On the free Hobby plan, requests will time out after 10 seconds. Consider using [Render](https://render.com/) for the backend if you're on a free tier.

### Deploying to Render (Long-Running Process)

Render supports the `Procfile` already included in this repo:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
```

1. Connect the repo in your Render dashboard
2. Set the environment variables
3. Deploy

---

## 🛡️ Security & Rate Limiting

| Feature | Implementation |
|---|---|
| **Rate Limiting** | 5 requests/min per IP on `/api/v1/consult` via `slowapi` |
| **Global Limit** | 20 requests/min per IP across all routes |
| **Security Headers** | X-Content-Type-Options, X-Frame-Options DENY, CSP |
| **CORS** | Restricted to origins listed in `ALLOWED_ORIGINS` |
| **Prompt Cap** | 800 characters max per request (prevents abuse) |
| **Token Cap** | 512 tokens max per model response |

---

## 🔧 Troubleshooting

### `EnvironmentError: OPENROUTER_API_KEY is not set`
Ensure your `.env` file exists in the project root (same directory as `main.py`) and is fully populated. Run `cat .env` to confirm. On Vercel, check your Environment Variables in the dashboard.

### `502 Bad Gateway` on the `/api/v1/consult` endpoint
The council deliberation timed out. This usually means either (a) the free-tier LLM models are under heavy load, or (b) you're on Vercel Hobby plan with a 10s timeout. Retry after a minute, or upgrade to Vercel Pro.

### The `/docs` page returns 404
`/docs` is only enabled when `ENVIRONMENT=development`. Set this in your `.env` for local development.

### `Cannot connect to localhost:8000` after starting the server
Ensure the virtual environment is activated (`venv\Scripts\activate` on Windows) and that you've installed requirements (`pip install -r requirements.txt`).

---

## 🗺️ Future Improvements

- [ ] **Streaming responses** — stream Stage 1 opinions to the frontend as they arrive instead of waiting for all 4
- [ ] **Persistent history** — save deliberation traces to a database (PostgreSQL via SQLAlchemy)
- [ ] **Model selection UI** — let users pick which council models to use
- [ ] **Custom Chairman** — allow users to designate a more powerful model (e.g. GPT-4o) as Chairman
- [ ] **Export trace** — download the full deliberation trace as a PDF or JSON file
- [ ] **Authentication** — user accounts to track and revisit past councils
- [ ] **Redis rate limiting** — replace in-memory rate limiter for multi-instance deployments

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">
Built with ⚡ FastAPI, 🧠 OpenRouter + Groq, and a commitment to epistemic rigor.
</div>
