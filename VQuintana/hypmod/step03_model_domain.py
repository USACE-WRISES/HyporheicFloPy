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

# %% [markdown] papermill={"duration": 0.00309, "end_time": "2025-04-09T19:17:59.567487", "exception": false, "start_time": "2025-04-09T19:17:59.564397", "status": "completed"}
# # Model Domain

# %%
from common_imports import *
from inputs import cfg

def run_notebook(cfg):
    # %% papermill={"duration": 0.96684, "end_time": "2025-04-09T19:18:03.310377", "exception": false, "start_time": "2025-04-09T19:18:02.343537", "status": "completed"}
    #------------------------------Model Grid--------------------------------#
    ## Plot Terrain Elevation
    _reprojected_terrain_elevation_raster = cfg.terrain_output_raster

    # Read raster data and extract elevation values
    with rasterio.open(_reprojected_terrain_elevation_raster) as src:
        _raster_array = src.read(1)  # Read the first band
        cfg.raster_transform = src.transform
        cfg.raster_crs = src.crs
        cfg.raster_bounds_box = box(*src.bounds)  # Create a shapely box for raster bounds
        cfg.terrain_elevation = np.ma.masked_equal(_raster_array, src.nodata)  # Mask no-data values

    # Find Bed Elevations
    cfg.bed_elevation = np.min(cfg.terrain_elevation) # Bed elevation is the minimum value of the cropped surface elevation

    # Calculate the extent of the raster
    cfg.raster_width = src.width * cfg.raster_transform[0]  # Width in feet
    cfg.raster_height = src.height * abs(cfg.raster_transform[4])  # Height in feet

    # Determine the number of rows and columns based on the cell size
    cfg.ncol = int(cfg.raster_width / cfg.cell_size_x)
    cfg.nrow = int(cfg.raster_height / cfg.cell_size_y)

    # Print the calculated grid dimensions
    print(f'Number of columns: {cfg.ncol}')
    print(f'Number of rows: {cfg.nrow}')

    cfg.top = np.full((cfg.nrow, cfg.ncol), cfg.gw_mod_depth)  # feet below bed surface (depth of groundwater model)
    cfg.nlay = int(cfg.top.max() / cfg.z)  # Number of groundwater layers based on default depth)

    # Calculate grid cell centers
    cfg.grid_x, cfg.grid_y = np.meshgrid(
        np.arange(0, cfg.ncol) * cfg.cell_size_x + (cfg.cell_size_x / 2),
        np.arange(0, cfg.nrow) * cfg.cell_size_y + (cfg.cell_size_y / 2),
    )

    # Convert cell centers to Points for intersection checks
    cfg.grid_points = gpd.GeoDataFrame(
        {"geometry": [Point(x, y) for x, y in zip(cfg.grid_x.ravel(), cfg.grid_y.ravel())]},
        crs= cfg.hec_ras_crs,  # Replace with the actual CRS of your grid
    )

    # Read raster data and extract elevation values
    with rasterio.open(_reprojected_terrain_elevation_raster) as src:
        _raster_array = src.read(1)  # Read the first band
        cfg.raster_transform = src.transform
        cfg.raster_crs = src.crs
        cfg.raster_bounds_box = box(*src.bounds)  # Create a shapely box for raster bounds
        cfg.terrain_elevation = np.ma.masked_equal(_raster_array, src.nodata)  # Mask no-data values

    # Create a GeoDataFrame for raster bounds
    raster_bounds_gdf = gpd.GeoDataFrame(
        {"geometry": [cfg.raster_bounds_box]}, crs=cfg.hec_ras_crs
    )

    # Reproject grid points to match raster CRS
    # Use the raster bounds to define the grid extent
    cfg.minx, cfg.miny, cfg.maxx, cfg.maxy = cfg.raster_bounds_box.bounds
    cfg.grid_x, cfg.grid_y = np.meshgrid(
        np.linspace(cfg.minx, cfg.maxx, cfg.ncol),
        np.linspace(cfg.miny, cfg.maxy, cfg.nrow),
    )

    # Recreate the grid points
    cfg.grid_points = gpd.GeoDataFrame(
        {"geometry": [Point(x, y) for x, y in zip(cfg.grid_x.ravel(), cfg.grid_y.ravel())]},
        crs=cfg.raster_crs,
    )

    # Check intersection between grid points and raster bounds
    cfg.intersecting_points = cfg.grid_points[cfg.grid_points.geometry.intersects(cfg.raster_bounds_box)]

    # Debugging: Print details about the GeoDataFrames
    print(f"Raster CRS: {raster_bounds_gdf.crs}")
    print(f"Grid CRS: {cfg.grid_points.crs}")
    print(f"Number of grid points: {len(cfg.grid_points)}")
    print(f"Number of intersecting points: {len(cfg.intersecting_points)}")

    # Set x and y origin
    cfg.xmin, cfg.ymin, cfg.xmax, cfg.ymax = cfg.raster_bounds_box.bounds  # Extract bounding box extent
    cfg.xorigin = cfg.xmin  # Set xorigin to the left-most boundary
    cfg.yorigin = cfg.ymin  # Set yorigin to the bottom-most boundary

    # Extract raster extent before looping
    _transform = cfg.raster_transform
    cfg.xmin = _transform.c
    cfg.ymax = _transform.f
    cfg.xmax = cfg.xmin + (cfg.terrain_elevation.shape[1] * _transform.a)
    cfg.ymin = cfg.ymax + (cfg.terrain_elevation.shape[0] * _transform.e)

    print(f"✅ Raster Extent: X = ({cfg.xmin}, {cfg.xmax}), Y = ({cfg.ymin}, {cfg.ymax})")

    # Initialize the top array
    top = np.full((cfg.nrow, cfg.ncol), np.nan)

    # Update "top" values for each cell in the first layer based on surface elevation
    for i in range(cfg.nrow):
        for _grid_col in range(cfg.ncol):
            # Calculate the x, y coordinates of the cell center
            _point_x = cfg.grid_x[i, _grid_col]
            _point_y = cfg.grid_y[i, _grid_col]

            # Convert the grid cell center coordinates to raster indices
            _col, _row = ~cfg.raster_transform * (_point_x, _point_y)
            _col, _row = int(_col), int(_row)

            # Check if the indices are within raster bounds
            if 0 <= _row < cfg.terrain_elevation.shape[0] and 0 <= _col < cfg.terrain_elevation.shape[1]:
                elevation_value = cfg.terrain_elevation[_row, _col]

                # Update "top" based on the raster value
                cfg.top[i, _grid_col] = elevation_value

    # Interpolate any remaining NA values in the top array
    cfg.top = hf.interpolate_na(np.ma.masked_invalid(cfg.top))

    ## Initialize `tops` and `botm` lists
    cfg.tops = [cfg.top]  # Add the top layer (surface elevation or default)
    cfg.botm = []

    # First layer bottom is calculated from the updated "top" values
    _first_layer_botm = np.full_like(cfg.top, cfg.bed_elevation)  # Subtract 0.5 ft for the first layer
    cfg.botm.append(_first_layer_botm)

    # Create remaining layers with a constant thickness of 0.5 ft
    for layer in range(1, 40):  # Layers 2 to 40
        _next_layer_top = cfg.botm[-1]  # The top of the current layer is the bottom of the previous layer
        _next_layer_botm = _next_layer_top - cfg.z  # Subtract thickness from the top
        cfg.tops.append(_next_layer_top)  # Add the top of the current layer
        cfg.botm.append(_next_layer_botm)  # Add the bottom of the current layer

    # Debugging: Check the top and bottom elevations for all layers
    print("Top layer elevation (max, min):", cfg.tops[0].max(), cfg.botm[0].min())
    for _layer_idx in range(len(cfg.tops)):
        print(f"Layer {_layer_idx + 1} top (max, min):", cfg.tops[_layer_idx].max(), cfg.tops[_layer_idx].min())
        print(f"Layer {_layer_idx + 1} botm (max, min):", cfg.botm[_layer_idx].max(), cfg.botm[_layer_idx].min())
        
    ## Visualization: Plot the top and last bottom layers
    _fig, _axs = plt.subplots(1, 2, figsize=(15, 8))

    # Plot the top layer elevation
    _im1 = _axs[0].imshow(top, cmap="terrain", interpolation="nearest", origin="lower")  # 🔹 Ensures (0,0) is bottom-left
    _axs[0].set_title("Top Layer Elevation")
    _axs[0].set_xlabel("Column")
    _axs[0].set_ylabel("Row")
    _fig.colorbar(_im1, _ax=_axs[0], label="Elevation (ft)")

    # Plot the bottom layer elevation (Layer 40)
    _im2 = _axs[1].imshow(cfg.botm[-1], cmap="terrain", interpolation="nearest", origin="lower")  # 🔹 Ensures bottom-left
    _axs[1].set_title("Bottom Layer Elevation (Layer 40)")
    _axs[1].set_xlabel("Column")
    _axs[1].set_ylabel("Row")
    _fig.colorbar(_im2, _ax=_axs[1], label="Elevation (ft)")

    plt.tight_layout()
    plt.show()