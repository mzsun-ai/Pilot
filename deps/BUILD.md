# Building openEMS + CSXCAD into the `Pilot` conda env (no root)

On this machine, **openEMS**, **CSXCAD**, and **libfparser** (C++, from [thliebig/fparser](https://github.com/thliebig/fparser)) were compiled and installed into:

`/home/mingze/miniforge3/envs/Pilot`

Source trees live under `deps/src/`:

- `src/fparser` — C++ expression parser (not the unrelated PyPI `fparser` Fortran package)
- `src/CSXCAD` — geometry / mesh (upstream `CMakeLists.txt` had a broken `find_library` block; fixed locally for cmake)
- `src/openEMS` — FDTD engine + Python bindings

**Git tags** were added so `setuptools_scm` works on shallow clones:

- CSXCAD: `v0.6.3`
- openEMS: `v0.0.36`

**Rough rebuild order** (after `conda activate Pilot` and build toolchain packages from `README.md` / conda-forge):

1. cmake build + install **fparser** → `$CONDA_PREFIX`
2. cmake build + install **CSXCAD** (`-DFPARSER_ROOT_DIR=$CONDA_PREFIX`, etc.)
3. `CSXCAD_INSTALL_PATH=$CONDA_PREFIX pip install ./CSXCAD/python`
4. cmake build + install **openEMS** (`-DCSXCAD_ROOT_DIR=$CONDA_PREFIX`, `-DFPARSER_ROOT_DIR=$CONDA_PREFIX`)
5. `OPENEMS_INSTALL_PATH=$CONDA_PREFIX CSXCAD_INSTALL_PATH=$CONDA_PREFIX pip install ./openEMS/python`

Verify:

```bash
python -c "from CSXCAD import ContinuousStructure; from openEMS import openEMS; print('OK')"
which openEMS
```
