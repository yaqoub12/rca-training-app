"""Database models for the RCA Risk Assessment app."""
from __future__ import annotations

from datetime import date

from sqlalchemy import CheckConstraint, Enum, UniqueConstraint
from sqlalchemy.sql import func

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class WorkOrder(TimestampMixin, db.Model):
    __tablename__ = "work_orders"

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)

    method_statements = db.relationship("MethodStatement", back_populates="work_order", cascade="all, delete-orphan")
    tasks = db.relationship("Task", back_populates="work_order", cascade="all, delete-orphan")

    def __repr__(self) -> str:  # pragma: no cover - repr debug helper
        return f"<WorkOrder {self.number}>"


class MethodStatement(TimestampMixin, db.Model):
    __tablename__ = "method_statements"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    source_filename = db.Column(db.String(255))
    version = db.Column(db.String(64))
    imported_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)

    work_order = db.relationship("WorkOrder", back_populates="method_statements")
    tasks = db.relationship("Task", back_populates="method_statement")


class Hazard(TimestampMixin, db.Model):
    __tablename__ = "hazards"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    default_severity = db.Column(db.Integer, default=3)
    default_likelihood = db.Column(db.Integer, default=3)
    requires_parameter = db.Column(db.Boolean, nullable=False, default=False)
    parameter_label = db.Column(db.String(120))
    parameter_unit = db.Column(db.String(40))

    __table_args__ = (UniqueConstraint("name", "category", name="uq_hazard_name_category"),)

    task_links = db.relationship("TaskHazard", back_populates="hazard", cascade="all, delete-orphan")


class ControlMeasure(TimestampMixin, db.Model):
    __tablename__ = "control_measures"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    effectiveness = db.Column(db.Integer, default=2)
    requires_parameter = db.Column(db.Boolean, nullable=False, default=False)
    parameter_label = db.Column(db.String(120))
    parameter_unit = db.Column(db.String(40))
    reference = db.Column(db.Text)  # Keep for backward compatibility

    __table_args__ = (UniqueConstraint("name", "category", name="uq_control_name_category"),)

    task_links = db.relationship("TaskControl", back_populates="control", cascade="all, delete-orphan")


class PersonnelAtRisk(TimestampMixin, db.Model):
    __tablename__ = "personnel_at_risk"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.Text)

    def __repr__(self):
        return f"<PersonnelAtRisk {self.name}>"


class RiskMatrixCategory(TimestampMixin, db.Model):
    __tablename__ = "risk_matrix_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    min_score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    color = db.Column(db.String(20), nullable=False)
    guidance = db.Column(db.Text)

    __table_args__ = (
        CheckConstraint("min_score >= 1 AND min_score <= 25", name="ck_risk_category_min_score_range"),
        CheckConstraint("max_score >= 1 AND max_score <= 25", name="ck_risk_category_max_score_range"),
        CheckConstraint("min_score <= max_score", name="ck_risk_category_score_order"),
    )

    def contains(self, score: int) -> bool:
        return self.min_score <= score <= self.max_score


class Task(TimestampMixin, db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    work_order_id = db.Column(db.Integer, db.ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False)
    method_statement_id = db.Column(db.Integer, db.ForeignKey("method_statements.id", ondelete="SET NULL"))
    sequence = db.Column(db.Integer, default=0)

    activity = db.Column(db.String(255), nullable=False)
    hazard_description = db.Column(db.Text)
    personnel_at_risk = db.Column(db.Text)
    existing_controls_summary = db.Column(db.Text)

    likelihood = db.Column(db.Integer, default=1)
    severity = db.Column(db.Integer, default=1)
    risk_score = db.Column(db.Integer, default=1)
    risk_category_id = db.Column(db.Integer, db.ForeignKey("risk_matrix_categories.id", ondelete="SET NULL"))

    additional_controls_summary = db.Column(db.Text)
    target_completion_date = db.Column(db.Date)

    residual_likelihood = db.Column(db.Integer, default=1)
    residual_severity = db.Column(db.Integer, default=1)
    residual_risk_score = db.Column(db.Integer, default=1)
    residual_risk_category_id = db.Column(db.Integer, db.ForeignKey("risk_matrix_categories.id", ondelete="SET NULL"))

    notes = db.Column(db.Text)

    work_order = db.relationship("WorkOrder", back_populates="tasks")
    method_statement = db.relationship("MethodStatement", back_populates="tasks")
    risk_category = db.relationship("RiskMatrixCategory", foreign_keys=[risk_category_id])
    residual_risk_category = db.relationship("RiskMatrixCategory", foreign_keys=[residual_risk_category_id])

    hazards = db.relationship("TaskHazard", back_populates="task", cascade="all, delete-orphan")
    controls = db.relationship("TaskControl", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("likelihood BETWEEN 1 AND 5", name="ck_task_likelihood_range"),
        CheckConstraint("severity BETWEEN 1 AND 5", name="ck_task_severity_range"),
        CheckConstraint("residual_likelihood BETWEEN 1 AND 5", name="ck_task_residual_likelihood_range"),
        CheckConstraint("residual_severity BETWEEN 1 AND 5", name="ck_task_residual_severity_range"),
    )

    def update_risk(self, categories: list[RiskMatrixCategory], residual: bool = False) -> None:
        if residual:
            score = (self.residual_likelihood or 1) * (self.residual_severity or 1)
            self.residual_risk_score = score
            self.residual_risk_category = _match_category(categories, score)
        else:
            score = (self.likelihood or 1) * (self.severity or 1)
            self.risk_score = score
            self.risk_category = _match_category(categories, score)


class TaskHazard(TimestampMixin, db.Model):
    __tablename__ = "task_hazards"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    hazard_id = db.Column(db.Integer, db.ForeignKey("hazards.id", ondelete="CASCADE"), nullable=False)
    parameter_value = db.Column(db.String(120))
    notes = db.Column(db.Text)
    is_primary = db.Column(db.Boolean, default=False)

    task = db.relationship("Task", back_populates="hazards")
    hazard = db.relationship("Hazard", back_populates="task_links")
    controls = db.relationship("TaskControl", back_populates="task_hazard", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("task_id", "hazard_id", name="uq_task_hazard"),)


class ControlPhase:
    EXISTING = "existing"
    ADDITIONAL = "additional"


class TaskControl(TimestampMixin, db.Model):
    __tablename__ = "task_controls"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    task_hazard_id = db.Column(db.Integer, db.ForeignKey("task_hazards.id", ondelete="CASCADE"), nullable=False)
    control_id = db.Column(db.Integer, db.ForeignKey("control_measures.id", ondelete="CASCADE"), nullable=False)
    phase = db.Column(Enum(ControlPhase.EXISTING, ControlPhase.ADDITIONAL, name="control_phase"), nullable=False)
    notes = db.Column(db.Text)

    task = db.relationship("Task", back_populates="controls")
    task_hazard = db.relationship("TaskHazard", back_populates="controls")
    control = db.relationship("ControlMeasure", back_populates="task_links")

    __table_args__ = (UniqueConstraint("task_hazard_id", "control_id", "phase", name="uq_task_hazard_control"),)


def _match_category(categories: list[RiskMatrixCategory], score: int) -> RiskMatrixCategory | None:
    for category in categories:
        if category.contains(score):
            return category
    return None

