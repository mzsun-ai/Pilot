"""Structured task specification for EM simulation requests."""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class StructureType(str, Enum):
    RECTANGULAR_PATCH = "rectangular_patch"
    UNKNOWN = "unknown"


class MaterialSpec(BaseModel):
    name: str = "FR4"
    relative_permittivity: float = 4.4
    loss_tangent: float = 0.02


class FrequencyTarget(BaseModel):
    center_ghz: float
    band_low_ghz: Optional[float] = None
    band_high_ghz: Optional[float] = None


class PerformanceTarget(BaseModel):
    s11_max_db: float = -10.0  # e.g. S11 < -10 dB means max allowed is -10 dB (more negative is better)
    description: str = ""


class GeometryHints(BaseModel):
    substrate_thickness_mm: float = 1.6
    # Patch dimensions may be filled by planner/builder
    patch_length_mm: Optional[float] = None
    patch_width_mm: Optional[float] = None
    ground_plane_mm: Optional[float] = None


class SimulationTaskSpec(BaseModel):
    """User-facing structured spec after NL parsing."""

    raw_query: str
    structure_type: StructureType = StructureType.UNKNOWN
    material: MaterialSpec = Field(default_factory=MaterialSpec)
    frequency: FrequencyTarget
    performance: PerformanceTarget = Field(default_factory=PerformanceTarget)
    geometry: GeometryHints = Field(default_factory=GeometryHints)
    notes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PlanStep(BaseModel):
    name: str
    description: str
    tool: str  # e.g. em_solver.openems_client


class SimulationPlan(BaseModel):
    task_id: str
    steps: list[PlanStep]
    estimated_order: list[str] = Field(default_factory=list)


class SimulationResults(BaseModel):
    task_id: str
    mode: str  # openems | mock
    solver: str = "openems"
    s11_at_target_db: Optional[float] = None
    peak_gain_dbi: Optional[float] = None
    resonance_ghz: Optional[float] = None
    export_paths: list[str] = Field(default_factory=list)
    raw_metrics: dict[str, Any] = Field(default_factory=dict)
    generated_script: Optional[str] = None
    openems_python: Optional[str] = None
