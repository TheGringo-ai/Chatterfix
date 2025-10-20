#!/bin/bash
# VM Deployment Script for Complete ChatterFix AI Platform
set -e

echo "🚀 Deploying Complete ChatterFix CMMS + All AI Providers to VM"
echo "============================================================="

# Setup directories
sudo mkdir -p /var/www/chatterfix
sudo mkdir -p /var/log/chatterfix
sudo chown -R $USER:$USER /var/www/chatterfix /var/log/chatterfix

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip nginx curl

# Install Python dependencies
pip3 install fastapi uvicorn flask flask-cors requests pydantic python-dotenv

# Copy application files
cp *.py /var/www/chatterfix/
cd /var/www/chatterfix

# Create environment file with API keys
cat > .env << 'ENV_EOF'
# AI Provider API Keys - UPDATE THESE
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
XAI_API_KEY=your_xai_grok_key_here

# Service Configuration
PORT=8080
FRED_AI_PORT=8005
DATABASE_URL=sqlite:///chatterfix.db
ENV_EOF

echo "⚠️  IMPORTANT: Update API keys in /var/www/chatterfix/.env"

# Create systemd service for main app
sudo tee /etc/systemd/system/chatterfix-main.service > /dev/null << 'MAIN_EOF'
[Unit]
Description=ChatterFix CMMS Main Application
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8080
ExecStart=/usr/bin/python3 enhanced_cmms_full_ai.py
Restart=always
RestartSec=3
EnvironmentFile=/var/www/chatterfix/.env

[Install]
WantedBy=multi-user.target
MAIN_EOF

# Create systemd service for Fix It Fred AI
sudo tee /etc/systemd/system/chatterfix-ai.service > /dev/null << 'AI_EOF'
[Unit]
Description=Fix It Fred AI Service with All Providers
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/var/www/chatterfix
Environment=PORT=8005
ExecStart=/usr/bin/python3 fix_it_fred_ai_service.py
Restart=always
RestartSec=3
EnvironmentFile=/var/www/chatterfix/.env

[Install]
WantedBy=multi-user.target
AI_EOF

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/chatterfix > /dev/null << 'NGINX_EOF'
server {
    listen 80;
    listen 443 ssl http2;
    server_name chatterfix.com www.chatterfix.com;
    
    # SSL Configuration (update with your certificates)
    # ssl_certificate /path/to/cert.pem;
    # ssl_certificate_key /path/to/key.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Main application
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # AI API endpoints
    location /api/ai/ {
        proxy_pass http://localhost:8005/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_connect_timeout 90s;
        proxy_send_timeout 90s;
        proxy_read_timeout 90s;
    }
    
    # Health checks
    location /health {
        proxy_pass http://localhost:8080/health;
        proxy_set_header Host $host;
    }
    
    # Static files and caching
    location /static/ {
        alias /var/www/chatterfix/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
NGINX_EOF

# Enable Nginx site
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/chatterfix /etc/nginx/sites-enabled/
sudo nginx -t

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload

# Start AI service first
sudo systemctl enable chatterfix-ai
sudo systemctl start chatterfix-ai
sleep 3

# Start main application
sudo systemctl enable chatterfix-main
sudo systemctl start chatterfix-main
sleep 2

# Start Nginx
sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
echo "🔍 Service Status:"
echo "=================="
sudo systemctl status chatterfix-main --no-pager -l | head -10
echo ""
sudo systemctl status chatterfix-ai --no-pager -l | head -10
echo ""
sudo systemctl status nginx --no-pager -l | head -5

echo ""
echo "✅ Complete ChatterFix AI Platform Deployed!"
echo "============================================="
echo "🌐 Access at: https://www.chatterfix.com"
echo "🤖 AI Providers: Ollama + OpenAI + Anthropic + Google + xAI Grok"
echo ""
echo "📊 Quick Health Check:"
curl -s http://localhost:8080/health | jq . || echo "Main app: Starting..."
echo ""
curl -s http://localhost:8005/health | jq . || echo "AI service: Starting..."

echo ""
echo "⚠️  Next Steps:"
echo "1. Update API keys in /var/www/chatterfix/.env"
echo "2. Restart services: sudo systemctl restart chatterfix-*"
echo "3. Configure SSL certificates for HTTPS"
echo "4. Test all AI providers at www.chatterfix.com"

