````md
# DotStatus (Flask-only)

A lightweight status dashboard built with **Flask-only** (single process) to monitor multiple services via a simple JSON endpoint (default: `/api/stats`).  
Includes **public dashboard** + **owner admin panel** (CRUD targets, DB viewer/export, update check).

---

## Features

### Public (`/`)
- Multi-service status overview
- **Uptime bars** (last 90 days)
- **Overall uptime**: 24h / 7d / 30d / 90d (computed from available samples; no data = gray)
- **Response time chart** (last 48h, Chart.js)
- Recent down/up events

### Owner Admin (`/owner`)
- Owner login
- CRUD targets (add/remove/enable/disable)
- Toggle **Public Click** (allow users to click hostname → open in new tab)
- DB viewer + export (safe, no SQL console)
- **Check Update** (shows latest GitHub Release link)

---

## Requirements
- Python 3.10+ (recommended 3.11/3.12)
- Works on Windows / Linux

---

## Quick Start

### 1) Create venv + install deps
```bash
python -m venv .venv
````

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

---

## Owner Password Setup

### 2) Generate password hash

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('YOUR_PASSWORD'))"
```

Example output (sample):

```
scrypt:32768:8:1$Mk7ekQlqb................8b62aa48de1cafcbeec0f3
```

> ✅ Copy the full string into `OWNER_PASSWORD_HASH`
> ❌ Do NOT paste the plain password into env.

---

## Environment Variables

### 3) Set env (Windows PowerShell)

```powershell
$env:SECRET_KEY="change-me"
$env:OWNER_USERNAME="owner"
$env:OWNER_PASSWORD_HASH='paste-hash-here'
$env:TIMEZONE="Asia/Bangkok"
```

### Optional: seed first target on first run

```powershell
$env:SEED_TARGET_NAME="my1"
$env:SEED_TARGET_BASE_URL="https://my1.dotuananh.me"
$env:SEED_TARGET_STATS_PATH="/api/stats"
```

### Optional: GitHub Update Checker

```powershell
$env:GITHUB_REPO="TroLyAmazon/VietUptime"
```

> If you run into GitHub API rate-limit, you can add:

```powershell
# $env:GITHUB_TOKEN="ghp_xxx"
```

---

## Run

### 4) Start server

```bash
python run.py
```

Open:

* Public dashboard: `http://127.0.0.1:5000/`
* Owner admin: `http://127.0.0.1:5000/owner/login`

---

## Notes / Scheduler

* Scheduler runs **every hour at minute 0** in `Asia/Bangkok` timezone inside the **same Flask process**.
* If deploying with **gunicorn**, keep **1 worker** to avoid double polling:

  ```bash
  gunicorn -w 1 -b 0.0.0.0:5000 run:app
  ```

---

## Debug: Test Password Hash

To verify your hash is correct:

```bash
python -c "import os; from werkzeug.security import check_password_hash; print(check_password_hash(os.getenv('OWNER_PASSWORD_HASH',''), 'YOUR_PASSWORD'))"
```

Expected output:

```
True
```

---

## Security Tips

* Use a strong `SECRET_KEY`
* Keep `/owner/*` behind authentication
* Only enable `Public Click` if you want users to open the service page from the public dashboard
* DB export is owner-only

---

## License

MIT (or your preferred license)

```
::contentReference[oaicite:0]{index=0}
```
