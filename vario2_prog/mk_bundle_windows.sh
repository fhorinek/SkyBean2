#!/bin/bash

#clear chache
rm -rf build/windows
#remove binary
rm dist/*.exe

cp ../vario2/Release/vario2.hex bundled.hex

script_path=`realpath "$0"`
dir_path=`dirname $script_path`
export WINEPREFIX="$dir_path/windows_env"
echo $WINEPREFIX
wine pyinstaller --onefile --add-data "bundled.hex;." prog.py --workpath "build/windows" --name "skybean2_update_windows" --icon="icon.ico"
