@echo off
echo Defining user input
:: Define user inputs for preprocessing and initialization

:: HEC-RAS SPATIAL FILES
:: These files are used to define the spatial domain of the model and the initial conditions for the simulation.
set WATER_SURFACE_RASTER=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\GMS\WSE (Max).USGS_1m_FebApril2018_DEM.U_USGS-3DEP_dtm_hyrdo_flattened_20240412.2041_1.tif
set TERRAIN_RASTER=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\GMS\BlendedTerrain.LoweredTerrain.tif
set GW_DOMAIN_SHAPEFILE=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\InputShapefiles\GWDomain.shp
set LEFT_BOUNDARY_SHAPEFILE=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\InputShapefiles\L_FPL.shp
set RIGHT_BOUNDARY_SHAPEFILE=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\InputShapefiles\R_FPL.shp
set PROJECTION_FILE=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\RAS\GIS_Data\102739_TX_central.prj
set SAT_IMAGE_PATH=C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\CH00365\GMS\HighResOrtho\HighResOrtho_23Oct2014_Clip.tif

:: MODFLOW 6 and MODPATH 7 EXECUTABLES
:: These executables are used to run the MODFLOW 6 and MODPATH 7 models.
set MODFLOW6_EXE=C:\Users\u4eeevmq\Documents\Python\Flo_Py\flopy\modflowExe\mf6.exe
set MODPATH7_EXE=C:\Users\u4eeevmq\Documents\Python\Flo_Py\flopy\modflowExe\mp7.exe

:: SIMULATION PARAMETERS
:: These parameters define the simulation settings, including the simulation name, output directory, and units.
set SIM_NAME=Hyporheic_Project
set WORKSPACE=HP_workspace
set OUTPUT_FOLDER=Hyporheic_output
set LENGTH_UNITS=feet
set TIME_UNITS=days
set DIRECTION=Forward

:: MODEL PARAMETERS
:: These parameters define the cell length, width, height, and groundwater modeling depth.
set CELL_SIZE_X=5.0
set CELL_SIZE_Y=5.0
set Z=0.5
set GW_MOD_DEPTH=20.0

:: These parameters define the hydraulic conductivity, vertical hydraulic conductivity, groundwater offset, porosity, recharge interface, and recharge inflow face.
set KH=10.0
set KV=1.0
set GW_OFFSET=0.5
set POROSITY=0.1
set RCH_IFACE=6
set RCH_IFLOWFACE=-1
set RECHARGE_RATE=0.005

:: These parameters define the number of time steps, length of each time step, and time step multiplier.
set NSTP=1
set PERLEN=1.0
set TSMULT=1.0

:: DEBUGGING INPUT FILES
if not exist "%WATER_SURFACE_RASTER%" (
    echo Error: Water surface raster file not found!
    exit /b
)

if not exist "%TERRAIN_RASTER%" (
    echo Error: Terrain raster file not found!
    exit /b
)

if not exist "%GW_DOMAIN_SHAPEFILE%" (
    echo Error: Groundwater domain shapefile not found!
    exit /b
)

if not exist "%LEFT_BOUNDARY_SHAPEFILE%" (
    echo Error: Left boundary floodplain shapefile not found!
    exit /b
)

if not exist "%RIGHT_BOUNDARY_SHAPEFILE%" (
    echo Error: Right boundary floodplain shapefile not found!
    exit /b
)

if not exist "%PROJECTION_FILE%" (
    echo Error: Projection file not found!
    exit /b
)

if not exist "%MODFLOW6_EXE%" (
    echo Error: MODFLOW 6 executable not found!
    exit /b
)

if not exist "%MODPATH7_EXE%" (
    echo Error: MODPATH 7 executable not found!
    exit /b
)

echo Activating virtual environment...
call .\.venv\Scripts\activate

echo Running preprocessing and initialization notebooks with inputs...
papermill VQuintana/notebooks/preprocessing.ipynb VQuintana/notebooks/preprocessing.ipynb ^
    -p water_surface_elevation_raster "%WATER_SURFACE_RASTER%" ^
    -p terrain_elevation_raster "%TERRAIN_RASTER%" ^
    -p ground_water_domain_shapefile "%GW_DOMAIN_SHAPEFILE%" ^
    -p left_boundary_floodplain "%LEFT_BOUNDARY_SHAPEFILE%" ^
    -p right_boundary_floodplain "%RIGHT_BOUNDARY_SHAPEFILE%" ^
    -p projection_file "%PROJECTION_FILE%"

papermill VQuintana/notebooks/initialization.ipynb VQuintana/notebooks/initialization.ipynb ^
    -p md6_exe_path "%MODFLOW6_EXE%" ^
    -p md7_exe_path "%MODPATH7_EXE%" ^
    -p sim_name "%SIM_NAME%" ^
    -p workspace "%WORKSPACE%" ^
    -p length_units "%LENGTH_UNITS%" ^
    -p time_units "%TIME_UNITS%" ^
    -p cell_size_x %CELL_SIZE_X% ^
    -p cell_size_y %CELL_SIZE_Y% ^
    -p gw_mod_depth %GW_MOD_DEPTH% ^
    -p z %Z% ^
    -p kh %KH% ^
    -p kv %KV% ^
    -p gw_offset %GW_OFFSET% ^
    -p porosity %POROSITY% ^
    -p rch_iface %RCH_IFACE% ^
    -p rch_iflowface %RCH_IFLOWFACE% ^
    -p recharge_rate %RECHARGE_RATE% ^
    -p nstp %NSTP% ^
    -p perlen %PERLEN% ^
    -p tsmult %TSMULT%

:: Execute model domain notebook
papermill VQuintana/notebooks/model_domain.ipynb VQuintana/notebooks/model_domain.ipynb

:: Execute define boundary notebook
papermill VQuintana/notebooks/define_boundary.ipynb VQuintana/notebooks/define_boundary.ipynb

:: Execute boundary conditions notebook
papermill VQuintana/notebooks/boundary_conditions.ipynb VQuintana/notebooks/boundary_conditions.ipynb

:: Execute run models notebook
papermill VQuintana/notebooks/run_models.ipynb VQuintana/notebooks/run_models.ipynb ^
    -p output_folder "%OUTPUT_FOLDER%" ^
    -p direction "%DIRECTION%" ^
    -p sat_image_path "%SAT_IMAGE_PATH%" ^
    -p groundwater_domain_shp_path "%GW_DOMAIN_SHAPEFILE%" 

echo Deleting old build files and subdirectories...
del /Q C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\* 2>nul
for /D %%i in (C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\*) do rmdir /S /Q "%%i"

echo Ensuring .nojekyll file exists...
if not exist C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll (
    echo. > C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll
)

echo Building Jupyter Book...
jupyter-book build VQuintana\notebooks\

echo Copying files and folders to docs directory...
xcopy VQuintana\notebooks\_build\html\* C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs /E /H /C /I /Y

echo Model Ran, Notebook Built, and Move Complete!
