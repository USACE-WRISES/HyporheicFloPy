#code that runs when you do  python -m hypmod


# %%
import os
import sys, pathlib
from pathlib import Path
import textwrap

# ── 1.  Tell Python where the repo lives ──────────────────────────────
_project_root = Path(__file__).resolve().parents[1]   # → …/HyporheicFloPy
sys.path.insert(0, str(_project_root))                # make it importable

import pkg_resources, pprint, sys, pathlib
# print("sys.path   -->"); pprint.pprint(sys.path[:5], width=120)
# print("found at   -->", pkg_resources.get_provider("functions").module_path)
# print("directory  -->", pathlib.Path(pkg_resources.get_provider("functions").module_path).parent)

# ───────────────────────────────────────────────────────── paths
ROOT         = Path(__file__).resolve().parent
#PROJECT_ROOT = ROOT.parent
MAIN_PY      = ROOT / "__main__.py"
INPUTS_YAML  = ROOT / "inputs.yaml"
GWF_ROOT     = ROOT / "HP_workspace/gwf_workspace"
MP7_ROOT    = ROOT / "HP_workspace/mp7_workspace"

os.chdir(ROOT)  # Set the root path as the working directory

print("Starting model run.")

from functions import path_utils as pu
from functions import raster_utils as ru
from functions import report_utils as reu
from functions import model_utils as mu

project_root = pu.find_project_root(pathlib.Path(__file__).parent)
sys.path.append(str(project_root))

from VQuintana.common_imports_for_main import *

# Only the first run actually downloads; later calls are near-instant
pu.download_modflow()                 # or download_modflow("some/other/folder")

# Then add the folder to PATH for this Python session
pu.add_modflow_executables()          # same folder default

# ––– let the user tweak the YAML before we import it ––––––––––––––––

from inputs import cfg
from tabulate import tabulate

# ── 2.  Load the YAML file (or read from STDIN) ────────────────────────
import argparse, io, sys
from inputs import cfg, load          # load() already returns a Settings obj

parser = argparse.ArgumentParser()
parser.add_argument("--yaml",       help="Path to YAML file (default inputs.yaml)")
parser.add_argument("--yaml-stdin", action="store_true",
                    help="Read YAML contents from STDIN")
args = parser.parse_args()

# print("Arguments passed to the script:")
# for arg, value in vars(args).items():
#     print(f"{arg}: {value}")

if args.yaml_stdin:
    yaml_source = io.StringIO(sys.stdin.read())
    print("YAML Source Content:")
    print(yaml_source.getvalue())
    cfg = load(yaml_source)          # load() already handles file-like objs
    # cfg = load(sys.stdin)          # just hand the stream to load()
else:
    # fall back to a path (explicit or default)
    cfg = load(Path(project_root) / "inputs.yaml")



# ... after you load cfg ...
pu.print_config_table(cfg, max_value_width=80)


# %%
## HEC-RAS Projection File
cfg.setup_projection()
### NOTE: If the projection file is not available, the CRS can be defined manually here.
# %%
cfg.setup_terrain(cfg.hec_ras_crs)

# %%
cfg.setup_water_surface(cfg.hec_ras_crs)

# %% papermill={"duration": 0.165627, "end_time": "2025-04-09T19:17:47.064495", "exception": false, "start_time": "2025-04-09T19:17:46.898868", "status": "completed"}
cfg.setup_vectors()


# %% #------------------------------Model Grid--------------------------------#

# -----------------------------------------------------------------------------
# 1. Load & mask terrain raster
# -----------------------------------------------------------------------------
_arr, _tfm, _crs, _nodata, _bounds_box = ru.load_raster(cfg.terrain_output_raster)
_terrain = ru.mask_nodata(_arr, _nodata)

# -----------------------------------------------------------------------------
# 2. Raster extent & grid dimensions
# -----------------------------------------------------------------------------
_xmin, _ymin, _xmax, _ymax = ru.raster_extent(_tfm, _arr.shape[1], _arr.shape[0])
_width_ft  = _xmax - _xmin
_height_ft = _ymax - _ymin

