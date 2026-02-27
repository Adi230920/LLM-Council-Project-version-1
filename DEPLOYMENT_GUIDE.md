# 🚀 BouleAI — Free Deployment Guide
## Backend on Render · Frontend on Vercel · Zero Cost

> **Who is this for?** First-time deployers. No Render or Vercel experience needed.
> Plain English, no skipping steps.

---

## Architecture Overview

```
Your Browser
   │
   ├── Loads the page from → VERCEL FREE (static CDN, instant)
   │                         frontend/index.html + CSS + JS
   │
   └── API calls go to    → RENDER FREE (web service, no timeout)
                            FastAPI, uvicorn, 3-stage LLM pipeline
```

**Why two platforms?**
Vercel Free has a 10-second function timeout. The BouleAI 3-stage pipeline takes 30–90 seconds. Render Free runs a persistent process with **no timeout at all**. Vercel Free serves the static HTML/CSS/JS from a global CDN with zero cost. Together they give you a 100% free, production-grade deployment.

---

## What You'll Need Before Starting

- [ ] A GitHub account (you already have one — your code is there)
- [ ] A [Render](https://render.com) account (free, sign up with GitHub)
- [ ] A [Vercel](https://vercel.com) account (free, sign up with GitHub)
- [ ] Your `OPENROUTER_API_KEY` from [openrouter.ai/keys](https://openrouter.ai/keys)
- [ ] Your `GROQ_API_KEY` from [console.groq.com/keys](https://console.groq.com/keys)

Grab both API keys now (both are free) before starting.

---

## STEP 1 — Deploy the Backend to Render

### 1a. Create your Render account

1. Go to **[render.com](https://render.com)** and click **"Get Started for Free"**
2. Choose **"Continue with GitHub"** — this lets Render see your repos
3. Complete the signup

### 1b. Create a new Web Service

1. From your Render Dashboard, click **"New +"** → **"Web Service"**
2. Click **"Connect a repository"**
3. Find **`LLM-Council-Project-version-1`** and click **"Connect"**

### 1c. Configure the Web Service

On the configuration screen, fill in exactly these values:

| Setting | Value |
|---|---|
| **Name** | `bouleai` (or any name you like) |
| **Region** | Choose the one closest to you |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |

> **Important:** The Start Command must be exactly as shown above. The `$PORT` variable is provided by Render automatically.

### 1d. Choose the Free plan

- Scroll down to **"Instance Type"**
- Select **"Free"**
- Click **"Create Web Service"**

### 1e. Set Environment Variables

Before your first deploy, add your secrets:

1. In your new Render service, go to **"Environment"** tab (in the left sidebar)
2. Click **"Add Environment Variable"** and add each one:

| Key | Value |
|---|---|
| `OPENROUTER_API_KEY` | Your real OpenRouter key (starts with `sk-or-v1-`) |
| `GROQ_API_KEY` | Your real Groq key (starts with `gsk_`) |
| `ENVIRONMENT` | `production` |
| `ALLOWED_ORIGINS` | `*` ← temporary value, we'll fix this after Vercel deploy |

> **Why `*` for ALLOWED_ORIGINS?** We don't know your Vercel URL yet. We'll update this after Step 3.

3. Click **"Save Changes"**

### 1f. Wait for first deploy

- Render will start building automatically
- Click the **"Logs"** tab to watch progress
- The build takes 2–4 minutes on first run

**What success looks like in the logs:**
```
==> pip install -r requirements.txt
Successfully installed fastapi uvicorn aiohttp ...
==> Starting service with 'uvicorn main:app ...'
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 BouleAI starting up…
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:10000
```

✅ You should see **"Your service is live"** at the top of the page.

---

## STEP 2 — Copy Your Render Backend URL

1. Go to the top of your Render service page
2. You'll see a URL like:
   ```
   https://bouleai.onrender.com
   ```
3. **Copy this URL exactly** — you'll need it in the next step

---

## STEP 3 — Update the Frontend with Your Render URL

This is the step that connects your Vercel frontend to your Render backend.

1. Open this file in your code editor:
   ```
   frontend/js/config.js
   ```

2. You'll see this line:
   ```javascript
   window.BOULE_BACKEND_URL = "";
   ```

3. Replace it with your Render URL (no trailing slash):
   ```javascript
   window.BOULE_BACKEND_URL = "https://bouleai.onrender.com";
   ```

4. Save the file, then commit and push:
   ```powershell
   git add frontend/js/config.js
   git commit -m "config: set Render backend URL for production"
   git push origin main
   ```

---

## STEP 4 — Deploy the Frontend to Vercel

### 4a. Create your Vercel account

1. Go to **[vercel.com](https://vercel.com)** and click **"Sign Up"**
2. Choose **"Continue with GitHub"**
3. Complete the signup

### 4b. Import your repository

1. From your Vercel Dashboard, click **"Add New..."** → **"Project"**
2. Find **`LLM-Council-Project-version-1`** and click **"Import"**

### 4c. Configure the project

On the configuration screen:

| Setting | Value |
|---|---|
| **Framework Preset** | **Other** (not Next.js, not React — this is static HTML) |
| **Root Directory** | Leave as `./` |
| **Build Command** | Leave blank (no build step needed) |
| **Output Directory** | `frontend` |
| **Install Command** | Leave blank |

> **Important:** Set **Output Directory** to `frontend` — this tells Vercel to serve files from the `frontend/` folder. The `vercel.json` in the repo also handles this automatically.

### 4d. No environment variables needed on Vercel

Vercel only hosts the static HTML/JS files. All secrets (API keys) live on Render. You don't need to add anything here.

### 4e. Click Deploy

- Click **"Deploy"**
- Vercel deploys in about 30 seconds (no build step!)
- You'll get a URL like `https://llm-council-project-version-1.vercel.app`

---

## STEP 5 — Lock Down CORS (Security)

Now that you have your Vercel URL, update `ALLOWED_ORIGINS` on Render:

1. Go back to **Render Dashboard** → your `bouleai` service → **"Environment"**
2. Edit `ALLOWED_ORIGINS` — replace `*` with your real Vercel URL:
   ```
   https://llm-council-project-version-1.vercel.app
   ```
3. Click **"Save Changes"**
4. Render will automatically redeploy (takes ~2 minutes)

---

## STEP 6 — Test the Full System

1. Open your Vercel URL in a browser (e.g. `https://llm-council-project-version-1.vercel.app`)
2. You should see the **BouleAI chat interface** — dark theme, welcome modal
3. Click **"Start Exploring"** to dismiss the modal
4. Type a question in the input box:
   ```
   What is the best approach to building a successful startup?
   ```
5. Click the send button and **wait 30–90 seconds**

**What success looks like:**
- A loading animation appears while the council deliberates
- Stage 1 opinion cards appear (4 different model responses)
- Stage 2 peer review scores load
- A final Chairman's Verdict appears at the bottom

✅ **Deployment complete!**

---

## ⚠️ Render Free Tier — Cold Start Warning

Render Free web services **spin down after 15 minutes of inactivity**. The first request after idle takes **~50 extra seconds** to wake the service back up. This is normal and expected.

**How to tell it's a cold start vs. an error:** The browser will wait silently for ~50s and then the full deliberation result appears. If you get a CORS error or a network error immediately, that's a different problem (see Troubleshooting below).

**To keep the service warm** (optional): Use a free uptime monitor like [UptimeRobot](https://uptimerobot.com) to ping your Render URL every 14 minutes. This prevents cold starts entirely on the free tier.

---

## 🔴 Troubleshooting

### "Network Error" or no response at all

**Cause A:** `BOULE_BACKEND_URL` in `config.js` is wrong or empty.
**Fix:** Open `frontend/js/config.js`, verify the URL matches your Render service URL exactly. Commit, push, wait for Vercel to redeploy (~30s).

**Cause B:** Your Render service is still starting up (cold start). Wait 60 seconds and try again.

### CORS error in browser DevTools (F12 → Console tab)

```
Access to fetch at 'https://bouleai.onrender.com/api/v1/consult' 
from origin 'https://your-project.vercel.app' has been blocked by CORS policy
```

**Fix:** `ALLOWED_ORIGINS` on Render doesn't match your Vercel URL.
1. Go to Render → Environment → `ALLOWED_ORIGINS`
2. Set it to exactly `https://your-project.vercel.app` (no trailing slash)
3. Save and wait for redeploy

### Render build fails with `ModuleNotFoundError`

**Fix:** Check that your `requirements.txt` is in the root of the repo (same level as `main.py`). Run `git ls-files requirements.txt` to confirm it's tracked.

### Vercel shows a blank page or 404

**Fix:** Make sure **Output Directory** is set to `frontend` in Vercel Project Settings → Build & Output Settings. The `vercel.json` in the repo also sets `"outputDirectory": "frontend"`.

### "OPENROUTER_API_KEY is not configured" appears in the chat response

**Fix:** The API key is missing or incorrect on Render. Go to Render → Environment, verify `OPENROUTER_API_KEY` starts with `sk-or-v1-` and is complete.

---

## ✅ Final Deployment Checklist

- [ ] Render service shows "Live" status
- [ ] Render build logs show `Application startup complete`
- [ ] `frontend/js/config.js` has the correct Render URL
- [ ] Vercel deployment succeeded (green checkmark)
- [ ] Vercel frontend URL loads the BouleAI chat interface
- [ ] Sending a question returns a full 3-stage deliberation result
- [ ] `ALLOWED_ORIGINS` on Render updated to the Vercel URL (not `*`)
- [ ] No API keys appear in any public GitHub files

---

## 🔁 Future Updates

Whenever you push new code to GitHub:
- **Render** auto-redeploys the backend (takes ~2–3 minutes)
- **Vercel** auto-redeploys the frontend (takes ~30 seconds)

You don't need to do anything manually after the first setup.

---

## 📞 Platform Links

| Platform | Link |
|---|---|
| Render Dashboard | [dashboard.render.com](https://dashboard.render.com) |
| Vercel Dashboard | [vercel.com/dashboard](https://vercel.com/dashboard) |
| OpenRouter Keys | [openrouter.ai/keys](https://openrouter.ai/keys) |
| Groq Keys | [console.groq.com/keys](https://console.groq.com/keys) |
| UptimeRobot (optional) | [uptimerobot.com](https://uptimerobot.com) |
