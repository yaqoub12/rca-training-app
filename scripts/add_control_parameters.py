#!/usr/bin/env python3
"""
Add parameter fields to control_measures table to match hazards approach
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def add_control_parameter_fields():
    """Add parameter fields to control_measures table"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Check current table structure
                result = conn.execute(db.text("PRAGMA table_info(control_measures)"))
                columns = result.fetchall()
                existing_columns = [col[1] for col in columns]
                
                print("Current control_measures table structure:")
                for col in columns:
                    print(f"  {col}")
                
                # Add requires_parameter column if it doesn't exist
                if 'requires_parameter' not in existing_columns:
                    print("Adding requires_parameter column...")
                    conn.execute(db.text("ALTER TABLE control_measures ADD COLUMN requires_parameter BOOLEAN NOT NULL DEFAULT 0"))
                    conn.commit()
                
                # Add parameter_label column if it doesn't exist
                if 'parameter_label' not in existing_columns:
                    print("Adding parameter_label column...")
                    conn.execute(db.text("ALTER TABLE control_measures ADD COLUMN parameter_label VARCHAR(120)"))
                    conn.commit()
                
                # Add parameter_unit column if it doesn't exist
                if 'parameter_unit' not in existing_columns:
                    print("Adding parameter_unit column...")
                    conn.execute(db.text("ALTER TABLE control_measures ADD COLUMN parameter_unit VARCHAR(40)"))
                    conn.commit()
                
                # Migrate existing reference data to new parameter system
                print("Migrating existing reference data to parameter system...")
                result = conn.execute(db.text("SELECT id, reference FROM control_measures WHERE reference IS NOT NULL AND reference != ''"))
                controls_with_references = result.fetchall()
                
                for control_id, reference in controls_with_references:
                    # Set requires_parameter to True and use reference as parameter_label
                    conn.execute(db.text("""
                        UPDATE control_measures 
                        SET requires_parameter = 1, parameter_label = ? 
                        WHERE id = ?
                    """), (reference, control_id))
                
                conn.commit()
                print(f"Migrated {len(controls_with_references)} controls with references to parameter system")
                
                # Verify the changes
                result = conn.execute(db.text("PRAGMA table_info(control_measures)"))
                new_columns = result.fetchall()
                print("\nUpdated control_measures table structure:")
                for col in new_columns:
                    print(f"  {col}")
                
                print("Control parameter fields added successfully!")
                return True
                
        except Exception as e:
            print(f"Error adding control parameter fields: {e}")
            return False

if __name__ == "__main__":
    success = add_control_parameter_fields()
    exit(0 if success else 1)