_ncol, _nrow = ru.grid_dimensions(_width_ft, _height_ft,
                                 cfg.cell_size_x, cfg.cell_size_y)
print(f"Number of columns: {_ncol}")
print(f"Number of rows   : {_nrow}")

# -----------------------------------------------------------------------------
# 3. Build grid & GeoDataFrame of cell centres
# -----------------------------------------------------------------------------
_grid_x, _grid_y = ru.generate_grid_centres(_ncol, _nrow,
                                          cfg.cell_size_x, cfg.cell_size_y,
                                          _xmin, _ymin)
_grid_points = ru.grid_to_geodataframe(_grid_x, _grid_y, _crs)

# -----------------------------------------------------------------------------
# 4. Initialise model-layer arrays (top & botm)
# -----------------------------------------------------------------------------
_top = np.full((_nrow, _ncol), np.nan)

for _i in range(_nrow):
    for _j in range(_ncol):
        # Convert cell centre to raster indices
        _col, _row = ~_tfm * (_grid_x[_i, _j], _grid_y[_i, _j])
        _col, _row = int(_col), int(_row)

        if 0 <= _row < _terrain.shape[0] and 0 <= _col < _terrain.shape[1]:
            _top[_i, _j] = _terrain[_row, _col]

# Fill holes via nearest-neighbour interpolation
_top = ru.interpolate_na(np.ma.masked_invalid(_top))

# First layer bottom (bed elevation)
_bed_elevation = float(_terrain.min())
_first_botm    = np.full_like(_top, _bed_elevation)

# Subsequent layers (constant thickness cfg.z)
_tops  = [_top]
_botms = [_first_botm]

for _ in range(1, 40):
    _next_top  = _botms[-1]
    _next_botm = _next_top - cfg.z
    _tops.append(_next_top)
    _botms.append(_next_botm)

print("Top layer elevation (max, min):", _tops[0].max(), _botms[0].min())
print("Bottom layer (40) (max, min)  :", _tops[-1].max(), _botms[-1].min())

# -----------------------------------------------------------------------------
# 5. Persist results back to cfg
# -----------------------------------------------------------------------------
cfg.raster_transform   = _tfm
cfg.raster_crs         = _crs
cfg.raster_bounds_box  = _bounds_box
cfg.terrain_elevation  = _terrain
cfg.bed_elevation      = _bed_elevation

cfg.ncol, cfg.nrow     = _ncol, _nrow
cfg.grid_x, cfg.grid_y = _grid_x, _grid_y
cfg.grid_points        = _grid_points
cfg.intersecting_points = _grid_points[_grid_points.geometry.intersects(_bounds_box)]

cfg.xmin, cfg.ymin, cfg.xmax, cfg.ymax = _xmin, _ymin, _xmax, _ymax

cfg.top   = _top
cfg.tops  = _tops
cfg.botm  = _botms
cfg.nlay  = len(_tops)

# # -----------------------------------------------------------------------------
# # 6. Quick visual check
# # -----------------------------------------------------------------------------

# reu.start_report("results.pdf", append=False) # create/append PDF in cwd

# # -------------------------------------------------------------------
# # Grid-point preview ─ with cropped WSE raster underlay
# # -------------------------------------------------------------------
# with reu.page(title="Grid centres – domain extent", show=False) as pg:
#     reu.add_text(
#         pg,
#         "Grid-cell centres over the cropped water-surface raster.\n"
#         "The view is clipped to the groundwater-domain envelope.",
#         fontsize=11,
#     )

#     # Envelope to zoom to
#     if not cfg.ground_water_domain.empty:
#         xmin, ymin, xmax, ymax = cfg.ground_water_domain.total_bounds
#     else:                                           # fallback
#         xmin, ymin, xmax, ymax = _xmin, _ymin, _xmax, _ymax

#     # --- main figure ------------------------------------------------
#     with reu.fig_stacked(pg, "Cell centres (zoomed)",
#                          array_shape=_grid_x.shape) as ax:

