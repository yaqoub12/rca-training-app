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
    """Populate the database with baseline hazards, controls, and sample work orders."""
    categories = load_risk_categories()

    _seed_hazards()
    _seed_controls()
    _seed_power_plant_work_orders(categories)
    
    db.session.commit()


def _seed_power_plant_work_orders(categories: Sequence[RiskMatrixCategory]) -> None:
    """Create power plant work orders with realistic tasks."""
    
    work_orders = [
        ("WO-2001", "Steam Turbine Maintenance", "Annual turbine maintenance"),
        ("WO-2002", "Generator Electrical Work", "Generator maintenance and testing"),
        ("WO-2003", "Boiler Tube Inspection", "Boiler pressure vessel inspection"),
        ("WO-2004", "Cooling Tower Service", "Cooling tower cleaning and repair"),
        ("WO-2005", "Transformer Maintenance", "Electrical transformer service"),
        ("WO-2006", "Coal Handling System", "Conveyor and coal system work"),
        ("WO-2007", "Ash Handling Work", "Ash system maintenance"),
        ("WO-2008", "Water Treatment", "Water treatment system service"),
        ("WO-2009", "Switchyard Work", "High voltage electrical work"),
        ("WO-2010", "Turbine Generator Alignment", "Precision alignment work"),
        ("WO-2011", "Condenser Cleaning", "Heat exchanger maintenance"),
        ("WO-2012", "Control System Upgrade", "DCS system modifications"),
        ("WO-2013", "Fuel Oil System", "Fuel handling system work"),
        ("WO-2014", "Emergency Diesel Test", "Backup generator testing"),
        ("WO-2015", "Stack Inspection", "Chimney and emissions work")
    ]
    
    for wo_num, title, desc in work_orders:
        if not WorkOrder.query.filter_by(number=wo_num).first():
            work_order = WorkOrder(number=wo_num, title=title, description=desc)
            db.session.add(work_order)
            db.session.flush()
            _create_tasks_for_work_order(work_order, categories)


def _create_tasks_for_work_order(work_order: WorkOrder, categories: Sequence[RiskMatrixCategory]) -> None:
    """Create realistic tasks based on work order type."""
    
    task_templates = {
        "WO-2001": [  # Steam Turbine
            ("Turbine shutdown and isolation", "High pressure steam release", "Operations team"),
            ("Remove turbine casing", "Heavy lifting operations", "Maintenance crew"),
            ("Blade inspection", "Sharp edges and confined space", "Technicians"),
            ("Rotor balancing", "Rotating machinery", "Specialists"),
            ("Reassembly and testing", "High pressure testing", "All teams")
        ],
        "WO-2002": [  # Generator
            ("Generator electrical isolation", "High voltage electrical shock", "Electrical team"),
            ("Winding resistance testing", "Electrical testing equipment", "Electricians"),
            ("Insulation testing", "High voltage testing", "Test technicians"),
            ("Brush replacement", "Carbon dust exposure", "Maintenance crew"),
            ("Vibration analysis", "Noise exposure", "Analysts")
        ],
        "WO-2003": [  # Boiler
            ("Boiler shutdown and cooldown", "Extreme heat exposure", "Operations"),
            ("Internal inspection access", "Confined space entry", "Inspectors"),
            ("Ultrasonic testing", "Chemical exposure", "NDT technicians"),
            ("Tube cleaning", "Chemical cleaning agents", "Cleaning crew"),
            ("Pressure testing", "High pressure water", "Test team")
        ],
        "WO-2004": [  # Cooling Tower
            ("Working at height on tower", "Fall from height", "Maintenance crew"),
            ("Fill material replacement", "Manual handling", "Workers"),
            ("Legionella sampling", "Biological hazard", "Environmental team"),
            ("Fan motor maintenance", "Rotating machinery", "Electricians"),
            ("Chemical treatment", "Chemical exposure", "Chemical technicians")
        ],
        "WO-2005": [  # Transformer
            ("Transformer de-energization", "High voltage electrical", "Electrical team"),
            ("Oil sampling", "Chemical exposure", "Lab technicians"),
            ("Bushing inspection", "Working at height", "Inspectors"),
            ("Cooling system maintenance", "Hot surfaces", "Maintenance"),
            ("Oil filtration", "Hot oil handling", "Specialists")
        ]
    }
    
    # Default tasks for work orders not in template
    default_tasks = [
        ("Equipment isolation", "Electrical hazards", "Operations team"),
        ("Component inspection", "Physical hazards", "Maintenance crew"),
        ("Repair/replacement work", "Manual handling", "Technicians"),
        ("Testing and commissioning", "Equipment hazards", "Test team"),
        ("Documentation and cleanup", "General hazards", "All personnel")
    ]
    
    tasks = task_templates.get(work_order.number, default_tasks)
    
    for idx, (activity, hazard_desc, personnel) in enumerate(tasks, 1):
        task = Task(
            work_order=work_order,
            sequence=idx,
            activity=activity,
            hazard_description=hazard_desc,
            personnel_at_risk=personnel,
            existing_controls_summary="Standard safety procedures",
            likelihood=3,  # Default moderate likelihood
            severity=3     # Default moderate severity
        )
        db.session.add(task)
        task.update_risk(categories)
        task.residual_likelihood = 2
        task.residual_severity = 2
        task.update_risk(categories, residual=True)


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


