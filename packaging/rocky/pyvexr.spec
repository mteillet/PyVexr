# -*- mode: python ; coding: utf-8 -*-
"""
Spec PyInstaller pour le bundle Rocky Linux de PyVexr.

Le bundle est genere en mode "onedir" avec contents_directory='.', c'est a dire
que l'executable et toutes ses dependances se trouvent a la racine du dossier.
C'est indispensable : pyVexr_gui.py et pyVexr_main.py resolvent leurs
ressources (imgs/, ocio/, config.json) via os.path.dirname(sys.argv[0]), donc
ces dossiers doivent etre a cote de l'executable.

Variables d'environnement utilisees :
  PYVEXR_ROOT         racine du depot (defaut : dossier courant)
  PYVEXR_CPP_MODULES  dossier contenant les .so compiles (exposureUp,
                      loadExrChannel) ; defaut : $PYVEXR_ROOT/cppModules
"""

import os

ROOT = os.path.abspath(os.environ.get('PYVEXR_ROOT', os.getcwd()))
CPP_MODULES = os.path.abspath(
    os.environ.get('PYVEXR_CPP_MODULES', os.path.join(ROOT, 'cppModules'))
)

datas = [
    (os.path.join(ROOT, 'imgs'), 'imgs'),
    (os.path.join(ROOT, 'ocio'), 'ocio'),
]

a = Analysis(
    [os.path.join(ROOT, 'pyVexr_gui.py')],
    pathex=[ROOT, CPP_MODULES],
    binaries=[],
    datas=datas,
    # Les deux modules C++ sont importes via un sys.path.append() dynamique,
    # l'analyse statique de PyInstaller ne peut pas les voir.
    hiddenimports=['exposureUp', 'loadExrChannel'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PySide2',
        'PySide6',
        'PyQt6',
        'IPython',
        'pytest',
        # imageio n'importe pkg_resources qu'en option (try/except avec repli).
        # L'embarquer traine tout setuptools et son jaraco/backports vendorises,
        # qui cassent au demarrage du bundle.
        'pkg_resources',
        'setuptools',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PyVexr',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Layout "plat" : tout est a cote de l'executable, comme attendu par
    # absPath = os.path.dirname(sys.argv[0]).
    contents_directory='.',
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PyVexr',
)
