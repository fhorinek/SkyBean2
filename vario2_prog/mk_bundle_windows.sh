#!/bin/bash

script_path=`realpath "$0"`
dir_path=`dirname $script_path`
export WINEPREFIX="$dir_path/windows_env"
echo $WINEPREFIX
wine pyinstaller --onefile --add-data "bundled.hex;." prog.py --workpath "build/windows" --name "skybean2_update_windows"
