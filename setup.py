#!/usr/bin/env python3
"""
Setup script for Naukri Auto Apply
Helps users set up the environment and configuration
"""

import os
import json
import getpass

def create_env_file():
    """Create .env file with user credentials"""
    print("=== Naukri.com Credentials Setup ===")
    email = input("Enter your Naukri.com email: ")
    password = getpass.getpass("Enter your Naukri.com password: ")
    
    headless = input("Run in headless mode? (y/n, default: n): ").lower().strip()
    headless_value = "true" if headless == 'y' else "false"
    
    env_content = f"""# Naukri.com Credentials
NAUKRI_EMAIL={email}
NAUKRI_PASSWORD={password}

# Optional Settings
HEADLESS={headless_value}  # Set to true to run browser in background"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")

def customize_config():
    """Allow user to customize job search configuration"""
    print("\n=== Job Search Configuration ===")
    
    # Load default config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    print("Current configuration:")
    print(f"Keywords: {', '.join(config['job_keywords'])}")
    print(f"Experience: {config['min_experience']}-{config['max_experience']} years")
    print(f"Locations: {', '.join(config['locations'])}")
    print(f"Max applications per run: {config['max_applications_per_run']}")
    
    customize = input("\nDo you want to customize these settings? (y/n, default: n): ").lower().strip()
    
    if customize == 'y':
        # Customize keywords
        new_keywords = input(f"Enter job keywords (comma-separated, press Enter to keep current): ").strip()
        if new_keywords:
            config['job_keywords'] = [k.strip() for k in new_keywords.split(',')]
        
        # Customize experience
        try:
            min_exp = input(f"Minimum experience (current: {config['min_experience']}): ").strip()
            if min_exp:
                config['min_experience'] = int(min_exp)
                
            max_exp = input(f"Maximum experience (current: {config['max_experience']}): ").strip()
            if max_exp:
                config['max_experience'] = int(max_exp)
        except ValueError:
            print("Invalid experience values, keeping current settings")
        
        # Customize locations
        new_locations = input(f"Enter preferred locations (comma-separated, press Enter to keep current): ").strip()
        if new_locations:
            config['locations'] = [l.strip() for l in new_locations.split(',')]
        
        # Customize max applications
        try:
            max_apps = input(f"Maximum applications per run (current: {config['max_applications_per_run']}): ").strip()
            if max_apps:
                config['max_applications_per_run'] = int(max_apps)
        except ValueError:
            print("Invalid number, keeping current setting")
        
        # Save updated config
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration updated successfully!")
    
    return config

def main():
    """Main setup function"""
    print("🚀 Naukri Auto Apply Setup")
    print("=" * 30)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        create_env_file()
    else:
        update_env = input(".env file already exists. Update it? (y/n, default: n): ").lower().strip()
        if update_env == 'y':
            create_env_file()
    
    # Customize configuration
    config = customize_config()
    
    print("\n=== Setup Complete! ===")
    print("✅ Environment configured")
    print("✅ Job search preferences set")
    print(f"✅ Ready to search for {len(config['job_keywords'])} types of jobs")
    print(f"✅ Will apply to maximum {config['max_applications_per_run']} jobs per run")
    
    print("\n📋 Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the script: python naukri_auto_apply.py")
    print("3. Check applied_jobs.csv and shortlisted_jobs.csv for results")
    
    print("\n⚠️  Important Notes:")
    print("- Ensure your Naukri profile is complete and updated")
    print("- Review shortlisted jobs manually for better success rates")
    print("- Use responsibly and comply with Naukri.com terms of service")

if __name__ == "__main__":
    main()