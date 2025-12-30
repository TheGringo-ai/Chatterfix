#!/bin/bash

echo "🌐 SETTING UP CHATTERFIX.COM DOMAIN DEPLOYMENT"
echo "=============================================="

# Deploy the domain setup to VM
ssh chatterfix-prod << 'ENDSSH'

echo "🔧 Installing nginx and certbot..."
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

echo "🛑 Stopping nginx temporarily..."
sudo systemctl stop nginx

echo "🌐 Creating nginx configuration for chatterfix.com..."
sudo tee /etc/nginx/sites-available/chatterfix.com > /dev/null << 'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name chatterfix.com www.chatterfix.com;
    
    # Redirect all HTTP traffic to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name chatterfix.com www.chatterfix.com;
    
    # SSL configuration (will be updated by certbot)
    ssl_certificate /etc/ssl/certs/ssl-cert-snakeoil.pem;
    ssl_certificate_key /etc/ssl/private/ssl-cert-snakeoil.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/javascript application/json;
    
    # Proxy to FastAPI app
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # Static files (if any)
    location /static {
        alias /opt/chatterfix-cmms/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Favicon
    location /favicon.ico {
        access_log off;
        log_not_found off;
    }
    
    # Robots.txt
    location /robots.txt {
        access_log off;
        log_not_found off;
    }
}
EOF

echo "🔗 Enabling the site..."
sudo ln -sf /etc/nginx/sites-available/chatterfix.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "✅ Testing nginx configuration..."
sudo nginx -t

echo "🚀 Starting nginx..."
sudo systemctl start nginx
sudo systemctl enable nginx

echo "🔒 Setting up SSL certificate with certbot..."
# First try to get certificate
sudo certbot --nginx -d chatterfix.com -d www.chatterfix.com --non-interactive --agree-tos --email admin@chatterfix.com --redirect

echo "📊 Testing SSL setup..."
systemctl status nginx --no-pager | head -5
systemctl status chatterfix-cmms --no-pager | head -5

echo "🧪 Testing endpoints..."
echo "HTTP redirect test:"
curl -I http://chatterfix.com 2>/dev/null | head -3

echo ""
echo "HTTPS test:"
curl -I https://chatterfix.com 2>/dev/null | head -3

echo ""
echo "Health check:"
curl -s https://chatterfix.com/health | head -3

echo ""
echo "🎉 DOMAIN SETUP COMPLETE!"
echo "========================="
echo "🌐 Your app is now available at:"
echo "   https://chatterfix.com"
echo "   https://www.chatterfix.com"
echo ""
echo "✅ Features enabled:"
echo "   • HTTPS with Let's Encrypt SSL"
echo "   • HTTP to HTTPS redirect"
echo "   • Security headers"
echo "   • Gzip compression"
echo "   • Nginx reverse proxy"
echo ""
echo "🤖 AI Assistant will be available on all pages!"

ENDSSH

echo "🎉 Domain deployment completed!"
echo "Your ChatterFix CMMS is now live at https://chatterfix.com"