# VQuintana/app_build/build_app.py
"""
Re-create a one-folder PyInstaller build for app_gui.py.

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

PYINSTALLER = (
    Path(sys.executable).with_name("pyinstaller.exe")   # venv / Windows
    if os.name == "nt"
    else "pyinstaller"                                  # POSIX
)

SEP = ";" if os.name == "nt" else ":"
def add_data(src: Path | str, dest: str) -> str:
    return f"{src}{SEP}{dest}"

# ────────────────────────────────────────────────────────────────────
# 1.  Remove previous artefacts
# ────────────────────────────────────────────────────────────────────
# for artefact in ("build", "dist", "app_gui.spec"):
#     target = SCRIPT_DIR / artefact
#     if target.is_dir():
#         shutil.rmtree(target, ignore_errors=True)
#     elif target.is_file():
#         target.unlink()

# ────────────────────────────────────────────────────────────────────
# 2.  Verify required files / folders exist
# ────────────────────────────────────────────────────────────────────
required = {
    "modflowExe folder" : PROJECT_ROOT / "modflowExe",
    "inputs.yaml"       : PROJECT_ROOT / "inputs.yaml",
    "__main__.py"       : PROJECT_ROOT / "__main__.py",
}

missing = [name for name, p in required.items() if not p.exists()]
if missing:
    raise FileNotFoundError(
        "Missing required asset(s): " + ", ".join(missing)
    )

# ────────────────────────────────────────────────────────────────────
# 3.  Assemble PyInstaller command
# ────────────────────────────────────────────────────────────────────
cmd = [
    str(PYINSTALLER),
    "--onedir",
    #"--windowed", turned off to make debuggin easier... turn this back on for prod
    "--noconfirm",
    "--workpath", "build",            # produced inside app_build
    "--distpath",  "dist",
    "--specpath",  ".",
    # "--icon", "icon.ico",           # uncomment if you have an icon
    "--add-data", add_data(required["modflowExe folder"], "modflowExe"),
    "--add-data", add_data(required["inputs.yaml"], "."),
    "--add-data", add_data(required["__main__.py"], "."),
    str(PROJECT_ROOT / "app_gui.py"),
]

print("Running PyInstaller:\n  " + " \\\n  ".join(cmd) + "\n")

# ────────────────────────────────────────────────────────────────────
# 4.  Execute build
# ────────────────────────────────────────────────────────────────────
subprocess.run(cmd, check=True, cwd=SCRIPT_DIR)

print("\n✅  Fresh build complete — see  VQuintana/app_build/dist/app_gui/")
