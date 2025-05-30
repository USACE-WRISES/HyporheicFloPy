from __future__ import annotations
"""
Hyporheic FloPy — PyQt5 GUI
───────────────────────────
• YAML editor (comment-preserving)
• Geometry tab – plan-view (Matplotlib + Flopy)
• Run tab      – runs __main__.py in a QThread
• Results tab  – placeholder for heads / PDF

Run →  python app_gui.py
"""
import sys, io, yaml, subprocess, traceback
from pathlib import Path
from collections import OrderedDict
from typing   import Dict, List, Tuple, Any
import os
import re

import numpy as np
from PyQt5 import QtCore, QtGui, QtWidgets

# ── Matplotlib / Flopy plotting
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import flopy.plot

from inputs import load as cfg_load
import functions.model_utils as mu

# ───────────────────────────────────────────────────────── paths
ROOT         = Path(__file__).resolve().parent
#PROJECT_ROOT = ROOT.parent
MAIN_PY      = ROOT / "__main__.py"
INPUTS_YAML  = ROOT / "inputs.yaml"
GWF_ROOT     = ROOT / "HP_workspace/gwf_workspace"
MP7_ROOT    = ROOT / "HP_workspace/mp7_workspace"

os.chdir(ROOT)  # Set the root path as the working directory



# ───────────────────────────────────────────────────────── YAML helpers
def _parse_yaml(path: Path) -> Tuple[
    Dict[str, str],
    OrderedDict[str, List[str]],
    Dict[str, str],
    Dict[str, int],
    List[str]
]:
    raw = path.read_text("utf-8").splitlines() if path.exists() else []
    try:
        typed: Dict[str, Any] = yaml.safe_load("\n".join(raw)) or {}
    except yaml.YAMLError:
        typed = {}

    sections: OrderedDict[str, List[str]] = OrderedDict()
    descs: Dict[str, str]  = {}
    line_map: Dict[str, int] = {}
    vals: Dict[str, str] = {}

    cur, divider, pending = "General", False, []
    for ln_no, ln in enumerate(raw):
        s = ln.lstrip()
        if s.startswith("#"):                                 # comment
            txt = s.lstrip("#").strip()
            if txt and all(ch == "-" for ch in txt):
                divider = True; continue
            if divider and txt:
                cur = txt; sections.setdefault(cur, []); divider = False; continue
            pending.append(txt); continue

        if ":" in ln and not ln.lstrip().startswith("-") and ln.count(":") == 1:
            key, rest = ln.split(":", 1)
            key = key.strip()
            inline = rest.split("#", 1)[1].strip() if "#" in rest else ""
            descs[key] = "\n".join([*pending, inline]).strip()
            sections.setdefault(cur, []).append(key)
            line_map[key] = ln_no
            raw_val = rest.split("#", 1)[0].strip() or str(typed.get(key, ""))
            vals[key] = raw_val
            pending.clear()
            continue
        pending.clear()

    for k, v in typed.items():
        vals.setdefault(k, str(v))

    return vals, sections, descs, line_map, raw

def _scalar_for_write(val: str) -> str:
    if val.lower() in {"true", "false"}:
        return val.lower()
    try:
        float(val); return val
    except ValueError:
        return val.strip()

# ───────────────────────────────────────────────────────── QThread runner
class Runner(QtCore.QThread):
    log_line    = QtCore.pyqtSignal(str)
    finished_ok = QtCore.pyqtSignal()

    def __init__(self, yaml_text: str):
        super().__init__()
        self.yaml_text = yaml_text            # stdin for __main__.py

    def run(self):
        cmd = [sys.executable, str(MAIN_PY), "--yaml-stdin"]
        proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", bufsize=1
        )
        proc.stdin.write(self.yaml_text); proc.stdin.close()
        for line in iter(proc.stdout.readline, ""):
            self.log_line.emit(line.rstrip())
        proc.wait()
        if proc.returncode == 0:
            self.finished_ok.emit()

