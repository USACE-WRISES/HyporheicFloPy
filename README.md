# HyporheicFloPy
# Python version 3.11.4


# Instead of tracking the virtual environment, you should:
Create a requirements.txt:
pip freeze > requirements.txt

Recreate the environment later with:
python -m venv venv
pip install -r requirements.txt

# Before updating requirements.txt, always pull the latest changes:
git pull origin main
pip install -r requirements.txt

# Updated gitignore to ignore virtual environment
To access the virtual environment in command prompt use
.venv\scripts\activate

# To install packages to your virtual environment
1) activate the virtual environment (if it's not already active)
2) use 'pip install [package name]'
3) to uninstall use 'pip uninstall [packagename]'