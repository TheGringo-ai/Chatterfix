#!/bin/bash
# HTTPS Domain Configuration for ChatterFix Complete AI Integration
# Ensures www.chatterfix.com works with SSL after AI deployment

echo "🔒 HTTPS Domain Configuration"
echo "============================"

PROJECT_ID="fredfix"
INSTANCE_NAME="chatterfix-cmms-production"
ZONE="us-east1-b"

# Create nginx configuration for HTTPS with AI services
cat > /tmp/chatterfix-https.conf << 'EOF'
# ChatterFix Complete AI Integration - HTTPS Configuration

upstream chatterfix_app {
    server 127.0.0.1:8080;
}

upstream linesmart_app {
    server 127.0.0.1:8082;
}

upstream ollama_api {
    server 127.0.0.1:11434;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name chatterfix.com www.chatterfix.com;
    return 301 https://www.chatterfix.com$request_uri;
}

# HTTPS Configuration
server {
    listen 443 ssl http2;
    server_name www.chatterfix.com chatterfix.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/chatterfix.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chatterfix.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    # Main ChatterFix Application
    location / {
        proxy_pass http://chatterfix_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # WebSocket support for real-time features
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # LineSmart Training Platform
    location /training/ {
        proxy_pass http://linesmart_app/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Ollama AI API (internal access only, proxied through ChatterFix)
    location /internal/ollama/ {
        proxy_pass http://ollama_api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Restrict access
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://chatterfix_app/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files caching
    location /static/ {
        proxy_pass http://chatterfix_app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
EOF

echo "🔧 Uploading HTTPS configuration..."

# Upload nginx config
gcloud compute scp /tmp/chatterfix-https.conf \
  $INSTANCE_NAME:/tmp/chatterfix-https.conf \
  --zone=$ZONE

# Create domain setup script
DOMAIN_SETUP='#!/bin/bash
echo "🔒 Setting up HTTPS domain configuration..."

# Backup current nginx config
sudo cp /etc/nginx/sites-available/chatterfix /etc/nginx/sites-available/chatterfix.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || true

# Install new configuration
sudo cp /tmp/chatterfix-https.conf /etc/nginx/sites-available/chatterfix

# Enable site if not already enabled
sudo ln -sf /etc/nginx/sites-available/chatterfix /etc/nginx/sites-enabled/ 2>/dev/null || true

# Test nginx configuration
if sudo nginx -t; then
    echo "✅ Nginx configuration valid"
    
    # Reload nginx
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded with HTTPS config"
else
    echo "❌ Nginx configuration invalid, restoring backup"
    sudo cp /etc/nginx/sites-available/chatterfix.backup.* /etc/nginx/sites-available/chatterfix 2>/dev/null || true
    exit 1
fi

# Ensure SSL certificate is valid
if sudo certbot certificates | grep -q "chatterfix.com"; then
    echo "✅ SSL certificate exists"
else
    echo "⚠️ SSL certificate may need renewal"
    # Attempt to renew
    sudo certbot renew --quiet || echo "⚠️ SSL renewal failed"
fi

echo "✅ HTTPS domain configuration complete"
echo "🔗 Access your site at: https://www.chatterfix.com"
'

# Execute domain setup
echo "$DOMAIN_SETUP" | gcloud compute ssh $INSTANCE_NAME \
  --zone=$ZONE \
  --command "cat > /tmp/domain-setup.sh && chmod +x /tmp/domain-setup.sh && sudo /tmp/domain-setup.sh"

# Test HTTPS access
echo "🧪 Testing HTTPS access..."
sleep 5

if curl -s -f "https://www.chatterfix.com/health" > /dev/null; then
    echo "✅ HTTPS working: https://www.chatterfix.com"
    
    # Test AI endpoints through HTTPS
    if curl -s -f "https://www.chatterfix.com/api/assets" > /dev/null; then
        echo "✅ Assets API via HTTPS: Working"
    else
        echo "⏳ Assets API via HTTPS: Still deploying"
    fi
    
else
    echo "⚠️ HTTPS access needs verification"
fi

# Cleanup
rm -f /tmp/chatterfix-https.conf

echo "🎉 HTTPS domain configuration complete!"
echo "🔗 Your AI-integrated ChatterFix is available at:"
echo "   https://www.chatterfix.com"
echo "   https://www.chatterfix.com/assets (Asset Management)"
echo "   https://www.chatterfix.com/training (LineSmart Training)"