# ---
# jupyter:
#   jupytext:
#     formats: VQuintana/notebooks//ipynb,VQuintana/hypmod//py:percent
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% 



# %%
import sys, pathlib

project_root = pathlib.Path(__file__).resolve().parents[2]   # ← HyporheicFloPy
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from common_imports import *
from inputs import cfg
from functions import path_utils as pu

# Only the first run actually downloads; later calls are near-instant
pu.download_modflow()                 # or download_modflow("some/other/folder")

# Then add the folder to PATH for this Python session
pu.add_modflow_executables()          # same folder default

print("Configuration settings:")
for key, value in cfg.__dict__.items():
    print(f"{key}: {value}")

# %% papermill={"duration": 0.02969, "end_time": "2025-04-09T19:17:46.560140", "exception": false, "start_time": "2025-04-09T19:17:46.530450", "status": "completed"}
# Print the parameters to verify
print(f"Water Surface Elevation Raster: {cfg.water_surface_elevation_raster}")
print(f"Terrain Elevation Raster: {cfg.terrain_elevation_raster}")
print(f"Groundwater Domain Shapefile: {cfg.ground_water_domain_shapefile}")
print(f"Left Boundary Floodplain: {cfg.left_boundary_floodplain}")
print(f"Right Boundary Floodplain: {cfg.right_boundary_floodplain}")
print(f"Projection File: {cfg.projection_file}")

#--------------------------------- Load Projection FIle -----------------------------------------#
## HEC-RAS Projection File
cfg.setup_projection()
### NOTE: If the projection file is not available, the CRS can be defined manually here.

# %%
cfg.setup_terrain(cfg.hec_ras_crs)

# %%
cfg.setup_water_surface(cfg.hec_ras_crs)

# %% papermill={"duration": 0.165627, "end_time": "2025-04-09T19:17:47.064495", "exception": false, "start_time": "2025-04-09T19:17:46.898868", "status": "completed"}
cfg.setup_vectors()
