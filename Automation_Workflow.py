# Create Python script to run the workflow for the HyporheicFloPy project
# This script will execute a series of Jupyter notebooks using papermill and pass parameters to each notebook.
# Next, Bundle the notebooks into a single executable file using PyInstaller.
# Executable will use configuration files to set the parameters for the workflow.
    # Users will edit the configuration files to set their own parameters.
# The script will also include error handling to ensure that any issues during execution are reported.

# Workflow Script for HyporheicFloPy Project
from VQuintana.common_imports_for_main import *  # Import all required libraries and utilities

import subprocess
import json
import sys

# Function to load configuration from a JSON file
def load_config(config_file):
    try:
        with open(config_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse configuration file '{config_file}'. {e}")
        sys.exit(1)

# Function to execute a notebook using papermill
def run_notebook(notebook_path, parameters):
    print(f"Running notebook: {notebook_path}")
    command = ["papermill", notebook_path, notebook_path]
    for key, value in parameters.items():
        command += ["-p", key, str(value)]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running notebook {notebook_path}: {e}")
        sys.exit(1)

# Main workflow execution
def main():
    # Load configuration from file
    config_file = "config.json"  # Path to the configuration file
    config = load_config(config_file)

    # Run introduction notebook
    run_notebook("VQuintana/intro.ipynb", {})

    # Run preprocessing notebook
    run_notebook("VQuintana/preprocessing.ipynb", {
        "water_surface_elevation_raster": config["water_surface_raster"],
        "terrain_elevation_raster": config["terrain_raster"],
        "ground_water_domain_shapefile": config["gw_domain_shapefile"],
        "left_boundary_floodplain": config["left_boundary_shapefile"],
        "right_boundary_floodplain": config["right_boundary_shapefile"],
        "projection_file": config["projection_file"]
    })

    # Run initialization notebook
    run_notebook("VQuintana/initialization.ipynb", {
        "md6_exe_path": config["modflow6_exe"],
        "md7_exe_path": config["modpath7_exe"],
        "sim_name": config["sim_name"],
        "workspace": config["workspace"],
        "length_units": config["length_units"],
        "time_units": config["time_units"],
        "cell_size_x": config["cell_size_x"],
        "cell_size_y": config["cell_size_y"],
        "gw_mod_depth": config["gw_mod_depth"],
        "z": config["z"],
        "kh": config["kh"],
        "kv": config["kv"],
        "gw_offset": config["gw_offset"],
        "porosity": config["porosity"],
        "rch_iface": config["rch_iface"],
        "rch_iflowface": config["rch_iflowface"],
        "recharge_rate": config["recharge_rate"],
        "nstp": config["nstp"],
        "perlen": config["perlen"],
        "tsmult": config["tsmult"]
    })

    # Run model domain notebook
    run_notebook("VQuintana/model_domain.ipynb", {})

    # Run define boundary notebook
    run_notebook("VQuintana/define_boundary.ipynb", {})

    # Run boundary conditions notebook
    run_notebook("VQuintana/boundary_conditions.ipynb", {})

    # Run models notebook
    run_notebook("VQuintana/run_models.ipynb", {})

    # Run results notebook
    run_notebook("VQuintana/results.ipynb", {})

    print("Workflow completed successfully!")

if __name__ == "__main__":
    main()