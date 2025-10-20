#!/bin/bash
# Deploy Enhanced ChatterFix CMMS to VM
set -e

echo "🚀 Deploying Enhanced ChatterFix CMMS to VM"
echo "============================================"

# VM Configuration
VM_IP="your-vm-ip"  # Replace with actual VM IP
VM_USER="ubuntu"    # Replace with VM username

echo "📦 Preparing deployment package..."

# Create deployment package
mkdir -p deployment-package
cd deployment-package

# Copy enhanced CMMS files
cp ../core/cmms/enhanced_cmms_app.py ./
cp ../core/cmms/database_service.py ./
cp ../core/cmms/work_orders_service.py ./
cp ../core/cmms/assets_service.py ./
cp ../core/cmms/parts_service.py ./
cp ../core/cmms/document_intelligence_service.py ./
cp ../core/cmms/enterprise_security_service.py ./
cp ../core/cmms/mobile_server.py ./
cp ../fix_it_fred_ai_service.py ./

# Create VM deployment script
cat > deploy-to-vm.sh << 'EOF'
#!/bin/bash
# VM Deployment Script
set -e

echo "🏗️  Setting up Enhanced ChatterFix CMMS on VM..."

# Install dependencies
sudo apt update
sudo apt install -y python3 python3-pip nginx

# Install Python packages
pip3 install fastapi uvicorn flask flask-cors requests pydantic python-dotenv

# Stop existing services
sudo systemctl stop nginx || true
sudo pkill -f python3 || true

# Create directories
sudo mkdir -p /var/www/chatterfix
sudo mkdir -p /var/log/chatterfix
sudo chown -R $USER:$USER /var/www/chatterfix
sudo chown -R $USER:$USER /var/log/chatterfix

# Copy application files
cp *.py /var/www/chatterfix/
cd /var/www/chatterfix

# Create systemd services for all microservices
echo "📋 Creating systemd services..."

# Main Gateway Service
sudo tee /etc/systemd/system/chatterfix-gateway.service > /dev/null << 'GATEWAY_EOF'
[Unit]
Description=ChatterFix CMMS Gateway
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8000
ExecStart=/usr/bin/python3 enhanced_cmms_app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
GATEWAY_EOF

# Database Service
sudo tee /etc/systemd/system/chatterfix-database.service > /dev/null << 'DB_EOF'
[Unit]
Description=ChatterFix Database Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8001
ExecStart=/usr/bin/python3 database_service.py --port 8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
DB_EOF

# Work Orders Service
sudo tee /etc/systemd/system/chatterfix-workorders.service > /dev/null << 'WO_EOF'
[Unit]
Description=ChatterFix Work Orders Service
After=network.target chatterfix-database.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8002
ExecStart=/usr/bin/python3 work_orders_service.py --port 8002
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
WO_EOF

# Assets Service
sudo tee /etc/systemd/system/chatterfix-assets.service > /dev/null << 'ASSETS_EOF'
[Unit]
Description=ChatterFix Assets Service
After=network.target chatterfix-database.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8003
ExecStart=/usr/bin/python3 assets_service.py --port 8003
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
ASSETS_EOF

# Parts Service
sudo tee /etc/systemd/system/chatterfix-parts.service > /dev/null << 'PARTS_EOF'
[Unit]
Description=ChatterFix Parts Service
After=network.target chatterfix-database.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8004
ExecStart=/usr/bin/python3 parts_service.py --port 8004
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
PARTS_EOF

# Fix It Fred AI Service
sudo tee /etc/systemd/system/chatterfix-ai.service > /dev/null << 'AI_EOF'
[Unit]
Description=Fix It Fred AI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8005
ExecStart=/usr/bin/python3 fix_it_fred_ai_service.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
AI_EOF

# Create Nginx configuration
echo "🌐 Configuring Nginx..."
sudo tee /etc/nginx/sites-available/chatterfix > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    server_name chatterfix.com www.chatterfix.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chatterfix.com www.chatterfix.com;
    
    # SSL Configuration (add your certificates)
    # ssl_certificate /path/to/your/certificate.crt;
    # ssl_certificate_key /path/to/your/private.key;
    
    # For now, serve without SSL
    listen 80;
    
    # Main application
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # API routes for microservices
    location /api/database/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/work_orders/ {
        proxy_pass http://localhost:8002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/assets/ {
        proxy_pass http://localhost:8003/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/parts/ {
        proxy_pass http://localhost:8004/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ai/ {
        proxy_pass http://localhost:8005/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Health checks
    location /health {
        proxy_pass http://localhost:8000/health;
        proxy_set_header Host $host;
    }
    
    # Static files
    location /static/ {
        alias /var/www/chatterfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Enable site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/chatterfix /etc/nginx/sites-enabled/
sudo nginx -t

# Initialize database
echo "🗄️  Initializing database..."
python3 database_service.py --init-db

# Enable and start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload

# Start services in order
sudo systemctl enable chatterfix-database
sudo systemctl start chatterfix-database
sleep 2

sudo systemctl enable chatterfix-workorders
sudo systemctl start chatterfix-workorders
sleep 1

sudo systemctl enable chatterfix-assets  
sudo systemctl start chatterfix-assets
sleep 1

sudo systemctl enable chatterfix-parts
sudo systemctl start chatterfix-parts
sleep 1

sudo systemctl enable chatterfix-ai
sudo systemctl start chatterfix-ai
sleep 2

sudo systemctl enable chatterfix-gateway
sudo systemctl start chatterfix-gateway
sleep 2

# Start Nginx
sudo systemctl enable nginx
sudo systemctl start nginx

# Check status
echo "🔍 Service Status:"
sudo systemctl status chatterfix-gateway --no-pager -l
sudo systemctl status chatterfix-database --no-pager -l
sudo systemctl status nginx --no-pager -l

echo ""
echo "✅ Enhanced ChatterFix CMMS deployed successfully!"
echo "🌐 Access at: https://www.chatterfix.com"
echo ""
echo "📊 Service Health Checks:"
curl -s http://localhost:8000/health | jq . || echo "Gateway: Starting..."
curl -s http://localhost:8001/health | jq . || echo "Database: Starting..."
curl -s http://localhost:8005/health | jq . || echo "AI: Starting..."

EOF

chmod +x deploy-to-vm.sh

echo "📁 Deployment package created!"
echo "Files ready for VM deployment:"
ls -la

echo ""
echo "🚀 To deploy to VM, run:"
echo "1. Copy files to VM: scp -r deployment-package/ $VM_USER@$VM_IP:~/"
echo "2. SSH to VM: ssh $VM_USER@$VM_IP"  
echo "3. Run deployment: cd deployment-package && ./deploy-to-vm.sh"
echo ""
echo "Or run this script with VM details to auto-deploy."