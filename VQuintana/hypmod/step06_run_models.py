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
#     display_name: .venv
#     language: python
#     name: python3
# ---

# %% [markdown] papermill={"duration": 0.003011, "end_time": "2025-04-09T19:18:39.985636", "exception": false, "start_time": "2025-04-09T19:18:39.982625", "status": "completed"}
# # Run Models

# %%
# #-----------------------Importing Libraries-----------------------#
# import subprocess
# import sys
# import logging

# # Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def install(package):
#     logger.info(f"Installing package: {package}")
#     subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# # List of required packages
# required_packages = [
#     "flopy",
#     "matplotlib",
#     "numpy",
#     "geopandas",
#     "pandas",
#     "rasterio",
#     "pyproj",
#     "shutil",
#     "random",
#     "pathlib",
#     "shapely",
#     "scipy",
#     "modflow_devtools",
#     "pickleshare",
#     "warnings"
# ]

# # Install required packages
# for package in required_packages:
#     try:
#         __import__(package)
#     except ImportError:
#         install(package)

# # Importing Libraries
# import os
# import flopy
# import pathlib
# import matplotlib.pyplot as plt
# import numpy as np
# import geopandas as gpd
# import pandas as pd
# import rasterio
# import pyproj
# import shutil
# import random
# import scipy
# import pathlib as pl
# import papermill as pm
# from pathlib import Path
# from rasterio.crs import CRS
# from rasterio.plot import show
# from rasterio.warp import calculate_default_transform, reproject, Resampling
# from rasterio.transform import from_bounds
# from rasterio.transform import rowcol
# from rasterio.mask import mask
# from shapely.geometry import box, Point, Polygon, LineString
# from flopy.utils.binaryfile import HeadFile
# from scipy.interpolate import griddata
# from pprint import pformat
# from flopy.plot.styles import styles
# from matplotlib.lines import Line2D
# from flopy.mf6 import MFSimulation
# from matplotlib import cbook, cm
# from matplotlib.colors import LightSource
# from modflow_devtools.misc import get_env, timed
# import jupyter_book

# # Runtime Settings
# import asyncio
# if asyncio.get_event_loop_policy().__class__.__name__ == "ProactorEventLoopPolicy":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# %% papermill={"duration": 3.665358, "end_time": "2025-04-09T19:18:43.652994", "exception": false, "start_time": "2025-04-09T19:18:39.987636", "status": "completed"} tags=["hide-input"]
# Import Libraries
# #%run ./common_imports.py

import common_imports

# Retrieve stored variables
# %store -r md6_exe_path
# %store -r md7_exe_path
# %store -r sim_name
# %store -r workspace
# %store -r figs_path
# %store -r gwf_name
# %store -r mp7_name
# %store -r gwf_ws
# %store -r mp7_ws
# %store -r headfile
# %store -r head_filerecord
# %store -r budgetfile
# %store -r budget_filerecord
# %store -r write
# %store -r run
# %store -r plot
# %store -r plot_show
# %store -r plot_save

# Retrieve model parameters
# %store -r length_units
# %store -r time_units
# %store -r nper
# %store -r cell_size_x
# %store -r cell_size_y
# %store -r gw_mod_depth
# %store -r z
# %store -r kh
# %store -r kv
# %store -r gw_offset
# %store -r porosity
# %store -r rch_iface
# %store -r rch_iflowface
# %store -r recharge_rate
# %store -r nstp
# %store -r perlen
# %store -r tsmult

# Retrieve spatial data
# %store -r hec_ras_crs
# %store -r terrain_elevation
# %store -r raster_transform
# %store -r transform
# %store -r raster_crs
# %store -r terrain_output_raster
# %store -r water_surface_output_raster
# %store -r cropped_output_raster
# %store -r ground_water_domain
# %store -r left_boundary
# %store -r right_boundary

# retrieve model domain data
# %store -r terrain_elevation
# %store -r raster_transform
# %store -r raster_crs
# %store -r raster_bounds_box
# %store -r bed_elevation
# %store -r raster_width
# %store -r raster_height
# %store -r ncol
# %store -r nrow
# %store -r top
# %store -r nlay
# %store -r grid_x
# %store -r grid_y
# %store -r grid_points
# %store -r intersecting_points
# %store -r xorigin
# %store -r yorigin
# %store -r xmin
# %store -r ymin
# %store -r xmax
# %store -r ymax
# %store -r tops
# %store -r botm

