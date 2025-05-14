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

# %% [markdown] papermill={"duration": 0.003094, "end_time": "2025-04-09T19:18:08.357582", "exception": false, "start_time": "2025-04-09T19:18:08.354488", "status": "completed"}
# # Flood Plain Boundaries and Groundwater Domain

# %% papermill={"duration": 3.094286, "end_time": "2025-04-09T19:18:11.455801", "exception": false, "start_time": "2025-04-09T19:18:08.361515", "status": "completed"} tags=["hide-input"]
# Import Libraries
# %run /Users/u4eeevmq/Documents/Python/HyporheicFloPy/VQuintana/common_imports.py

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

# %% papermill={"duration": 0.014196, "end_time": "2025-04-09T19:18:11.471997", "exception": false, "start_time": "2025-04-09T19:18:11.457801", "status": "completed"}
#--------------------------- Define Flood Plain Boundaries -----------------------------#
## Extract the first (start) and last (end) coordinates from each boundary geometry
left_start = left_boundary.geometry.iloc[0].coords[0]  # First point
left_end = left_boundary.geometry.iloc[-1].coords[-1]  # Last point

right_start = right_boundary.geometry.iloc[0].coords[0]  # First point
right_end = right_boundary.geometry.iloc[-1].coords[-1]  # Last point

## Print start and end coordinates
print(f"Left Boundary Start: {left_start}, Left Boundary End: {left_end}")
print(f"Right Boundary Start: {right_start}, Right Boundary End: {right_end}")

## Upstream boundary coordinates (use left and right start points)
upstream_start_x, upstream_start_y = left_start  # Start of upstream from left boundary
upstream_end_x, upstream_end_y = right_start  # End of upstream from right boundary

## Downstream boundary coordinates (use left and right end points)
downstream_start_x, downstream_start_y = left_end  # Start of downstream from left boundary
downstream_end_x, downstream_end_y = right_end  # End of downstream from right boundary

## Print extracted coordinates
print(f"Upstream Start: ({upstream_start_x}, {upstream_start_y}), Upstream End: ({upstream_end_x}, {upstream_end_y})")
print(f"Downstream Start: ({downstream_start_x}, {downstream_start_y}), Downstream End: ({downstream_end_x}, {downstream_end_y})")

## Use the extracted start and end points
upstream_line = LineString([(upstream_start_x, upstream_start_y), (upstream_end_x, upstream_end_y)])
downstream_line = LineString([(downstream_start_x, downstream_start_y), (downstream_end_x, downstream_end_y)])

## Convert to GeoDataFrame
upstream_boundary = gpd.GeoDataFrame(geometry=[upstream_line], crs=left_boundary.crs)
downstream_boundary = gpd.GeoDataFrame(geometry=[downstream_line], crs=left_boundary.crs)

## Print boundary lines
print(f"Upstream Line: {upstream_line}")
print(f"Downstream Line: {downstream_line}")

## Check if boundaries were created successfully
if not upstream_boundary.empty and not downstream_boundary.empty:
    print("✅ Upstream and Downstream boundaries created successfully!")
else:
    print("❌ Error: One or both boundaries are empty. Check input data.")

# %% papermill={"duration": 0.518779, "end_time": "2025-04-09T19:18:11.992791", "exception": false, "start_time": "2025-04-09T19:18:11.474012", "status": "completed"}
#--------------------------- Define Active Cells using Groundwater Domain -----------------------------#
## Define grid cell polygons based on grid resolution
grid_cells = []
for row in range(nrow):
    for col in range(ncol):
        x_min = grid_x[row, col] - (cell_size_x / 2)
        x_max = grid_x[row, col] + (cell_size_x / 2)
        y_min = grid_y[row, col] - (cell_size_y / 2)
        y_max = grid_y[row, col] + (cell_size_y / 2)
        grid_cells.append(Polygon([(x_min, y_min), (x_min, y_max), (x_max, y_max), (x_max, y_min)]))

## Convert to GeoDataFrame
grid_gdf = gpd.GeoDataFrame(geometry=grid_cells, crs=ground_water_domain.crs)

## Perform Spatial Join
grid_gdf["inside_domain"] = grid_gdf.geometry.intersects(ground_water_domain.unary_union)

## Initialize IDOMAIN array
idomain = np.zeros((nlay, nrow, ncol), dtype=int)

## Assign active cells where grid intersects groundwater domain
for idx, inside in enumerate(grid_gdf["inside_domain"]):
    row, col = divmod(idx, ncol)  # Convert flat index to row, col
    if inside:
        idomain[:, row, col] = 1  # Mark as active

## Debugging: Print active/inactive cell count
print(f"✅ Total Active Cells: {np.sum(idomain == 1)}")
print(f"✅ Total Inactive Cells: {np.sum(idomain == 0)}")

# %% papermill={"duration": 0.413578, "end_time": "2025-04-09T19:18:12.409019", "exception": false, "start_time": "2025-04-09T19:18:11.995441", "status": "completed"} tags=["hide-input"]
# Store new variables
# %store left_start
# %store left_end
# %store right_start
# %store right_end
# %store upstream_start_x
# %store upstream_start_y
# %store upstream_end_x
# %store upstream_end_y
# %store downstream_start_x
# %store downstream_start_y
# %store downstream_end_x
# %store downstream_end_y
# %store upstream_line
# %store downstream_line
# %store upstream_boundary
# %store downstream_boundary
# %store grid_cells
# %store grid_gdf
# %store idomain
