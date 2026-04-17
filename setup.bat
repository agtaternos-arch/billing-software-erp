@echo off
REM Billing ERP System - Setup Script (Windows)

echo.
echo ================================
echo Billing ERP System - Setup
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

REM Install requirements
echo.
echo Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo.
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created. Please update it with your settings.
) else (
    echo .env file already exists.
)

REM Run migrations
echo.
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Create directories if they don't exist
if not exist "logs" mkdir logs
if not exist "media" mkdir media
if not exist "staticfiles" mkdir staticfiles

REM Collect static files
echo.
echo Collecting static files...
python manage.py collectstatic --noinput

REM Create superuser
echo.
echo Creating superuser...
echo Please enter superuser credentials:
python manage.py createsuperuser

echo.
echo ================================
echo Setup Complete!
echo ================================
echo.
echo To start the development server, run:
echo   python manage.py runserver
echo.
echo The application will be available at:
echo   http://localhost:8000
echo.
echo Admin panel:
echo   http://localhost:8000/admin
echo.
pause
