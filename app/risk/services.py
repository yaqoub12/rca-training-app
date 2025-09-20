"""Service layer for risk assessment operations."""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

import yaml
from flask import current_app
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import (
    ControlMeasure,
    ControlPhase,
    Hazard,
    MethodStatement,
    RiskMatrixCategory,
    Task,
    TaskControl,
    TaskHazard,
    WorkOrder,
)


def load_risk_categories(cache: bool = True) -> list[RiskMatrixCategory]:
    """Retrieve risk categories from the database, seeding defaults if required."""
    categories = RiskMatrixCategory.query.order_by(RiskMatrixCategory.min_score).all()
    if categories:
        return categories

    config_path = Path(current_app.config["RISK_MATRIX_DEFAULT"])
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for entry in data.get("risk_categories", []):
        category = RiskMatrixCategory(
            name=entry["label"],
            color=entry["color"],
            guidance=entry["guidance"],
            min_score=entry["min_score"],
            max_score=entry["max_score"],
        )
        db.session.add(category)
    db.session.commit()
    return RiskMatrixCategory.query.order_by(RiskMatrixCategory.min_score).all()


def bootstrap_seed_data() -> None:
    """Populate the database with baseline hazards, controls, and a sample work order."""
    categories = load_risk_categories()

    _seed_hazards()
    _seed_controls()

    if not WorkOrder.query.filter_by(number="WO-1001").first():
        work_order = WorkOrder(number="WO-1001", title="Pump Overhaul", description="Sample overhaul sequence")
        db.session.add(work_order)
        db.session.flush()

        csv_path = Path(current_app.root_path).parent / "data" / "method_statements" / "wo1001_pump_overhaul.csv"
        if csv_path.exists():
            import_method_statement(work_order, csv_path, categories)
    db.session.commit()


