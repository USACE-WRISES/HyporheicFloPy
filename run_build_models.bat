@echo off
echo Activating virtual environment...
call .\.venv\Scripts\activate

echo Deleting old build files and subdirectories...
del /Q C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\* 2>nul
for /D %%i in (C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\*) do rmdir /S /Q "%%i"

echo Ensuring .nojekyll file exists...
if not exist C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll (
    echo. > C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs\.nojekyll
)

echo Building Jupyter Book...
jupyter-book build VQuintana/

echo Copying files and folders to docs directory...
xcopy VQuintana\_build\html\* C:\Users\u4eeevmq\Documents\Python\HyporheicFloPy\docs /E /H /C /I /Y

echo Build and move complete!
