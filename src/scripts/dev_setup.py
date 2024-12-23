import os
import subprocess
import sys
from pathlib import Path

def setup_dev_environment():
    """Setup development environment."""
    print("Setting up development environment for Algame...")

    # Get project root directory
    root_dir = Path(__file__).parent.parent

    # Install package in development mode
    print("\nInstalling package in development mode...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])

    # Install development requirements
    print("\nInstalling development requirements...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"])

    print("\nSetup complete! You can now run:")
    print("- 'python -m algame.gui' to start the GUI")
    print("- 'pytest tests/' to run tests")
    print("- 'python examples/basic_usage.py' to run example code")

if __name__ == "__main__":
    setup_dev_environment()