# retrieve model boundary data
# %store -r left_start
# %store -r left_end
# %store -r right_start
# %store -r right_end
# %store -r upstream_start_x
# %store -r upstream_start_y
# %store -r upstream_end_x
# %store -r upstream_end_y
# %store -r downstream_start_x
# %store -r downstream_start_y
# %store -r downstream_end_x
# %store -r downstream_end_y
# %store -r upstream_line
# %store -r downstream_line
# %store -r upstream_boundary
# %store -r downstream_boundary
# %store -r grid_cells
# %store -r grid_gdf
# %store -r idomain

# retrieve model boundary conditions
# %store -r boundary_cells
# %store -r left_boundary_cells
# %store -r right_boundary_cells
# %store -r upstream_boundary_cells
# %store -r downstream_boundary_cells
# %store -r all_boundary_cells
# %store -r unique_boundary_cells
# %store -r left_boundary_cells_first_layer
# %store -r right_boundary_cells_first_layer
# %store -r upstream_boundary_cells_first_layer
# %store -r downstream_boundary_cells_first_layer
# %store -r max_elevation_upstream
# %store -r max_elevation_downstream
# %store -r gw_elevation_left_first
# %store -r gw_elevation_left_last
# %store -r gw_elevation_right_first
# %store -r gw_elevation_right_last
# %store -r gw_elevation_upstream_first
# %store -r gw_elevation_upstream_last
# %store -r gw_elevation_downstream_first
# %store -r gw_elevation_downstream_last
# %store -r gw_elevation_left
# %store -r gw_elevation_right
# %store -r gw_elevation_upstream
# %store -r gw_elevation_downstream
# %store -r grid_points_coords
# %store -r elevation_values
# %store -r grid_points_df
# %store -r output_csv
# %store -r cropped_df
# %store -r river_cells
# %store -r river_x
# %store -r river_y
# %store -r river_elevation
# %store -r chd_data
# %store -r unique_chd_cells
# %store -r duplicate_chd_cells
# %store -r chd_data_converted

# retrieve well data
# %store -r wel_data

# retrieve nodes
# # %store -r nodes


# %% [markdown] papermill={"duration": 0.003005, "end_time": "2025-04-09T19:18:43.658009", "exception": false, "start_time": "2025-04-09T19:18:43.655004", "status": "completed"}
# ## MODFLOW 6 Groundwater Model

