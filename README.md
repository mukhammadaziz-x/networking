# ClothCRM

ClothCRM is the internal back-office customer relationship management (CRM) and system dashboard for a wholesale clothing distribution company.

## Tech Stack
- **Backend:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, Jinja2 Templates
- **Frontend:** HTML/CSS/JS, Bootstrap 5
- **Database:** PostgreSQL 15
- **Containerization:** Docker & Docker Compose

---

## Getting Started

### Option 1: Running Locally (Development)

1. **Prerequisites:** Python 3.11 installed locally.
2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   ```
3. **Activate virtual environment:**
   - **Windows PowerShell:**
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - **Git Bash / macOS / Linux:**
     ```bash
     source .venv/bin/activate
     ```
4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Set up Environment Variables:**
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Modify `DATABASE_URL` in `.env` to point to your local PostgreSQL instance (e.g., `postgresql://postgres:postgres@localhost:5432/clothcrm`).
6. **Start the Application:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Option 2: Running with Docker Compose (Recommended)

Docker Compose automatically spins up the FastAPI application and a PostgreSQL database.

1. **Start Services:**
   ```bash
   docker-compose up --build
   ```
2. **Stop Services:**
   ```bash
   docker-compose down
   ```

---

## Verification and Testing

Once the application is running, you can access the following routes:

- **Dashboard (Home Page):** [http://localhost:8000/](http://localhost:8000/)
- **Health Check API:** [http://localhost:8000/health](http://localhost:8000/health) (Returns `{"status": "ok"}`)
