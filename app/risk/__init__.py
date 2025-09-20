"""Risk management blueprint package."""
from flask import Blueprint

risk_bp = Blueprint("risk", __name__, template_folder="../templates")

from . import routes  # noqa: E402,pylint:disable=wrong-import-position
