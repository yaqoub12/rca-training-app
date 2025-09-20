#!/usr/bin/env python3
"""
Fix timestamp constraints for task_controls table
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def fix_timestamp_constraints():
    """Fix timestamp constraints for task_controls table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if the table exists and has the right structure
            with db.engine.connect() as conn:
                # First, let's see the current table structure
                result = conn.execute(db.text("PRAGMA table_info(task_controls)"))
                columns = result.fetchall()
                print("Current task_controls table structure:")
                for col in columns:
                    print(f"  {col}")
                
                # Check if created_at and updated_at have proper defaults
                has_created_at = any(col[1] == 'created_at' for col in columns)
                has_updated_at = any(col[1] == 'updated_at' for col in columns)
                
                if not has_created_at:
                    print("Adding created_at column...")
                    conn.execute(db.text("ALTER TABLE task_controls ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"))
                    conn.commit()
                
                if not has_updated_at:
                    print("Adding updated_at column...")
                    conn.execute(db.text("ALTER TABLE task_controls ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL"))
                    conn.commit()
                
                # Update existing records to have timestamps if they don't
                print("Updating existing records with timestamps...")
                conn.execute(db.text("""
                    UPDATE task_controls 
                    SET created_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                    WHERE created_at IS NULL OR updated_at IS NULL
                """))
                conn.commit()
                
                print("Timestamp constraints fixed successfully!")
                return True
                
        except Exception as e:
            print(f"Error fixing timestamp constraints: {e}")
            return False

if __name__ == "__main__":
    success = fix_timestamp_constraints()
    exit(0 if success else 1)
