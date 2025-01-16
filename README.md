# HyporheicFloPy

--NOTES--

We are using python version: 3.11.4

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