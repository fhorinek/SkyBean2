#!/bin/bash

#clear chache
rm -rf build
#remove binary
rm dist/*_linux

source linux_env/bin/activate
pyinstaller -w --onefile --add-data "data:data" main.py --workpath "build" --name "skybean2_app_linux" --icon "data/icon.ico"