#         # ── 1.  Under-lay : cropped WSE raster ──────────────────────
#         import rasterio
#         with rasterio.open(cfg.cropped_water_surface_raster) as src:
#             img = src.read(1, masked=True)
#             tfm = src.transform
#             ras_extent = [
#                 tfm.c,                          # min-x
#                 tfm.c + src.width * tfm.a,      # max-x
#                 tfm.f + src.height * tfm.e,     # min-y  (note: tfm.e is negative)
#                 tfm.f,                          # max-y
#             ]
#         ax.imshow(
#             img,
#             extent=ras_extent,
#             cmap="terrain",
#             origin="upper",     # matches raster orientation
#             alpha=0.6,
#         )

#         # ── 2.  Domain outline ──────────────────────────────────────
#         if not cfg.ground_water_domain.empty:
#             cfg.ground_water_domain.boundary.plot(
#                 ax=ax, color="black", linewidth=1.2, label="domain outline"
#             )

#         # ── 3.  Grid points ─────────────────────────────────────────
#         cfg.grid_points.plot(
#             ax=ax,
#             markersize=5,
#             color="tab:blue",
#             alpha=0.65,
#             label="cell centre",
#         )

#         # final touches
#         ax.set_xlim(xmin, xmax)
#         ax.set_ylim(ymin, ymax)
#         ax.set_aspect("equal")
#         ax.set_xlabel("Easting")
#         ax.set_ylabel("Northing")
#         ax.legend(loc="upper right")

# # -------------------------------------------------------------------
# # Stack-up: top & bottom layers share all the remaining space equally
# # -------------------------------------------------------------------
# with reu.page(title="Top vs. Bottom (stacked)") as pg:
#     # 1) Caption (flows like any other text block)
#     reu.add_text(pg,
#                  "Vertical comparison of the first and last model layers.",
#                  fontsize=11)
#     top_of_plots = pg._cursor_y            # free space starts here

#     gs = pg.add_gridspec(
#         2, 1,
#         left   = 0.05,
#         right  = 0.95,
#         top    = top_of_plots,             # start exactly where cursor is
#         bottom = 0.05,                     # keep bottom margin
#         hspace = 0.15
#     )

#     # 3) Draw the two plots
#     ax1 = pg.add_subplot(gs[0, 0])
#     ax2 = pg.add_subplot(gs[1, 0])

#     im1 = ax1.imshow(_top, cmap="terrain", origin="lower")
#     ax1.set_title("Top layer elevation")
#     pg.colorbar(im1, ax=ax1, label="ft")

#     im2 = ax2.imshow(_botms[-1], cmap="terrain", origin="lower")
#     ax2.set_title("Bottom layer elevation (L40)")
#     pg.colorbar(im2, ax=ax2, label="ft")

#     # 4) Tell the flow-layout that we’ve consumed all remaining space
#     #    (so the next add_text / fig_stacked would force a new page).
#     pg._cursor_y = 0.03                    # a hair above bottom margin

#%% DEFINE BOUNDARIES, BCS, RIVER CELLS, AND CHD DATA
# ──────────────────────────────────────────────────────────────────────
# Domain & boundary analysis  (generic helpers live in model_utils)
# ──────────────────────────────────────────────────────────────────────
upstream_bd, downstream_bd = mu.make_up_down_stream(cfg.left_boundary,
                                                    cfg.right_boundary, _crs)

grid_polys = mu.build_grid_polygons(_grid_x, _grid_y,
                                    cfg.cell_size_x, cfg.cell_size_y, _crs)
_idomain   = mu.idomain_from_domain(grid_polys, cfg.ground_water_domain,
                                    cfg.nlay, _nrow, _ncol)

# ---------------------------------------------------------------------
# 1.  Boundary-cell discovery & classification
# ---------------------------------------------------------------------
_boundary_cells  = mu.identify_boundary_cells(_idomain)
_boundary_groups = mu.classify_boundary_cells_fast(
    _boundary_cells,
    grid_polys,
    {
        "left":  cfg.left_boundary,
        "right": cfg.right_boundary,
        "up":    upstream_bd,
        "down":  downstream_bd,
    },
    _ncol,
)

