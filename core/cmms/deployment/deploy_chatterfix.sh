#!/bin/bash

# ChatterFix CMMS Deployment Script
# This script deploys the fixed ChatterFix application

echo "======================================"
echo "ChatterFix CMMS Deployment Script"
echo "======================================"

# Set variables
DEPLOY_DIR="/home/chatterfix/cmms"
BACKUP_DIR="/home/chatterfix/backups"
SERVICE_NAME="chatterfix-cmms"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup current deployment
if [ -d "$DEPLOY_DIR" ]; then
    echo "Creating backup of current deployment..."
    tar -czf "$BACKUP_DIR/chatterfix_backup_$TIMESTAMP.tar.gz" -C "$DEPLOY_DIR" .
    echo "Backup created: $BACKUP_DIR/chatterfix_backup_$TIMESTAMP.tar.gz"
fi

# Create deployment directory
mkdir -p $DEPLOY_DIR

# Extract new files
echo "Extracting new ChatterFix files..."
tar -xzf /tmp/chatterfix-cmms-fixed.tar.gz -C $DEPLOY_DIR

# Install Python dependencies
echo "Installing Python dependencies..."
cd $DEPLOY_DIR
python3 -m pip install --user fastapi uvicorn pydantic python-multipart

# Stop existing service
echo "Stopping existing ChatterFix service..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=ChatterFix CMMS Application
After=network.target

[Service]
Type=simple
User=chatterfix
WorkingDirectory=$DEPLOY_DIR
ExecStart=/usr/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
echo "Starting ChatterFix service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME
sudo systemctl start $SERVICE_NAME

# Check service status
sleep 3
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ ChatterFix CMMS is running!"
    echo "Service status:"
    sudo systemctl status $SERVICE_NAME --no-pager
else
    echo "❌ Failed to start ChatterFix CMMS"
    echo "Check logs with: sudo journalctl -u $SERVICE_NAME -n 50"
fi

# Test the application
echo ""
echo "Testing application endpoints..."
curl -s http://localhost:8000/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Application is responding on port 8000"
else
    echo "❌ Application is not responding"
fi

echo ""
echo "======================================"
echo "Deployment complete!"
echo "Access the application at: http://35.237.149.25/"
echo "======================================"