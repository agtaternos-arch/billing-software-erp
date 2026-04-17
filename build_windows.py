import os
import subprocess
import shutil
import sys

def run_command(command, description):
    print(f"\n>>> {description}...")
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during {description}: {e}")
        sys.exit(1)

def build():
    # 1. Install desktop requirements using the current python executable
    python_exe = sys.executable
    run_command(f'"{python_exe}" -m pip install -r requirements_desktop.txt', "Ensuring desktop dependencies")

    # 2. Set environment for collectstatic
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.desktop_settings'
    
    # 3. Collect static files
    run_command(f'"{python_exe}" manage.py collectstatic --noinput', "Collecting static files")

    # 4. Define PyInstaller command
    pyinstaller_cmd = [
        f'"{python_exe}"', "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--console",
        "--name=TorvixBills",
        "--exclude-module=celery",
        "--exclude-module=webview",
        "--exclude-module=torch",
        "--exclude-module=cv2",
        "--exclude-module=matplotlib",
        "--exclude-module=IPython",
        "--exclude-module=ultralytics",
        "--exclude-module=scipy",
        "--exclude-module=numpy",
        "--hidden-import=whitenoise.middleware",
        "--hidden-import=crispy_forms",
        "--hidden-import=crispy_bootstrap5",
        "--hidden-import=rest_framework",
        "--hidden-import=django_filters",
        "--hidden-import=mathfilters",
        "--hidden-import=jaraco.text",
        "--hidden-import=jaraco.functools",
        "--hidden-import=jaraco.context",
        "--hidden-import=jaraco.collections",
        "--add-data=templates;templates",
        "--add-data=staticfiles;staticfiles",
        "--add-data=static/img;static/img",
        "--add-data=apps;apps",
        "--add-data=config;config",
        "--add-data=manage.py;.",
        "desktop_launcher.py"
    ]

    print("\n>>> Building Executable (this may take a few minutes)...")
    subprocess.run(" ".join(pyinstaller_cmd), shell=True)

    print("\n========================================")
    print("Build Complete!")
    print("The executable can be found in the 'dist/' directory as TorvixBills.exe")
    print("========================================")

if __name__ == "__main__":
    build()
