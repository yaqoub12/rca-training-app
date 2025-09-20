"""CLI commands for risk blueprint."""
from __future__ import annotations

import click
from flask.cli import with_appcontext


@click.command("import-sample-data")
@with_appcontext
def import_sample_data() -> None:
    """Seed the database with baseline hazards, controls, and example work order."""
    from . import services

    services.bootstrap_seed_data()
    click.secho("Sample risk data imported.", fg="green")
