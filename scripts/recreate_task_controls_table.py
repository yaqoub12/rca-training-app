#!/usr/bin/env python3
"""
Recreate task_controls table with proper timestamp defaults
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def recreate_task_controls_table():
    """Recreate task_controls table with proper schema"""
    app = create_app()
    
    with app.app_context():
        try:
            with db.engine.connect() as conn:
                # Backup existing data
                print("Backing up existing task_controls data...")
                result = conn.execute(db.text("SELECT * FROM task_controls"))
                existing_data = result.fetchall()
                print(f"Found {len(existing_data)} existing records")
                
                # Drop and recreate table with proper schema
                print("Recreating task_controls table...")
                conn.execute(db.text("DROP TABLE IF EXISTS task_controls"))
                
                # Create table with proper timestamp defaults
                conn.execute(db.text("""
                    CREATE TABLE task_controls (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id INTEGER NOT NULL,
                        task_hazard_id INTEGER NOT NULL,
                        control_id INTEGER NOT NULL,
                        phase TEXT NOT NULL,
                        notes TEXT,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
                        FOREIGN KEY (task_hazard_id) REFERENCES task_hazards(id) ON DELETE CASCADE,
                        FOREIGN KEY (control_id) REFERENCES control_measures(id) ON DELETE CASCADE,
                        UNIQUE (task_hazard_id, control_id, phase)
                    )
                """))
                
                # Restore data with proper timestamps
                if existing_data:
                    print("Restoring existing data...")
                    for row in existing_data:
                        # Convert row to list for easier handling
                        row_data = list(row)
                        # Ensure we have all 8 columns, pad with None if needed
                        while len(row_data) < 8:
                            row_data.append(None)
                        
                        conn.execute(db.text("""
                            INSERT INTO task_controls (task_id, task_hazard_id, control_id, phase, notes)
                            VALUES (?, ?, ?, ?, ?)
                        """), (row_data[1], row_data[2], row_data[3], row_data[4], row_data[5]))
                
                conn.commit()
                print("Task controls table recreated successfully!")
                return True
                
        except Exception as e:
            print(f"Error recreating task_controls table: {e}")
            return False

if __name__ == "__main__":
    success = recreate_task_controls_table()
    exit(0 if success else 1)