# ───────────────────────────────────────────────────────── GWCanvas widget
class GWCanvas(QtWidgets.QWidget):
    """Plan-view MapView + layer navigator + rubber-band zoom."""
    def __init__(self, parent=None):
        super().__init__(parent)
        h = QtWidgets.QHBoxLayout(self); h.setContentsMargins(4, 4, 4, 4)

        # -- navigator / layer switches ---------------------------------
        ctl = QtWidgets.QVBoxLayout(); h.addLayout(ctl, 0)

        self.btn_load = QtWidgets.QPushButton("Create Geometry")
        ctl.addWidget(self.btn_load)

        self.timeseries = None          # list‑of‑recarrays (lazy‑loaded)
        self.btn_ts     = None          # will hold the “Show timeseries” button
        nav = QtWidgets.QHBoxLayout()
        self.btn_up   = QtWidgets.QToolButton(text="▲")
        self.btn_down = QtWidgets.QToolButton(text="▼")

        # >>> fixed-width QLineEdit (4 setters ← KEY FIX) <<<
        self.txt_k = QtWidgets.QLineEdit()
        self.txt_k.setMaxLength(4)
        self.txt_k.setFixedWidth(40)
        self.txt_k.setAlignment(QtCore.Qt.AlignCenter)
        # ----------------------------------------------------
        nav.addWidget(self.btn_up)
        nav.addWidget(self.txt_k)
        nav.addWidget(self.btn_down)
        ctl.addLayout(nav)

        self.btn_top    = QtWidgets.QPushButton("Top")
        self.btn_bottom = QtWidgets.QPushButton("Bottom")
        ctl.addWidget(self.btn_top); ctl.addWidget(self.btn_bottom)
        ctl.addSpacing(8)

        # layer toggles
        self.chk_terrain = QtWidgets.QCheckBox("Terrain");           self.chk_terrain.setChecked(True)
        self.chk_lfp     = QtWidgets.QCheckBox("Left FPL");  self.chk_lfp.setChecked(False)
        self.chk_rfp     = QtWidgets.QCheckBox("Right FPL"); self.chk_rfp.setChecked(False)
        self.chk_gwd     = QtWidgets.QCheckBox("GW domain");         self.chk_gwd.setChecked(False)
        self.chk_active  = QtWidgets.QCheckBox("Active Cells");      self.chk_active.setChecked(False)
        self.chk_bc      = QtWidgets.QCheckBox("BC cells");       self.chk_bc.setChecked(True)
        self.chk_heads   = QtWidgets.QCheckBox("Calc'd Heads") ; self.chk_heads.setChecked(False)
        self.chk_paths   = QtWidgets.QCheckBox("Calc'd Paths") ; self.chk_paths.setChecked(False)
                            
        for w in ( self.chk_terrain, self.chk_lfp, self.chk_rfp,
                   self.chk_gwd,     self.chk_active, self.chk_bc, self.chk_heads, self.chk_paths):
            ctl.addWidget(w)
            w.stateChanged.connect(lambda _=None: self._redraw())


        # --- timeseries popup button -----------------------------------------
        self.btn_ts = QtWidgets.QPushButton("Show timeseries…")
        ctl.addWidget(self.btn_ts)
        self.btn_ts.clicked.connect(self._show_timeseries)

        ctl.addSpacing(8)
        # zoom tools
        self.btn_zoom = QtWidgets.QPushButton("Zoom box"); self.btn_zoom.setCheckable(True)
        self.btn_full = QtWidgets.QPushButton("Zoom full")
        ctl.addWidget(self.btn_zoom); ctl.addWidget(self.btn_full)
        ctl.addStretch(1)

        # -- Matplotlib canvas -----------------------------------------
        self.fig = plt.Figure(figsize=(6, 6), dpi=100, constrained_layout=True)
        self.ax  = self.fig.add_subplot(1, 1, 1, aspect="equal")
        self.canvas = FigureCanvas(self.fig)
        h.addWidget(self.canvas, 1)

        # runtime
        self.model = None
        self.heads      = None   # 3‑D NumPy array (nlay, nrow, ncol)
        self.pathlines  = None   # list of Pathline objects
        self.nlay  = 0
        self.k     = 0
        self.ext_full: tuple[float, float, float, float] | None = None
        self.rb_origin: QtCore.QPoint | None = None
        self.rubber: QtWidgets.QRubberBand | None = None
        self.shp_paths: dict[str, str] = {}

        # signals
        self.btn_up.clicked.connect(lambda: self._step(-1))
        self.btn_down.clicked.connect(lambda: self._step(+1))
        self.txt_k.returnPressed.connect(self._jump)
        self.btn_top.clicked.connect(lambda: self._goto(0))
        self.btn_bottom.clicked.connect(lambda: self._goto(self.nlay - 1))
        self.btn_full.clicked.connect(self._zoom_full)
        for w in (
            self.chk_terrain, self.chk_lfp, self.chk_rfp,
            self.chk_gwd,     self.chk_active,
            self.chk_bc, self.chk_paths,                                          # ← add here
        ):
            w.stateChanged.connect(lambda _=None: self._redraw())

        # rubber-band mouse events
        self.canvas.mpl_connect("button_press_event",   self._on_press)
        self.canvas.mpl_connect("motion_notify_event",  self._on_move)
        self.canvas.mpl_connect("button_release_event", self._on_release)

    # ..................................................................
    # public API
    def set_model(
        self,
        gwf,
        *, heads: np.ndarray | None = None,
        shp_left="", shp_right="", shp_domain=""
    ):
        self.model     = gwf
        self.heads     = heads                 # may be None
        # remember where the .hds file lives  ⭐
        self._model_ws = Path(gwf.simulation.sim_path)
        self._model_nm = gwf.name

        self.nlay      = int(gwf.dis.nlay.data)
        self.k = 0
        self.txt_k.setValidator(QtGui.QIntValidator(1, self.nlay))
        self.shp_paths = {"left": shp_left, "right": shp_right, "domain": shp_domain}

        mg = gwf.modelgrid
        xmin, xmax, ymin, ymax = mg.extent        # tuple → four floats
        
        
        self.ext_full = (xmin, xmax, ymin, ymax)
        self._redraw()

    # ­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­­ NEW helper for one‑time debug pop‑ups
    def _debug_show_shapefile(self, shp_path: str, title: str) -> None:
        """Open *shp_path* in a separate figure once, for quick inspection."""
        import geopandas as gpd
        try:
            gdf = gpd.read_file(shp_path)
            if gdf.empty:
                print(f"[DEBUG] {title}: file has NO geometries.")
                return
            fig, ax = plt.subplots(figsize=(5, 5))
            gdf.plot(ax=ax, edgecolor="black", facecolor="none")
            ax.set_title(title)
            fig.show()
            print(f"[DEBUG] {title}: shown {len(gdf)} features.")
        except Exception as err:
            print(f"[DEBUG] {title}: could not open ({err})")

    # ..................................................................
    # navigation helpers
    def _step(self, d): self._goto(self.k + d)
    def _goto(self, k):
        if self.model and 0 <= k < self.nlay:
            self.k = k; self._redraw()
    def _jump(self):
        try: self._goto(int(self.txt_k.text()) - 1)
        except ValueError: pass

        # ────────────────────────────────────────────────────────────────
    def _ensure_heads_loaded(self) -> None:
        """Load heads from <ws>/<model>.hds if we don't have them yet."""
        if self.heads is not None or self._model_ws is None:
            return

        hfile = self._model_ws / f"{self._model_nm}.hds"
        if hfile.exists():
            try:
                self.heads = flopy.utils.HeadFile(hfile).get_data()
                print(f"[INFO] Heads loaded from {hfile}")
            except Exception as err:
                print(f"[WARN] Couldn’t read heads file: {err}")

    def _ensure_pathlines_loaded(self):
        """
        Lazy‑load MODPATH pathlines into self.pathlines (once).
        Assumes self.model.simulation.sim_path is the workspace.
        """
        if self.pathlines is not None:
            return                          # already cached
        try:
            from flopy.utils import PathlineFile
            ws = Path(MP7_ROOT)
            # look for *the* mp7 model in that workspace
            pl_files = list(ws.glob("*.mppth"))
            if not pl_files:
                print("[GUI] No .mppth pathline file found.")
                return
            pf = PathlineFile(pl_files[0])
            self.pathlines = pf.get_alldata()     # list of recarrays
            print(f"[GUI] Loaded {len(self.pathlines)} pathlines")
        except Exception as err:
            print(f"[GUI] Could not load pathlines: {err}")
            self.pathlines = None

    def _ensure_timeseries_loaded(self):
        """Cache the first *.timeseries file under MP7_ROOT in self.timeseries."""
        if self.timeseries is not None:               # already cached
            return

        from flopy.utils import TimeseriesFile
        ws = Path(MP7_ROOT)
        ts_files = list(ws.glob("*.timeseries"))
        if not ts_files:
            print("[GUI] No .timeseries file found in", ws)
            self.timeseries = None
            return

        try:
            tf = TimeseriesFile(ts_files[0])
            self.timeseries = tf.get_alldata()        # numpy structured array
            # print(f"[GUI] Loaded {self.timeseries.size:,} rows from {ts_files[0].name}")
        except Exception as err:
            print(f"[GUI] Could not read timeseries file: {err}")
            self.timeseries = None

    def _show_timeseries(self):
        """Open a modal dialog with the timeseries in a QTableWidget."""
        self._ensure_timeseries_loaded()

        if self.timeseries is None:
            QtWidgets.QMessageBox.information(self, "Timeseries",
                                            "No *.timeseries file could be loaded.")
            return

        data = self.timeseries           # numpy recarray
        cols = data[0].dtype.names

        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("MODPATH timeseries")
        dlg.resize(800, 600)

        table = QtWidgets.QTableWidget(parent=dlg)
        table.setColumnCount(len(cols))
        table.setRowCount(len(data))
        table.setHorizontalHeaderLabels(cols)
        

        # populate —‑ this is fast enough for O(10⁴) rows
        for row, rec in enumerate(data):
            for col, name in enumerate(cols):
                item = QtWidgets.QTableWidgetItem(str(rec[name]))
                item.setFlags(item.flags() ^ QtCore.Qt.ItemIsEditable)  # read‑only
                table.setItem(row, col, item)

        lay = QtWidgets.QVBoxLayout(dlg)
        lay.addWidget(table)
        dlg.exec()                       # modal – blocks until user closes


    def _redraw(self):
        """Refresh the plan‑view map for the current layer `self.k`."""
        import os, geopandas as gpd, numpy as np
        from pathlib import Path

        if not self.model:
            return


        # keep current zoom
        keep_xlim, keep_ylim = self.ax.get_xlim(), self.ax.get_ylim()
        has_zoom = keep_xlim != (0.0, 1.0) and keep_ylim != (0.0, 1.0)

        self.txt_k.setText(str(self.k + 1))
        self.ax.clear()

        mv = flopy.plot.PlotMapView(model=self.model, layer=self.k, ax=self.ax)

        # ─── heads overlay (load lazily if needed) ──────────────────────────
        if self.chk_heads.isChecked():
            self._ensure_heads_loaded()

        if self.chk_heads.isChecked() and self.heads is not None:
            h_arr = np.ma.masked_where(
                self.model.dis.idomain.array[self.k] == 0,
                self.heads[self.k],
            )
            # coloured raster
            mv.plot_array(h_arr, cmap="viridis", alpha=0.65, zorder=5)

            # black contour lines – draw straight on the Axes
            # modelgrid.extent -> [xmin, xmax, ymin, ymax]
            xmin, xmax, ymin, ymax = self.model.modelgrid.extent
            levels = np.linspace(h_arr.min(), h_arr.max(), 10)
            self.ax.contour(
                h_arr,
                origin="upper",
                extent=[xmin, xmax, ymin, ymax],
                levels=levels,
                colors="k",
                linewidths=0.4,
                zorder=6,
            )

        # ─── Calc'd Pathlines ───────────────────────────────────────────────
        if self.chk_paths.isChecked():
            self._ensure_pathlines_loaded()

        if self.chk_paths.isChecked() and self.pathlines:
            # Plot pathlines for the current layer only; use layer="all"
            # if you prefer a single 2‑D projection
            mv.plot_pathline(
                self.pathlines,
                layer="all",#self.k,#"all",
                colors=["purple"],
                lw=1.5,
                alpha=0.6,
                zorder=7,
            )

        # 1) terrain raster
        if self.chk_terrain.isChecked():
            mv.plot_array(self.model.dis.top.array, cmap="terrain", alpha=0.5, zorder=1)

        # 2) grid outlines
        mv.plot_grid(linewidth=0.25, color="0.4", alpha=0.4, zorder=2)

        # 3) domain fill – active vs all cells
        if self.chk_active.isChecked():
            mv.plot_ibound(zorder=3)  # active only
        else:
            full = np.ones_like(self.model.dis.idomain.array[self.k], dtype=float)
            mv.plot_array(full, cmap="Greys", alpha=0.15, zorder=3)

        # 4) BC cells – controlled by new checkbox
        if self.chk_bc.isChecked():
            for key in ("riv", "chd", "ghb", "wel"):
                if self.model.get_package(key):
                    mv.plot_bc(key.upper(), zorder=4)

        # ── helper: plot shapefile through Flopy, with CRS fix ─────────────
        def _draw_shape(obj, *, _tag: str, **style):
            """
            Draw *obj* on self.ax.

            Order of attempts
              1. mv.plot_shapefile(path_or_gdf)
              2. mv.plot_shapes(shapefile.Reader(path))
              3. GeoPandas gdf.plot(…)

            Always re‑projects GeoDataFrames to the model‑grid CRS first.
            """
            if obj is None:
                return

            import geopandas as gpd, shapefile, os
            from pathlib import Path, PurePath

            grid_epsg = self.model.modelgrid.epsg
            grid_crs  = f"EPSG:{grid_epsg}" if grid_epsg else self.model.modelgrid.proj4

            try:
                # ───────── acquire a GeoDataFrame OR a path ─────────────
                gdf, shp_path = None, None

                if isinstance(obj, (str, os.PathLike, PurePath)):
                    shp_path = Path(obj).expanduser().resolve()
                    if shp_path.suffix.lower() != ".shp" or not shp_path.exists():
                        print(f"[DEBUG] {_tag}: invalid shapefile → {shp_path}")
                        return
                    # # one‑time raw pop‑up
                    # flag = f"_shown_{_tag.replace(' ', '_')}"
                    # if not getattr(self, flag, False):
                    #     self._debug_show_shapefile(str(shp_path), f"{_tag} – raw shapefile")
                    #     setattr(self, flag, True)
                    # # read for CRS check / possible reprojection
                    gdf = gpd.read_file(shp_path)

                elif isinstance(obj, gpd.GeoDataFrame):
                    gdf = obj.copy()

                else:
                    print(f"[WARN] {_tag}: unsupported type {type(obj)}")
                    return

                # ───────── CRS alignment (if we have a gdf) ─────────────
                if gdf is not None and gdf.crs is not None and str(gdf.crs) != str(grid_crs):
                    gdf = gdf.to_crs(grid_crs)

                # ───────── 1) mv.plot_shapefile ─────────────────────────
                try:
                    mv.plot_shapefile(gdf if gdf is not None else shp_path, **style)
                    return
                except Exception as err:
                    print(f"[DEBUG] {_tag}: plot_shapefile failed → {err}")

                # ───────── 2) mv.plot_shapes via PyShp ──────────────────
                try:
                    if shp_path is None:
                        # need a .shp path on disk; write gdf to a temp file
                        with Path(self.model.modelname).with_suffix(".tmp.shp").as_posix() as tmp:
                            gdf.to_file(tmp)
                            shp_path = Path(tmp)
                    with shapefile.Reader(str(shp_path)) as rdr:
                        mv.plot_shapes(rdr, **style)
                        return
                except Exception as err:
                    print(f"[DEBUG] {_tag}: plot_shapes failed → {err}")

                # ───────── 3) final GeoPandas fallback ──────────────────
                if gdf is not None:
                    gdf.plot(ax=self.ax, **style)

            except Exception as err:
                print(f"[WARN] {_tag}: total failure → {err}")

        # 5) optional shapefile overlays
        if self.chk_lfp.isChecked():
            _draw_shape(self.shp_paths.get("left"),   _tag="left_fp",
                        edgecolor="red",   facecolor="none", linewidth=5.0, zorder=10)
        if self.chk_rfp.isChecked():
            _draw_shape(self.shp_paths.get("right"),  _tag="right_fp",
                        edgecolor="orange", facecolor="none", linewidth=5.0, zorder=10)
        if self.chk_gwd.isChecked():
            _draw_shape(self.shp_paths.get("domain"), _tag="gw_domain",
                        edgecolor="magenta", facecolor="none", linewidth=1.5, zorder=9)

        # restore zoom
        if has_zoom:
            self.ax.set_xlim(keep_xlim); self.ax.set_ylim(keep_ylim)

        self.ax.set_title(f"Plan view – layer {self.k + 1}")
        self.canvas.draw_idle()

    # ..................................................................
    # zoom – full
    def _zoom_full(self):
        if self.ext_full:
            xmin, xmax, ymin, ymax = self.ext_full
            self.ax.set_xlim(xmin, xmax); self.ax.set_ylim(ymin, ymax)
            self.canvas.draw_idle()

    # ..................................................................
    # rubber-band callbacks
    def _on_press(self, ev):
        if not (self.btn_zoom.isChecked() and ev.inaxes is self.ax): return
        self.rb_origin = ev.guiEvent.pos()
        self.rubber = QtWidgets.QRubberBand(QtWidgets.QRubberBand.Rectangle,
                                            self.canvas)
        self.rubber.setGeometry(QtCore.QRect(self.rb_origin, QtCore.QSize()))
        self.rubber.show()

    def _on_move(self, ev):
        if self.rubber and self.rb_origin:
            cur = ev.guiEvent.pos()
            self.rubber.setGeometry(QtCore.QRect(self.rb_origin, cur).normalized())

    def _on_release(self, ev):
        """Finish a rubber‑band zoom and rescale the axes."""
        if not self.rubber:            # user clicked without dragging
            return

        # --- grab the rectangle in canvas‑pixel (widget) coordinates ----------
        rb = self.rubber.geometry()

        # tear down the rubber‑band
        self.rubber.hide()
        self.rubber.deleteLater()
        self.rubber = None

        # --- widget → data‑space conversion -----------------------------------
        inv = self.ax.transData.inverted()
        h   = self.canvas.height()      # needed to flip Y

        # Qt origin (0,0) is top‑left; Matplotlib display origin is bottom‑left
        x0, y0 = inv.transform((rb.left(),  h - rb.bottom()))   # bottom‑left
        x1, y1 = inv.transform((rb.right(), h - rb.top()))      # top‑right

        # ignore clicks that produce a zero‑area box
        if abs(x1 - x0) > 1e-6 and abs(y1 - y0) > 1e-6:
            self.ax.set_xlim(min(x0, x1), max(x0, x1))
            self.ax.set_ylim(min(y0, y1), max(y0, y1))
            self.canvas.draw_idle()

        # reset the toolbar button
        self.btn_zoom.setChecked(False)

