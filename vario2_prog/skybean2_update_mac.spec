# -*- mode: python -*-

block_cipher = None


a = Analysis(['prog.py'],
             pathex=['/Users/horinek/dev/SkyBean2/vario2_prog'],
             binaries=[],
             datas=[('bundled.hex', '.')],
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
          name='skybean2_update_mac',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True , icon='icon.icns')
