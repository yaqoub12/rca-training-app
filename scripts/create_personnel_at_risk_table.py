#!/usr/bin/env python3
"""
Create personnel_at_risk table and seed with default data
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db
from app.models import PersonnelAtRisk

def create_personnel_at_risk_table():
    """Create personnel_at_risk table and seed with default data"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the table
            db.create_all()
            
            # Seed with default personnel categories
            default_personnel = [
                {
                    "name": "Maintenance crew",
                    "description": "Maintenance technicians and engineers performing equipment maintenance"
                },
                {
                    "name": "Operations staff",
                    "description": "Control room operators and field operators"
                },
                {
                    "name": "Other staff",
                    "description": "Support staff, supervisors, and other personnel in the area"
                },
                {
                    "name": "Contractor",
                    "description": "External contractors and their personnel"
                },
                {
                    "name": "Visitors",
                    "description": "Visitors, auditors, and temporary personnel"
                },
                {
                    "name": "Emergency responders",
                    "description": "Fire brigade, medical personnel, and emergency response team"
                }
            ]
            
            for person_data in default_personnel:
                # Check if already exists
                existing = PersonnelAtRisk.query.filter_by(name=person_data["name"]).first()
                if not existing:
                    person = PersonnelAtRisk(
                        name=person_data["name"],
                        description=person_data["description"]
                    )
                    db.session.add(person)
            
            db.session.commit()
            print(f"Personnel at Risk table created and seeded with {len(default_personnel)} entries")
            return True
            
        except Exception as e:
            print(f"Error creating personnel_at_risk table: {e}")
            return False

if __name__ == "__main__":
    success = create_personnel_at_risk_table()
    exit(0 if success else 1)
