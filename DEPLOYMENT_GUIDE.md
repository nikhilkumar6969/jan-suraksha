# 🚀 JAN SURAKSHA — Production Deployment & PWA Installation Guide

This guide provides step-by-step instructions to run, test, deploy, and install **Jan Suraksha** as a high-performance, offline-first Progressive Web Application (PWA).

---

## 1. Local Environment Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12 (Python 3.11 recommended)
- Git installed on your system
- Modern Web Browser (Google Chrome, Microsoft Edge, or Mozilla Firefox)

### Step 1: Clone or Open Repository
```bash
cd c:\project\hackasol
```

### Step 2: Create & Activate Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Local Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
Generate a cryptographically secure token for report signing:
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```
Set the generated key in `.env`:
```text
PORT=8000
HOST=127.0.0.1
SURAKSHA_REPORT_SECRET=<your_generated_secret>
SURAKSHA_DB_PATH=backend/data/suraksha.db
```

### Step 5: Start Local Development / Offline Server
```powershell
cd backend
..\.venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser at:
```text
http://127.0.0.1:8000/
```

---

## 2. Testing Offline Functionality Locally
1. Open `http://127.0.0.1:8000/` in Chrome or Edge.
2. Press **F12** to open Developer Tools &rarr; Go to the **Network** tab.
3. Change the dropdown from **No throttling** to **Offline** (or disconnect your Wi-Fi).
4. Refresh the page:
   - Notice the site still loads instantly from the Service Worker cache!
   - The status badge changes to **"ऑफलाइन (Offline)"**.
   - Paste a suspicious SMS &rarr; On-device offline rule engine scans and flags threats instantly.
   - Submit an anonymous report &rarr; It is saved to `localStorage` and automatically syncs when you switch Network back to **Online**.

---

## 3. Public Cloud Deployment on Render

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "feat(pwa): production PWA manifest, service worker, health check, and render config"
git push origin main
```

### Step 2: Create Web Service on Render
1. Log in to [Render.com](https://dashboard.render.com).
2. Click **New +** &rarr; Select **Web Service**.
3. Choose **Build and deploy from a Git repository** &rarr; Select your `jan-suraksha` repository.
4. Fill in the deployment settings:

| Field | Configuration Value |
|---|---|
| **Name** | `jan-suraksha` |
| **Language** | `Python 3` |
| **Branch** | `main` |
| **Region** | `Oregon (US West)` (or closest region) |
| **Root Directory** | *(Leave completely empty/blank)* |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |

### Step 3: Configure Environment Variables in Render
In the **Environment** tab on Render, add:
- `PYTHON_VERSION`: `3.11.8`
- `ENVIRONMENT`: `production`
- `SURAKSHA_REPORT_SECRET`: `T7_jfdRRiyGwjKKQPQZOrJQ4DkIP6mqVckaxUmNzjiLnwxloXCDL2sd7yNHNzAjp`
- `SURAKSHA_DB_PATH`: `backend/data/suraksha.db`

### Step 4: Persistent Disk (Optional for Heavy Community Reporting)
If you require SQLite report records to persist across zero-downtime redeploys on Render:
1. Go to **Disks** in your Render dashboard.
2. Add a disk with Mount Path `/var/data` and Size 1 GB.
3. Update environment variable `SURAKSHA_DB_PATH` to `/var/data/suraksha.db`.

### Step 5: Verify Live Deployment
Render will build and deploy the application. Once the deployment logs show:
```text
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:10000
==> Your service is live 🎉
```
Click on your public HTTPS URL (e.g., `https://jan-suraksha.onrender.com`).

---

## 4. Installing Jan Suraksha on Android & Desktop

### On Android (Chrome / Edge / Samsung Internet):
1. Open your live HTTPS link (`https://<your-service>.onrender.com`) on your Android phone.
2. You will see the floating banner: **"जन सुरक्षा ऐप इंस्टॉल करें (📲 इंस्टॉल करें)"**.
3. Tap **"📲 इंस्टॉल करें"** or tap the **"ऐप इंस्टॉल"** button in the top navigation bar.
4. Alternatively, tap the **three dots (⋮)** in Chrome and select **"Add to Home screen"** / **"Install app"**.
5. The Jan Suraksha icon will appear on your phone home screen and app drawer. It launches in full-screen standalone mode without any browser address bar!

### On Desktop (Windows / Mac / Linux Chrome or Edge):
1. Open the URL in Chrome or Edge.
2. Click the **Install icon** in the right side of the URL address bar, or click the **"ऐप इंस्टॉल"** button in the top bar.
3. The app opens in its own clean native window with full keyboard shortcuts and local caching.

---

## 5. Troubleshooting & Maintenance

### Port Binding Error on Render
If you see `Error: Address already in use` or connection timeouts, ensure your start command uses:
```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```
Never hardcode `8000` in cloud production startup scripts.

### Clearing Stale Service Worker Cache
If you update assets or JavaScript and need clients to immediately get updates:
1. Change the `CACHE_NAME` in `frontend/sw.js` (e.g. from `suraksha-pwa-v3.0` to `suraksha-pwa-v3.1`).
2. The service worker's `activate` event will automatically purge all old cache versions and claim clients.
