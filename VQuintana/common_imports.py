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
    "warnings"
]

# Install required packages
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        install(package)

# Importing Libraries
import os
import flopy
import pathlib
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd
import rasterio
import pyproj
import shutil
import random
import scipy
import pathlib as pl
from pathlib import Path
from rasterio.crs import CRS
from rasterio.plot import show
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.transform import rowcol
from rasterio.mask import mask
from shapely.geometry import box, Point, Polygon, LineString
from flopy.utils.binaryfile import HeadFile
from scipy.interpolate import griddata
from pprint import pformat
from flopy.plot.styles import styles
from matplotlib.lines import Line2D
from flopy.mf6 import MFSimulation
from matplotlib import cbook, cm
from matplotlib.colors import LightSource
from modflow_devtools.misc import get_env, timed
import jupyter_book