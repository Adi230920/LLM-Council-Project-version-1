# 🚀 BouleAI — Step-by-Step Vercel Deployment Guide

> **Who is this guide for?** First-time deployers. No prior Vercel experience needed.
> Read every step carefully — this guide is written specifically for the **BouleAI** project structure.

---

## What You're Deploying

You are deploying a **full-stack Python web application**:

| Layer | Technology | Where it Runs on Vercel |
|---|---|---|
| **Backend** | FastAPI (Python 3.12) | Vercel Serverless Function (`api/index.py`) |
| **Frontend** | Vanilla HTML/CSS/JS | Vercel CDN Edge (served from `frontend/`) |
| **API Route** | `POST /api/v1/consult` | Python Function |
| **Home Page** | `frontend/index.html` | CDN (instant load, no Python needed) |

---

## ⚠️ Before You Start — Read This

> **The 3-stage LLM pipeline can take 30–90 seconds** because it calls 4+ LLM models, runs peer reviews, and runs synthesis. Vercel has two timeout limits:
>
> - **Hobby (Free) Plan:** 10 seconds → **deliberation will time out** on free plan
> - **Pro Plan:** Up to 60 seconds → covered by this project's `vercel.json`
>
> **Recommendation:** Use **Vercel Pro** for this project, OR deploy the backend on [Render](https://render.com) (free tier, no timeout) and only host the frontend on Vercel.

---

## Step 1 — Make Sure Your Code Is Pushed to GitHub

Open your terminal (PowerShell on Windows) and run:

```powershell
cd "d:\Personal Work\Personal Projects\LLM Council - BouleAI - version 1"
git status
```

You should see a clean working tree after the recent deployment prep commit. If not, run:

```powershell
git add .
git commit -m "feat: prepare for Vercel serverless deployment"
git push origin main
```

✅ **Success looks like:** `git push` completes without errors. Your repo at `github.com/Adi230920/LLM-Council-Project-version-1` shows the updated files.

---

## Step 2 — Create Your Vercel Account

1. Go to **[vercel.com](https://vercel.com)**
2. Click **"Sign Up"**
3. Choose **"Continue with GitHub"** — this links your GitHub account so Vercel can see your repos
4. Complete the signup flow

> If you already have a Vercel account linked to GitHub, skip this step.

---

## Step 3 — Import Your Repository

1. From your Vercel dashboard, click the **"Add New..."** button → **"Project"**
2. You will see a list of your GitHub repositories
3. Find **`LLM-Council-Project-version-1`** and click **"Import"**

---

## Step 4 — Configure the Project (Very Important)

On the "Configure Project" screen, you will see several settings. Here's exactly what to do:

### Framework Preset
- Vercel may ask what framework you're using
- Select **"Other"** (not Next.js, not Create React App — this is a Python backend)
- The `vercel.json` in your repo handles all configuration automatically

### Build and Output Settings
- **Build Command:** Leave blank (Python has no build step)
- **Output Directory:** Leave blank (`vercel.json` handles this)
- **Install Command:** Leave blank

### Root Directory
- Leave as **`./`** (the project root)

> 🔑 The most important thing here is **Environment Variables** — see Step 5.

---

## Step 5 — Add Your Environment Variables

This is the most critical step. Without these, the app will crash immediately.

1. On the Configure Project screen, scroll down to **"Environment Variables"**
2. Add each variable one by one:

| Name | Value | Notes |
|---|---|---|
| `OPENROUTER_API_KEY` | `sk-or-v1-your-real-key` | Get from [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | `gsk_your-real-key` | Get from [console.groq.com/keys](https://console.groq.com/keys) |
| `ENVIRONMENT` | `production` | Disables API docs for security |
| `ALLOWED_ORIGINS` | `https://YOUR-PROJECT.vercel.app` | Add your actual Vercel URL after first deploy |

> **Where is my Vercel URL?** After the first deploy, Vercel assigns a URL like `llm-council-project-version-1.vercel.app`. Come back to Settings → Environment Variables and update `ALLOWED_ORIGINS` with this URL, then redeploy.

---

## Step 6 — Click Deploy

1. Click the **"Deploy"** button
2. You will see a build log appear — watch it carefully

### What You Will See in the Build Log

```
[Build] Installing Python dependencies from requirements.txt...
[Build] Collecting fastapi>=0.111.0
[Build] Collecting uvicorn[standard]>=0.29.0
[Build] Collecting aiohttp>=3.9.0
[Build] Collecting slowapi>=0.1.9
[Build] Successfully installed all packages.
[Build] Build completed.
```

✅ **Success looks like:** A green checkmark and "Deployment Successful" with a live URL.

🔴 **If you see a build error**, see the Troubleshooting section below.

---

## Step 7 — Test Your Deployment

1. Click the URL shown in the Vercel dashboard (e.g., `https://llm-council-project-version-1.vercel.app`)
2. You should see the **BouleAI chat interface** — the dark-themed chat screen
3. Type a short question in the input box (e.g., "What is the best approach to building a startup?")
4. Click **"Consult the Council"** and wait
5. After 30–90 seconds, you should see the 3-stage deliberation results appear

✅ **What success looks like:**
- Stage 1: Four opinion cards from different models
- Stage 2: Peer review scores appear
- Stage 3: A synthesized "Chairman's Verdict" appears at the bottom

---

## Step 8 — Update ALLOWED_ORIGINS

After your first successful deploy:

1. Copy your Vercel URL (e.g., `https://llm-council-project-version-1.vercel.app`)
2. Go to Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
3. Edit `ALLOWED_ORIGINS` and replace the placeholder with your real URL:
   ```
   https://llm-council-project-version-1.vercel.app
   ```
4. Click Save, then go to **Deployments** → Click **"Redeploy"** on the latest deployment

---

## 🔴 Troubleshooting Build Failures

### Error: `ModuleNotFoundError: No module named 'fastapi'`
**Cause:** Vercel couldn't install your requirements.  
**Fix:** Check that `requirements.txt` is in the root directory (same level as `vercel.json`). Commit and push if missing.

### Error: `Error: No serverless functions were found`
**Cause:** Vercel cannot find any Python function file.  
**Fix:** Ensure `api/index.py` exists in your repo. Run `git ls-files api/` to confirm it is tracked by git.

### Error: `FUNCTION_INVOCATION_TIMEOUT`
**Cause:** The LLM deliberation took longer than your plan's timeout.  
**Fix:** Option A — Upgrade to Vercel Pro (60s timeout). Option B — Deploy backend on Render.com (no timeout) and update `ALLOWED_ORIGINS` to your Render URL.

### The page loads but "Consult the Council" returns an error
**Cause:** API keys are not set or incorrect.  
**Fix:** Go to Vercel → Settings → Environment Variables. Verify `OPENROUTER_API_KEY` and `GROQ_API_KEY` are correct. Redeploy after saving.

### CORS error in browser console
**Cause:** `ALLOWED_ORIGINS` does not match your Vercel deployment URL.  
**Fix:** Update `ALLOWED_ORIGINS` in Vercel env vars to exactly match your deployment URL (no trailing slash).

---

## 🔁 How to Redeploy After Code Changes

Every time you push to your `main` branch on GitHub, Vercel **automatically redeploys**. You don't need to do anything manually.

```powershell
# Make your changes, then:
git add .
git commit -m "your change description"
git push origin main
# Vercel picks it up automatically within ~30 seconds
```

---

## ✅ Deployment Readiness Checklist

Before considering your deployment complete, verify all of these:

- [ ] `git push` completed without errors
- [ ] Vercel build log shows "Build completed" with no errors
- [ ] The deployed URL loads the BouleAI chat interface
- [ ] Submitting a question returns a deliberation result (not an error)
- [ ] `ALLOWED_ORIGINS` has been updated with your real Vercel URL
- [ ] No API keys are visible in any public GitHub files (check `git log` to be sure)

---

## 📞 Need Help?

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **FastAPI / Vercel Python Runtime:** [vercel.com/docs/functions/runtimes/python](https://vercel.com/docs/functions/runtimes/python)
- **OpenRouter API:** [openrouter.ai/docs](https://openrouter.ai/docs)
- **Groq API:** [console.groq.com/docs](https://console.groq.com/docs)
