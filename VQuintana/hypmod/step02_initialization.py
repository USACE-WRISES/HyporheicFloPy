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

# %% [markdown] papermill={"duration": 0.001974, "end_time": "2025-04-09T19:17:51.688769", "exception": false, "start_time": "2025-04-09T19:17:51.686795", "status": "completed"}
# # Initializing Variables
# This section defines the modeling executables, directories, and parameters used to run the model. The user can define the model grid through cell size and depth, and also define the depth of the groundwater model.

# %% papermill={"duration": 2.839236, "end_time": "2025-04-09T19:17:54.530331", "exception": false, "start_time": "2025-04-09T19:17:51.691095", "status": "completed"} tags=["hide-input"]
from VQuintana.common_imports_for_main import *
from inputs import cfg

def run_notebook(cfg):
    print("Configuration settings:")
    for key, value in cfg.__dict__.items():
        print(f"{key}: {value}")
