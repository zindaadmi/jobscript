#!/usr/bin/env python3
"""
Launcher script for Naukri Job Application Automation
"""

import sys
import os
import argparse
from pathlib import Path

def check_requirements():
    """Check if all requirements are met"""
    try:
        import selenium
        import requests
        import bs4
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_config():
    """Check if config file exists and is valid"""
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"❌ Config file {config_file} not found!")
        print("Please run: python setup.py")
        return False
    
    try:
        import json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        required_fields = ['email', 'password']
        for field in required_fields:
            if field not in config or not config[field]:
                print(f"❌ Missing or empty field '{field}' in config.json")
                return False
        
        if config['email'] == 'your_email@example.com':
            print("❌ Please update your email in config.json")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False

def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description='Naukri Job Application Automation')
    parser.add_argument('--version', choices=['basic', 'enhanced'], default='enhanced',
                       help='Choose version to run (default: enhanced)')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file (default: config.json)')
    parser.add_argument('--setup', action='store_true',
                       help='Run setup instead of main application')
    
    args = parser.parse_args()
    
    print("🚀 Naukri Job Application Automation")
    print("=" * 40)
    
    if args.setup:
        print("Running setup...")
        os.system("python setup.py")
        return
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check config
    if not check_config():
        sys.exit(1)
    
    # Create necessary directories
    Path('logs').mkdir(exist_ok=True)
    Path('output').mkdir(exist_ok=True)
    
    # Run the appropriate version
    if args.version == 'basic':
        print("Running basic version...")
        os.system(f"python naukri_job_applier.py")
    else:
        print("Running enhanced version...")
        os.system(f"python enhanced_naukri_applier.py")

if __name__ == "__main__":
    main()