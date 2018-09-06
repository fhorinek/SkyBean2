# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/Users/horinek/dev/SkyBean2/vario2_app'],
             binaries=[],
             datas=[('data', 'data')],
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
          exclude_binaries=True,
          name='skybean2_app_mac',
          debug=False,
          strip=False,
          upx=True,
          console=False , icon='data/icon.icns')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='skybean2_app_mac')
app = BUNDLE(coll,
             name='skybean2_app_mac.app',
             icon='data/icon.icns',
             bundle_identifier=None)
