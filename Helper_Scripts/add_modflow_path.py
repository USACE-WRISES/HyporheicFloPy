# add_modflow_path.py

import os
from pathlib import Path

# Define the modflow executable path, two directories up from the current working directory
modflow_exe_path = Path("../modflowExe")

# Check if the modflowExe directory exists
if not modflow_exe_path.exists():
    raise FileNotFoundError(f"The path '{modflow_exe_path}' does not exist. Please check the directory location.")

# Add all executables from the modflowExe folder to the PATH
for exe in modflow_exe_path.iterdir():
    if exe.is_file():
        os.environ["PATH"] += os.pathsep + str(exe.parent.resolve())
        print(f"Executable added to PATH: {exe.name}")