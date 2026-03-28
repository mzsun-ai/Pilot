# 迁移 / 打包说明

## 解压后在新服务器上

```bash
cd /path/to
tar -xzf Pilot-for-transfer.tar.gz
cd Pilot
python3 -m venv .venv && source .venv/bin/activate   # 或 conda activate Pilot
pip install -r requirements.txt
uvicorn web.app:app --host 0.0.0.0 --port 8765
```

浏览器访问 `http://<服务器IP>:8765/`。

## 本包可能排除的内容

为减小体积，打包时可能已排除：

- `outputs/openems_runs/`（大量仿真产物）
- `outputs/reports/`、`outputs/task_specs/`
- `.git`、`__pycache__`

在新机器上首次运行会自动再生成 `outputs/` 下所需目录。

## 配置

编辑 `configs/config.yaml`：`em_solver.mode`、`knowledge.llm_provider`、`surrogate.admin_register_key` 等。
