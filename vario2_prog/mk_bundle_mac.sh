#!/bin/bash

#clear chache
rm -rf build
#remove binary
rm dist/*_mac

cp ../vario2/Release/vario2.hex bundled.hex

source mac_env/bin/activate
pyinstaller --onefile --add-data "bundled.hex:." prog.py --workpath "build" --name "skybean2_update_mac" --icon=icon.icns

mv dist/skybean2_update_mac "dist/SkyBean2 firmware update"
dmgbuild -s skybean2_update_mac.image a a
rm -rf "dist/SkyBean2 firmware update"