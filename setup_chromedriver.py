#!/usr/bin/env python3
"""
Setup script to ensure ChromeDriver is properly installed
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys

def setup_chromedriver():
    """Download and setup ChromeDriver automatically"""
    try:
        print("Setting up ChromeDriver...")
        
        # This will download ChromeDriver if not present
        service = Service(ChromeDriverManager().install())
        
        # Test if it works
        driver = webdriver.Chrome(service=service)
        print("ChromeDriver setup successful!")
        driver.quit()
        
        return True
        
    except Exception as e:
        print(f"Error setting up ChromeDriver: {str(e)}")
        print("\nPlease ensure Google Chrome is installed on your system.")
        print("You can download it from: https://www.google.com/chrome/")
        return False

if __name__ == "__main__":
    if setup_chromedriver():
        print("\nChromeDriver is ready! You can now run the main script.")
        sys.exit(0)
    else:
        sys.exit(1)