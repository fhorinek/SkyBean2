#!/bin/bash


source linux_env/bin/activate
pyinstaller --onefile --add-data "bundled.hex:." prog.py --workpath "build/linux" --name "skybean2_update_linux"
