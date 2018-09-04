#!/bin/bash


source mac_env/bin/activate
pyinstaller --onefile --add-data "bundled.hex:." prog.py --workpath "build/mac" --name "skybean2_update_mac"
