#!/bin/bash
# Optimize Ollama and Fix It Fred on ChatterFix VM
set -e

echo "🚀 Optimizing Ollama and Fix It Fred for Production VM"
echo "VM Specs: e2-standard-4 (4 vCPUs, 16GB RAM, 50GB disk)"
echo "=================================================="

# Create optimized Ollama configuration
cat > ollama-optimized.env << 'EOF'
# Ollama Production Optimizations for e2-standard-4 VM
OLLAMA_HOST=0.0.0.0:11434
OLLAMA_ORIGINS=*
OLLAMA_MODELS=/var/lib/ollama/models
OLLAMA_KEEP_ALIVE=5m
OLLAMA_MAX_LOADED_MODELS=1
OLLAMA_NUM_PARALLEL=2
OLLAMA_MAX_QUEUE=4
OLLAMA_CONCURRENCY=2
OLLAMA_FLASH_ATTENTION=true
OLLAMA_GPU_OVERHEAD=0
OLLAMA_RUNNER_SLEEP_TIME=1s
OLLAMA_REQUEST_TIMEOUT=60s
EOF

# Create systemd service for Ollama
cat > ollama.service << 'EOF'
[Unit]
Description=Ollama AI Service
Documentation=https://ollama.ai
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/ollama serve
User=root
Group=root
Restart=always
RestartSec=5
KillMode=mixed
KillSignal=SIGINT
TimeoutStopSec=30
WorkingDirectory=/var/lib/ollama
Environment=OLLAMA_HOST=0.0.0.0:11434
Environment=OLLAMA_ORIGINS=*
Environment=OLLAMA_KEEP_ALIVE=5m
Environment=OLLAMA_MAX_LOADED_MODELS=1
Environment=OLLAMA_NUM_PARALLEL=2
Environment=OLLAMA_CONCURRENCY=2
Environment=OLLAMA_FLASH_ATTENTION=true

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Fix It Fred
cat > fix-it-fred.service << 'EOF'
[Unit]
Description=Fix It Fred AI Assistant
Documentation=https://chatterfix.com
After=network.target ollama.service
Wants=ollama.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/yoyofred_gringosgambit_com/chatterfix-docker/app/fix_it_fred_ai_service.py
User=yoyofred_gringosgambit_com
Group=yoyofred_gringosgambit_com
WorkingDirectory=/home/yoyofred_gringosgambit_com/chatterfix-docker/app
Restart=always
RestartSec=10
KillMode=mixed
TimeoutStopSec=15
Environment=PORT=9000
Environment=OLLAMA_HOST=localhost:11434
Environment=DEFAULT_MODEL=llama3.2:1b

[Install]
WantedBy=multi-user.target
EOF

# Create monitoring script
cat > monitor-services.py << 'EOF'
#!/usr/bin/env python3
"""
ChatterFix Services Monitor
Monitors Ollama and Fix It Fred services with auto-restart
"""
import subprocess
import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/chatterfix-monitor.log'),
        logging.StreamHandler()
    ]
)

def check_service_status(service_name):
    """Check if systemd service is active"""
    try:
        result = subprocess.run(
            ['systemctl', 'is-active', service_name],
            capture_output=True, text=True
        )
        return result.stdout.strip() == 'active'
    except:
        return False

def check_ollama_health():
    """Check if Ollama is responding"""
    try:
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except:
        return False

def check_fred_health():
    """Check if Fix It Fred is responding"""
    try:
        response = requests.get('http://localhost:9000/health', timeout=5)
        return response.status_code == 200
    except:
        return False

def restart_service(service_name):
    """Restart a systemd service"""
    try:
        subprocess.run(['systemctl', 'restart', service_name], check=True)
        logging.info(f"Restarted {service_name}")
        return True
    except Exception as e:
        logging.error(f"Failed to restart {service_name}: {e}")
        return False

