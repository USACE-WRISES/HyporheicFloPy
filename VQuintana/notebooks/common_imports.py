# filepath: /c:/Users/u4eeevmq/Documents/Python/HyporheicFloPy/VQuintana/common_imports.py
#-----------------------Importing Libraries-----------------------#
import subprocess
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install(package):
    logger.info(f"Installing package: {package}")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# List of required packages
required_packages = [
    "flopy",
    "matplotlib",
    "numpy",
    "geopandas",
    "pandas",
    "rasterio",
    "pyproj",
    "shutil",
    "random",
    "pathlib",
    "shapely",
    "scipy",
    "modflow_devtools",
    "pickleshare",
    "warnings",
    "typing",
    "contextily",
    "zipfile",
    "seaborn",
]

# Install required packages
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

# Importing Libraries
import os
import json
import flopy
import pathlib
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import pyproj
import shutil
import random
import scipy
import types
import alphashape
import pathlib as pl
import papermill as pm
from pathlib import Path, PurePath
from pyproj import CRS  # Import the CRS class from pyproj
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.transform import rowcol
from rasterio.mask import mask
from shapely.geometry import box, Point, Polygon, LineString
from flopy.utils.binaryfile import HeadFile, CellBudgetFile
from flopy.modpath import Modpath7, ParticleGroup, ParticleData
from scipy.interpolate import griddata
from pprint import pformat
from flopy.plot.styles import styles
from matplotlib.lines import Line2D
from flopy.mf6 import MFSimulation
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from modflow_devtools.misc import get_env, timed
import jupyter_book
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Any, Sequence, Tuple, List
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
import contextily as ctx # For satellite basemaps
import zipfile # For creating KMZ files
import seaborn as sns # For histograms/kde plots
from mpl_toolkits.axes_grid1 import make_axes_locatable


# Runtime Settings
import asyncio
if asyncio.get_event_loop_policy().__class__.__name__ == "ProactorEventLoopPolicy":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())