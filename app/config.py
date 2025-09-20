"""Configuration objects for RCA Flask app."""
from __future__ import annotations

from pathlib import Path


class Config:
    SECRET_KEY = "change-me"
    SQLALCHEMY_DATABASE_URI = "sqlite:///rca.sqlite"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    RISK_MATRIX_DEFAULT = Path(__file__).resolve().parent / "risk" / "risk_matrix.yml"


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