# %% papermill={"duration": 0.01202, "end_time": "2025-04-09T19:18:43.672791", "exception": false, "start_time": "2025-04-09T19:18:43.660771", "status": "completed"}
#----------------------Model Setup Functions ------------------------#
def build_gwf_model(example_name):
    print(f"Building GWF model for {example_name}")

    # Instantiate the MODFLOW 6 GWF simulation object
    gwfsim = flopy.mf6.MFSimulation(
        sim_name=gwf_name, exe_name=md6_exe_path, sim_ws=gwf_ws
    )

    # Instantiate the MODFLOW 6 temporal discretization package
    flopy.mf6.modflow.mftdis.ModflowTdis(
        gwfsim,
        pname="tdis",
        time_units="DAYS",
        nper=nper,
        perioddata=[(perlen, nstp, tsmult)],
    )

    # Instantiate the MODFLOW 6 gwf (groundwater-flow) model
    gwf = flopy.mf6.ModflowGwf(
        gwfsim, modelname=gwf_name, model_nam_file=f"{gwf_name}.nam", save_flows=True
    )

    # Instantiate the MODFLOW 6 gwf discretization package
    flopy.mf6.modflow.mfgwfdis.ModflowGwfdis(
        gwf,
        nlay=len(botm),  # Number of layers (based on `botm` list length)
        nrow=nrow,       # Number of rows in the grid
        ncol=ncol,       # Number of columns in the grid
        delr=cell_size_x,  # Cell width
        delc=cell_size_y,  # Cell height
        top=tops[0],       # List of dynamically calculated top elevation of the first layer
        botm=botm,          # List of bottom elevations for all layers
        idomain=idomain,    # List of dynamically calculated active and inactive cells in the model domain
        xorigin=xorigin,  # Assign dynamically calculated xorigin
        yorigin=yorigin   # Assign dynamically calculated yorigin
    )
    
    # Add initial conditions (IC package)
    strt_array = np.full((len(botm), nrow, ncol), bed_elevation)

    # Instantiate the MODFLOW 6 gwf initial conditions package
    flopy.mf6.modflow.mfgwfic.ModflowGwfic(gwf, pname="ic", strt=strt_array)
    
    # Instantiate the MODFLOW 6 gwf node property flow package
    flopy.mf6.modflow.mfgwfnpf.ModflowGwfnpf(
        gwf,
        pname="npf",
        icelltype=2,
        k=kh,
        k33=kv,
        save_flows=True,
        save_saturation=True,
        save_specific_discharge=True,
    )

    # # Instantiate the MODFLOW 6 gwf recharge package
    # flopy.mf6.modflow.mfgwfrcha.ModflowGwfrcha(
    #     gwf,
    #     recharge=recharge_rate,
    #     auxiliary=["iface", "iflowface"],
    #     aux=[rch_iface, rch_iflowface],
    #     save_flows=True,
    # )
    
    # Create an iterative model solution (IMS) for the MODFLOW 6 gwf model
    flopy.mf6.ModflowIms(
        gwfsim,
        print_option="SUMMARY",
        outer_dvclose=1e-4,  # Increase convergence criteria for outer iterations
        outer_maximum=200,  # Increase maximum number of outer iterations
        under_relaxation="NONE",
        inner_maximum=500,  # Increase maximum number of inner iterations
        inner_dvclose=1e-4,  # Increase convergence criteria for inner iterations
        rcloserecord=1e-4,  # Increase residual convergence criteria
        linear_acceleration="BICGSTAB",  # Switch to Bi-Conjugate Gradient Stabilized method
        scaling_method="NONE",
        reordering_method="NONE",
        relaxation_factor=0.97,  # Adjust relaxation factor
    )

    # Assign CHD Package to the model if there are valid unique boundary cells
    if not chd_data_converted:
        print("❌ No CHD boundary cells assigned. Please check the input data and conditions.")
    else:
        # Format the CHD values to ensure they are not in scientific notation
        formatted_chd_data = [
            [item[0], item[1], item[2], float(f"{item[3]:.2f}")]
            for item in chd_data_converted
        ]
    
        # Assuming 'gwf' is your groundwater flow model instance
        flopy.mf6.ModflowGwfchd(
            gwf,
            maxbound=len(formatted_chd_data),  # Set to actual assigned CHD cells
            stress_period_data={0: formatted_chd_data},  # Apply the boundary conditions in stress period 0
            pname="CHD",
            save_flows=True,
            filename=f"{gwf_name}.chd"
        )

    print(f"✅ Assigned {len(formatted_chd_data)} unique CHD boundary cells.")

    # Instantiate the MODFLOW 6 prt output control package
    saverecord = [("HEAD", "ALL"), ("BUDGET", "ALL")]
    printrecord = [("HEAD", "LAST")]
    flopy.mf6.ModflowGwfoc(
        gwf,
        saverecord=saverecord,
        head_filerecord=head_filerecord,
        budget_filerecord=budget_filerecord,
        printrecord=printrecord,
    )
    return gwfsim, gwf


# %% [markdown] papermill={"duration": 0.002966, "end_time": "2025-04-09T19:18:43.678772", "exception": false, "start_time": "2025-04-09T19:18:43.675806", "status": "completed"}
# ## MODPATH 7 Particle Tracking

