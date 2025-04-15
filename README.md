# HyporheicFloPy

--Resources--
<br/> https://flopy.readthedocs.io/
<br/> https://flopy.readthedocs.io/en/3.4.2/examples.html

## Modflow Notes

<br/> We can use UGSS ModelMuse and USGS ModelViewer, which are standalone executibles, to verify our created models.  We can ship this with the script we produce.

## Programming Notes

We are using python version: 3.11.4

Folders ending with '_gitignore', will NOT be uploaded to github.  I recommend having a Data_gitignore folder in your directory, then having an 'input' and 'ouput' folder.  Use this for data heavy input/output folders.  Do not upload large files (e.g., model results or setup files) to github.

Recreate the virtual environment (only if you don't already have the .venv folder): 
<br/> 'python -m venv .venv'
<br/> This will make a '.venv' folder in your HyporheicFloPy directory.

To access the virtual environment in command prompt use: 
<br/> '.venv\scripts\activate'

To get the latest packages in your virtual environment: 
<br/> 'pip install -r requirements.txt'

To install packages to your virtual environment
1) activate the virtual environment (if it's not already active)
2) use 'pip install [package name]'
3) to uninstall use 'pip uninstall [packagename]'

Before updating requirements.txt, always pull the latest changes:
<br/> 'git pull origin main'
<br/> 'pip install -r requirements.txt'

If you add packages to your virtual environment, you'll need to update requirements.txt: 
<br/> 'pip freeze > requirements.txt'

You can push changes with source control.  Always use a concise commit message to describe the change.

## Directory Notes

Notebook Files:
<br/> - intro.ipynb
<br/> - preprocessing.ipynb
<br/> - initialization.ipynb
<br/> - model_domain.ipynb
<br/> - define_boundary.ipynb
<br/> - boundary_conditions.ipynb
<br/> - wells.ipynb
<br/> - nodes.ipynb
<br/> - run_models.ipynb
<br/> - results.ipynb

Results Directories:
<br/> - HP_Workspace
<br/> - gwf_workspace
<br/> - mp7_workspace


## Running MODFLOW6 with MODPATH7 Simulations:

To run the MODFLOW6 with MODPATH7 simulations and save the results, use the following command in the command prompt:
<br/> '.\run_models.bat'

To build the html document and run MODFLOW6 with MODPATH 7 for hosting Webpage, use the following command in the command prompt:
<br/> '.\build_notebook.bat'

