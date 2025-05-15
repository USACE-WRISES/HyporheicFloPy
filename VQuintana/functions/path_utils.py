from __future__ import annotations
"""Filesystem & environment helpers shared across the project.

Public helpers
--------------
* ``find_project_root(start, marker="inputs.yaml")`` – walk upwards until a
  directory containing *marker* is found.
* ``add_modflow_executables(folder="modflowExe")`` – append executables in
  *folder* to the running process ``PATH``.
* ``download_modflow(folder="modflowExe")`` – fetch MODFLOW binaries with
  ``flopy.utils.get_modflow`` and place them into *folder*.

Centralising these utilities avoids duplicating common patterns across scripts.
"""
from pathlib import Path
from typing import Iterable
import os
import sys

BASE_DIR = Path(__file__).resolve().parent.parent   # .../dist/app_gui on frozen build

def resource(*parts: str) -> Path:
    """Return an absolute path inside the bundled folder."""
    s = BASE_DIR.joinpath(*parts)
    return s

# Optional import – only required for the download helper
try:
    from flopy.utils import get_modflow as _get_modflow  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – Flopy may not be installed
    _get_modflow = None  # will raise inside download_modflow if used

__all__ = [
    "find_project_root",
    "add_modflow_executables",
    "download_modflow",
]

# -----------------------------------------------------------------------------
# 1. Project‑root discovery
# -----------------------------------------------------------------------------

def find_project_root(start: Path, marker: str = "inputs.yaml") -> Path:
    """Walk up from *start* until a directory containing *marker* is found."""
    _cur = start.resolve()
    while _cur != _cur.parent:  # stop at filesystem root
        if (_cur / marker).exists():
            return _cur
        _cur = _cur.parent
    raise RuntimeError(
        f"Project root not found – '{marker}' not encountered above {start}"
    )

# -----------------------------------------------------------------------------
# 2. Environment helper – add existing executables to PATH
# -----------------------------------------------------------------------------

def _iter_executables(folder: Path) -> Iterable[Path]:
    """Yield files in *folder* that look like executables (platform‑agnostic)."""
    _exts = {".exe", ""} if sys.platform.startswith("win") else {""}
    for _p in folder.iterdir():
        if _p.is_file() and _p.suffix.lower() in _exts:
            yield _p

def add_modflow_executables(folder: str | Path = "modflowExe") -> None:
    """Append every file in *folder* to the process ``PATH``."""
    _folder = Path(folder).resolve()
    if not _folder.exists():
        raise FileNotFoundError(
            f"The path '{_folder}' does not exist. Please check the directory."
        )

    for _exe in _iter_executables(_folder):
        _exe_dir = str(_exe.parent)
        if _exe_dir not in os.environ["PATH"].split(os.pathsep):
            os.environ["PATH"] += os.pathsep + _exe_dir
            print(f"Executable added to PATH: {_exe.name}")

# -----------------------------------------------------------------------------
# 3. Convenience – download MODFLOW binaries via Flopy
# -----------------------------------------------------------------------------

def download_modflow(folder: str | Path = "modflowExe") -> None:
    """Download MODFLOW executables into *folder* using Flopy—**only if needed**.

    * If at least one executable already exists in *folder*, nothing is
      downloaded and the function returns immediately.
    * Otherwise it calls ``flopy.utils.get_modflow`` to fetch mf6, mp7, etc.
    """
    if _get_modflow is None:
        raise ImportError(
            "Flopy is not installed – `pip install flopy` to enable downloads."
        )

    _folder = Path(folder).resolve()
    _folder.mkdir(parents=True, exist_ok=True)

    # ── Bail out early if executables are already there ────────────────────
    existing_exes = list(_iter_executables(_folder))
    if existing_exes:
        print(
            f"✔ MODFLOW executables already present in '{_folder}'. "
            "Download skipped."
        )
        return  # nothing else to do

    # ── Otherwise fetch them via Flopy ─────────────────────────────────────
    try:
        _get_modflow(bindir=str(_folder))
        print("MODFLOW executables downloaded successfully.")
    except Exception as _exc:  # noqa: BLE001 – bubble up after logging
        raise RuntimeError(f"Error downloading MODFLOW: {_exc}") from _exc

    # List contents for verification
    print("Contents of the MODFLOW executable directory:")
    for _item in _folder.iterdir():
        print("  •", _item.name)
