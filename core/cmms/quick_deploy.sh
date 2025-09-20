#!/bin/bash

# Quick deployment script for ChatterFix CMMS
echo "Starting ChatterFix deployment..."

# Check current directory
pwd
ls -la

# Check if there's an existing cmms directory
if [ -d "/home/yoyofred/cmms" ]; then
    echo "Found existing CMMS directory at /home/yoyofred/cmms"
    cd /home/yoyofred/cmms
elif [ -d "/opt/cmms" ]; then
    echo "Found existing CMMS directory at /opt/cmms"
    cd /opt/cmms
elif [ -d "/var/www/cmms" ]; then
    echo "Found existing CMMS directory at /var/www/cmms"
    cd /var/www/cmms
else
    echo "Creating new CMMS directory at /home/yoyofred/cmms"
    mkdir -p /home/yoyofred/cmms
    cd /home/yoyofred/cmms
fi

# Show current Python files
echo "Current Python files:"
ls -la *.py 2>/dev/null || echo "No Python files found"

# Check Python and pip
echo "Python version:"
python3 --version

# Install dependencies
echo "Installing dependencies..."
pip3 install --user fastapi uvicorn pydantic python-multipart

# Check if service exists
echo "Checking for existing service..."
sudo systemctl status chatterfix-cmms --no-pager 2>/dev/null || echo "No service found"

# Find the application
echo "Looking for application files..."
find /home -name "app.py" -type f 2>/dev/null | head -5
find /opt -name "app.py" -type f 2>/dev/null | head -5
find /var -name "app.py" -type f 2>/dev/null | head -5

echo "Deployment check complete!"