def main():
    logging.info("Starting ChatterFix Services Monitor")
    
    failure_counts = {'ollama': 0, 'fix-it-fred': 0}
    max_failures = 3
    
    while True:
        try:
            # Check Ollama
            if not check_service_status('ollama') or not check_ollama_health():
                failure_counts['ollama'] += 1
                logging.warning(f"Ollama unhealthy (failures: {failure_counts['ollama']})")
                
                if failure_counts['ollama'] >= max_failures:
                    logging.error("Ollama max failures reached, restarting...")
                    if restart_service('ollama'):
                        failure_counts['ollama'] = 0
                        time.sleep(30)  # Wait for restart
            else:
                failure_counts['ollama'] = 0
            
            # Check Fix It Fred
            if not check_service_status('fix-it-fred') or not check_fred_health():
                failure_counts['fix-it-fred'] += 1
                logging.warning(f"Fix It Fred unhealthy (failures: {failure_counts['fix-it-fred']})")
                
                if failure_counts['fix-it-fred'] >= max_failures:
                    logging.error("Fix It Fred max failures reached, restarting...")
                    if restart_service('fix-it-fred'):
                        failure_counts['fix-it-fred'] = 0
                        time.sleep(15)  # Wait for restart
            else:
                failure_counts['fix-it-fred'] = 0
            
            # Log status every 10 minutes
            if int(time.time()) % 600 == 0:
                logging.info("Services healthy - Ollama and Fix It Fred running")
            
            time.sleep(30)  # Check every 30 seconds
            
        except KeyboardInterrupt:
            logging.info("Monitor stopped by user")
            break
        except Exception as e:
            logging.error(f"Monitor error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
EOF

# Create performance test script
cat > test-performance.py << 'EOF'
#!/usr/bin/env python3
"""Quick performance test for Ollama and Fix It Fred"""
import requests
import time
import json

def test_ollama():
    print("🧪 Testing Ollama performance...")
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': 'llama3.2:1b',
                'prompt': 'Hello, this is a quick test.',
                'stream': False
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            tokens = len(data.get('response', '').split())
            tokens_per_second = tokens / elapsed if elapsed > 0 else 0
            
            print(f"✅ Ollama Response Time: {elapsed:.2f}s")
            print(f"📊 Tokens per Second: {tokens_per_second:.1f}")
            return True
        else:
            print(f"❌ Ollama Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama Test Failed: {e}")
        return False

def test_fix_it_fred():
    print("\n🤖 Testing Fix It Fred performance...")
    start_time = time.time()
    
    try:
        response = requests.post(
            'http://localhost:9000/api/chat',
            json={
                'message': 'Quick test - what maintenance should I do?',
                'provider': 'ollama',
                'model': 'llama3.2:1b'
            },
            timeout=30
        )
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Fix It Fred Response Time: {elapsed:.2f}s")
            print(f"🎯 Success: {data.get('success', False)}")
            return True
        else:
            print(f"❌ Fix It Fred Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Fix It Fred Test Failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ChatterFix AI Performance Test")
    print("=" * 40)
    
    ollama_ok = test_ollama()
    fred_ok = test_fix_it_fred()
    
    print("\n📊 SUMMARY:")
    print(f"Ollama: {'✅ HEALTHY' if ollama_ok else '❌ NEEDS ATTENTION'}")
    print(f"Fix It Fred: {'✅ HEALTHY' if fred_ok else '❌ NEEDS ATTENTION'}")
    
    if ollama_ok and fred_ok:
        print("\n🎉 All systems optimal!")
    else:
        print("\n⚠️  Some services need attention")
EOF

# Create deployment script
cat > deploy-optimizations.sh << 'EOF'
#!/bin/bash
echo "🚀 Deploying Ollama Optimizations to VM..."

# Stop existing services
sudo systemctl stop ollama || true
sudo pkill -f ollama || true
sudo pkill -f fix_it_fred || true

# Apply Ollama optimizations
sudo mkdir -p /etc/systemd/system
sudo cp ollama.service /etc/systemd/system/
sudo cp fix-it-fred.service /etc/systemd/system/
sudo systemctl daemon-reload

# Install monitor as service
sudo cp monitor-services.py /usr/local/bin/
sudo chmod +x /usr/local/bin/monitor-services.py

# Start services
sudo systemctl enable ollama
sudo systemctl enable fix-it-fred
sudo systemctl start ollama

# Wait for Ollama to start
sleep 10

# Load optimized model
sudo -u root /usr/local/bin/ollama pull llama3.2:1b

# Start Fix It Fred
sudo systemctl start fix-it-fred

# Wait and test
sleep 15
python3 test-performance.py

echo "✅ Optimization deployment complete!"
echo "📊 Services status:"
sudo systemctl status ollama --no-pager
sudo systemctl status fix-it-fred --no-pager

echo ""
echo "🔧 To monitor services:"
echo "sudo journalctl -u ollama -f"
echo "sudo journalctl -u fix-it-fred -f"
echo ""
echo "🧪 To test performance:"
echo "python3 test-performance.py"
EOF

chmod +x *.sh *.py

echo ""
echo "🎯 OLLAMA OPTIMIZATION PACKAGE READY!"
echo "===================================="
echo ""
echo "📁 Created files:"
echo "  • ollama-optimized.env - Performance tuning"
echo "  • ollama.service - Systemd service"
echo "  • fix-it-fred.service - Systemd service"
echo "  • monitor-services.py - Auto-monitoring"
echo "  • test-performance.py - Performance testing"
echo "  • deploy-optimizations.sh - Complete deployment"
echo ""
echo "🚀 To deploy to your VM:"
echo "  scp -r . chatterfix-cmms-production:/tmp/ollama-optimization"
echo "  ssh chatterfix-cmms-production 'cd /tmp/ollama-optimization && sudo ./deploy-optimizations.sh'"
echo ""
echo "🎯 Expected results:"
echo "  • Response times: 3-8 seconds"
echo "  • Auto-restart on failures"
echo "  • Reliable production operation"
echo "  • Performance monitoring"