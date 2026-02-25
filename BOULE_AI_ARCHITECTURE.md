# BouleAI System Architecture & Coding Guidelines

## 1. Project Overview
BouleAI is a multi-model AI advisory council. It queries 4 distinct LLMs simultaneously via OpenRouter's free tier, aggregates their responses, and passes them to a 5th "Chairman" model to synthesize a final, highly refined consensus answer. 

## 2. Technology Stack
* **Backend:** Python 3.10+, FastAPI, `aiohttp`, `asyncio`.
* **Frontend:** Vanilla HTML5, CSS3, JavaScript (Fetch API).
* **Provider:** OpenRouter (Free tier models only).

## 3. Core Architectural Pattern

The system uses a Scatter-Gather multi-agent pattern:
1.  **Scatter (Broadcast):** The user prompt is sent to 4 Council models asynchronously.
2.  **Gather (Aggregate):** The backend waits for all 4 models to return (or timeout/fail gracefully) and concatenates their answers.
3.  **Synthesize (Chairman):** The aggregated text + original prompt is sent to the Chairman model for the final verdict.

## 4. Strict Coding Rules for AI Agents
* **Rule 1: Asynchronous Everything.** Never use synchronous blocking libraries like `requests`. You MUST use `aiohttp` for all external API calls. Use `asyncio.gather` for concurrent model queries.
* **Rule 2: Extreme Resilience.** OpenRouter free endpoints drop connections and timeout. Every API call must be wrapped in a `try-except` block with exponential backoff (max 3 retries). 
* **Rule 3: Graceful Degradation.** If a Council model fails after 3 retries, DO NOT crash the system. Return a fallback string for that specific model (e.g., "[Model X failed to respond]") so the Chairman can still synthesize the remaining successful answers.
* **Rule 4: Lightweight Frontend.** No React, no Vue, no Node.js for the frontend. Stick to pure vanilla files served via FastAPI static files or a simple HTTP server.
* **Rule 5: Environment Variables.** Always load the `OPENROUTER_API_KEY` from a `.env` file. Never hardcode it.