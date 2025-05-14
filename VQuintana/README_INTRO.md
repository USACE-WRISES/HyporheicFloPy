# Hyporheic Project

## Overview

The **Hyporheic Project** automates the integration of surface‑water outputs from **HEC‑RAS** into groundwater flow models built with **FloPy / MODFLOW 6**. By streamlining the hand‑off between river hydraulics and groundwater simulation, the project makes coupled surface‑groundwater modelling faster to learn, easier to reproduce, and more useful for ecological assessments—particularly those focused on the hyporheic zone.

### Why the hyporheic zone matters

The hyporheic zone—the thin, dynamic interface where river water and groundwater mix—supports nutrient cycling, temperature buffering, and critical habitat for aquatic organisms. Making it straightforward to include surface‑water drivers in MODFLOW helps researchers and practitioners **quantify those ecological benefits**, not just describe them qualitatively.

## Project goals

1. **Streamline data processing** • Pre‑process HEC‑RAS outputs (rasters, shapefiles, tables) into MODFLOW‑ready inputs.
2. **Automate model initialisation** • Generate MODFLOW 6 packages and directory structures with a single call.
3. **Simulate groundwater flow** • Run transient or steady simulations that honour time‑varying river stages.
4. **Visualise & analyse results** • Provide ready‑made plotting helpers (contours, time‑series, cross‑sections).
5. **Integrate particle tracking** • Launch MODPATH 7 runs from flow outputs, then analyse travel times and paths.
6. **Quantify ecological benefits** • Translate model outputs into metrics relevant to nutrient cycling, habitat suitability, and restoration outcomes.

## Repository layout
```
HyporheicFloPy/
├── inputs.yaml          # project‑specific paths & parameters
├── hypmod/              # core Python package
│   ├── __init__.py
│   ├── __main__.py      # `python -m hypmod` entry point
│   ├── pipeline.py      # orchestrates the numbered steps
│   ├── step01_preprocessing.py
│   ├── step02_initialization.py
│   ├── … etc …
│   └── common_imports.py
├── notebooks/           # Jupyter notebooks (examples generating plots)
└── README.md            # you are here
```

## Workflow summary

Below is the high‑level sequence implemented in `hypmod.pipeline` (and mirrored in the notebooks):

| Step                       | Purpose                                                                |
| -------------------------- | ---------------------------------------------------------------------- |
| **1  Pre‑processing**      | Load HEC‑RAS rasters, re‑project, clean, & format for MODFLOW.         |
| **2  Initialisation**      | Set up folder structure, executables, base grid, and package defaults. |
| **3  Model domain**        | Define vertical layering & domain extent from terrain DEM.             |
| **4  Define boundaries**   | Build boundary polygons and masks; clip grid.                          |
| **5  Boundary conditions** | Assign head, flux, recharge, and river packages.                       |
| **6  (Opt.) Wells**        | Insert extraction / injection wells (if provided).                     |
| **7  (Opt.) Nodes**        | Add internal observation nodes or SSM entries.                         |
| **8  Run models**          | Execute MODFLOW 6 then MODPATH 7; monitor convergence.                 |
| **9  Quantify benefits**   | Post‑process flow & particle outputs into ecological metrics.          |

Each step can be executed from the corresponding notebook **or** via a single command:
```bash
python -m hypmod --cfg inputs.yaml
```

## Getting started

1. **Clone** the repository and create a virtual environment.
2. **Install** requirements: `pip install -r requirements.txt`.
3. **Edit** `inputs.yaml` to point at your HEC‑RAS rasters & shapefiles.
4. **Run** the full pipeline: `python -m hypmod` (or run notebooks in order).

## Citation

If you use this workflow in academic or professional work, please cite:

> *Your Name*. (2025). *Hyporheic Project: Automated coupling of HEC‑RAS and MODFLOW 6 for groundwater–surface‑water interaction studies.* Version X.Y. Zenodo. DOI:xx.xxxx/zenodo.xxxxxx

---

*Last updated: 28 April 2025*
