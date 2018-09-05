#!/bin/bash

#clear chache
rm -rf build/linux
#remove binary
rm dist/*_linux

cp ../vario2/Release/vario2.hex bundled.hex

source linux_env/bin/activate
pyinstaller --onefile --add-data "bundled.hex:." prog.py --workpath "build/linux" --name "skybean2_update_linux"

