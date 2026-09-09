# Deploying Edusphere

The whole app ships as **one container** — FastAPI serves the API and the built
frontend from the same origin. One service to deploy, one URL, no CORS.

---

## What you need first

**A Gemini API key.** Free, no card, about a minute:
[aistudio.google.com/apikey](https://aistudio.google.com/apikey). Without it the
app still retrieves and cites sources correctly, but says it cannot write an
answer.

**Your code on GitHub.** Already done — `github.com/Yashvi2874/edusphere`.

---

## Optional — "Sign in with Google"

**The button is hidden unless a real Google OAuth client id is configured.**
Email and password sign-in always works; this is an extra.

It is hidden rather than shown-and-broken because the client id falls back to
the placeholder `YOUR_GOOGLE_CLIENT_ID`, which Google rejects — so the button
used to appear and then fail with nothing to explain why.

To enable it:

1. [console.cloud.google.com](https://console.cloud.google.com) → create a project
2. **APIs & Services → OAuth consent screen** → External → fill in the app name
   and your email
3. **Credentials → Create Credentials → OAuth client ID → Web application**
4. Under **Authorised JavaScript origins**, add every origin you will use:
   - `http://localhost:5001` (Docker)
   - `http://localhost:3000` (Vite dev)
   - your deployed URL, e.g. `https://edusphere-xxxx.onrender.com`
5. Copy the client id — it ends in `.apps.googleusercontent.com` — into
   `Edusphere_frontend/.env`:

```
VITE_GOOGLE_CLIENT_ID=1234567890-abcdefg.apps.googleusercontent.com
```

6. Rebuild. Vite bakes environment variables in at **build** time, so an
   existing container will not pick this up until it is rebuilt.

The origins must match exactly, including `http` vs `https` and the port.
A mismatch gives `redirect_uri_mismatch` or `origin_mismatch`.

## Run it locally first

```bash
docker compose up --build
```

Then open **http://localhost:5001**. Frontend and API are both there.

The first build takes 5–15 minutes: it downloads PyTorch and bakes the embedding
model into the image. Later builds reuse cached layers and take seconds unless
you change dependencies.

Stop with `Ctrl+C`, or `docker compose down`.

---

## Option A — Render (recommended)

Free tier, builds straight from a Dockerfile, no card required.

1. **Sign in** at [render.com](https://render.com) with GitHub.
2. **New → Web Service**, pick the `edusphere` repository.
3. Set:
   - **Language / Runtime:** `Docker`
   - **Dockerfile Path:** `./Dockerfile`
   - **Instance Type:** `Free`
4. **Environment → Add Environment Variable:**

   | Key | Value |
   |---|---|
   | `GEMINI_API_KEY` | your key |
   | `LITELLM_MODEL` | `gemini/gemini-2.5-flash` |

   Do **not** commit these. Render injects them at run time, which is what the
   Dockerfile expects.
5. **Create Web Service.** The first build takes 10–20 minutes.

You get `https://edusphere-xxxx.onrender.com`.

### Two things to know about the free tier

**It sleeps after 15 minutes idle**, and the next visitor waits 30–60 seconds
while it wakes. Warn anyone you send the link to, or open it yourself a minute
beforehand.

**The disk is ephemeral.** Accounts and conversations are wiped on every
redeploy, because they live in JSON files inside the container. Fine for a demo.
To keep them, add a Render Disk mounted at `/app/data`, or move to a database.

---

## Option B — Railway

Similar, usually faster builds, small monthly credit rather than a free tier.

1. [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. It detects the Dockerfile automatically.
3. **Variables:** add `GEMINI_API_KEY` and `LITELLM_MODEL`.
4. **Settings → Networking → Generate Domain.**

Railway sets `PORT` itself; the Dockerfile already reads it.

---

## Option C — Fly.io

Best if you want it to stay awake and close to India.

```bash
fly launch --no-deploy          # detects the Dockerfile
fly secrets set GEMINI_API_KEY=your_key_here
fly secrets set LITELLM_MODEL=gemini/gemini-2.5-flash
fly deploy
```

Pick the `bom` (Mumbai) region when asked. Fly needs a card on file even on the
free allowance.

---

## After it is live

**Open it and ask a real question**, not just the home page — that exercises
retrieval and generation together.

**Check the quota.** Gemini's free tier caps requests per minute and per day.
Once reached, the app says so and still shows its sources; it recovers on its
own.

**Put the URL in the README** so anyone landing on the repo can try it without
cloning:

```markdown
**[Live demo](https://your-url.onrender.com)**
```

Then add it to your resume and LinkedIn. A working link is worth considerably
more than a repository nobody runs.

---

## If something breaks

| Symptom | Cause |
|---|---|
| Build fails on `pip install torch` | Both index URLs are needed — `--index-url` replaces PyPI, so torch's own build dependencies vanish. Already handled in the Dockerfile; do not remove the `--extra-index-url`. |
| Build fails with `invalid file request` | A OneDrive placeholder that was never downloaded. Right-click the folder → **Always keep on this device**, or build from a copy outside OneDrive. |
| App loads, every answer is a fallback | `GEMINI_API_KEY` is not set, or the quota is exhausted. The message says which. |
| Blank page, API works | The frontend build did not land in `/app/static`. Check the `COPY --from=frontend` line. |
| First request very slow | Cold start. The embedding model loads once at boot; the healthcheck allows 90 seconds for it. |
| `ImportError: cannot import name 'NotRequired' from 'typing'` | Python 3.10. Current litellm needs 3.11+. The image is on 3.11; if you hit this **locally**, upgrade your Python or pin an older litellm. |

---

## A note on your local Python

The container runs **Python 3.11**. Your machine has **3.10.0**, which is fine
today because the installed litellm predates the change — but the moment you run
`pip install -U litellm` locally you will hit the `NotRequired` import error
above, and the app will refuse to start.

Upgrading local Python to 3.11 or later removes the mismatch and makes local
behaviour match the deployed container.
