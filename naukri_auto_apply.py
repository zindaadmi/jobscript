#!/usr/bin/env python3
"""
Naukri.com Job Auto-Apply Script
Automates job applications for Backend Java Developer positions with 3+ years experience.
Shortlists jobs requiring manual intervention.
"""

import os
import time
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import dotenv

# Load environment variables
dotenv.load_dotenv()

class NaukriJobApplier:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_driver()
        self.applied_jobs = self.load_applied_jobs()
        self.shortlisted_jobs = []
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('naukri_job_apply.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_config(self):
        """Load configuration from environment variables and config file"""
        self.config = {
            'email': os.getenv('NAUKRI_EMAIL'),
            'password': os.getenv('NAUKRI_PASSWORD'),
            'job_keywords': ['Backend Java Developer', 'Java Developer', 'Spring Boot Developer', 'Backend Developer Java'],
            'min_experience': 3,
            'max_experience': 8,
            'locations': ['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai', 'Delhi NCR', 'Remote'],
            'skills': ['Java', 'Spring Boot', 'Microservices', 'REST API', 'Spring Framework'],
            'max_applications_per_run': 20,
            'delay_between_applications': 5  # seconds
        }
        
        # Load additional config from file if exists
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                file_config = json.load(f)
                self.config.update(file_config)
                
        if not self.config['email'] or not self.config['password']:
            raise ValueError("Please set NAUKRI_EMAIL and NAUKRI_PASSWORD in .env file")
            
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Run in headless mode if specified
        if os.getenv('HEADLESS', 'false').lower() == 'true':
            chrome_options.add_argument('--headless')
            
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
        
    def load_applied_jobs(self) -> set:
        """Load previously applied job IDs"""
        applied_jobs = set()
        if os.path.exists('applied_jobs.csv'):
            try:
                df = pd.read_csv('applied_jobs.csv')
                applied_jobs = set(df['job_id'].astype(str))
            except Exception as e:
                self.logger.warning(f"Error loading applied jobs: {e}")
        return applied_jobs
        
    def save_applied_job(self, job_info: Dict):
        """Save applied job information to CSV"""
        file_exists = os.path.exists('applied_jobs.csv')
        with open('applied_jobs.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['job_id', 'title', 'company', 'location', 'experience', 'applied_date', 'status'])
            writer.writerow([
                job_info.get('job_id', ''),
                job_info.get('title', ''),
                job_info.get('company', ''),
                job_info.get('location', ''),
                job_info.get('experience', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'applied'
            ])
            
    def save_shortlisted_job(self, job_info: Dict):
        """Save shortlisted job information to CSV"""
        file_exists = os.path.exists('shortlisted_jobs.csv')
        with open('shortlisted_jobs.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['job_id', 'title', 'company', 'location', 'experience', 'url', 'reason', 'shortlisted_date'])
            writer.writerow([
                job_info.get('job_id', ''),
                job_info.get('title', ''),
                job_info.get('company', ''),
                job_info.get('location', ''),
                job_info.get('experience', ''),
                job_info.get('url', ''),
                job_info.get('reason', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
            
    def login(self):
        """Login to Naukri.com"""
        try:
            self.logger.info("Logging in to Naukri.com...")
            self.driver.get("https://www.naukri.com/nlogin/login")
            
            # Wait for login form
            email_input = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            password_input = self.driver.find_element(By.ID, "passwordField")
            
            email_input.clear()
            email_input.send_keys(self.config['email'])
            password_input.clear()
            password_input.send_keys(self.config['password'])
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "nI-gNb-drawer__icon")))
            self.logger.info("Successfully logged in!")
            time.sleep(3)
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            raise
            
    def search_jobs(self, keyword: str, location: str = "") -> List[str]:
        """Search for jobs with given keyword and location"""
        try:
            search_url = f"https://www.naukri.com/{keyword.replace(' ', '-').lower()}-jobs"
            if location:
                search_url += f"-in-{location.replace(' ', '-').lower()}"
                
            # Add experience filter
            search_url += f"?experience={self.config['min_experience']}"
            
            self.logger.info(f"Searching jobs: {search_url}")
            self.driver.get(search_url)
            time.sleep(3)
            
            # Get job URLs from search results
            job_urls = []
            try:
                job_elements = self.driver.find_elements(By.CSS_SELECTOR, ".srp-jobtuple-wrapper .title a")
                for element in job_elements[:self.config['max_applications_per_run']]:
                    job_url = element.get_attribute('href')
                    if job_url:
                        job_urls.append(job_url)
                        
            except NoSuchElementException:
                self.logger.warning("No job elements found on search page")
                
            self.logger.info(f"Found {len(job_urls)} jobs")
            return job_urls
            
        except Exception as e:
            self.logger.error(f"Error searching jobs: {e}")
            return []
            
    def extract_job_info(self, job_url: str) -> Dict:
        """Extract job information from job page"""
        try:
            self.driver.get(job_url)
            time.sleep(2)
            
            job_info = {'url': job_url}
            
            # Extract job ID from URL
            job_id = job_url.split('/')[-1] if '/' in job_url else job_url
            job_info['job_id'] = job_id
            
            # Extract job title
            try:
                title_element = self.driver.find_element(By.CSS_SELECTOR, ".jd-header-title")
                job_info['title'] = title_element.text.strip()
            except NoSuchElementException:
                job_info['title'] = "N/A"
                
            # Extract company name
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, ".jd-header-comp-name")
                job_info['company'] = company_element.text.strip()
            except NoSuchElementException:
                job_info['company'] = "N/A"
                
            # Extract location
            try:
                location_element = self.driver.find_element(By.CSS_SELECTOR, ".jd-location")
                job_info['location'] = location_element.text.strip()
            except NoSuchElementException:
                job_info['location'] = "N/A"
                
            # Extract experience requirement
            try:
                exp_element = self.driver.find_element(By.CSS_SELECTOR, ".jd-exp")
                job_info['experience'] = exp_element.text.strip()
            except NoSuchElementException:
                job_info['experience'] = "N/A"
                
            return job_info
            
        except Exception as e:
            self.logger.error(f"Error extracting job info from {job_url}: {e}")
            return {'url': job_url, 'job_id': job_url, 'title': 'N/A', 'company': 'N/A', 'location': 'N/A', 'experience': 'N/A'}
            
    def check_if_external_application(self) -> bool:
        """Check if job requires external application"""
        try:
            # Look for external application indicators
            external_indicators = [
                "Apply on company website",
                "Visit company website",
                "External application",
                "Apply directly",
                "Redirect to"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in external_indicators:
                if indicator.lower() in page_text:
                    return True
                    
            # Check for external links in apply button
            try:
                apply_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".jd-header-btn-wrapper a, .apply-button a")
                for button in apply_buttons:
                    href = button.get_attribute('href')
                    if href and 'naukri.com' not in href:
                        return True
            except:
                pass
                
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking external application: {e}")
            return False
            
    def has_application_questions(self) -> bool:
        """Check if job application has additional questions"""
        try:
            # Look for common question indicators
            question_indicators = [
                "questionnaire",
                "additional information",
                "cover letter",
                "why should we hire you",
                "tell us about yourself"
            ]
            
            page_text = self.driver.page_source.lower()
            for indicator in question_indicators:
                if indicator in page_text:
                    return True
                    
            # Check for form elements that might indicate questions
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']:not([name='email']):not([name='phone'])")
            return len(form_elements) > 0
            
        except Exception as e:
            self.logger.error(f"Error checking application questions: {e}")
            return False
            
    def apply_to_job(self, job_info: Dict) -> bool:
        """Apply to a job if possible, otherwise shortlist it"""
        try:
            job_id = job_info['job_id']
            
            # Skip if already applied
            if job_id in self.applied_jobs:
                self.logger.info(f"Already applied to job: {job_info['title']}")
                return False
                
            self.logger.info(f"Processing job: {job_info['title']} at {job_info['company']}")
            
            # Check if external application required
            if self.check_if_external_application():
                job_info['reason'] = "External application required"
                self.save_shortlisted_job(job_info)
                self.shortlisted_jobs.append(job_info)
                self.logger.info(f"Shortlisted job (external): {job_info['title']}")
                return False
                
            # Check if has additional questions
            if self.has_application_questions():
                job_info['reason'] = "Additional questions/details required"
                self.save_shortlisted_job(job_info)
                self.shortlisted_jobs.append(job_info)
                self.logger.info(f"Shortlisted job (questions): {job_info['title']}")
                return False
                
            # Try to apply automatically
            apply_button = None
            try:
                # Look for apply button
                apply_selectors = [
                    ".jd-header-btn-wrapper .btn-apply",
                    ".apply-button",
                    "button[data-job-id]",
                    ".btn-apply"
                ]
                
                for selector in apply_selectors:
                    try:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if apply_button.is_displayed() and apply_button.is_enabled():
                            break
                    except NoSuchElementException:
                        continue
                        
                if not apply_button:
                    raise NoSuchElementException("No apply button found")
                    
                # Click apply button
                self.driver.execute_script("arguments[0].click();", apply_button)
                time.sleep(2)
                
                # Handle any popup confirmations
                try:
                    confirm_button = self.driver.find_element(By.CSS_SELECTOR, ".confirm-apply, .apply-confirm")
                    confirm_button.click()
                    time.sleep(1)
                except NoSuchElementException:
                    pass
                    
                # Check for success message or applied status
                success_indicators = ["applied successfully", "application submitted", "applied"]
                page_text = self.driver.page_source.lower()
                
                applied_successfully = any(indicator in page_text for indicator in success_indicators)
                
                if applied_successfully:
                    self.save_applied_job(job_info)
                    self.applied_jobs.add(job_id)
                    self.logger.info(f"Successfully applied to: {job_info['title']}")
                    return True
                else:
                    job_info['reason'] = "Application process unclear"
                    self.save_shortlisted_job(job_info)
                    self.shortlisted_jobs.append(job_info)
                    self.logger.info(f"Shortlisted job (unclear process): {job_info['title']}")
                    return False
                    
            except Exception as e:
                job_info['reason'] = f"Application failed: {str(e)}"
                self.save_shortlisted_job(job_info)
                self.shortlisted_jobs.append(job_info)
                self.logger.warning(f"Failed to apply to {job_info['title']}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing job {job_info.get('title', 'Unknown')}: {e}")
            return False
            
    def run(self):
        """Main execution function"""
        try:
            self.logger.info("Starting Naukri job application automation...")
            
            # Login
            self.login()
            
            applications_made = 0
            
            # Search for each keyword
            for keyword in self.config['job_keywords']:
                if applications_made >= self.config['max_applications_per_run']:
                    break
                    
                self.logger.info(f"Searching for: {keyword}")
                
                # Search in different locations
                for location in self.config['locations']:
                    if applications_made >= self.config['max_applications_per_run']:
                        break
                        
                    job_urls = self.search_jobs(keyword, location)
                    
                    for job_url in job_urls:
                        if applications_made >= self.config['max_applications_per_run']:
                            break
                            
                        # Extract job information
                        job_info = self.extract_job_info(job_url)
                        
                        # Apply to job
                        if self.apply_to_job(job_info):
                            applications_made += 1
                            
                        # Delay between applications
                        time.sleep(self.config['delay_between_applications'])
                        
            self.logger.info(f"Automation completed. Applied to {applications_made} jobs.")
            self.logger.info(f"Shortlisted {len(self.shortlisted_jobs)} jobs for manual application.")
            
            # Print summary
            print(f"\n=== SUMMARY ===")
            print(f"Applications made: {applications_made}")
            print(f"Jobs shortlisted: {len(self.shortlisted_jobs)}")
            print(f"Check 'applied_jobs.csv' for applied jobs")
            print(f"Check 'shortlisted_jobs.csv' for jobs requiring manual application")
            
        except Exception as e:
            self.logger.error(f"Error in main execution: {e}")
            raise
        finally:
            self.driver.quit()
            
if __name__ == "__main__":
    try:
        applier = NaukriJobApplier()
        applier.run()
    except KeyboardInterrupt:
        print("\nScript interrupted by user")
    except Exception as e:
        print(f"Script failed: {e}")
        logging.error(f"Script failed: {e}")