# %% papermill={"duration": 0.012314, "end_time": "2025-04-09T19:18:43.692971", "exception": false, "start_time": "2025-04-09T19:18:43.680657", "status": "completed"}
def build_particle_models(example_name, gwf, river_cells):
    print(f"Building MODPATH 7 model for {example_name}")

    # Define the MODPATH 7 model name and workspace for forward tracking
    mpnamf = f"{example_name}_mp_forward"
    mp_forward = flopy.modpath.Modpath7.create_mp7(
        modelname=mpnamf,
        trackdir="forward",
        flowmodel=gwf,
        model_ws=str(mp7_ws),
        rowcelldivisions=1,
        columncelldivisions=1,
        layercelldivisions=1,
        exe_name=md7_exe_path,
    )

    # Define particle starting locations at riverbed cells for backward tracking
    particle_data_forward = []
    for cell in river_cells:
        nlay, nrow, ncol = cell[0], cell[1], cell[2]
        
        # Add backward particle
        particle_data_forward.append((nlay, nrow, ncol, "forward"))
   
    # Create MODPATH 7 particle data file for forward tracking
    mp_forward.particle_data = flopy.modpath.ParticleData(
        structured=True,
        particledata=particle_data_forward,
    )

    # Write MODPATH 7 input files for forward tracking
    mp_forward.write_input()
    print(f"MODPATH 7 forward model for {example_name} created successfully.")

    # Define the MODPATH 7 model name and workspace for backward tracking
    mpnamb = f"{example_name}_mp_backward"
    mp_backward = flopy.modpath.Modpath7.create_mp7(
        modelname=mpnamb,
        trackdir="backward",
        flowmodel=gwf,
        model_ws=str(mp7_ws),
        rowcelldivisions=1,
        columncelldivisions=1,
        layercelldivisions=1,
        exe_name=md7_exe_path,
    )

    # Define particle starting locations at riverbed cells for backward tracking
    particle_data_backward = []
    for cell in river_cells:
        nlay, nrow, ncol = cell[0], cell[1], cell[2]
        
        # Add backward particle
        particle_data_backward.append((nlay, nrow, ncol, "backward"))
   
    # Create MODPATH 7 particle data file for backward tracking
    mp_backward.particle_data = flopy.modpath.ParticleData(
        structured=True,
        particledata=particle_data_backward,
    )

    # Write MODPATH 7 input files for backward tracking
    mp_backward.write_input()
    print(f"MODPATH 7 backward model for {example_name} created successfully.")

    return mp_forward, mp_backward


# %% [markdown] papermill={"duration": 0.00301, "end_time": "2025-04-09T19:18:43.697995", "exception": false, "start_time": "2025-04-09T19:18:43.694985", "status": "completed"}
# ## Simulation Settings

# %% papermill={"duration": 0.008979, "end_time": "2025-04-09T19:18:43.709527", "exception": false, "start_time": "2025-04-09T19:18:43.700548", "status": "completed"}
def write_models(*sims, silent=False):
    for sim in sims:
        if isinstance(sim, flopy.mf6.MFSimulation):
            sim.write_simulation(silent=silent)
        else:
            sim.write_input()

@timed
def run_models(*sims, silent=False):
    for sim in sims:
        if isinstance(sim, flopy.mf6.MFSimulation):
            print(f"Running simulation: {sim.name}")
            success, buff = sim.run_simulation(silent=silent, report=True)
        else:
            print(f"Running model: {sim.name}")
            success, buff = sim.run_model(silent=silent, report=True)
        
        if not success:
            print(f"Simulation {sim.name} failed.")
            print(buff)
            break
        else:
            print(f"Simulation {sim.name} succeeded.")


# %% papermill={"duration": 0.017168, "end_time": "2025-04-09T19:18:43.729219", "exception": false, "start_time": "2025-04-09T19:18:43.712051", "status": "completed"}
## Plot Groundwater Model Results
def load_head():
    # Assuming you have a head file to load
    head_file = gwf_ws / headfile
    head_obj = flopy.utils.HeadFile(head_file)
    head = head_obj.get_data()
    return head

