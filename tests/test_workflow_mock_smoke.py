import json
from pathlib import Path

from pilot.workflow import run_pilot_pipeline


def test_end_to_end_mock(tmp_path: Path):
    cfg = {
        "paths": {
            "outputs_dir": "outputs",
            "logs_dir": "logs",
            "task_specs_dir": "outputs/task_specs",
            "reports_dir": "outputs/reports",
            "openems_runs_dir": "outputs/openems_runs",
        },
        "em_solver": {"mode": "mock"},
        "parser": {
            "default_dielectric": 4.4,
            "default_loss_tangent": 0.02,
            "default_substrate_thickness_mm": 1.6,
        },
        "logging": {"level": "INFO", "file_name": "test.log"},
    }
    q = "2.4 GHz rectangular patch on FR4 show return loss"
    out = run_pilot_pipeline(q, config=cfg, root=tmp_path)
    assert out["state"] == "done"
    trace = out.get("pipeline_trace")
    assert isinstance(trace, list)
    assert len(trace) >= 5
    stages = [t["stage"] for t in trace]
    assert "parse" in stages and "execute" in stages
    tid = out["task_id"]
    spec_path = tmp_path / "outputs" / "task_specs" / f"{tid}_task_spec.json"
    assert spec_path.exists()
    data = json.loads(spec_path.read_text())
    assert data["frequency"]["center_ghz"] == 2.4
    script = Path(out["generated_script"])
    assert script.exists()
    assert "openEMS" in script.read_text()
