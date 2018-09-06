#!/bin/bash

echo "type pyenv activate mac_env first"

#clear chache
rm -rf build
#remove binary
rm -rf dist/*_mac*

#pyinstaller -w --onefile --add-data "data:data" main.py --workpath "build" --name "skybean2_app_mac" --icon "data/icon.icns"
pyinstaller -w --add-data "data:data" main.py --workpath "build" --name "skybean2_app_mac" --icon "data/icon.icns"

zip -r dist/skybean2_app_mac.zip dist/skybean2_app_mac.app
rm -rf dist/skybean2_app_mac.app
rm -rf dist/skybean2_app_mac





