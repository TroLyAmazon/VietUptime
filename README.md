
# 📈 DotStatus

!Python
!License

You can use this repo https://github.com/TroLyAmazon/PteroMon with DotStatus

A lightweight, single-process status dashboard built with **Flask**. It monitors multiple services via a simple JSON endpoint (default: `/api/stats`) and includes both a **public dashboard** and a secure **owner admin panel**.

---

## ✨ Features

### 🌐 Public Dashboard (`/`)
*   **Multi-service Overview**: At-a-glance status for all services.
*   **Uptime Bars**: Visual history of the last 90 days.
*   **Overall Uptime Stats**: 24h, 7d, 30d, and 90d calculations (gray if no data).
*   **Response Time Chart**: Interactive Chart.js graph for the last 48 hours.
*   **Event Log**: Recent down/up events.

### 🛡️ Owner Admin (`/owner`)
*   **Secure Login**: Password-protected admin area.
*   **Target Management**: CRUD operations (Add, Remove, Enable, Disable targets).
*   **Public Click Toggle**: Control if users can click hostnames to open them.
*   **Database Tools**: Safe DB viewer and export functionality (no raw SQL).
*   **Update Checker**: Checks for the latest GitHub Release.

---

## 📦 Requirements

*   **Python**: 3.10+ (Recommended: 3.11/3.12)
*   **OS**: Windows / Linux / macOS

---

## 🚀 Quick Start

You can choose between the **Automated Setup** (recommended) or **Manual Setup**.

### Option 1: Automated Setup (Recommended)

We provide a `Setup.py` script that handles virtual environment creation, dependency installation, and configuration generation.

1.  **Run Setup**:
    ```bash
    python Setup.py
    ```
    *   Follow the interactive prompts to set your `SECRET_KEY`, `OWNER_PASSWORD`, etc.
    *   The script will generate a `.venv` folder and startup scripts (`run.cmd`, `run.ps1`).

2.  **Start Server**:
    *   **Windows (CMD)**: Double-click `run.cmd` or run `run.cmd`.
    *   **Windows (PowerShell)**: Run `.\run.ps1`.
    *   **Linux/macOS**:
        ```bash
        ./.venv/bin/python run.py
        ```

---

### Option 2: Manual Setup

#### 1. Setup Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Generate Password Hash

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
