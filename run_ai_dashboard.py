#!/usr/bin/env python3
"""
🚀 AI TEAM DASHBOARD LAUNCHER
============================
Quick launcher for the AI Team Dashboard.

Usage:
    python run_ai_dashboard.py

The dashboard will be available at: http://localhost:8888
"""

import os
import platform
import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print the AI Team Dashboard banner"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║                  🚀 AI TEAM DASHBOARD                      ║
║                                                            ║
║  Comprehensive monitoring and control for your AI team    ║
║                                                            ║
║  Features:                                                 ║
║  • Real-time system monitoring                           ║
║  • Memory system analytics                               ║
║  • Team collaboration tools                              ║
║  • Pattern analysis and learning insights               ║
║  • Interactive WebSocket updates                         ║
║                                                            ║
║  Access: http://localhost:8888                           ║
╚════════════════════════════════════════════════════════════╝
"""
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ["fastapi", "uvicorn", "aiofiles", "websockets"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Installing missing packages...")

        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {package}")
                return False

    return True


def open_browser():
    """Open the dashboard in the default browser"""
    url = "http://localhost:8888"

    try:
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", url])
        elif platform.system() == "Windows":  # Windows
            subprocess.run(["start", url], shell=True)
        elif platform.system() == "Linux":  # Linux
            subprocess.run(["xdg-open", url])

        print(f"🌐 Opening dashboard in browser: {url}")
    except Exception as e:
        print(f"ℹ️  Please open {url} manually in your browser")


def main():
    """Main launcher function"""
    print_banner()

    # Check if we're in the right directory
    project_root = Path(__file__).parent
    dashboard_script = project_root / "ai_team" / "local_dashboard.py"

    if not dashboard_script.exists():
        print("❌ Error: AI Team Dashboard script not found!")
        print(f"   Expected: {dashboard_script}")
        sys.exit(1)

    print("🔍 Checking dependencies...")
    if not check_dependencies():
        print("❌ Failed to install required dependencies")
        sys.exit(1)

    print("✅ All dependencies are available")
    print("🚀 Starting AI Team Dashboard...")

    # Change to the project directory
    os.chdir(project_root)

    # Start the dashboard in a separate process
    try:
        # Open browser after a short delay
        import threading
        import time

        def delayed_browser_open():
            time.sleep(3)  # Wait for server to start
            open_browser()

        browser_thread = threading.Thread(target=delayed_browser_open)
        browser_thread.daemon = True
        browser_thread.start()

        # Run the dashboard
        subprocess.run([sys.executable, str(dashboard_script)])

    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