def plot_gwf_all(gwfsim):
    # get gwf model
    gwf = gwfsim.get_model(gwf_name)
    head = load_head()

    # Load the discretization file to access model grid information
    dis = gwf.get_package("DIS")
    nlay, nrow, ncol = dis.nlay.data, dis.nrow.data, dis.ncol.data

    # Load the idomain array to identify active cells
    idomain = dis.idomain.array # No results will be visible otherwise

    # Choose the layer you want to plot, e.g., the first layer (layer 0)
    layer_to_plot = 1  # You can change this to any other layer (0-based index)

    # Extract the groundwater head for the specified layer (nrow, ncol)
    head_layer = head[layer_to_plot, :, :]

    # Mask the inactive cells in the head_layer array
    head_layer_masked = np.ma.masked_where(idomain[layer_to_plot, :, :] == 0, head_layer)

    # Plot the groundwater head for the chosen layer
    plt.figure(figsize=(10, 6))
    plt.imshow(head_layer_masked, cmap='viridis', origin='lower', extent=[0, ncol, 0, nrow])
    plt.colorbar(label='Groundwater Head (m)')
    plt.title(f'Groundwater Head at Layer {layer_to_plot + 1}')
    plt.xlabel('Column')
    plt.ylabel('Row')
    plt.show()

    # Load the surface elevation data
    surface_elevation = dis.top.array

    # Choose the layers you want to plot, e.g., the first layer (layer 0) and the last layer
    layer_to_plot_first = 0  # First layer (0-based index)
    layer_to_plot_last = nlay - 1  # Last layer (0-based index)

    # Extract the groundwater head for the specified layers (nrow, ncol)
    head_layer_first = head[layer_to_plot_first, :, :]
    head_layer_last = head[layer_to_plot_last, :, :]

    # Mask the inactive cells in the head_layer arrays
    head_layer_first_masked = np.ma.masked_where(idomain[layer_to_plot_first, :, :] == 0, head_layer_first)
    head_layer_last_masked = np.ma.masked_where(idomain[layer_to_plot_last, :, :] == 0, head_layer_last)

    # Plot the surface elevation for active cells and overlay groundwater head contours
    fig, axs = plt.subplots(1, 2, figsize=(20, 10))

    # Plot for the first layer
    top_active_first = np.ma.masked_where(idomain[layer_to_plot_first, :, :] == 0, surface_elevation)
    im1 = axs[0].imshow(top_active_first, cmap="terrain", interpolation="nearest", origin="lower",
                        extent=[0, ncol, 0, nrow], alpha=0.7)
    plt.colorbar(im1, ax=axs[0], label='Surface Elevation (m)')

    # Check if the minimum and maximum values are different before creating contour levels
    if head_layer_first_masked.min() != head_layer_first_masked.max():
        contour_first = axs[0].contour(head_layer_first_masked, levels=np.linspace(head_layer_first_masked.min(), head_layer_first_masked.max(), 10), colors='blue', extent=[0, ncol, 0, nrow])
        axs[0].clabel(contour_first, inline=True, fontsize=8, fmt='%1.1f')
    axs[0].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer_to_plot_first + 1}')
    axs[0].set_xlabel('Column')
    axs[0].set_ylabel('Row')

    # Plot for the last layer
    top_active_last = np.ma.masked_where(idomain[layer_to_plot_last, :, :] == 0, surface_elevation)
    im2 = axs[1].imshow(top_active_last, cmap="terrain", interpolation="nearest", origin="lower",
                        extent=[0, ncol, 0, nrow], alpha=0.7)
    plt.colorbar(im2, ax=axs[1], label='Surface Elevation (m)')

    # Check if the minimum and maximum values are different before creating contour levels
    if head_layer_last_masked.min() != head_layer_last_masked.max():
        contour_last = axs[1].contour(head_layer_last_masked, levels=np.linspace(head_layer_last_masked.min(), head_layer_last_masked.max(), 10), colors='blue', extent=[0, ncol, 0, nrow])
        axs[1].clabel(contour_last, inline=True, fontsize=8, fmt='%1.1f')
    axs[1].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer_to_plot_last + 1}')
    axs[1].set_xlabel('Column')
    axs[1].set_ylabel('Row')

    plt.tight_layout()
    plt.show()

    #---------------------- Zoom In to idomain ------------------------#
    # Choose the layers you want to plot
    layers_to_plot = [1, 19, 39]  # 1st, 20th, and 40th layers (0-based index)

    # Extract the groundwater head for the specified layers (nrow, ncol)
    head_layers = [head[layer, :, :] for layer in layers_to_plot]

    # Mask the inactive cells in the head_layer arrays
    head_layers_masked = [np.ma.masked_where(idomain[layer, :, :] == 0, head_layers[i]) for i, layer in enumerate(layers_to_plot)]

    # Determine the extent of the active cells
    active_cells = np.any(idomain, axis=0)
    active_rows, active_cols = np.where(active_cells)
    row_min, row_max = active_rows.min(), active_rows.max()
    col_min, col_max = active_cols.min(), active_cols.max()

    # Define the extent for the plots
    extent = [col_min, col_max + 1, row_min, row_max + 1]

    # Plot the surface elevation for active cells and overlay groundwater head contours
    fig, axs = plt.subplots(3, 1, figsize=(10, 30))

    for i, layer in enumerate(layers_to_plot):
        # Plot for each layer
        top_active = np.ma.masked_where(idomain[layer, :, :] == 0, surface_elevation)
        im = axs[i].imshow(top_active[row_min:row_max+1, col_min:col_max+1], cmap="terrain", interpolation="nearest", origin="lower",
                           extent=extent, alpha=0.7)
        plt.colorbar(im, ax=axs[i], label='Surface Elevation (m)')
        contour = axs[i].contour(head_layers_masked[i][row_min:row_max+1, col_min:col_max+1], levels=np.linspace(head_layers_masked[i].min(), head_layers_masked[i].max(), 10), colors='blue', extent=extent)
        axs[i].clabel(contour, inline=True, fontsize=8, fmt='%1.1f')
        axs[i].set_title(f'Surface Elevation and Groundwater Head Contours at Layer {layer + 1}')
        axs[i].set_xlabel('Column')
        axs[i].set_ylabel('Row')

    plt.tight_layout()
    plt.show()

    #---------------------- 3D Plot of the Model ------------------------#
    top = dis.top.array
    botm = dis.botm.array
    idomain = dis.idomain.array  # Assuming idomain is part of the dis object

    # Combine top and botm to get the elevation data for all layers
    elevation_data = np.concatenate(([top], botm), axis=0)

    # Get the number of rows and columns
    nrows, ncols = top.shape

    # Layer to plot for terrain
    terrain_layer = 0

    # Create a meshgrid for x and y coordinates
    x = np.linspace(0, ncols - 1, ncols)
    y = np.linspace(0, nrows - 1, nrows)
    x, y = np.meshgrid(x, y)

    # Mask the elevation data using the idomain array
    #z = np.ma.masked_where(idomain[terrain_layer, :, :] == 0, elevation_data[terrain_layer, :, :])

    # Set up plot
    fig, ax = plt.subplots(subplot_kw=dict(projection='3d'))

    # Light source for hillshading
    ls = LightSource(270, 45)

    # Plot the masked elevation data
    z = elevation_data[terrain_layer, :, :]
    rgb = ls.shade(z, cmap=cm.gist_earth, vert_exag=0.1, blend_mode='soft')
    surf = ax.plot_surface(x, y, z, rstride=1, cstride=1, facecolors=rgb,
                        linewidth=0, antialiased=False, shade=False)

    # Set plot labels and title
    ax.set_title('3D Terrain Elevation')
    ax.set_xlabel('Column')
    ax.set_ylabel('Row')
    ax.set_zlabel('Elevation (ft)')

    plt.show()

