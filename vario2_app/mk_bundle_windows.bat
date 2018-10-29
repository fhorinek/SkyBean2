
REM remove chache
rm -rf build
REM remove binary
rm dist/*_windows

REM pyinstaller -w --onefile --add-data "data;data" main.py --workpath "build" --name "skybean2_app_windows" --icon "data/icon.ico"
pyinstaller skybean2_app_windows.spec
