# Deploy PayState Bridge

Step-by-step guide to putting PayState Bridge online: the Next.js console on Vercel, the FastAPI recovery engine on Railway (or Render).

> **Reminder.** This is a demo. `APP_ENV` must stay `demo`, only `rzp_test_` keys are accepted (a startup guard rejects live keys), and all data is synthetic. Never commit `.env` — keys live only in the platform dashboards.

---

## Overview

```
┌────────────────────┐      HTTPS       ┌────────────────────────┐
│  Vercel            │ ───────────────► │  Railway / Render      │
│  apps/web          │   NEXT_PUBLIC_   │  apps/api (Dockerfile) │
│  Next.js console   │    API_URL       │  FastAPI recovery      │
└────────────────────┘                  └───────────┬────────────┘
                                                     │
                                                     ▼
                                         SQLite (ephemeral)
                                         synthetic seed baked
                                         in at Docker build
```

- The web app calls the API using `NEXT_PUBLIC_API_URL`.
- The API allows the web origin via `ALLOWED_ORIGINS` (CORS).
- SQLite is ephemeral. The Docker build runs `python -m app.db.seed`, so every fresh
  instance ships with the synthetic incident set. Restarts reset to the seeded state,
  which is fine for a demo.

---

## 1. Deploy the API on Railway

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select `BhaveshKhaple/PayStateBridge`.
2. In the service settings, set the **Root Directory** to `apps/api`. Railway auto-detects the `Dockerfile` (`railway.json` pins the builder to `DOCKERFILE`).
3. Add environment variables:
   | Key | Value |
   |---|---|
   | `APP_ENV` | `demo` |
   | `ALLOWED_ORIGINS` | your Vercel URL, e.g. `https://paystate-bridge.vercel.app` (leave `http://localhost:3000` until you have it) |
   | `RAZORPAY_KEY_ID` | *(optional)* `rzp_test_...` |
   | `RAZORPAY_KEY_SECRET` | *(optional)* test secret |
   | `RAZORPAY_WEBHOOK_SECRET` | *(optional)* webhook secret |
   | `GEMINI_API_KEY` | *(optional)* enables the AI field extractor |
4. Deploy. Railway injects `$PORT`; the start command binds uvicorn to it.
5. Copy the generated public API URL (e.g. `https://paystate-api-production.up.railway.app`).

---

## 2. Deploy the API on Render (alternative)

1. Go to [render.com](https://render.com) → **New** → **Web Service** → connect the repo.
2. Choose **Docker** runtime, set the **Root Directory** to `apps/api`. (`render.yaml` also
   declares `dockerfilePath: ./apps/api/Dockerfile` and `dockerContext: ./apps/api`.)
3. Add the same environment variables as the Railway table above.
4. Deploy and copy the public API URL.

---

## 3. Deploy the Web console on Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New… → Project** → import `BhaveshKhaple/PayStateBridge`.
2. Set the **Root Directory** to `apps/web`. Vercel detects Next.js (`vercel.json` pins the framework).
3. Add environment variable:
   | Key | Value |
   |---|---|
   | `NEXT_PUBLIC_API_URL` | the Railway/Render API URL from step 1 or 2 |
4. Deploy. Copy the Vercel URL (e.g. `https://paystate-bridge.vercel.app`).

---

## 4. Wire the two together

1. Put the Vercel URL into the API's `ALLOWED_ORIGINS` (Railway/Render env var).
2. Redeploy the API so CORS picks up the new origin.
3. The web app's `NEXT_PUBLIC_API_URL` should already point at the API — if you changed it, redeploy the web app too.

---

## 5. Razorpay webhook (optional — for real Test Mode proof)

Only needed if you set the `rzp_test_` keys and want live Test Mode payment confirmations.

1. Razorpay Dashboard → **Settings → Webhooks → Add New Webhook**.
2. URL: `<api-url>/v1/webhooks/razorpay`.
3. Secret: set it to match `RAZORPAY_WEBHOOK_SECRET` in the API env.
4. Subscribe to the `payment_link.paid` event.
5. Save. Test Mode payments will now post back to the API.

---

## Security notes

- Never commit `.env`. Keys go only in the platform dashboard env settings.
- `APP_ENV` must stay `demo`. The startup guard exits if it is anything else.
- Only `rzp_test_` keys are accepted — the startup guard rejects live keys.
- All GMV and recovery figures are simulated/synthetic.

---

## Verify

```bash
# API health
curl https://<api-url>/health

# Web pages
open https://<vercel-url>/world
open https://<vercel-url>/recover
```

If `/health` returns OK and the console pages load their cases, the deploy is wired correctly.
