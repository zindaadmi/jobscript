#!/usr/bin/env python3
"""
Naukri.com Job Application Automation Script
Automatically applies to Java backend developer jobs with 3+ years experience
Shortlists jobs requiring external applications or additional details
"""

import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('naukri_job_application.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NaukriJobApplier:
    def __init__(self, config_file: str = 'config.json'):
        """Initialize the Naukri job applier with configuration"""
        self.config = self._load_config(config_file)
        self.driver = None
        self.wait = None
        self.applied_jobs = []
        self.shortlisted_jobs = []
        self.failed_jobs = []
        
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found!")
            raise
            
    def setup_driver(self):
        """Setup Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Add headless mode if specified in config
        if self.config.get('headless', False):
            chrome_options.add_argument("--headless")
            
        # Use webdriver-manager to handle ChromeDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        logger.info("Chrome driver initialized successfully")
        
    def login(self):
        """Login to Naukri.com"""
        try:
            logger.info("Logging into Naukri.com...")
            self.driver.get("https://www.naukri.com/nlogin/login")
            time.sleep(2)
            
            # Enter username
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            username_field.send_keys(self.config['username'])
            
            # Enter password
            password_field = self.driver.find_element(By.ID, "passwordField")
            password_field.send_keys(self.config['password'])
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            if "home" in self.driver.current_url or "mnjuser" in self.driver.current_url:
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed!")
                return False
                
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            return False
            
    def search_jobs(self):
        """Search for Java backend developer jobs with 3+ years experience"""
        try:
            logger.info("Searching for jobs...")
            
            # Navigate to job search
            self.driver.get("https://www.naukri.com/jobs")
            time.sleep(3)
            
            # Enter search keywords
            search_box = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "suggestor-input"))
            )
            search_box.clear()
            search_keywords = self.config.get('search_keywords', 'java backend developer springboot')
            search_box.send_keys(search_keywords)
            time.sleep(1)
            
            # Enter location if specified
            if 'location' in self.config:
                location_box = self.driver.find_elements(By.CLASS_NAME, "suggestor-input")[1]
                location_box.clear()
                location_box.send_keys(self.config['location'])
                time.sleep(1)
                
            # Click search button
            search_button = self.driver.find_element(By.CLASS_NAME, "qsbSubmit")
            search_button.click()
            
            time.sleep(3)
            
            # Apply experience filter (3+ years)
            self._apply_experience_filter()
            
            logger.info("Job search completed")
            
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}")
            
    def _apply_experience_filter(self):
        """Apply experience filter for 3+ years"""
        try:
            # Click on experience filter
            exp_filter = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Experience')]"))
            )
            exp_filter.click()
            time.sleep(1)
            
            # Select 3-6 years or similar options
            exp_options = self.driver.find_elements(By.XPATH, "//label[contains(@for,'exp_')]")
            for option in exp_options:
                text = option.text.lower()
                if any(x in text for x in ['3-6', '3-5', '3-7', '3 to', '4-7', '5-']):
                    option.click()
                    logger.info(f"Selected experience filter: {option.text}")
                    
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"Could not apply experience filter: {str(e)}")
            
    def get_job_listings(self) -> List[Dict]:
        """Get all job listings from current page"""
        jobs = []
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "jobTuple")
            
            for card in job_cards:
                try:
                    job_data = {
                        'title': card.find_element(By.CLASS_NAME, "title").text,
                        'company': card.find_element(By.CLASS_NAME, "subTitle").text,
                        'experience': card.find_element(By.CLASS_NAME, "experience").text,
                        'salary': self._safe_get_text(card, By.CLASS_NAME, "salary"),
                        'location': card.find_element(By.CLASS_NAME, "location").text,
                        'job_id': card.get_attribute("data-job-id"),
                        'link': card.find_element(By.CLASS_NAME, "title").get_attribute("href")
                    }
                    jobs.append(job_data)
                except Exception as e:
                    logger.warning(f"Error parsing job card: {str(e)}")
                    continue
                    
            logger.info(f"Found {len(jobs)} jobs on current page")
            return jobs
            
        except Exception as e:
            logger.error(f"Error getting job listings: {str(e)}")
            return []
            
    def _safe_get_text(self, element, by, value):
        """Safely get text from element, return empty string if not found"""
        try:
            return element.find_element(by, value).text
        except:
            return ""
            
    def apply_to_job(self, job: Dict) -> str:
        """
        Apply to a specific job
        Returns: 'applied', 'shortlisted', or 'failed'
        """
        try:
            logger.info(f"Attempting to apply to: {job['title']} at {job['company']}")
            
            # Open job in new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(job['link'])
            time.sleep(3)
            
            # Check if it's an external application
            if self._is_external_application():
                logger.info("External application detected - shortlisting")
                self.shortlisted_jobs.append({
                    **job,
                    'reason': 'External application required',
                    'timestamp': datetime.now().isoformat()
                })
                self._close_current_tab()
                return 'shortlisted'
                
            # Check if additional details are required
            if self._requires_additional_details():
                logger.info("Additional details required - shortlisting")
                self.shortlisted_jobs.append({
                    **job,
                    'reason': 'Additional details required',
                    'timestamp': datetime.now().isoformat()
                })
                self._close_current_tab()
                return 'shortlisted'
                
            # Try to apply
            apply_button = self._find_apply_button()
            if apply_button:
                apply_button.click()
                time.sleep(2)
                
                # Handle any popups or confirmations
                if self._handle_application_popup():
                    logger.info(f"Successfully applied to job: {job['title']}")
                    self.applied_jobs.append({
                        **job,
                        'timestamp': datetime.now().isoformat()
                    })
                    self._close_current_tab()
                    return 'applied'
                else:
                    logger.warning("Could not complete application")
                    self.failed_jobs.append({
                        **job,
                        'reason': 'Application popup handling failed',
                        'timestamp': datetime.now().isoformat()
                    })
                    self._close_current_tab()
                    return 'failed'
            else:
                logger.warning("Apply button not found")
                self.failed_jobs.append({
                    **job,
                    'reason': 'Apply button not found',
                    'timestamp': datetime.now().isoformat()
                })
                self._close_current_tab()
                return 'failed'
                
        except Exception as e:
            logger.error(f"Error applying to job: {str(e)}")
            self.failed_jobs.append({
                **job,
                'reason': f'Exception: {str(e)}',
                'timestamp': datetime.now().isoformat()
            })
            self._close_current_tab()
            return 'failed'
            
    def _is_external_application(self) -> bool:
        """Check if job requires external application"""
        try:
            # Check for external application indicators
            external_indicators = [
                "apply on company site",
                "apply on company website",
                "external site",
                "redirected to",
                "company career page",
                "external job board"
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for indicator in external_indicators:
                if indicator in page_text:
                    return True
                    
            # Check for external links in apply button
            apply_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply')]")
            for button in apply_buttons:
                onclick = button.get_attribute("onclick") or ""
                if "external" in onclick.lower() or "redirect" in onclick.lower():
                    return True
                    
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for external application: {str(e)}")
            return False
            
    def _requires_additional_details(self) -> bool:
        """Check if job application requires additional details"""
        try:
            # Check for questionnaire or additional forms
            additional_indicators = [
                "answer the following",
                "additional questions",
                "questionnaire",
                "screening questions",
                "please provide",
                "tell us about",
                "why do you want"
            ]
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for indicator in additional_indicators:
                if indicator in page_text:
                    return True
                    
            # Check for form fields beyond basic application
            form_fields = self.driver.find_elements(By.XPATH, "//input[@type='text'] | //textarea")
            if len(form_fields) > 5:  # More than typical resume upload form
                return True
                
            return False
            
        except Exception as e:
            logger.warning(f"Error checking for additional details: {str(e)}")
            return False
            
    def _find_apply_button(self):
        """Find and return the apply button element"""
        try:
            # Try different selectors for apply button
            selectors = [
                (By.ID, "apply-button"),
                (By.CLASS_NAME, "apply-button"),
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//button[contains(text(), 'Apply Now')]"),
                (By.XPATH, "//button[contains(@class, 'apply')]"),
                (By.XPATH, "//a[contains(text(), 'Apply')]")
            ]
            
            for by, value in selectors:
                try:
                    button = self.driver.find_element(by, value)
                    if button.is_displayed() and button.is_enabled():
                        return button
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logger.error(f"Error finding apply button: {str(e)}")
            return None
            
    def _handle_application_popup(self) -> bool:
        """Handle application confirmation popup"""
        try:
            # Wait for popup to appear
            time.sleep(2)
            
            # Check if application was already submitted
            if "already applied" in self.driver.page_source.lower():
                logger.info("Already applied to this job")
                return False
                
            # Look for confirmation button
            confirm_selectors = [
                (By.XPATH, "//button[contains(text(), 'Submit')]"),
                (By.XPATH, "//button[contains(text(), 'Send')]"),
                (By.XPATH, "//button[contains(text(), 'Apply')]"),
                (By.XPATH, "//button[contains(text(), 'Yes')]"),
                (By.XPATH, "//button[contains(text(), 'Confirm')]")
            ]
            
            for by, value in confirm_selectors:
                try:
                    confirm_button = self.driver.find_element(by, value)
                    if confirm_button.is_displayed() and confirm_button.is_enabled():
                        confirm_button.click()
                        time.sleep(2)
                        return True
                except:
                    continue
                    
            # If no popup, assume application was successful
            return True
            
        except Exception as e:
            logger.error(f"Error handling application popup: {str(e)}")
            return False
            
    def _close_current_tab(self):
        """Close current tab and switch back to main window"""
        try:
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
        except:
            pass
            
    def navigate_to_next_page(self) -> bool:
        """Navigate to next page of job listings"""
        try:
            next_button = self.driver.find_element(By.XPATH, "//a[contains(@class, 'fright') and contains(text(), 'Next')]")
            if next_button.is_enabled():
                next_button.click()
                time.sleep(3)
                return True
            return False
        except:
            logger.info("No more pages to navigate")
            return False
            
    def save_results(self):
        """Save application results to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save applied jobs
        if self.applied_jobs:
            df_applied = pd.DataFrame(self.applied_jobs)
            df_applied.to_csv(f"applied_jobs_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.applied_jobs)} applied jobs")
            
        # Save shortlisted jobs for manual application
        if self.shortlisted_jobs:
            df_shortlisted = pd.DataFrame(self.shortlisted_jobs)
            df_shortlisted.to_csv(f"shortlisted_jobs_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.shortlisted_jobs)} shortlisted jobs")
            
        # Save failed jobs
        if self.failed_jobs:
            df_failed = pd.DataFrame(self.failed_jobs)
            df_failed.to_csv(f"failed_jobs_{timestamp}.csv", index=False)
            logger.info(f"Saved {len(self.failed_jobs)} failed jobs")
            
        # Save summary
        summary = {
            'total_applied': len(self.applied_jobs),
            'total_shortlisted': len(self.shortlisted_jobs),
            'total_failed': len(self.failed_jobs),
            'timestamp': timestamp
        }
        
        with open(f"application_summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2)
            
    def run(self, max_applications: int = 50, max_pages: int = 10):
        """Main execution function"""
        try:
            self.setup_driver()
            
            if not self.login():
                logger.error("Login failed. Exiting...")
                return
                
            self.search_jobs()
            
            applications_count = 0
            page_count = 0
            
            while applications_count < max_applications and page_count < max_pages:
                logger.info(f"Processing page {page_count + 1}")
                
                jobs = self.get_job_listings()
                
                for job in jobs:
                    if applications_count >= max_applications:
                        break
                        
                    # Skip if already applied (check job_id)
                    if any(j.get('job_id') == job['job_id'] for j in self.applied_jobs):
                        continue
                        
                    result = self.apply_to_job(job)
                    
                    if result == 'applied':
                        applications_count += 1
                        
                    # Add delay between applications
                    time.sleep(self.config.get('delay_between_applications', 5))
                    
                # Try to go to next page
                if not self.navigate_to_next_page():
                    break
                    
                page_count += 1
                
            logger.info(f"Completed! Applied to {applications_count} jobs")
            
            # Save results
            self.save_results()
            
        except Exception as e:
            logger.error(f"Error in main execution: {str(e)}")
            
        finally:
            if self.driver:
                self.driver.quit()
                

if __name__ == "__main__":
    applier = NaukriJobApplier()
    applier.run(max_applications=50, max_pages=10)