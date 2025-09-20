#!/usr/bin/env python3
"""
Deployment initialization script
Runs all necessary setup for production deployment
"""

import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent
sys.path.insert(0, str(app_dir))

from app import create_app
from app.extensions import db

def deploy_init():
    """Initialize application for deployment"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🚀 Initializing deployment...")
            
            # Create all tables
            print("📊 Creating database tables...")
            db.create_all()
            
            # Initialize risk categories and sample data
            print("🎯 Seeding risk categories...")
            from app.risk import services
            services.bootstrap_seed_data()
            
            # Seed comprehensive catalogs
            print("📚 Seeding hazards and controls catalogs...")
            exec(open(app_dir / 'scripts' / 'seed_comprehensive_catalogs.py').read())
            
            # Create personnel at risk data
            print("👥 Creating personnel at risk data...")
            exec(open(app_dir / 'scripts' / 'create_personnel_at_risk_table.py').read())
            
            print("✅ Deployment initialization complete!")
            print("🌐 Application ready for training sessions!")
            
            return True
            
        except Exception as e:
            print(f"❌ Deployment initialization failed: {e}")
            return False

if __name__ == "__main__":
    success = deploy_init()
    exit(0 if success else 1)
