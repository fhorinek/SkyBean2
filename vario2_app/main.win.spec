# -*- mode: python -*-

import os, sys

deps = []

from kivy.deps import sdl2, glew
deps = sdl2.dep_bins + glew.dep_bins

block_cipher = None


path = os.path.realpath(sys.argv[0])

a = Analysis(['main.py'],
             pathex=['path'],
             binaries=[],
             datas=[("data", "data")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
		  *[Tree(p) for p in (deps)],		  
          name='main',
          debug=False,
          strip=False,
          upx=False,
          runtime_tmpdir=None,
          console=False)
