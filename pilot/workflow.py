"""End-to-end orchestration: parse -> plan -> openEMS (or mock) -> report."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from em_solver.mock_client import run_openems_mock
from em_solver.openems_builder import build_openems_patch_script
from em_solver.openems_client import probe_openems_python, run_generated_script
from em_solver.results_extractor import summarize_s11
from pilot.logging_utils import get_logger, setup_logging
from pilot.parser import parse_natural_language
from pilot.planner import build_plan
from pilot.reporter import build_markdown_report, save_report
from pilot.schema import SimulationResults, SimulationTaskSpec
from pilot.state_machine import StateMachine, WorkflowEvent
from pilot.utils import ensure_dirs, write_json


def _validate_task_spec(spec: SimulationTaskSpec) -> tuple[str, list[str]]:
    """Non-blocking checks; returns (status 'ok'|'warn', human-readable messages)."""
    warns: list[str] = []
    if spec.frequency.center_ghz <= 0:
        warns.append("center_ghz should be positive")
    low, high = spec.frequency.band_low_ghz, spec.frequency.band_high_ghz
    if low is not None and high is not None and low >= high:
        warns.append("frequency band_low_ghz must be below band_high_ghz")
    if spec.geometry.substrate_thickness_mm <= 0:
        warns.append("substrate thickness should be positive")
    return ("ok", []) if not warns else ("warn", warns)


def run_pilot_pipeline(
    query: str,
    *,
    config: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    log = get_logger("pilot.workflow")
    paths_cfg = config.get("paths", {})
    em_cfg = config.get("em_solver", {})
    parser_cfg = config.get("parser", {})

    outputs = root / paths_cfg.get("outputs_dir", "outputs")
    logs = root / paths_cfg.get("logs_dir", "logs")
    task_specs = root / paths_cfg.get("task_specs_dir", "outputs/task_specs")
    reports = root / paths_cfg.get("reports_dir", "outputs/reports")
    openems_runs = root / paths_cfg.get("openems_runs_dir", "outputs/openems_runs")
    ensure_dirs(outputs, logs, task_specs, reports, openems_runs)

    log_cfg = config.get("logging", {})
    if not logging.getLogger("pilot").handlers:
        setup_logging(
            logs,
            level=log_cfg.get("level", "INFO"),
            file_name=log_cfg.get("file_name", "pilot_run.log"),
        )

    sm = StateMachine()
    spec: SimulationTaskSpec | None = None
    pipeline_trace: list[dict[str, Any]] = []

    def trace(stage: str, label: str, status: str = "ok", detail: str = "") -> None:
        pipeline_trace.append({"stage": stage, "label": label, "status": status, "detail": detail})

    try:
        spec = parse_natural_language(
            query,
            default_er=float(parser_cfg.get("default_dielectric", 4.4)),
            default_tan_delta=float(parser_cfg.get("default_loss_tangent", 0.02)),
            substrate_thickness_mm=float(parser_cfg.get("default_substrate_thickness_mm", 1.6)),
        )
        sm.transition(WorkflowEvent.PARSE_OK)
        trace("parse", "Parse natural language → task specification")

        plan = build_plan(spec)
        sm.transition(WorkflowEvent.PLAN_OK)
        task_spec_path = task_specs / f"{plan.task_id}_task_spec.json"
        write_json(task_spec_path, spec.model_dump())
        plan_path = task_specs / f"{plan.task_id}_plan.json"
        write_json(plan_path, plan.model_dump())
        log.info("Wrote task spec %s", task_spec_path)
        trace("plan", "Execution plan and persisted task spec")

        val_st, val_msgs = _validate_task_spec(spec)
        trace(
            "validate",
            "Validator — frequency and geometry sanity",
            val_st,
            "; ".join(val_msgs) if val_msgs else "checks passed",
        )

        run_dir = openems_runs / plan.task_id
        script_path = build_openems_patch_script(spec, run_dir)
        trace("generate", "Generated openEMS driver script", "ok", str(script_path.name))

        mode_pref = str(em_cfg.get("mode", "auto")).lower()
        timeout_sec = int(em_cfg.get("timeout_sec", 900))
        python_override = em_cfg.get("python_exe") or None

        sm.transition(WorkflowEvent.SOLVER_OK)

        use_openems = mode_pref == "openems" or mode_pref == "auto"
        if mode_pref == "mock":
            use_openems = False

        ok_probe, py_exe, probe_msg = probe_openems_python(python_override)
        log.info("openEMS probe: %s", probe_msg)

        result_dict: dict[str, Any] = {
            "export_paths": [str(script_path)],
            "raw_metrics": {"probe": probe_msg},
            "s11_at_target_db": None,
            "peak_gain_dbi": None,
            "resonance_ghz": None,
            "subprocess_stderr": "",
        }
        solver_mode = "mock"
        openems_py: str | None = None

        if use_openems and ok_probe:
            openems_py = py_exe
            try:
                run_res = run_generated_script(
                    script_path,
                    python_exe=py_exe,
                    cwd=run_dir,
                    timeout_sec=timeout_sec,
                )
                result_dict["subprocess_stderr"] = run_res.stderr
                result_dict["raw_metrics"]["subprocess_rc"] = run_res.returncode
                csv_path = run_dir / "s11.csv"
                if run_res.returncode == 0 and csv_path.exists():
                    solver_mode = "openems"
                    summary = summarize_s11(csv_path, target_ghz=spec.frequency.center_ghz)
                    result_dict["raw_metrics"].update(summary)
                    result_dict["resonance_ghz"] = summary.get("at_ghz")
                    result_dict["s11_at_target_db"] = summary.get("s11_at_target_db")
                    png = run_dir / "s11.png"
                    result_dict["export_paths"] = [str(script_path), str(csv_path)]
                    if png.exists():
                        result_dict["export_paths"].append(str(png))
                else:
                    log.error("openEMS run failed or no s11.csv; falling back to mock. stderr=%s", run_res.stderr[:500])
                    mock_out = run_openems_mock(spec, run_dir)
                    result_dict.update(mock_out)
                    solver_mode = "mock"
            except Exception as e:
                log.exception("openEMS execution error: %s", e)
                mock_out = run_openems_mock(spec, run_dir)
                result_dict.update(mock_out)
                solver_mode = "mock"
        else:
            if use_openems and not ok_probe:
                log.warning("%s — using mock S11.", probe_msg)
            mock_out = run_openems_mock(spec, run_dir)
            result_dict.update(mock_out)
            solver_mode = "mock"

        trace("execute", "FDTD execution", "ok", f"backend={solver_mode}")

        sm.transition(WorkflowEvent.BUILD_OK)
        sm.transition(WorkflowEvent.SETUP_OK)
        sm.transition(WorkflowEvent.RUN_OK)

        csv_final = run_dir / "s11.csv"
        if csv_final.exists():
            summary = summarize_s11(csv_final, target_ghz=spec.frequency.center_ghz)
            result_dict["raw_metrics"].update(summary)
            result_dict["resonance_ghz"] = summary.get("at_ghz")
            result_dict["s11_at_target_db"] = summary.get("s11_at_target_db")

        sm.transition(WorkflowEvent.EXTRACT_OK)

        exports = list(
            dict.fromkeys([str(script_path)] + list(result_dict.get("export_paths", [])))
        )
        results = SimulationResults(
            task_id=plan.task_id,
            mode=solver_mode,
            solver="openems" if solver_mode == "openems" else "mock_lorentzian",
            s11_at_target_db=result_dict.get("s11_at_target_db"),
            peak_gain_dbi=result_dict.get("peak_gain_dbi"),
            resonance_ghz=result_dict.get("resonance_ghz"),
            export_paths=exports,
            raw_metrics=result_dict.get("raw_metrics", {}),
            generated_script=str(script_path),
            openems_python=openems_py,
        )
        report_md = build_markdown_report(spec, plan, results)
        report_path = reports / f"{plan.task_id}_report.md"
        save_report(report_path, report_md)
        sm.transition(WorkflowEvent.REPORT_OK)

        summary_path = reports / f"{plan.task_id}_summary.json"
        write_json(summary_path, results.model_dump())
        trace("report", "Markdown report and summary JSON", "ok", str(report_path.name))

        log.info("Done. Report: %s", report_path)
        return {
            "task_id": plan.task_id,
            "state": sm.state.value,
            "task_spec_path": str(task_spec_path),
            "plan_path": str(plan_path),
            "report_path": str(report_path),
            "summary_path": str(summary_path),
            "generated_script": str(script_path),
            "results": results.model_dump(),
            "report_markdown": report_md,
            "pipeline_trace": pipeline_trace,
        }
    except Exception as e:
        log.exception("Pipeline failed: %s", e)
        sm.transition(WorkflowEvent.FAIL)
        raise
