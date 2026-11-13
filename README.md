# AegisLPS (Lightnin)

Lightning Protection Engineering Workbench (IEC 62305:2024 / IEEE Std 80-2013 / IEC 62561).

## Quick Start (Python Backend & Diagnostics)

### Option A — One-command bootstrap & launch
Creates `.venv`, installs `requirements.txt`, runs pre-flight diagnostics, and starts the local FastAPI server on `http://127.0.0.1:8000`:

```bash
python run_aegislps.py --bootstrap
```

### Option B — Manual virtual environment setup

**Windows (PowerShell / CMD):**
```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python run_aegislps.py
```

**Linux / macOS:**
```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run_aegislps.py
```

> Once `.venv` exists in the repository root, running `python run_aegislps.py` will automatically detect and use the `.venv` interpreter even if the virtual environment is not activated in your shell.

### Diagnostics only (without starting the API server)
```bash
python run_aegislps.py --no-server
```

## Web Frontend (separate terminal)
```bash
npm install
npm run dev --workspace=apps/web
```