## Code from:
# https://github.com/matplotlib/matplotlib/tree/cfe5bf75eaf378b9523830908036f2123acfe4e7/examples/frontpage/3D.py


# %% [markdown] papermill={"duration": 0.003014, "end_time": "2025-04-09T19:18:43.734702", "exception": false, "start_time": "2025-04-09T19:18:43.731688", "status": "completed"}
# ## Plot Particle Tracking Results

# %% papermill={"duration": 0.01231, "end_time": "2025-04-09T19:18:43.748527", "exception": false, "start_time": "2025-04-09T19:18:43.736217", "status": "completed"}
def plot_modpath7_results(mpnamf, ws, gwf):
    """
    Process MODPATH 7 results to filter hyporheic flow paths and calculate:
    A) Flow path length distribution
    B) Residence time distribution
    C) Spatial extent of the hyporheic zone

    Parameters:
    - mpnamf: str, MODPATH 7 model name
    - ws: str, workspace directory for MODPATH 7
    - gwf: flopy.mf6.ModflowGwf, MODFLOW 6 groundwater flow model
    """
    # Load forward tracking pathline data
    pathline_file_forward = os.path.join(ws, f"{mpnamf_forward}.mppth")
    pathlines_forward = flopy.utils.PathlineFile(pathline_file_forward).get_alldata()

    # Load backward tracking pathline data
    pathline_file_backward = os.path.join(ws, f"{mpnamf_backward}.mppth")
    pathlines_backward = flopy.utils.PathlineFile(pathline_file_backward).get_alldata()

    # Combine forward and backward pathlines
    all_pathlines = list(pathlines_forward) + list(pathlines_backward)

    # Filter hyporheic flow paths (start and end at the riverbed)
    hyporheic_paths = []
    for pathline in all_pathlines:
        start_layer, start_row, start_column = pathline["k0"], pathline["i0"], pathline["j0"]
        end_layer, end_row, end_column = pathline["k"], pathline["i"], pathline["j"]

        # Check if both start and end points are in riverbed cells
        if is_riverbed_cell(start_layer, start_row, start_column, gwf) and \
           is_riverbed_cell(end_layer, end_row, end_column, gwf):
            hyporheic_paths.append(pathline)

    # Calculate flow path lengths
    flow_path_lengths = [pathline.get_length() for pathline in hyporheic_paths]

    # Calculate residence times
    residence_times = [pathline["time"] for pathline in hyporheic_paths]

    # Calculate spatial extent of the hyporheic zone
    hyporheic_extent = calculate_hyporheic_extent(hyporheic_paths, gwf)

    # Plot flow path length distribution
    plt.figure(figsize=(10, 6))
    plt.hist(flow_path_lengths, bins=20, color="skyblue", edgecolor="black")
    plt.title("Flow Path Length Distribution")
    plt.xlabel("Flow Path Length")
    plt.ylabel("Frequency")
    plt.grid()
    plt.show()

    # Plot residence time distribution
    plt.figure(figsize=(10, 6))
    plt.hist(residence_times, bins=20, color="lightgreen", edgecolor="black")
    plt.title("Residence Time Distribution")
    plt.xlabel("Residence Time")
    plt.ylabel("Frequency")
    plt.grid()
    plt.show()

    # Print spatial extent of the hyporheic zone
    print(f"Spatial Extent of Hyporheic Zone:")
    print(f"  Total Volume: {hyporheic_extent['volume']:.2f} cubic units")
    print(f"  Width: {hyporheic_extent['width']:.2f} units")
    print(f"  Depth: {hyporheic_extent['depth']:.2f} units")