# ---------------------------------------------------------------------
# 2.  River-stage sampling from the cropped WSE raster
# ---------------------------------------------------------------------
csv_df = mu.csv_points_elevation(cfg.grid_points,
                                 cfg.cropped_water_surface_raster)

csv_df = mu.fit_csv_to_grid(csv_df, _ncol, _nrow, _xmin, _ymin, _xmax, _ymax)

total_pts          = len(cfg.grid_points)          # every cell centre
pts_in_wse_raster  = len(csv_df)                   # only those that

river_cells = mu.extract_river_cells(
    csv_df,            # DataFrame with x_transformed / y_transformed / elevation
    _idomain,          # 3-D active-cell mask
    cfg.tops,             # list of top-of-layer arrays   (len == cfg.nlay)
    cfg.botm             # list of bottom-of-layer arrays
)
pts_in_river_cells = len(river_cells)             # only those that

# -------------------------------------------------------------------
# Grid-point preview ─ with cropped WSE raster underlay + river cells
# -------------------------------------------------------------------
# with reu.page(title="Grid centres – domain extent", show=False) as pg:
#     reu.add_text(
#         pg,
#         f"Grid-cell centres overlaid on the cropped water-surface raster.\n"
#         f"Red dots are the {len(river_cells):,} cells that receive "
#         "river-stage particles.",
#         fontsize=11,
#     )

#     # Envelope to zoom to
#     if not cfg.ground_water_domain.empty:
#         xmin, ymin, xmax, ymax = cfg.ground_water_domain.total_bounds
#     else:                                           # fallback
#         xmin, ymin, xmax, ymax = _xmin, _ymin, _xmax, _ymax

#     # ── main figure ────────────────────────────────────────────────
#     with reu.fig_stacked(pg, "Cell centres (zoomed)",
#                          array_shape=_grid_x.shape) as ax:

#         # 1) Under-lay : cropped WSE raster
#         import rasterio
#         with rasterio.open(cfg.cropped_water_surface_raster) as src:
#             img = src.read(1, masked=True)
#             tfm = src.transform
#             ras_extent = [
#                 tfm.c,                         # min-x
#                 tfm.c + src.width  * tfm.a,    # max-x
#                 tfm.f + src.height * tfm.e,    # min-y  (tfm.e < 0)
#                 tfm.f,                         # max-y
#             ]
#         ax.imshow(img, extent=ras_extent, cmap="terrain",
#                   origin="upper", alpha=0.6)

#         # 2) Domain outline
#         if not cfg.ground_water_domain.empty:
#             cfg.ground_water_domain.boundary.plot(
#                 ax=ax, color="black", linewidth=1.2, label="domain outline"
#             )

#         # 3) Grid-cell centres
#         cfg.grid_points.plot(
#             ax=ax, markersize=5, color="tab:blue",
#             alpha=0.65, label="cell centre"
#         )

#         # 4) River-cell overlay  (convert (k,i,j,…) → x,y)
#         xs = [_grid_x[i, j] for (_, i, j, _) in river_cells]
#         ys = [_grid_y[i, j] for (_, i, j, _) in river_cells]
#         ax.scatter(xs, ys, s=18, color="red", edgecolor="k",
#                    label="river-stage cell", zorder=3)

#         # Final touches
#         ax.set_xlim(xmin, xmax)
#         ax.set_ylim(ymin, ymax)
#         ax.set_aspect("equal")
#         ax.set_xlabel("Easting")
#         ax.set_ylabel("Northing")
#         ax.legend(loc="upper right")

# ---------------------------------------------------------------------
# 3.  Boundary-head interpolation
# ---------------------------------------------------------------------
max_up   = csv_df.elevation.max()      # highest surface-water elevation
max_down = csv_df.elevation.min()      # lowest  “      ”        ”
_offset  = cfg.gw_offset               # user-chosen offset below surface WSE

