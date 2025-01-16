# HyporheicFloPy
Python version: 3.11.4

--NOTES--

Recreate the virtual environment (you only need to do this once): 'python -m venv .venv'
This will make a '.venv' folder in your HyporheicFloPy directory.

To access the virtual environment in command prompt use: '.venv\scripts\activate'

To get the latest packages in your virtual environment: 'pip install -r requirements.txt'

To install packages to your virtual environment
1) activate the virtual environment (if it's not already active)
2) use 'pip install [package name]'
3) to uninstall use 'pip uninstall [packagename]'

Before updating requirements.txt, always pull the latest changes:
'git pull origin main'
'pip install -r requirements.txt'

If you add packages to your virtual environment, you'll need to update requirements.txt: 'pip freeze > requirements.txt'