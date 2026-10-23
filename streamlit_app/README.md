# Caption Studio - Streamlit frontend

This Python interface uses the existing FastAPI service for BLIP captions, Groq captions, captioned PNG rendering, and shared SQLite history. AI logic remains in the backend.

## Setup

From the repository root, create a virtual environment and install only the Streamlit frontend requirements:

```powershell
python -m venv streamlit_app/.venv
.\streamlit_app\.venv\Scripts\Activate.ps1
python -m pip install -r streamlit_app/requirements.txt
```

Set `BACKEND_API_URL` only if the backend is not at its default URL:

```powershell
$env:BACKEND_API_URL = "http://127.0.0.1:8000"
```

## Run

Start FastAPI in one terminal from the repository root:

```powershell
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

Start Streamlit in a second terminal, also from the repository root:

```powershell
streamlit run streamlit_app/app.py
```

Open the local URL printed by Streamlit (usually `http://localhost:8501`). The interface calls the combined caption endpoint once per button click, then requests a captioned PNG. If rendering fails, the generated captions remain visible. The History section uses the backend's shared history and requires no separate database setup in Streamlit.
