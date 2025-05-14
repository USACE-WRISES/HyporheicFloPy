"""
inputs.py – Centralised configuration, spatial layers & runtime helpers
------------------------------------------------------------------------
Importing this module provides:

* **cfg** – a `Settings` instance validated by Pydantic and initialised via
  `cfg.setup_workspace()`. Run extra helpers when needed:

    * `cfg.setup_projection()` – read `projection_file` and create
      `hec_ras_crs`.
    * `cfg.setup_terrain(target_crs)` – re‑project the terrain raster and add
      terrain‑related attributes.
    * `cfg.setup_water_surface(target_crs)` – re‑project the water‑surface
      raster **and** crop it to the terrain extent.

* Vector layers (`ground_water_domain`, `left_boundary`, `right_boundary`) in
  the project CRS as soon as you import.

Typical workflow
----------------
```python
from inputs import cfg

cfg.setup_projection()                  # => cfg.hec_ras_crs
cfg.setup_terrain(cfg.hec_ras_crs)      # => cfg.terrain_output_raster, etc.
cfg.setup_water_surface(cfg.hec_ras_crs)  # => cfg.cropped_water_surface_raster
```
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional, Any, List, Union, TextIO, IO
import io
from pydantic import field_validator, ValidationInfo

import yaml
from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    PositiveInt,
    ValidationError,
)

# raster / gis deps (import lazily where possible)
import geopandas as gpd
import rasterio
from pyproj import CRS

# ---------------------------------------------------------------------
# 1.  Data model (Pydantic v2) with built‑in defaults
# ---------------------------------------------------------------------
class Settings(BaseModel):
    class Config:                       # legacy name
        arbitrary_types_allowed = True
        extra = "allow"              # no extra fields allowed

    # ── spatial input paths ────────────────────────────────────────────────
    water_surface_elevation_raster: Optional[Path] = None
    terrain_elevation_raster:       Optional[Path] = None
    ground_water_domain_shapefile:  Optional[Path] = None
    left_boundary_floodplain:       Optional[Path] = None
    right_boundary_floodplain:      Optional[Path] = None
    projection_file:                Optional[Path] = None  # text CRS

    # ── executables ────────────────────────────────────────────────────────
    md6_exe_path: Path = Path("./modflowExe/mf6.exe")
    md7_exe_path: Path = Path("./modflowExe/mp7.exe")

    # ── simulation meta ────────────────────────────────────────────────────
    sim_name: str = "Hyporheic_Project"
    workspace: str = "HP_workspace"
    length_units: str = Field("feet", pattern="^(feet|meters)$")
    time_units: str = Field("days", pattern="^(days|seconds)$")

    # ── grid / domain constants ───────────────────────────────────────────
    cell_size_x: PositiveFloat = 10.0
    cell_size_y: PositiveFloat = 10.0
    gw_mod_depth: PositiveFloat = 20.0
    z: PositiveFloat = 0.5

    # ── hydraulic parameters ──────────────────────────────────────────────
    kh: PositiveFloat = 10.0
    kv: PositiveFloat = 1.0
    gw_offset: PositiveFloat = 0.5
    porosity: PositiveFloat = Field(0.1, le=0.6)
    rch_iface: int = 6
    rch_iflowface: int = -1
    recharge_rate: PositiveFloat = 0.005

    # ── stress‑period / timestep ──────────────────────────────────────────
    nper: PositiveInt = 1
    nstp: PositiveInt = 1
    perlen: PositiveFloat = 1.0
    tsmult: PositiveFloat = 1.0

    # ── runtime‑generated variables (populated by helpers / notebooks) ────
    hec_ras_crs: Optional[Any] = None

    # workspace & file names
    gwf_name: Optional[str] = None
    mp7_name: Optional[str] = None
    gwf_ws: Optional[str] = None
    mp7_ws: Optional[str] = None
    headfile: Optional[str] = None
    head_filerecord: Optional[List[str]] = None
    budgetfile: Optional[str] = None
    budget_filerecord: Optional[List[str]] = None

    # ── terrain raster attributes ─────────────────────────────────────────
    terrain_elevation: Optional[Any] = None          # MaskedArray
    raster_transform: Optional[Any] = None           # Affine (orig)
    raster_crs: Optional[Any] = None                 # CRS (orig)
    raster_bounds_box: Optional[Any] = None          # shapely Polygon
    transform: Optional[Any] = None                  # Affine (re-projected)
    bed_elevation: Optional[Any] = None              # float32 or array
    raster_width: Optional[float] = None
    raster_height: Optional[float] = None
    ncol: Optional[int] = None
    nrow: Optional[int] = None
    top: Optional[Any] = None                        # MaskedArray
    nlay: Optional[int] = None
    terrain_output_raster: Optional[str] = None
    xmin: Optional[float] = None
    xmax: Optional[float] = None
    ymin: Optional[float] = None
    ymax: Optional[float] = None
    grid_rotation_degrees: Optional[float] = None

    # ── grid arrays & points ──────────────────────────────────────────────
    grid_x: Optional[Any] = None                     # ndarray
    grid_y: Optional[Any] = None                     # ndarray
    grid_points: Optional[gpd.GeoDataFrame] = None
    intersecting_points: Optional[gpd.GeoDataFrame] = None
    xorigin: Optional[float] = None
    yorigin: Optional[float] = None
    tops: Optional[List[Any]] = None                 # list of arrays
    botm: Optional[List[Any]] = None                 # list of arrays

    # ── water‑surface raster attrs ────────────────────────────────────────
    surface_elevation: Optional[Any] = None          # MaskedArray
    ws_transform: Optional[Any] = None               # Affine (orig)
    ws_raster_crs: Optional[Any] = None              # CRS (orig)
    water_surface_output_raster: Optional[str] = None
    cropped_water_surface_raster: Optional[str] = None

    # ── vector layers ─────────────────────────────────────────────────────
    project_crs: Any = "EPSG:4326"
    ground_water_domain: Optional[gpd.GeoDataFrame] = None
    left_boundary: Optional[gpd.GeoDataFrame] = None
    right_boundary: Optional[gpd.GeoDataFrame] = None
    cropped_output_raster: Optional[str] = None

    # ── flags ─────────────────────────────────────────────────────────────
    write: bool = False
    run: bool = False
    plot: bool = False
    plot_show: bool = False
    plot_save: bool = False

    # helper
    workspace_path: Path | None = None

    # ------------------------------------------------------------------
    # Helper attributes (set internally)
    # ------------------------------------------------------------------
    workspace_path: Path | None = None

    # ── runtime flags / artefacts ───────────────────────────────────
    results_ready: bool = False                   # << NEW <<
    gwf_sim: Optional[Any] = None                 # optional, handy for Results
    gwf_model: Optional[Any] = None             # optional, handy for Results
    app_running: bool = False                  # << NEW <<
    inputs_yaml_file: Optional[Path] = None                 # << NEW <<

    # inside class Settings  ────────────────────────────────────────────────
    @field_validator(
        "water_surface_elevation_raster",
        "terrain_elevation_raster",
        "ground_water_domain_shapefile",
        "left_boundary_floodplain",
        "right_boundary_floodplain",
        "projection_file",
        "md6_exe_path",
        "md7_exe_path",
        mode="before",
    )
    @classmethod
    def _resolve_rel_paths(cls, v, info: ValidationInfo) -> Path:            # noqa: N805
        """
        Convert strings → Path **only for the fields above** and make them
        absolute relative to the directory that contains *inputs.yaml*.
        """
        if v is None:
            return v

        p = Path(v) if not isinstance(v, Path) else v
        if p.is_absolute():
            return p

        cfg_dir: Path = info.context["cfg_dir"]
        return (cfg_dir / p).resolve()

    # ---------------------------- METHODS -----------------------------
    def setup_workspace(self, clean: bool = True) -> None:
        """Prepare folders, filenames, and toggle flags."""
        # 1. Workspace directory
        self.workspace_path = Path(self.workspace)
        if clean and self.workspace_path.exists():
            shutil.rmtree(self.workspace_path)
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # 2. Model names (≤16 chars)
        self.gwf_name = self.gwf_name or "gwf_model"
        self.mp7_name = self.mp7_name or "mp7_model"

        # 3. Sub‑workspaces
        gwf_ws_path = Path(self.gwf_ws) if self.gwf_ws else self.workspace_path / "gwf_workspace"
        mp7_ws_path = Path(self.mp7_ws) if self.mp7_ws else self.workspace_path / "mp7_workspace"
        gwf_ws_path.mkdir(exist_ok=True)
        mp7_ws_path.mkdir(exist_ok=True)
        self.gwf_ws = str(gwf_ws_path)
        self.mp7_ws = str(mp7_ws_path)

        # 4. Output file names
        self.headfile = self.headfile or f"{self.gwf_name}.hds"
        self.head_filerecord = self.head_filerecord or [self.headfile]
        self.budgetfile = self.budgetfile or f"{self.gwf_name}.cbb"
        self.budget_filerecord = self.budget_filerecord or [self.budgetfile]

        # 5. Env flags
        try:
            from modflow_devtools.misc import get_env  # preferred
        except ImportError:
            def get_env(name: str, default: bool | str):
                raw = os.getenv(name)
                if raw is None:
                    return default
                return str(raw).lower() in ("1", "true", "yes", "y")
        for flag in ("write", "run", "plot", "plot_show", "plot_save"):
            setattr(self, flag, get_env(flag.upper(), getattr(self, flag)))

    # -----------------------------------------------------------------
    def setup_projection(self) -> None:
        if not self.projection_file or not Path(self.projection_file).exists():
            raise FileNotFoundError("projection_file path is missing or does not exist.")
        self.hec_ras_crs = CRS.from_string(Path(self.projection_file).read_text().strip())
        print(f"Loaded HEC‑RAS CRS: {self.hec_ras_crs}")
    # -----------------------------------------------------------------
    def setup_terrain(self, target_crs: Any, output_name: str | None = None) -> None:
        """Load and re‑project the *terrain_elevation_raster*.

        Parameters
        ----------
        target_crs : rasterio CRS or anything accepted by rasterio (e.g. "EPSG:...")
            CRS to re‑project into (usually HEC‑RAS CRS).
        output_name : str, optional
            Filename to write inside the workspace. Defaults to
            'reprojected_terrain_raster.tif'.
        """
        if not self.terrain_elevation_raster or not Path(self.terrain_elevation_raster).exists():
            raise FileNotFoundError("terrain_elevation_raster path is missing or does not exist.")

        import numpy as np  # local import to avoid heavy deps at top
        from rasterio.warp import calculate_default_transform, reproject, Resampling

        output_name = output_name or "reprojected_terrain_raster.tif"
        output_path = Path(self.workspace_path or ".") / output_name

        with rasterio.open(self.terrain_elevation_raster) as src:
            self.terrain_elevation = src.read(1)
            self.raster_transform = src.transform
            self.raster_crs = src.crs

            dst_transform, width, height = calculate_default_transform(
                self.raster_crs, target_crs, src.width, src.height, *src.bounds
            )
            self.transform = dst_transform

            new_meta = src.meta.copy()
            new_meta.update({
                "crs": target_crs,
                "transform": dst_transform,
                "width": width,
                "height": height,
            })

            with rasterio.open(output_path, "w", **new_meta) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=self.raster_transform,
                    src_crs=self.raster_crs,
                    dst_transform=dst_transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                )

        self.terrain_output_raster = str(output_path)
        print(f"Reprojected terrain raster saved as {output_path}")
    # -----------------------------------------------------------------
    def setup_water_surface(self, target_crs: Any, output_name: str | None = None) -> None:
        """Re-project the water-surface raster and crop it to the terrain extent.

        Requires
        --------
        * `self.water_surface_elevation_raster`  – path to the input WSE raster.
        * `self.transform` (set by `setup_terrain`) – so we know the terrain extent.

        Side effects
        ------------
        * Saves `<workspace>/reprojected_water_surface_raster.tif`
          (or *output_name* if supplied).
        * Saves `<workspace>/cropped_water_surface_raster.tif`.
        * Populates these attributes:
          `surface_elevation`, `ws_transform`, `ws_raster_crs`,
          `water_surface_output_raster`, `cropped_water_surface_raster`.
        """
        if not self.water_surface_elevation_raster or not Path(self.water_surface_elevation_raster).exists():
            raise FileNotFoundError("water_surface_elevation_raster is missing or cannot be found.")
        if self.transform is None:
            raise RuntimeError("Run setup_terrain() first so the terrain extent is available.")

        from rasterio.warp import calculate_default_transform, reproject, Resampling
        from rasterio.mask import mask
        from shapely.geometry import box

        ws_output = Path(self.workspace_path or ".") / (output_name or "reprojected_water_surface_raster.tif")
        cropped_output = Path(self.workspace_path or ".") / "cropped_water_surface_raster.tif"

        # ── Step 1: re-project WSE raster to target CRS ───────────────────────
        with rasterio.open(self.water_surface_elevation_raster) as src:
            self.surface_elevation = src.read(1)
            self.ws_transform = src.transform
            self.ws_raster_crs = src.crs

            dst_transform, width, height = calculate_default_transform(
                self.ws_raster_crs, target_crs, src.width, src.height, *src.bounds
            )

            meta = src.meta.copy()
            meta.update({"crs": target_crs, "transform": dst_transform, "width": width, "height": height})

            with rasterio.open(ws_output, "w", **meta) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=self.ws_transform,
                    src_crs=self.ws_raster_crs,
                    dst_transform=dst_transform,
                    dst_crs=target_crs,
                    resampling=Resampling.nearest,
                )

        self.water_surface_output_raster = str(ws_output)
        print(f"Reprojected water-surface raster saved as {ws_output}")

        # ── Step 2: crop to terrain extent -----------------------------------
        # Use the bounds of the (already re-projected) terrain raster
        if not self.terrain_output_raster or not Path(self.terrain_output_raster).exists():
            raise RuntimeError("Terrain raster not yet created; run setup_terrain() first.")

        with rasterio.open(self.terrain_output_raster) as terrain_src:
            terrain_bounds = terrain_src.bounds
            terrain_geom = box(*terrain_bounds)

        with rasterio.open(ws_output) as src:
            out_image, out_transform = mask(src, [terrain_geom], crop=True)
            out_meta = src.meta.copy()
            out_meta.update(
                {
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                }
            )

            with rasterio.open(cropped_output, "w", **out_meta) as dst:
                dst.write(out_image)

        self.cropped_water_surface_raster = str(cropped_output)
        print(f"Cropped water-surface raster saved as {cropped_output}")
    # -----------------------------------------------------------------    
    def setup_vectors(self) -> None:
        ## Load and reproject shapefiles to match the raster CRS
        """Derive project CRS (from WSE raster if available) and load shapefiles."""
        # 1) Determine project CRS if not already set by projection/terrain
        if self.hec_ras_crs:
            self.project_crs = self.hec_ras_crs
        elif self.water_surface_elevation_raster and Path(self.water_surface_elevation_raster).exists():
            try:
                with rasterio.open(self.water_surface_elevation_raster) as src:
                    self.project_crs = src.crs
            except Exception as exc:  # noqa: BLE001
                print("⚠️  Could not read CRS; defaulting to EPSG:4326", exc)
        else:
            self.project_crs = "EPSG:4326"

        # 2) Load shapefiles
        def _load(path: Optional[Path | str]):
            if path and Path(path).exists():
                return gpd.read_file(path).to_crs(self.project_crs)
            return gpd.GeoDataFrame()

        self.ground_water_domain = _load(self.ground_water_domain_shapefile)
        self.left_boundary = _load(self.left_boundary_floodplain)
        self.right_boundary = _load(self.right_boundary_floodplain)
        print("Vector layers loaded and re-projected to", self.project_crs)


# ---------------------------------------------------------------------
# 2.  Loader helper & eager workspace setup
# ---------------------------------------------------------------------

def _find_inputs_yaml(start: Path) -> Path:
    """Walk up from *start* until we hit inputs.yaml or filesystem root."""
    cur = start.resolve()
    while cur != cur.parent:  # stop at root
        candidate = cur / "inputs.yaml"
        if candidate.exists():
            return candidate
        cur = cur.parent
    raise FileNotFoundError("inputs.yaml not found up the directory tree.")


def _load_from_mapping(data: dict, cfg_dir: Path) -> Settings:
    """Common helper – validates and returns a Settings object."""
    cfg = Settings.model_validate(data, context={"cfg_dir": cfg_dir})
    cfg.setup_workspace()
    return cfg


def load(source: Union[str, Path, IO[str]] | None = None,
         *,
         inputs_yaml_file: str | None = None) -> Settings:
    """
    Load *source* and return a validated :class:`Settings`.

    Parameters
    ----------
    source
        • ``Path`` / str pointing to a YAML file **or**  
        • an open *text* file-like object (``StringIO``, ``sys.stdin`` …) **or**  
        • a YAML *string* (must contain at least one newline).
    inputs_yaml_file
        Kept for backward-compatibility – overrides *source* when given.
    """
    # ----------- decide what kind of thing we received ----------------
    if inputs_yaml_file is not None:
        source = Path(inputs_yaml_file)

    # 1) file-like object  ------------------------------------------------
    if isinstance(source, io.IOBase) and not isinstance(source, (str, Path)):
        text = source.read()
        data = yaml.safe_load(text) or {}
        cfg_dir = Path.cwd()
        return _load_from_mapping(data, cfg_dir)

    # 2) raw YAML string  -------------------------------------------------
    if isinstance(source, str) and "\n" in source and not Path(source).exists():
        data = yaml.safe_load(source) or {}
        cfg_dir = Path.cwd()
        return _load_from_mapping(data, cfg_dir)

    # 3) path-like (old behaviour)  --------------------------------------
    if source is None:
        # keep the previous path-resolution logic …
        #   (beside this file → walk up from CWD → etc.)
        # < existing code that finds *path* >
        path = _find_inputs_yaml(Path.cwd())
    else:
        path = Path(source).expanduser().resolve()

    yaml_dir = path.parent
    data = yaml.safe_load(path.read_text()) or {}
    return _load_from_mapping(data, yaml_dir)

# eager-load cfg on import... keep it all blanked until we call setup_workspace()
cfg: Settings = Settings()

# ---------------------------------------------------------------------
# 3.  Public API/Exports
# ---------------------------------------------------------------------
__all__ = [
    "cfg",
]
