#!/usr/bin/env python3
"""Setup development environment for ChatterFix CMMS."""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Set up the development environment."""
    print("🚀 Setting up ChatterFix CMMS development environment...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️ Warning: Not running in a virtual environment!")
        response = input("Continue anyway? (y/N): ").lower()
        if response != 'y':
            print("Exiting. Please activate a virtual environment first.")
            sys.exit(1)
    
    # Install development dependencies
    if not run_command("pip install -r requirements-dev.txt", "Installing development dependencies"):
        return False
    
    # Install pre-commit hooks
    if not run_command("pre-commit install", "Installing pre-commit hooks"):
        return False
    
    # Run initial code formatting
    print("🎨 Running initial code formatting...")
    run_command("black app/ *.py", "Formatting with black")
    run_command("isort app/ *.py", "Sorting imports")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    print("\n✅ Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Run 'make format' to format your code")
    print("2. Run 'make lint' to check code quality")
    print("3. Run 'make test' to run tests")
    print("4. Run 'make run' to start the development server")
    print("5. Use 'make help' to see all available commands")


if __name__ == "__main__":
    main()