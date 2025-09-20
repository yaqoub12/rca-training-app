"""Flask application factory for the RCA Risk Assessment app."""
from __future__ import annotations

from pathlib import Path

from flask import Flask

from .config import Config
from .extensions import csrf, db, migrate


def create_app(config_class: type[Config] | None = None) -> Flask:
    """Application factory pattern."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class or Config)

    _ensure_instance_folder(app)
    _load_instance_config(app)
    _register_extensions(app)
    _register_blueprints(app)
    _register_cli(app)

    return app


def _ensure_instance_folder(app: Flask) -> None:
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)


def _load_instance_config(app: Flask) -> None:
    instance_config = Path(app.instance_path) / "config.py"
    if instance_config.exists():
        app.config.from_pyfile("config.py")


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)


def _register_blueprints(app: Flask) -> None:
    from .risk.routes import risk_bp

    app.register_blueprint(risk_bp)


def _register_cli(app: Flask) -> None:
    from .risk.cli import import_sample_data

    app.cli.add_command(import_sample_data)
