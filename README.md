# BouleAI — LLM Advisory Council

> **Four minds. Three stages. One verdict.**
> Experience a rigorous, 3-stage deliberation process. Instead of a single AI, your queries are evaluated by a whole council of expert models to produce a high-confidence, synthesized consensus.

---

## 🚀 The 3-Stage Pipeline

| Stage | Activity | Description |
| :--- | :--- | :--- |
| **Stage 1** | **Opinions** | Multiple AI models (Groq/OpenRouter) generate independent, parallel responses. |
| **Stage 2** | **Peer Review** | Council members rigorously cross-review and critique each other's reasoning anonymously. |
| **Stage 3** | **Synthesis** | A "Chairman" model arbitrates contradictions and synthesizes the final Consensus Verdict. |

---

## 🛠️ Tech Stack

- **Backend:** FastAPI (Async Python 3.10+)
- **LLM Providers:** Groq & OpenRouter (Multi-model support)
- **Frontend:** Vanilla HTML5 / Modern CSS / ES6+ JavaScript (Zero dependencies)
- **Security:** Rate limiting (slowapi), Security Headers, CSP Hardening

---

## 📦 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/your-username/boule-ai.git
cd boule-ai

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory:
```toml
OPENROUTER_API_KEY=sk-or-v1-...
GROQ_API_KEY=gsk_...
ENVIRONMENT=production
ALLOWED_ORIGINS=http://localhost:8000
```

### 3. Run the Server
```bash
uvicorn main:app --reload
```
Open **[http://127.0.0.1:8000](http://127.0.0.1:8000)** to consult the council.

---

## 🛡️ Production Hardening
- **Rate Limiting:** IP-based throttling (5 requests/min per endpoint).
- **Security Headers:** Nosniff, Frame-Options Deny, Strict-Origin Referrer, and CSP enabled.
- **Fail-Safe:** Every API call has a 25s timeout and automatic fallback; the council never crashes if one model fails.
- **Privacy:** Anonymized peer reviews ensure unbiased Stage 2 critiquing.

---

## 📁 Project Structure
```text
├── main.py              # FastAPI Entry Point & Middleware
├── routers/             # API routes (/api/v1/consult)
├── services/            # Council Orchestrator, Review Service, Providers
├── models/              # Pydantic Schemas & Data Models
├── utils/               # Anonymization & Security Helpers
└── frontend/            # HTML/CSS/JS (Static Assets)
```