def is_riverbed_cell(layer, row, column, gwf):
    """
    Check if a cell is part of the riverbed.

    Parameters:
    - layer: int, layer index
    - row: int, row index
    - column: int, column index
    - gwf: flopy.mf6.ModflowGwf, MODFLOW 6 groundwater flow model

    Returns:
    - bool: True if the cell is part of the riverbed, False otherwise
    """
    # Example logic: Check if the cell is in the riverbed layer and has a river stage
    river_stage = gwf.riv.stress_period_data.array["stage"]
    bed_elevation = gwf.dis.top.array[row, column] - gwf.dis.botm.array[layer, row, column]
    return river_stage[row, column] > bed_elevation


def calculate_hyporheic_extent(hyporheic_paths, gwf):
    """
    Calculate the spatial extent of the hyporheic zone.

    Parameters:
    - hyporheic_paths: list, filtered hyporheic flow paths
    - gwf: flopy.mf6.ModflowGwf, MODFLOW 6 groundwater flow model

    Returns:
    - dict: Dictionary containing total volume, width, and depth of the hyporheic zone
    """
    # Extract unique cells from hyporheic paths
    unique_cells = set((pathline["k"], pathline["i"], pathline["j"]) for pathline in hyporheic_paths)

    # Calculate spatial extent
    cell_volume = gwf.dis.delr.array[0] * gwf.dis.delc.array[0] * gwf.dis.thickness.array[0]
    total_volume = len(unique_cells) * cell_volume
    width = gwf.dis.delc.array[0] * len(set(cell[2] for cell in unique_cells))  # Unique columns
    depth = gwf.dis.thickness.array[0] * len(set(cell[0] for cell in unique_cells))  # Unique layers

    return {"volume": total_volume, "width": width, "depth": depth}


