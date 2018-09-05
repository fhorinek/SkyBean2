# -*- mode: python -*-

block_cipher = None


a = Analysis(['main.py'],
             pathex=['/home/horinek/git/vario2/vario2_app'],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='skybean2_app_linux',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='data/icon.ico')