heads = {
    # bank-to-bank gradient (upstream → downstream) interpolated along each side
    "left":  mu.interpolate_gw_elevation(
                 [c for c in _boundary_groups["left"]  if c[0] == 0],
                 max_up   + _offset,
                 max_down + _offset,
                 cfg.nlay),

    "right": mu.interpolate_gw_elevation(
                 [c for c in _boundary_groups["right"] if c[0] == 0],
                 max_up   + _offset,
                 max_down + _offset,
                 cfg.nlay),

    # upstream / downstream faces get uniform heads
    "up":    [max_up   + _offset] * len(_boundary_groups["up"]),
    "down":  [max_down + _offset] * len(_boundary_groups["down"]),
}

# ---------------------------------------------------------------------
# 4.  Constant-head list for the CHD package
# ---------------------------------------------------------------------
chd_data = mu.build_chd_data(river_cells, _boundary_groups, heads)

print("\n─────────────────────────────────────────────────────────────")
print("📊  Boundary / river-cell summary")
print("─────────────────────────────────────────────────────────────")
print(f"Left-bank    cells : {len(_boundary_groups['left'])}")
print(f"Right-bank   cells : {len(_boundary_groups['right'])}")
print(f"Up-stream    cells : {len(_boundary_groups['up'])}")
print(f"Down-stream  cells : {len(_boundary_groups['down'])}")
print(f"River stage  cells : {len(river_cells)}")
print("─────────────────────────────────────────────────────────────")
print(f"✅ Assigned   {len(chd_data)} unique CHD rows\n")

# ──────────────────────────────────────────────────────────────────────
# Build  ➜  write  ➜  run  ➜  plot
#     (nothing in model_utils prints; logging stays in **main**)
# ──────────────────────────────────────────────────────────────────────
print("\nBuilding MODFLOW-6 groundwater-flow model …")
_gwf_sim, _gwf_model = mu.build_gwf_model(cfg, chd_data, _idomain)
print("✅ GWF container ready.")

print("Building MODPATH 7 forward / backward particle-tracking models …")
mp_fwd, mp_back = mu.build_particle_models(cfg.sim_name, _gwf_model, river_cells)
print("✅ MODPATH 7 models ready.")

# _gwf_sim.set_all_data_external(binary=True)
_gwf_sim.simulation_data.auto_set_sizes = False
_gwf_sim.simulation_data.verify_data = False
_gwf_sim.simulation_data.lazy_io=True

# ---------- write input files ----------------------------------------
print("\n┌─ Writing all input files ──────────────────────────────────────")
mu.write_models(_gwf_sim, mp_fwd, mp_back, silent=False)
print("└─ Files written into:", cfg.workspace_path)

# ---------- run the models -------------------------------------------
print("\n┌─ Running simulations – this can take a while ──────────────────")
mu.run_models(_gwf_sim, mp_fwd, silent=False) #mp_fwd, 
print("└─ All simulations finished.\n")

# ---------- post-processing / plots ----------------------------------
#print("Plotting groundwater-flow results …")
#mu.plot_gwf_all(_gwf_sim)

# reu.finish_report()  # Close the report PDF

# If you later want to process / plot MODPATH results:
# mu.plot_modpath7_results(f"{cfg.sim_name}_mp_forward",
#                          f"{cfg.sim_name}_mp_backward",
#                          ws=str(cfg.mp7_ws), gwf=gwf_model)
#print("Finished modeling")

#%%
# print("Launching interactive head browser (close window to continue)…")
# interactive modal dialog – lets you explore every layer

# if not cfg.app_running:
#     mu.interactive_head_viewer(_gwf_sim)  # blocks until closed

cfg.gwf_sim = _gwf_sim
cfg.results_ready = True
cfg.gwf_model = _gwf_model

# serialize gwf_sim so the GUI can reopen it
from joblib import dump
artifact_dir = Path(cfg.workspace_path or ".")
dump(_gwf_sim, artifact_dir / "gwf_sim.joblib")

print("Finished")
# %%
