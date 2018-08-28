#!/bin/bash

cp ../vario2/Release/vario2.hex bundled.hex
rm -rf dist
rm -rf build

./mk_bundle_windows.sh
./mk_bundle_linux.sh

rm -rf *.spec
