@echo off
echo Activating virtual environment...
call .\.venv\Scripts\activate

echo Deleting old build files...
del /Q C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\*

echo Ensuring .nojekyll file exists...
if not exist C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll (
    echo. > C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll
)

echo Building Jupyter Book...
jupyter-book build VQuintana/

echo Moving files to docs directory...
move VQuintana\_build\html\* C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs

echo Build and move complete!
