# BouleAI — LLM Advisory Council

> **Four minds. One verdict.**
> BouleAI broadcasts your question to 4 free-tier AI models simultaneously, aggregates their answers, then passes everything to a 5th "Chairman" model to produce a single, synthesized consensus response.

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [How It Works](#2-how-it-works)
3. [Prerequisites](#3-prerequisites)
4. [Installation](#4-installation)
5. [Configuration — `.env` File](#5-configuration--env-file)
6. [Running the Application](#6-running-the-application)
7. [Using the API Directly](#7-using-the-api-directly)
8. [Project Structure](#8-project-structure)
9. [Architecture Rules](#9-architecture-rules)

---

## 1. Project Overview

BouleAI implements a **Scatter → Gather → Synthesize** multi-agent pattern on top of [OpenRouter](https://openrouter.ai)'s free-tier LLM endpoints:

| Stage | What happens |
|---|---|
| **Scatter** | User prompt is sent to **4 council models** concurrently via `asyncio.gather` |
| **Gather** | All 4 responses (or graceful failure strings) are collected and formatted |
| **Synthesize** | The formatted block is sent to a **Chairman model** that arbitrates contradictions and returns one definitive answer |

The backend is a **FastAPI** async Python server. The frontend is **pure vanilla HTML/CSS/JS** — no React, no Node.js build step.

---

## 2. How It Works

```
User Prompt
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  SCATTER  (asyncio.gather — all 4 fire simultaneously)  │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Council 1   │  │  Council 2   │  │  Council 3   │  │  Council 4   │ │
│  │ trinity-large│  │ glm-4.5-air  │  │ trinity-mini │  │  openchat-7b │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
└─────────┼─────────────────┼─────────────────┼─────────────────┼─────────┘
          │                 │                 │                 │
          └─────────────────┴────────┬────────┴─────────────────┘
                                     │
                              GATHER & FORMAT
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │   Chairman Model       │
                         │  trinity-large-preview │
                         │                        │
                         │  • Resolves conflicts  │
                         │  • No 5th opinion      │
                         │  • Structured output   │
                         └───────────┬────────────┘
                                     │
                                     ▼
                            Final Verdict (JSON)
```

**Resilience:** Every API call has a 10s connect / 60s read timeout plus **3 retries with exponential backoff** (2s → 4s → 8s + jitter). If a council model fails all 3 retries, it returns a labelled fallback string — the Chairman still synthesizes the remaining answers, so the system **never crashes**.

---

## 3. Prerequisites

| Requirement | Version / Notes |
|---|---|
| **Python** | 3.10 or newer (`python --version`) |
| **OpenRouter API key** | Free account at [openrouter.ai](https://openrouter.ai) → *Keys* |
| **pip** | Comes with Python |

> **No Node.js, no npm, no build tools required.** The frontend is served directly by FastAPI as static files.

---

## 4. Installation

```powershell
# 1. Clone / download the project
cd "LLM Council - BouleAI"

# 2. (Recommended) Create a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt
```

**`requirements.txt` contents:**
```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
aiohttp>=3.9.0
python-dotenv>=1.0.0
```

---

## 5. Configuration — `.env` File

> ⚠️ **The server will refuse to start if `OPENROUTER_API_KEY` is missing or empty.** This is intentional — a missing key means every API call would fail anyway.

**Step 1** — Copy the template:
```powershell
copy .env.example .env
```

**Step 2** — Open `.env` in any text editor and fill in your key:
```dotenv
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Rules for the `.env` file:**
- The file must be named exactly **`.env`** (not `env.txt`, not `.env.example`)
- The key must be on **one line**, no spaces around the `=`
- Do **not** wrap the value in quotes — `python-dotenv` reads it literally
- The `.env` file must be in the **project root** (same folder as `main.py`)
- **Never commit `.env` to Git** — add it to `.gitignore`

**Example of a correctly formatted `.env`:**
```
OPENROUTER_API_KEY=sk-or-v1-abc123def456ghi789jkl012mno345pqr678stu
```

**Example of common mistakes that will crash the server:**
```dotenv
# ❌ WRONG — quotes included in the key value
OPENROUTER_API_KEY="sk-or-v1-..."

# ❌ WRONG — spaces around equals
OPENROUTER_API_KEY = sk-or-v1-...

# ❌ WRONG — file named env.txt instead of .env
```

---

## 6. Running the Application

```powershell
# From the project root (where main.py lives):
uvicorn main:app --reload
```

Expected startup output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started server process [...]
✅ Frontend static files mounted from: ...\frontend
🚀 BouleAI starting up…
INFO:     Application startup complete.
```

Open **http://127.0.0.1:8000** in your browser.

> **Note:** Free-tier OpenRouter models can take **15–25 seconds** to respond. The UI shows a live timer and cycling status messages while you wait — this is expected behaviour, not a hang.

---

## 7. Using the API Directly

The Swagger UI at **http://127.0.0.1:8000/docs** lets you test the endpoint interactively.

**`POST /api/v1/consult`**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/consult \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are the trade-offs between REST and GraphQL?",
    "council_models": [
      "arcee-ai/trinity-large-preview:free",
      "z-ai/glm-4.5-air:free",
      "arcee-ai/trinity-mini:free",
      "openchat/openchat-7b:free"
    ],
    "chairman_model": "arcee-ai/trinity-large-preview:free"
  }'
```

**Response shape:**
```json
{
  "verdict": "## Consensus Verdict\n...\n## Key Points of Agreement\n...",
  "aggregated_council_responses": "==...== [Council Member 1/4] ...",
  "council_members": [
    {
      "model": "arcee-ai/trinity-large-preview:free",
      "short_name": "trinity-large-preview",
      "succeeded": true,
      "response_preview": "First 200 chars of the response…"
    }
  ],
  "meta": {
    "council_models_queried": 4,
    "council_models_succeeded": 4,
    "council_models_failed": 0,
    "chairman_model": "arcee-ai/trinity-large-preview:free",
    "timing": {
      "council_scatter_gather_seconds": 12.3,
      "chairman_synthesis_seconds": 6.1,
      "total_seconds": 18.4
    }
  }
}
```

**Health check:**
```bash
curl http://127.0.0.1:8000/health
# → {"status": "ok", "service": "BouleAI"}
```

---

## 8. Project Structure

```
LLM Council - BouleAI/
│
├── main.py                        # FastAPI app entry point
│
├── routers/
│   └── api.py                     # POST /api/v1/consult endpoint
│
├── services/
│   ├── openrouter_client.py       # Async aiohttp client, backoff, timeouts
│   └── council_orchestrator.py   # query_council() + synthesize_consensus()
│
├── frontend/
│   ├── index.html                 # UI shell
│   ├── style.css                  # Dark theme, pure CSS
│   └── app.js                     # Fetch API controller, state management
│
├── .env                           # Your secrets (never commit this)
├── .env.example                   # Safe template to copy from
├── requirements.txt               # Python dependencies
└── BOULE_AI_ARCHITECTURE.md       # Canonical architecture & coding rules
```

---

## 9. Architecture Rules

These rules are enforced throughout the codebase (see `BOULE_AI_ARCHITECTURE.md`):

| Rule | Enforcement |
|---|---|
| **Async everything** | `aiohttp` only — `requests` is never imported |
| **Extreme resilience** | 3 retries + exponential backoff on every API call |
| **Graceful degradation** | Failed model → fallback string, Chairman still runs |
| **Lightweight frontend** | No React/Vue/Node — vanilla HTML/CSS/JS only |
| **Environment variables** | Key loaded from `.env` only, never hardcoded |
