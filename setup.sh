#!/bin/bash

# Billing ERP System - Setup Script
# This script sets up the development environment for the project

set -e

echo "================================"
echo "Billing ERP System - Setup"
echo "================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ".env file created. Please update it with your settings."
else
    echo ".env file already exists."
fi

# Run migrations
echo ""
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create directories if they don't exist
mkdir -p logs media staticfiles

# Collect static files
echo ""
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser
echo ""
echo "Creating superuser..."
echo "Please enter superuser credentials:"
python manage.py createsuperuser

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "To start the development server, run:"
echo "  python manage.py runserver"
echo ""
echo "The application will be available at:"
echo "  http://localhost:8000"
echo ""
echo "Admin panel:"
echo "  http://localhost:8000/admin"
echo ""
