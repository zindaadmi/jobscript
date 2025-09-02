#!/usr/bin/env python3
"""
Setup script for Naukri Job Application Automation
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def install_requirements():
    """Install required Python packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_config():
    """Setup configuration file with user input"""
    print("\n🔧 Setting up configuration...")
    
    config = {}
    
    # Get user credentials
    print("Enter your Naukri.com credentials:")
    config['email'] = input("Email: ").strip()
    config['password'] = input("Password: ").strip()
    
    # Get job preferences
    print("\nEnter your job preferences:")
    config['notice_period'] = input("Notice period (in days) [30]: ").strip() or "30"
    config['current_salary'] = input("Current salary (annual) [600000]: ").strip() or "600000"
    config['expected_salary'] = input("Expected salary (annual) [800000]: ").strip() or "800000"
    
    # Get preferred locations
    print("\nEnter preferred locations (comma-separated):")
    locations_input = input("Locations [Bangalore, Mumbai, Delhi, Pune, Hyderabad]: ").strip()
    if locations_input:
        config['preferred_locations'] = [loc.strip() for loc in locations_input.split(',')]
    else:
        config['preferred_locations'] = ["Bangalore", "Mumbai", "Delhi", "Pune", "Hyderabad"]
    
    # Get job keywords
    print("\nEnter job keywords (comma-separated):")
    keywords_input = input("Keywords [backend java developer, java spring boot, java backend]: ").strip()
    if keywords_input:
        config['job_keywords'] = [kw.strip() for kw in keywords_input.split(',')]
    else:
        config['job_keywords'] = ["backend java developer", "java spring boot", "java backend"]
    
    # Other settings
    config['experience_years'] = int(input("Minimum experience years [3]: ").strip() or "3")
    config['max_applications_per_run'] = int(input("Max applications per run [20]: ").strip() or "20")
    config['delay_between_applications'] = int(input("Delay between applications (seconds) [5]: ").strip() or "5")
    
    # Save config
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration saved to config.json!")
    return True

def check_chrome():
    """Check if Chrome browser is installed"""
    print("\n🔍 Checking Chrome browser...")
    
    chrome_paths = [
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Chrome browser found!")
            return True
    
    print("❌ Chrome browser not found. Please install Chrome browser.")
    print("Download from: https://www.google.com/chrome/")
    return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ['logs', 'output']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print("🚀 Naukri Job Application Automation Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required!")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check Chrome
    if not check_chrome():
        print("\n⚠️  Please install Chrome browser and run setup again.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup configuration
    if not setup_config():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Review and update config.json if needed")
    print("2. Ensure your Naukri.com profile is complete")
    print("3. Run: python naukri_job_applier.py")
    print("\nFor help, check README.md")

if __name__ == "__main__":
    main()