FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create instance directory for SQLite database
RUN mkdir -p instance

# Initialize database
RUN python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
RUN python scripts/init_db.py
RUN python scripts/seed_comprehensive_catalogs.py
RUN python scripts/create_personnel_at_risk_table.py

# Expose port
EXPOSE 5000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
