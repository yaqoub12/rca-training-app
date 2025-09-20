# 🛡️ RCA Risk Assessment App

A comprehensive Flask-based risk assessment application designed for power plant activities and HSE training sessions. This application enables users to conduct thorough risk assessments using a structured approach with hazard identification, control selection, and risk evaluation on a 5×5 matrix.

## 🎯 Perfect for Training Sessions

This app is specifically designed for Risk Assessment (RA) training sessions, providing:
- **Interactive Learning**: Hands-on experience with real risk assessment workflows
- **Comprehensive Catalogs**: 21+ hazards and 50+ controls based on power plant operations
- **Professional Interface**: Industry-standard risk matrix and control hierarchy
- **Multi-User Support**: Perfect for group training sessions

## Architecture Overview

- **Flask application** (`app/`)
  - `app/__init__.py`: application factory, configuration loading, extension registration.
  - `app/config.py`: environment-specific settings (SQLite default).
  - `app/extensions.py`: shared Flask extensions (SQLAlchemy, Marshmallow, CSRF).
  - `app/models.py`: ORM models for work orders, tasks, hazards, controls, risk categories, and associations.
  - `app/risk/`: blueprint exposing HTML endpoints and JSON APIs for task CRUD, CSV imports, and catalog management.
  - `app/templates/`: Jinja templates (Bootstrap 5 + modular partials).
  - `app/static/js/`: modular ES6 scripts orchestrating table rendering, modal pickers, and AJAX synchronization.
  - `app/static/css/`: custom styling, including risk color palette aligned with ALARP guidance.

- **Database**: SQLite stored in `instance/rca.sqlite`. SQLAlchemy models capture:
  - `WorkOrder`, `MethodStatement`, `Task` with risk evaluation fields (severity, likelihood, calculated risk level, residual values, due date).
  - Catalog tables `Hazard`, `ControlMeasure` with category metadata and configurable attributes (e.g., load weight, voltage tier).
  - Association tables `TaskHazard`, `TaskControl` (with `phase` = `existing` or `additional`).
  - `RiskMatrixCategory` defining score bands, colors, and guidance text for 5×5 evaluation.

- **Data ingestion**
  - CSV importer reads MS files placed under `data/method_statements/` (or uploaded via UI) and populates `MethodStatement` + `Task` records.
  - Sample CSVs and seed catalogs provided through `scripts/seed_data.py`.

- **Front end workflow**
  - Landing page prompts for WO number -> fetches tasks with hazards/controls via JSON.
  - Bootstrap table mirrors the provided template; users click cells to open modals for multi-select hazards/controls, edit fields inline, add/remove tasks, and record additional controls with due dates.
  - Client computes risk scores instantly while server persists authoritative values.

- **APIs** (JSON)
  - `GET /api/work-orders/<wo_number>`: retrieve WO details and tasks.
  - `POST /api/work-orders/<wo_number>/import`: import tasks from CSV/MS library.
  - `POST /api/tasks`, `PUT /api/tasks/<id>`, `DELETE /api/tasks/<id>`: manage tasks.
  - `PUT /api/tasks/<id>/hazards` and `/controls`: update associations.
  - `GET/POST /api/catalog/hazards`, `/controls`, `/risk-categories`: maintain catalogs.

- **Testing** (`tests/`)
  - Pytest suite covers importer normalization, risk scoring, and API contract tests using Flask's test client.

## 🚀 Deployment for Training Sessions

### Quick Deploy Options

#### Option 1: Railway (Recommended - Free Tier)
1. Fork this repository to your GitHub account
2. Visit [Railway.app](https://railway.app) and sign up with GitHub
3. Click "Deploy from GitHub repo" and select your fork
4. Railway will automatically detect the `railway.toml` and deploy
5. Your app will be live at `https://your-app-name.railway.app`

#### Option 2: Render (Free Tier)
1. Fork this repository to your GitHub account
2. Visit [Render.com](https://render.com) and sign up with GitHub
3. Click "New Web Service" and connect your GitHub repo
4. Render will use the `render.yaml` configuration automatically
5. Your app will be live at `https://your-app-name.onrender.com`

#### Option 3: Heroku (Free Tier Discontinued)
1. Install Heroku CLI
2. `heroku create your-app-name`
3. `git push heroku main`
4. `heroku run python scripts/init_db.py`

### Training Session Setup

#### For Multiple Training Sessions:
1. **Create separate deployments** for each training group:
   - `rca-training-group-1.railway.app`
   - `rca-training-group-2.railway.app`
   - etc.

2. **Pre-populate with sample data**:
   - Each deployment automatically includes comprehensive hazards/controls catalogs
   - Sample work order data for immediate use
   - Ready-to-use risk assessment scenarios

3. **Share URLs with trainees**:
   - Each group gets their own isolated environment
   - No data conflicts between training sessions
   - Fresh database for each session

## 💻 Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd RCA-App4
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python scripts/init_db.py
   python scripts/seed_comprehensive_catalogs.py
   python scripts/create_personnel_at_risk_table.py
   ```

5. **Run the application**:
   ```bash
   python wsgi.py
   ```
   
6. **Access the app**: Open `http://localhost:5000`

## Roadmap

- Implement authentication/role management for catalog administration.
- Add PDF export for completed risk assessments.
- Integrate notification reminders for outstanding control actions.

