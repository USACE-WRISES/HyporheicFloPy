# VQuintana/app_build/build_app.py
"""
Re-create a one-folder PyInstaller build for app_gui.py,
ensuring modflowExe/*, inputs.yaml, inputs.py, and __main__.py are included.

▶ Run with:
    python build_app.py

All temporary folders and the .spec file are deleted on every run,
and the new artefacts stay inside VQuintana/app_build/.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# ────────────────────────────────────────────────────────────────────
# 0.  Paths
# ────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent          # …/VQuintana/app_build
PROJECT_ROOT = SCRIPT_DIR.parent                        # …/VQuintana

# Locate PyInstaller in this env (Windows) or fallback to PATH (POSIX)
if os.name == "nt":
    PYINSTALLER = Path(sys.executable).with_name("pyinstaller.exe")
else:
    PYINSTALLER = "pyinstaller"

# Separator for `--add-data`
SEP = ";" if os.name == "nt" else ":"
def add_data(src: str, dest: str) -> str:
    return f"{src}{SEP}{dest}"

# ────────────────────────────────────────────────────────────────────
# 1.  Clean previous artefacts
# ────────────────────────────────────────────────────────────────────
for artefact in ("build_gitignore", "dist_gitignore", "app_gui.spec"):
    target = SCRIPT_DIR / artefact
    if target.is_dir():
        shutil.rmtree(target, ignore_errors=True)
    elif target.is_file():
        target.unlink()

# ────────────────────────────────────────────────────────────────────
# 2.  Verify required assets exist
# ────────────────────────────────────────────────────────────────────
required = {
    "modflowExe": PROJECT_ROOT / "modflowExe",
    "inputs.yaml": PROJECT_ROOT / "inputs.yaml",
    "inputs.py":   PROJECT_ROOT / "inputs.py",
    "__main__.py": PROJECT_ROOT / "__main__.py",
    "functions":    PROJECT_ROOT / "functions",
}
missing = [name for name, p in required.items() if not p.exists()]
if missing:
    raise FileNotFoundError("Missing required asset(s): " + ", ".join(missing))

# ────────────────────────────────────────────────────────────────────
# 3.  Assemble PyInstaller command
# ────────────────────────────────────────────────────────────────────
# Use wildcard to include all files under modflowExe/
modflow_pattern = str(required["modflowExe"] / "*")

cmd = [
    str(PYINSTALLER),
    "--onedir",
    "--windowed",
    "--noconfirm",
    "--workpath", "build_gitignore",
    "--distpath", "dist_gitignore",
    "--specpath", ".",
    "--add-data",  add_data(modflow_pattern,  "modflowExe"),
    "--add-data",  add_data(str(required["inputs.yaml"]), "."),
    "--add-data",  add_data(str(required["inputs.py"]),    "."),
    "--add-data",  add_data(str(required["__main__.py"]),  "."),
    "--add-data", add_data(str(required["functions"]),   "functions"),
    "--hidden-import", "pydantic",
    "--hidden-import", "pydantic._internal",
    "--collect-submodules", "rasterio",
    "--collect-submodules", "rasterio._io",   # some C-extensions live here
     "--hidden-import", "tabulate", 
    str(PROJECT_ROOT / "app_gui.py"),
]

print("Running PyInstaller:\n  " + " \\\n  ".join(cmd) + "\n")

# ────────────────────────────────────────────────────────────────────
# 4.  Execute build
# ────────────────────────────────────────────────────────────────────
subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)

print("\n✅  Build complete — see  VQuintana/app_build/dist_gitignore/app_gui/")
