#!/bin/bash

echo "first type 'pyenv activate mac_env'"

#clear chache
rm -rf build
#remove binary
rm -rf dist/*_mac*

pyinstaller -w --add-data "data:data" main.py --workpath "build" --name "skybean2_app_mac" --icon "data/icon.icns"

mv dist/skybean2_app_mac.app dist/SkyBean2.app
dmgbuild -s skybean2_app_mac.image a a
rm -rf dist/skybean2_app_mac
rm -rf dist/SkyBean2.app






