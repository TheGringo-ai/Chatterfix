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
