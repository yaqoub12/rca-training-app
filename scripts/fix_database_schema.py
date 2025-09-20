#!/usr/bin/env python3
"""
Fix database schema issues and ensure all tables are properly created
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def fix_database_schema():
    """Fix database schema issues"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Checking database schema...")
            
            # Drop all tables and recreate them
            print("Dropping all tables...")
            db.drop_all()
            
            print("Creating all tables with proper schema...")
            db.create_all()
            
            # Verify tables were created
            with db.engine.connect() as conn:
                # Check risk_matrix_categories table
                result = conn.execute(db.text("PRAGMA table_info(risk_matrix_categories)"))
                columns = result.fetchall()
                print("risk_matrix_categories table structure:")
                for col in columns:
                    print(f"  {col}")
                
                # Check personnel_at_risk table
                result = conn.execute(db.text("PRAGMA table_info(personnel_at_risk)"))
                columns = result.fetchall()
                print("personnel_at_risk table structure:")
                for col in columns:
                    print(f"  {col}")
            
            print("Database schema fixed successfully!")
            print("Note: You will need to re-seed your data (hazards, controls, risk categories, personnel)")
            return True
            
        except Exception as e:
            print(f"Error fixing database schema: {e}")
            return False

if __name__ == "__main__":
    success = fix_database_schema()
    exit(0 if success else 1)
