"""HTTP routes for the risk assessment blueprint."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import (Blueprint, abort, current_app, jsonify, render_template,
                   request)

from ..extensions import csrf, db
from ..models import ControlMeasure, ControlPhase, Hazard, PersonnelAtRisk, Task, TaskHazard, WorkOrder
from . import risk_bp
from . import services


@risk_bp.route("/")
def index() -> str:
    categories = services.load_risk_categories()
    hazards = Hazard.query.order_by(Hazard.category, Hazard.name).limit(10).all()
    controls = ControlMeasure.query.order_by(ControlMeasure.category, ControlMeasure.name).limit(10).all()
    return render_template(
        "index.html",
        risk_categories=categories,
        hazards=hazards,
        controls=controls,
    )


@risk_bp.route("/hazards")
def hazards() -> str:
    """Hazards catalog management page"""
    return render_template("hazards.html")


@risk_bp.route("/controls")
def controls() -> str:
    """Controls catalog management page"""
    return render_template("controls.html")


@risk_bp.get("/api/risk-matrix")
def api_risk_matrix():
    categories = services.load_risk_categories()
    return jsonify({"risk_categories": [risk_category_to_dict(cat) for cat in categories]})


@risk_bp.get("/api/catalog/hazards")
def api_list_hazards():
    hazards = Hazard.query.order_by(Hazard.category, Hazard.name).all()
    return jsonify({"hazards": [hazard_to_dict(h) for h in hazards]})


@risk_bp.post("/api/catalog/hazards")
@csrf.exempt
def api_create_hazard():
    payload = request.get_json(force=True)
    requires_parameter = payload.get("requires_parameter", False)
    if isinstance(requires_parameter, str):
        requires_parameter = requires_parameter.lower() not in {"false", "0", "no"}
    hazard = Hazard(
        name=payload["name"],
        category=payload.get("category", "General"),
        description=payload.get("description", ""),
        default_likelihood=payload.get("default_likelihood", 3),
        default_severity=payload.get("default_severity", 3),
        requires_parameter=requires_parameter,
        parameter_label=payload.get("parameter_label"),
        parameter_unit=payload.get("parameter_unit"),
    )
    db.session.add(hazard)
    db.session.commit()
    return jsonify({"hazard": hazard_to_dict(hazard)}), 201


@risk_bp.put("/api/catalog/hazards/<int:hazard_id>")
@csrf.exempt
def api_update_hazard(hazard_id: int):
    hazard = Hazard.query.get_or_404(hazard_id)
    payload = request.get_json(force=True)
    
    hazard.name = payload.get("name", hazard.name)
    hazard.category = payload.get("category", hazard.category)
    hazard.description = payload.get("description", hazard.description)
    hazard.default_likelihood = payload.get("default_likelihood", hazard.default_likelihood)
    hazard.default_severity = payload.get("default_severity", hazard.default_severity)
    
    requires_parameter = payload.get("requires_parameter", hazard.requires_parameter)
    if isinstance(requires_parameter, str):
        requires_parameter = requires_parameter.lower() not in {"false", "0", "no"}
    hazard.requires_parameter = requires_parameter
    
    hazard.parameter_label = payload.get("parameter_label", hazard.parameter_label)
    hazard.parameter_unit = payload.get("parameter_unit", hazard.parameter_unit)
    
    db.session.commit()
    return jsonify({"hazard": hazard_to_dict(hazard)})


@risk_bp.delete("/api/catalog/hazards/<int:hazard_id>")
@csrf.exempt
def api_delete_hazard(hazard_id: int):
    hazard = Hazard.query.get_or_404(hazard_id)
    db.session.delete(hazard)
    db.session.commit()
    return ("", 204)


@risk_bp.get("/api/catalog/controls")
def api_list_controls():
    controls = ControlMeasure.query.order_by(ControlMeasure.category, ControlMeasure.name).all()
    return jsonify({"controls": [control_to_dict(c) for c in controls]})


@risk_bp.post("/api/catalog/controls")
@csrf.exempt
def api_create_control():
    payload = request.get_json(force=True)
    control = ControlMeasure(
        name=payload["name"],
        category=payload.get("category", "General"),
        description=payload.get("description", ""),
        effectiveness=payload.get("effectiveness", 2),
        requires_parameter=payload.get("requires_parameter", False),
        parameter_label=payload.get("parameter_label", ""),
        parameter_unit=payload.get("parameter_unit", ""),
        reference=payload.get("reference", ""),  # Keep for backward compatibility
    )
    db.session.add(control)
    db.session.commit()
    return jsonify({"control": control_to_dict(control)}), 201


@risk_bp.put("/api/catalog/controls/<int:control_id>")
@csrf.exempt
def api_update_control(control_id: int):
    control = ControlMeasure.query.get_or_404(control_id)
    payload = request.get_json(force=True)
    
    control.name = payload.get("name", control.name)
    control.category = payload.get("category", control.category)
    control.description = payload.get("description", control.description)
    control.effectiveness = payload.get("effectiveness", control.effectiveness)
    control.requires_parameter = payload.get("requires_parameter", control.requires_parameter)
    control.parameter_label = payload.get("parameter_label", control.parameter_label)
    control.parameter_unit = payload.get("parameter_unit", control.parameter_unit)
    control.reference = payload.get("reference", control.reference)  # Keep for backward compatibility
    
    db.session.commit()
    return jsonify({"control": control_to_dict(control)})


@risk_bp.delete("/api/catalog/controls/<int:control_id>")
@csrf.exempt
def api_delete_control(control_id: int):
    control = ControlMeasure.query.get_or_404(control_id)
    db.session.delete(control)
    db.session.commit()
    return ("", 204)


@risk_bp.get("/api/catalog/personnel")
def api_list_personnel():
    personnel = PersonnelAtRisk.query.order_by(PersonnelAtRisk.name).all()
    return jsonify({"personnel": [personnel_to_dict(p) for p in personnel]})


@risk_bp.post("/api/catalog/personnel")
@csrf.exempt
def api_create_personnel():
    payload = request.get_json(force=True)
    personnel = PersonnelAtRisk(
        name=payload["name"],
        description=payload.get("description", ""),
    )
    db.session.add(personnel)
    db.session.commit()
    return jsonify({"personnel": personnel_to_dict(personnel)}), 201


@risk_bp.put("/api/catalog/personnel/<int:personnel_id>")
@csrf.exempt
def api_update_personnel(personnel_id: int):
    personnel = PersonnelAtRisk.query.get_or_404(personnel_id)
    payload = request.get_json(force=True)
    
    personnel.name = payload.get("name", personnel.name)
    personnel.description = payload.get("description", personnel.description)
    
    db.session.commit()
    return jsonify({"personnel": personnel_to_dict(personnel)})


@risk_bp.delete("/api/catalog/personnel/<int:personnel_id>")
@csrf.exempt
def api_delete_personnel(personnel_id: int):
    personnel = PersonnelAtRisk.query.get_or_404(personnel_id)
    db.session.delete(personnel)
    db.session.commit()
    return ("", 204)


@risk_bp.get("/api/work-orders/<wo_number>")
def api_get_work_order(wo_number: str):
    work_order = services.get_work_order_by_number(wo_number)
    if not work_order:
        abort(404, description="Work order not found")

    tasks = services.get_tasks_for_work_order(wo_number)
    return jsonify({
        "work_order": work_order_to_dict(work_order),
        "tasks": [task_to_dict(task) for task in tasks],
    })


@risk_bp.post("/api/work-orders/<wo_number>/import")
@csrf.exempt
def api_import_work_order(wo_number: str):
    payload = request.get_json(silent=True) or {}
    if request.form:
        payload.update(request.form.to_dict())

    replace_value = payload.get("replace", True)
    if isinstance(replace_value, str):
        replace = replace_value.lower() not in {"false", "0", "no"}
    else:
        replace = bool(replace_value)

    if replace:
        for task in list(work_order.tasks):
            db.session.delete(task)
        for ms in list(work_order.method_statements):
            db.session.delete(ms)
        db.session.flush()

    csv_path: Path | None = None
    if "filename" in payload:
        csv_path = Path(current_app.root_path).parent / "data" / "method_statements" / payload["filename"]
        if not csv_path.exists():
            abort(400, description="Specified CSV file not found in data directory")
    elif "file" in request.files:
        upload_dir = Path(current_app.instance_path) / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        uploaded = request.files["file"]
        csv_path = upload_dir / uploaded.filename
        uploaded.save(csv_path)
    else:
        abort(400, description="Provide either filename in payload or upload file")

    categories = services.load_risk_categories()
    services.import_method_statement(work_order, csv_path, categories)
    db.session.commit()

    tasks = services.get_tasks_for_work_order(wo_number)
    return jsonify({
        "work_order": work_order_to_dict(work_order),
        "tasks": [task_to_dict(task) for task in tasks],
    }), 201


@risk_bp.post("/api/tasks")
@csrf.exempt
def api_create_task():
    payload = request.get_json(force=True)
    wo_number = payload.get("work_order_number")
    work_order = services.get_work_order_by_number(wo_number)
    if not work_order:
        abort(404, description="Work order not found")

    task = Task(
        work_order=work_order,
        sequence=payload.get("sequence", len(work_order.tasks) + 1),
        activity=payload.get("activity", "New Task"),
        hazard_description=payload.get("hazard_description", ""),
        personnel_at_risk=payload.get("personnel_at_risk", ""),
        existing_controls_summary=payload.get("existing_controls_summary", ""),
    )
    services.upsert_task(task, payload)
    db.session.commit()
    return jsonify({"task": task_to_dict(task)}), 201


@risk_bp.put("/api/tasks/<int:task_id>")
@csrf.exempt
def api_update_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    payload = request.get_json(force=True)
    services.upsert_task(task, payload)
    db.session.commit()
    return jsonify({"task": task_to_dict(task)})


@risk_bp.delete("/api/tasks/<int:task_id>")
@csrf.exempt
def api_delete_task(task_id: int):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return ("", 204)


@risk_bp.put("/api/tasks/<int:task_id>/hazards")
@csrf.exempt
def api_update_task_hazards(task_id: int):
    payload = request.get_json(force=True)
    task = Task.query.get_or_404(task_id)
    hazard_payload = payload.get("hazards")
    if hazard_payload is None:
        hazard_payload = payload.get("hazard_ids", [])
    try:
        services.replace_task_hazards(task, hazard_payload or [])
    except ValueError as exc:
        abort(400, description=str(exc))
    db.session.commit()
    return jsonify({"task": task_to_dict(task)})


@risk_bp.put("/api/tasks/<int:task_id>/controls")
@csrf.exempt
def api_update_task_controls(task_id: int):
    payload = request.get_json(force=True)
    task = Task.query.get_or_404(task_id)
    phase = payload.get("phase", ControlPhase.EXISTING)
    if phase not in {ControlPhase.EXISTING, ControlPhase.ADDITIONAL}:
        abort(400, description="Invalid control phase")
    services.replace_task_controls(task, payload.get("control_ids", []), phase)
    db.session.commit()
    return jsonify({"task": task_to_dict(task)})


@risk_bp.put("/api/tasks/<int:task_id>/hazards/<int:hazard_id>/controls")
@csrf.exempt
def api_update_hazard_controls(task_id: int, hazard_id: int):
    payload = request.get_json(force=True)
    task_hazard = TaskHazard.query.filter_by(task_id=task_id, hazard_id=hazard_id).first_or_404()
    phase = payload.get("phase", ControlPhase.EXISTING)
    if phase not in {ControlPhase.EXISTING, ControlPhase.ADDITIONAL}:
        abort(400, description="Invalid control phase")
    
    # Handle controls with parameters
    controls_with_parameters = payload.get("controls_with_parameters", [])
    control_parameters = {cp["id"]: cp.get("parameter_value") for cp in controls_with_parameters}
    
    services.replace_hazard_controls(task_hazard, payload.get("control_ids", []), phase, control_parameters)
    db.session.commit()
    return jsonify({"task": task_to_dict(task_hazard.task)})


def task_to_dict(task: Task) -> dict[str, Any]:
    return {
        "id": task.id,
        "sequence": task.sequence,
        "activity": task.activity,
        "hazard_description": task.hazard_description,
        "personnel_at_risk": task.personnel_at_risk,
        "existing_controls_summary": task.existing_controls_summary,
        "additional_controls_summary": task.additional_controls_summary,
        "likelihood": task.likelihood,
        "severity": task.severity,
        "risk_score": task.risk_score,
        "risk_category": risk_category_to_dict(task.risk_category) if task.risk_category else None,
        "controls": {
            "existing": [control_to_dict(link.control) for link in task.controls if link.phase == ControlPhase.EXISTING],
            "additional": [control_to_dict(link.control) for link in task.controls if link.phase == ControlPhase.ADDITIONAL],
        },
        "hazards": [task_hazard_to_dict(link) for link in task.hazards],
        "target_completion_date": task.target_completion_date.isoformat() if task.target_completion_date else None,
        "residual_likelihood": task.residual_likelihood,
        "residual_severity": task.residual_severity,
        "residual_risk_score": task.residual_risk_score,
        "residual_risk_category": risk_category_to_dict(task.residual_risk_category)
        if task.residual_risk_category
        else None,
        "notes": task.notes,
    }


def task_hazard_to_dict(link: TaskHazard) -> dict[str, Any]:
    hazard_data = hazard_to_dict(link.hazard)
    hazard_data.update({
        "parameter_value": link.parameter_value,
        "is_primary": link.is_primary,
        "notes": link.notes,
        "controls": {
            "existing": [task_control_to_dict(control_link) for control_link in link.controls if control_link.phase == ControlPhase.EXISTING],
            "additional": [task_control_to_dict(control_link) for control_link in link.controls if control_link.phase == ControlPhase.ADDITIONAL],
        },
    })
    return hazard_data

def hazard_to_dict(hazard: Hazard) -> dict[str, Any]:
    return {
        "id": hazard.id,
        "name": hazard.name,
        "category": hazard.category,
        "description": hazard.description,
        "default_likelihood": hazard.default_likelihood,
        "default_severity": hazard.default_severity,
        "requires_parameter": hazard.requires_parameter,
        "parameter_label": hazard.parameter_label,
        "parameter_unit": hazard.parameter_unit,
    }


def control_to_dict(control: ControlMeasure) -> dict[str, Any]:
    return {
        "id": control.id,
        "name": control.name,
        "category": control.category,
        "description": control.description,
        "effectiveness": control.effectiveness,
        "requires_parameter": control.requires_parameter,
        "parameter_label": control.parameter_label,
        "parameter_unit": control.parameter_unit,
        "reference": control.reference,  # Keep for backward compatibility
    }


def task_control_to_dict(task_control: TaskControl) -> dict[str, Any]:
    """Convert TaskControl to dict including parameter value from notes"""
    control_data = control_to_dict(task_control.control)
    control_data.update({
        "parameter_value": task_control.notes,
        "phase": task_control.phase,
    })
    return control_data


def personnel_to_dict(personnel: PersonnelAtRisk) -> dict[str, Any]:
    return {
        "id": personnel.id,
        "name": personnel.name,
        "description": personnel.description,
    }


def work_order_to_dict(work_order: WorkOrder) -> dict[str, Any]:
    return {
        "id": work_order.id,
        "number": work_order.number,
        "title": work_order.title,
        "description": work_order.description,
    }


def risk_category_to_dict(category) -> dict[str, Any] | None:
    if category is None:
        return None
    return {
        "id": category.id,
        "label": category.name,  # Changed from category.label to category.name
        "color": category.color,
        "guidance": category.guidance,
        "min_score": category.min_score,
        "max_score": category.max_score,
    }