def import_method_statement(
    work_order: WorkOrder,
    csv_path: Path,
    categories: Sequence[RiskMatrixCategory] | None = None,
) -> MethodStatement:
    """Import a method statement CSV into the database and attach to the work order."""
    categories = list(categories or load_risk_categories())

    method_statement = MethodStatement(
        work_order=work_order,
        title=csv_path.stem.replace("_", " ").title(),
        source_filename=csv_path.name,
    )
    db.session.add(method_statement)
    db.session.flush()

    with csv_path.open("r", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for idx, row in enumerate(reader, start=1):
            task = Task(
                work_order=work_order,
                method_statement=method_statement,
                sequence=idx,
                activity=row.get("Work Activity", "").strip() or f"Task {idx}",
                hazard_description=row.get("Hazard Description", "").strip(),
                personnel_at_risk=row.get("Personnel At Risk", "").strip(),
                existing_controls_summary=row.get("Existing Controls", "").strip(),
            )
            db.session.add(task)

            default_likelihood, default_severity = _defaults_from_catalog(row.get("Hazard Description"))
            task.likelihood = default_likelihood
            task.severity = default_severity
            task.update_risk(categories)
            task.residual_likelihood = max(default_likelihood - 1, 1)
            task.residual_severity = max(default_severity - 1, 1)
            task.update_risk(categories, residual=True)
    return method_statement


def get_work_order_by_number(wo_number: str) -> WorkOrder | None:
    return WorkOrder.query.filter_by(number=wo_number).one_or_none()


def get_tasks_for_work_order(wo_number: str) -> list[Task]:
    stmt = (
        select(Task)
        .join(WorkOrder)
        .options(joinedload(Task.hazards).joinedload(TaskHazard.hazard))
        .options(joinedload(Task.controls).joinedload(TaskControl.control))
        .where(WorkOrder.number == wo_number)
        .order_by(Task.sequence)
    )
    return db.session.execute(stmt).unique().scalars().all()


def upsert_task(task: Task, data: dict, categories: Sequence[RiskMatrixCategory] | None = None) -> Task:
    categories = list(categories or load_risk_categories())
    for field in (
        "activity",
        "hazard_description",
        "personnel_at_risk",
        "existing_controls_summary",
        "additional_controls_summary",
        "notes",
    ):
        if field in data:
            setattr(task, field, data[field])

    if "likelihood" in data:
        task.likelihood = int(data["likelihood"])
    if "severity" in data:
        task.severity = int(data["severity"])
    if "residual_likelihood" in data:
        task.residual_likelihood = int(data["residual_likelihood"])
    if "residual_severity" in data:
        task.residual_severity = int(data["residual_severity"])

    if "target_completion_date" in data:
        raw = data["target_completion_date"]
        task.target_completion_date = date.fromisoformat(raw) if raw else None

    task.update_risk(categories)
    task.update_risk(categories, residual=True)
    db.session.add(task)
    return task


def replace_task_hazards(task: Task, hazards_payload: Iterable[dict]) -> Task:
    payload_list: list[dict] = []
    for item in hazards_payload:
        if isinstance(item, dict):
            payload_list.append(item)
        else:
            payload_list.append({"id": int(item)})

    incoming_ids = {int(entry["id"]) for entry in payload_list}
    existing = {link.hazard_id: link for link in task.hazards}

    hazards = {hazard.id: hazard for hazard in Hazard.query.filter(Hazard.id.in_(incoming_ids)).all()}

    for removed_id in set(existing) - incoming_ids:
        db.session.delete(existing[removed_id])

    for entry in payload_list:
        hazard_id = int(entry["id"])
        parameter_value = entry.get("parameter_value")
        hazard = hazards.get(hazard_id)
        if hazard and hazard.requires_parameter and not parameter_value:
            raise ValueError(f"Hazard '{hazard.name}' requires a parameter value.")
        if hazard_id in existing:
            existing_link = existing[hazard_id]
            existing_link.parameter_value = parameter_value
        else:
            db.session.add(TaskHazard(task=task, hazard_id=hazard_id, parameter_value=parameter_value))

    return task


def replace_hazard_controls(task_hazard: TaskHazard, control_ids: Iterable[int], phase: str, control_parameters: dict = None) -> TaskHazard:
    """Replace controls for a specific hazard within a task."""
    existing = {link.control_id: link for link in task_hazard.controls if link.phase == phase}
    incoming = set(int(c_id) for c_id in control_ids)
    control_parameters = control_parameters or {}

    for removed_id in set(existing) - incoming:
        db.session.delete(existing[removed_id])

    for control_id in incoming - set(existing):
        parameter_value = control_parameters.get(control_id)
        db.session.add(TaskControl(
            task=task_hazard.task,
            task_hazard=task_hazard,
            control_id=control_id,
            phase=phase,
            notes=parameter_value
        ))
    
    # Update existing controls with new parameter values
    for control_id in incoming & set(existing):
        parameter_value = control_parameters.get(control_id)
        existing[control_id].notes = parameter_value

    return task_hazard


def replace_task_controls(task: Task, control_ids: Iterable[int], phase: str) -> Task:
    """Legacy function - kept for backward compatibility. 
    Applies controls to all hazards in the task."""
    for task_hazard in task.hazards:
        replace_hazard_controls(task_hazard, control_ids, phase)
    return task


def _defaults_from_catalog(hazard_description: str | None) -> tuple[int, int]:
    if not hazard_description:
        return 3, 3
    hazard = Hazard.query.filter(Hazard.name.ilike(f"%{hazard_description}%")).first()
    if hazard:
        return hazard.default_likelihood or 3, hazard.default_severity or 3
    return 3, 3


def _seed_hazards() -> None:
    presets = [
        {"name": "Manual handling", "category": "Manual Handling", "description": "Manual lifting / carrying tasks", "default_severity": 4, "default_likelihood": 3, "requires_parameter": True, "parameter_label": "Load weight (kg)", "parameter_unit": "kg"},
        {"name": "Live electrical conductors", "category": "Electrical", "default_severity": 5, "default_likelihood": 2},
        {"name": "Stored energy release", "category": "Mechanical", "default_severity": 4, "default_likelihood": 2},
        {"name": "Chemical exposure - corrosive", "category": "Chemical", "default_severity": 4, "default_likelihood": 2},
        {"name": "Working at height >2m", "category": "Work At Height", "default_severity": 5, "default_likelihood": 2},
    ]
    for preset in presets:
        exists = Hazard.query.filter_by(name=preset["name"], category=preset["category"]).first()
        if not exists:
            db.session.add(Hazard(**preset))


def _seed_controls() -> None:
    presets = [
        {"name": "Lock-out tag-out", "category": "Electrical Isolation", "description": "Apply LOTOTO to all energy sources."},
        {"name": "Permit to Work", "category": "Procedural", "description": "Issue/brief permit covering task controls."},
        {"name": "PPE - Chemical resistant gloves", "category": "PPE", "description": "Use gloves rated for chemical exposure."},
        {"name": "Mechanical lifting aid", "category": "Handling Equipment", "description": "Use hoist or lifting beam to move heavy loads."},
        {"name": "Job safety briefing", "category": "Communication", "description": "Conduct toolbox talk before execution."},
        {"name": "Spotter assigned", "category": "Supervision", "description": "Dedicated person to monitor pinch point hazards."},
    ]
    for preset in presets:
        exists = ControlMeasure.query.filter_by(name=preset["name"], category=preset["category"]).first()
        if not exists:
            db.session.add(ControlMeasure(**preset))