# ───────────────────────────────────────────────────────── Main window
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hyporheic FloPy — GUI"); self.resize(1000, 800)

        self.tabs = QtWidgets.QTabWidget(); self.setCentralWidget(self.tabs)
        self.tabs.addTab(self._build_setup(),  "Setup")
        self.tabs.addTab(self._build_geom(),   "Viewer")
        self.tabs.addTab(self._build_run(),    "Run")

    # .............................................................. setup
    def _build_setup(self):
        # parse the default YAML
        vals, sections, descs, lm, raw = _parse_yaml(INPUTS_YAML)
        self._yaml_raw, self._line_map, self._yaml_path = raw, lm, INPUTS_YAML

        # helper dicts
        self._widgets: Dict[str, QtWidgets.QLineEdit] = {}
        self._section_boxes: Dict[str, QtWidgets.QFormLayout] = {}
        self._labels: Dict[str, QtWidgets.QLabel] = {}

        # function to add one row, with optional Browse… for any “filepath”
        def _add_row(sec: str, key: str, value: str, helper: str):
            # create (or fetch) the section’s form
            if sec not in self._section_boxes:
                box = QtWidgets.QGroupBox(sec)
                form = QtWidgets.QFormLayout(box)
                self._section_boxes[sec] = form
                self._setup_vlay.addWidget(box)
            else:
                form = self._section_boxes[sec]

            # label
            lbl_text = f"{key} ({helper})" if helper else key
            lbl = QtWidgets.QLabel(lbl_text)
            lbl.setToolTip(helper)
            self._labels[key] = lbl

            # line edit
            le = QtWidgets.QLineEdit(value)
            le.setToolTip(helper)
            self._widgets[key] = le

            # if the helper mentions “filepath”, give it a Browse… button
            if "filepath" in helper.lower():
                container = QtWidgets.QWidget()
                hl = QtWidgets.QHBoxLayout(container)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.addWidget(le)
                btn = QtWidgets.QPushButton("...")
                btn.setFixedWidth(36)

                def _browse():
                    # optional extension filter from “[tif]” in helper
                    m = re.search(r"\[([A-Za-z0-9]+)\]", helper)
                    filt = "All Files (*)"
                    if m:
                        ext = m.group(1)
                        filt = f"{ext.upper()} (*.{ext});;All Files (*)"
                    path, _ = QtWidgets.QFileDialog.getOpenFileName(
                        self, f"Select {key}", "", filt
                    )
                    if path:
                        le.setText(path)

                btn.clicked.connect(_browse)
                hl.addWidget(btn)
                form.addRow(lbl, container)
            else:
                form.addRow(lbl, le)

        # build the scrollable form
        area = QtWidgets.QScrollArea()
        area.setWidgetResizable(True)
        self._setup_inner = QtWidgets.QWidget()
        self._setup_vlay = QtWidgets.QVBoxLayout(self._setup_inner)

        for sec, keys in sections.items():
            for k in keys:
                _add_row(sec, k, vals.get(k, ""), descs.get(k, ""))

        self._setup_vlay.addStretch(1)
        area.setWidget(self._setup_inner)

        # bottom buttons
        bt_open   = QtWidgets.QPushButton("Open…")
        bt_save   = QtWidgets.QPushButton("Save")
        bt_saveas = QtWidgets.QPushButton("Save as…")
        h = QtWidgets.QHBoxLayout()
        h.addWidget(bt_open)
        h.addWidget(bt_save)
        h.addWidget(bt_saveas)
        h.addStretch()

        page = QtWidgets.QWidget()
        lay = QtWidgets.QVBoxLayout(page)
        lay.addWidget(area)
        lay.addLayout(h)

        bt_open.clicked.connect(self._yaml_open)
        bt_save.clicked.connect(self._yaml_save)
        bt_saveas.clicked.connect(self._yaml_save_as)

        return page


    # helper I/O
    def _yaml_open(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open YAML", str(self._yaml_path.parent), "YAML (*.yaml *.yml)"
        )
        if not path:
            return

        vals, sections, descs, lm, raw = _parse_yaml(Path(path))
        self._yaml_raw, self._line_map, self._yaml_path = raw, lm, Path(path)

        # if a key wasn’t in the form yet, add it (with Browse support)
        def _add_if_missing(sec: str, key: str):
            if key in self._widgets:
                return
            # make the section/form if needed
            if sec not in self._section_boxes:
                box = QtWidgets.QGroupBox(sec)
                form = QtWidgets.QFormLayout(box)
                self._section_boxes[sec] = form
                # insert just before the final stretch
                self._setup_vlay.insertWidget(self._setup_vlay.count() - 1, box)
            else:
                form = self._section_boxes[sec]

            lbl = QtWidgets.QLabel()
            self._labels[key] = lbl
            le = QtWidgets.QLineEdit()
            self._widgets[key] = le

            helper = descs.get(key, "")
            lbl_text = f"{key} ({helper})" if helper else key
            lbl.setText(lbl_text)
            lbl.setToolTip(helper)
            le.setToolTip(helper)

            if "filepath" in helper.lower():
                container = QtWidgets.QWidget()
                hl = QtWidgets.QHBoxLayout(container)
                hl.setContentsMargins(0, 0, 0, 0)
                hl.addWidget(le)
                btn = QtWidgets.QPushButton("...")
                btn.setFixedWidth(36)

                def _browse():
                    m = re.search(r"\[([A-Za-z0-9]+)\]", helper)
                    filt = "All Files (*)"
                    if m:
                        ext = m.group(1)
                        filt = f"{ext.upper()} (*.{ext});;All Files (*)"
                    p, _ = QtWidgets.QFileDialog.getOpenFileName(
                        self, f"Select {key}", "", filt
                    )
                    if p:
                        le.setText(p)

                btn.clicked.connect(_browse)
                hl.addWidget(btn)
                form.addRow(lbl, container)
            else:
                form.addRow(lbl, le)

        # ensure every key in the new YAML has a widget
        for sec, keys in sections.items():
            for k in keys:
                _add_if_missing(sec, k)

        # now update all values and labels
        for k, le in self._widgets.items():
            le.setText(vals.get(k, ""))
            helper = descs.get(k, "")
            le.setToolTip(helper)
            lbl = self._labels[k]
            txt = f"{k} ({helper})" if helper else k
            lbl.setText(txt)
            lbl.setToolTip(helper)


    def _yaml_save(self):
        lines = self._yaml_raw.copy()
        for k, w in self._widgets.items():
            val = _scalar_for_write(w.text())
            if k not in self._line_map or self._line_map[k] >= len(lines):
                self._line_map[k] = len(lines); lines.append(f"{k}: {val}"); continue
            idx = self._line_map[k]; pre, rest = lines[idx].split(":", 1)
            before, *cmt = rest.split("#", 1); indent = " " if before.startswith(" ") else ""
            lines[idx] = f"{pre}:{indent}{val}" + (f"  # {cmt[0].strip()}" if cmt else "")
        self._yaml_path.write_text("\n".join(lines) + "\n", "utf-8")
        QtWidgets.QMessageBox.information(self, "Saved", f"Wrote {self._yaml_path}")

    def _yaml_save_as(self):
        """Save to a **new file** chosen by the user and switch the session
        to that file afterwards."""
        fn, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save YAML as…", str(self._yaml_path.parent),
            "YAML (*.yaml *.yml)"
        )
        if not fn:
            return                                   # user cancelled

        # remember the new location, then delegate to the normal saver
        self._yaml_path = Path(fn)
        self._yaml_save()

    def _yaml_text(self) -> str:
        lines = self._yaml_raw.copy()
        for k, w in self._widgets.items():
            val = _scalar_for_write(w.text())
            if k not in self._line_map or self._line_map[k] >= len(lines):
                self._line_map[k] = len(lines); lines.append(f"{k}: {val}"); continue
            idx = self._line_map[k]; pre, rest = lines[idx].split(":", 1)
            before, *cmt = rest.split("#", 1); indent = " " if before.startswith(" ") else ""
            lines[idx] = f"{pre}:{indent}{val}" + (f"  # {cmt[0].strip()}" if cmt else "")
        return "\n".join(lines) + "\n"

    def _busy(self, on: bool):
        if on:
            self._overlay.raise_()           # bring to front
        self._overlay.setVisible(on)
        # QtWidgets.QApplication.setOverrideCursor(
        #     QtCore.Qt.WaitCursor if on else QtCore.Qt.ArrowCursor)
        QtWidgets.QApplication.processEvents()      # paint immediately


    def eventFilter(self, obj, event):
        # keep the overlay the same size as the geometry page
        if obj is getattr(self, "_geom_page", None) and event.type() == QtCore.QEvent.Resize:
            if hasattr(self, "_overlay"):
                self._overlay.setGeometry(self._geom_page.rect())
        return super().eventFilter(obj, event)

    # .............................................................. geometry
    def _build_geom(self):
        page = QtWidgets.QWidget()
        self._geom_page = page        # ← keep a reference for the event‑filter
        h    = QtWidgets.QHBoxLayout(page); h.setContentsMargins(0, 0, 0, 0)

        # the canvas (unchanged)
        self.view = GWCanvas()
        h.addWidget(self.view, 1)
        self.view.btn_load.clicked.connect(self._geom_load)

        # ── overlay ------------------------------------------------------
        self._overlay = QtWidgets.QWidget(page)
        self._overlay.setStyleSheet(
            "background-color: rgba(120,120,120,150);"     # grey + 60 % alpha
            "color: white; font: bold 16px 'Segoe UI';"
        )
        self._overlay.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self._overlay.hide()

        ov_l = QtWidgets.QVBoxLayout(self._overlay)
        ov_l.setAlignment(QtCore.Qt.AlignCenter)
        ov_l.addWidget(QtWidgets.QLabel("Loading – please wait…"))

        # make sure the overlay always fills the page
        self._overlay.setGeometry(page.rect())
        page.installEventFilter(self)                     # see § 2

        return page

    def _geom_load(self):

        self._busy(True)                     # ← show overlay & hour‑glass
        try:
            cfg = cfg_load(io.StringIO(self._yaml_text()))
            cfg.setup_projection(); cfg.setup_terrain(cfg.hec_ras_crs)
            cfg.setup_water_surface(cfg.hec_ras_crs); cfg.setup_vectors()
            mu.build_full_grid(cfg)

            idomain, chd = mu.prepare_idomain_and_chd(cfg)
            _, gwf = mu.build_gwf_model(cfg, chd, idomain)

            # ── try to load the last head file ───────────────────────
            hfile = Path(cfg.workspace_path) / f"{gwf.name}.hds"
            heads = None
            if hfile.exists():
                try:
                    heads = flopy.utils.HeadFile(hfile).get_data()
                except Exception as err:
                    print(f"[INFO] Couldn’t read heads ({err}) – continuing without.")

            self.view.set_model(
                gwf,
                heads      = heads,
                shp_left   = cfg.left_boundary_floodplain,
                shp_right  = cfg.right_boundary_floodplain,
                shp_domain = cfg.ground_water_domain_shapefile,
            )

        except Exception as exc:
            QtWidgets.QMessageBox.critical(
                self, "Geometry build failed",
                f"{exc}\n\n{traceback.format_exc(limit=1)}")

        finally:
            self._busy(False)                # ← always hide overlay

    # .............................................................. run tab
    def _build_run(self):
        page = QtWidgets.QWidget(); v = QtWidgets.QVBoxLayout(page)
        h = QtWidgets.QHBoxLayout()
        self.bt_start = QtWidgets.QPushButton("Start run")
        self.bt_stop  = QtWidgets.QPushButton("Stop"); self.bt_stop.setEnabled(False)
        h.addWidget(self.bt_start); h.addWidget(self.bt_stop); h.addStretch()
        v.addLayout(h)

        self.txt_log = QtWidgets.QPlainTextEdit(); self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QtGui.QFont("Consolas", 10))
        v.addWidget(self.txt_log)

        self.bt_start.clicked.connect(self._run_start); self.bt_stop.clicked.connect(self._run_stop)
        return page

    def _run_start(self):
        self.bt_start.setEnabled(False); self.bt_stop.setEnabled(True); self.txt_log.clear()
        self.runner = Runner(self._yaml_text())
        self.runner.log_line.connect(self.txt_log.appendPlainText)
        self.runner.finished_ok.connect(lambda: self.bt_start.setEnabled(True))
        self.runner.finished_ok.connect(lambda: self.bt_stop.setEnabled(False))
        self.runner.start()

    def _run_stop(self):
        if hasattr(self, "runner") and self.runner.isRunning():
            self.runner.terminate(); self.bt_stop.setEnabled(False)
            self.txt_log.appendPlainText("⚠️  Stop requested…")

    # .............................................................. results stub
    def _build_results(self):
        page = QtWidgets.QWidget(); v = QtWidgets.QVBoxLayout(page)
        v.addWidget(QtWidgets.QLabel("Results tab placeholder", alignment=QtCore.Qt.AlignCenter))
        return page

# ───────────────────────────────────────────────────────── entry-point
def main():
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = MainWindow(); win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
