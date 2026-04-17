# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

crispy_forms_datas = collect_data_files('crispy_forms')
crispy_bootstrap5_datas = collect_data_files('crispy_bootstrap5')

a = Analysis(
    ['desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates'), ('staticfiles', 'staticfiles'), ('static/img', 'static/img'), ('apps', 'apps'), ('config', 'config'), ('manage.py', '.')] + crispy_forms_datas + crispy_bootstrap5_datas,
    hiddenimports=['whitenoise.middleware', 'crispy_forms', 'crispy_bootstrap5', 'crispy_bootstrap5.templatetags.crispy_bootstrap5_field', 'rest_framework', 'django_filters', 'mathfilters', 'jaraco.text', 'jaraco.functools', 'jaraco.context', 'jaraco.collections'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['celery', 'webview', 'torch', 'cv2', 'matplotlib', 'IPython', 'ultralytics', 'scipy', 'numpy'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TorvixBills',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
