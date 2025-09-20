#!/usr/bin/env python3
"""
Add reference field to ControlMeasure model
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def add_control_reference_field():
    """Add reference field to control_measures table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Add the reference column to control_measures table
            with db.engine.connect() as conn:
                conn.execute(db.text('ALTER TABLE control_measures ADD COLUMN reference TEXT'))
                conn.commit()
            print("Added 'reference' column to control_measures table")
            return True
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("Reference column already exists")
                return True
            else:
                print(f"Error adding reference column: {e}")
                return False

if __name__ == "__main__":
    success = add_control_reference_field()
    exit(0 if success else 1)