# %% [markdown] papermill={"duration": 0.00353, "end_time": "2025-04-09T19:18:43.755586", "exception": false, "start_time": "2025-04-09T19:18:43.752056", "status": "completed"}
# ## Run Simulations

# %% papermill={"duration": 17.544938, "end_time": "2025-04-09T19:19:01.305038", "exception": false, "start_time": "2025-04-09T19:18:43.760100", "status": "completed"}
#---------------------- Simulation Scenario ------------------------#
def scenario(silent=False):
    """
    Orchestrates the building, running, and plotting of the MODFLOW 6 and MODPATH 7 models.

    Parameters:
    - sim_name: str, simulation name
    - gwf_name: str, groundwater flow model name
    - md6_exe_path: str, path to the MODFLOW 6 executable
    - gwf_ws: str, workspace for the GWF model
    - nper: int, number of stress periods
    - perlen: float, length of each stress period
    - nstp: int, number of time steps per stress period
    - tsmult: float, time step multiplier
    - botm: list, bottom elevations of the layers
    - nrow: int, number of rows in the grid
    - ncol: int, number of columns in the grid
    - cell_size_x: float, cell width
    - cell_size_y: float, cell height
    - tops: list, top elevations of the layers
    - idomain: list, active/inactive cell array
    - xorigin: float, x-coordinate origin
    - yorigin: float, y-coordinate origin
    - bed_elevation: float, bed elevation
    - kh: float, horizontal hydraulic conductivity
    - kv: float, vertical hydraulic conductivity
    - chd_data_converted: list, constant head boundary data
    - head_filerecord: str, head file record
    - budget_filerecord: str, budget file record
    - mp7_ws: str, workspace for MODPATH 7
    - write: bool, whether to write input files
    - run: bool, whether to run the models
    - plot: bool, whether to plot results
    - silent: bool, whether to suppress output
    """
    # Build the GWF model
    gwfsim, gwf = build_gwf_model(sim_name)
    
    # Debug print to check if the GWF model is built
    print("GWF model built:", gwfsim)
    
    if write:
        write_models(gwfsim, silent=silent)
        
        # Debug print to check if files are written
        print("GWF files written to:", gwf_ws)
    
    if run:
        # Run the MODFLOW model
        print("Running MODFLOW model...")
        run_models(gwfsim, silent=silent)
        print("FINISHED! Running GWF MODFLOW 6")
    
    if plot:
        print("Plotting Groundwater Flow Model")
        plot_gwf_all(gwfsim)
    
    # Attempt to build, run, and plot the MODPATH 7 particle tracking models
    try:
        # Build the MODPATH 7 forward and backward models
        mp_forward, mp_backward = build_particle_models(sim_name, gwf, river_cells)
        
        # Debug print to check if the MODPATH 7 models are built
        print("MODPATH 7 forward model built:", mp_forward)
        print("MODPATH 7 backward model built:", mp_backward)
        
        if write:
            # Write input files for both forward and backward models
            write_models(mp_forward, mp_backward, silent=silent)
            print("MODPATH 7 files written to:", mp7_ws)
        
        if run:
            # Run both forward and backward models
            print("Running MODPATH 7 forward model...")
            run_models(mp_forward, silent=silent)
            print("FINISHED! Running MODPATH 7 forward model")
            
            print("Running MODPATH 7 backward model...")
            run_models(mp_backward, silent=silent)
            print("FINISHED! Running MODPATH 7 backward model")
        
        if plot:
            print("Plotting MODPATH 7 Results")
            
            # Plot results for both forward and backward models
            plot_modpath7_results(
                mpnamf_forward=f"{sim_name}_mp_forward",
                mpnamf_backward=f"{sim_name}_mp_backward",
                ws=str(mp7_ws),
                gwf=gwf
            )
    
    except Exception as e:
        print(f"An error occurred while building, running, or plotting the MODPATH 7 models: {e}")

# Example usage:
scenario(silent=True)
