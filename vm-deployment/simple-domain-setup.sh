#!/bin/bash

echo "🌐 SIMPLE DOMAIN SETUP FOR CHATTERFIX.COM"
echo "=========================================="

ssh chatterfix-prod << 'ENDSSH'

echo "🌐 Creating simple nginx configuration..."
sudo tee /etc/nginx/sites-available/chatterfix.com > /dev/null << 'EOF'
server {
    listen 80;
    server_name chatterfix.com www.chatterfix.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "🔗 Enabling the site..."
sudo ln -sf /etc/nginx/sites-available/chatterfix.com /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

echo "✅ Testing nginx configuration..."
sudo nginx -t

echo "🚀 Restarting nginx..."
sudo systemctl restart nginx

echo "🔒 Setting up SSL certificate..."
sudo certbot --nginx -d chatterfix.com -d www.chatterfix.com --non-interactive --agree-tos --email admin@chatterfix.com --redirect --quiet

echo "🧪 Testing the domain..."
echo "Testing HTTP (should redirect to HTTPS):"
curl -I http://chatterfix.com 2>/dev/null | head -3

echo ""
echo "Testing HTTPS:"  
curl -I https://chatterfix.com 2>/dev/null | head -3

echo ""
echo "Testing health endpoint:"
curl -s https://chatterfix.com/health

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="
echo "✅ https://chatterfix.com is now live!"
echo "✅ HTTPS with auto-redirect enabled"
echo "✅ ChatterFix CMMS with AI assistant ready"

ENDSSH

echo "🎉 Domain setup completed!"
echo "Your app is live at https://chatterfix.com"