import os

os.system(
    'python -m PyInstaller '
    '--onefile '
    '--windowed '
    '--icon="assets/mechsoc_32.ico" '
    '--add-data "assets/mechsoc_32.ico;assets" '
    '--add-data "assets/mechsoc_128.png;assets" '
    '--add-data "assets/mechsoc_256.png;assets" '
    'main.py'
)