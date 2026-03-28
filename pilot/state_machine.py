"""Workflow state machine for Pilot runs."""

from __future__ import annotations

from enum import Enum
from typing import Callable, Optional

from pilot.logging_utils import get_logger


class WorkflowState(str, Enum):
    IDLE = "idle"
    PARSED = "parsed"
    PLANNED = "planned"
    BUILDING = "building"
    SETUP = "setup"
    RUNNING = "running"
    EXTRACTING = "extracting"
    REPORTING = "reporting"
    DONE = "done"
    ERROR = "error"


class WorkflowEvent(str, Enum):
    PARSE_OK = "parse_ok"
    PLAN_OK = "plan_ok"
    SOLVER_OK = "solver_ok"
    BUILD_OK = "build_ok"
    SETUP_OK = "setup_ok"
    RUN_OK = "run_ok"
    EXTRACT_OK = "extract_ok"
    REPORT_OK = "report_ok"
    FAIL = "fail"


_TRANSITIONS: dict[tuple[WorkflowState, WorkflowEvent], WorkflowState] = {
    (WorkflowState.IDLE, WorkflowEvent.PARSE_OK): WorkflowState.PARSED,
    (WorkflowState.PARSED, WorkflowEvent.PLAN_OK): WorkflowState.PLANNED,
    (WorkflowState.PLANNED, WorkflowEvent.SOLVER_OK): WorkflowState.BUILDING,
    (WorkflowState.BUILDING, WorkflowEvent.BUILD_OK): WorkflowState.SETUP,
    (WorkflowState.SETUP, WorkflowEvent.SETUP_OK): WorkflowState.RUNNING,
    (WorkflowState.RUNNING, WorkflowEvent.RUN_OK): WorkflowState.EXTRACTING,
    (WorkflowState.EXTRACTING, WorkflowEvent.EXTRACT_OK): WorkflowState.REPORTING,
    (WorkflowState.REPORTING, WorkflowEvent.REPORT_OK): WorkflowState.DONE,
}


class StateMachine:
    def __init__(self, on_transition: Optional[Callable[[WorkflowState, WorkflowState], None]] = None):
        self.state = WorkflowState.IDLE
        self._log = get_logger("pilot.state_machine")
        self._on_transition = on_transition

    def transition(self, event: WorkflowEvent) -> WorkflowState:
        if event == WorkflowEvent.FAIL:
            old = self.state
            self.state = WorkflowState.ERROR
            self._log.error("transition FAIL: %s -> ERROR", old.value)
            if self._on_transition:
                self._on_transition(old, self.state)
            return self.state
        key = (self.state, event)
        if key not in _TRANSITIONS:
            raise ValueError(f"Invalid transition: state={self.state} event={event}")
        old = self.state
        self.state = _TRANSITIONS[key]
        self._log.info("state %s --%s--> %s", old.value, event.value, self.state.value)
        if self._on_transition:
            self._on_transition(old, self.state)
        return self.state

    def force(self, state: WorkflowState) -> None:
        self._log.warning("force state %s -> %s", self.state.value, state.value)
        self.state = state
