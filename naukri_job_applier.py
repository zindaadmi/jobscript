#!/usr/bin/env python3
"""
Naukri.com Job Application Automation Script
Automatically applies to backend Java developer jobs with 3+ years experience
"""

import time
import json
import csv
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import requests
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('naukri_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobDetails:
    """Data class to store job information"""
    title: str
    company: str
    location: str
    experience: str
    salary: str
    description: str
    url: str
    is_external: bool = False
    applied: bool = False
    application_date: Optional[str] = None

class NaukriJobApplier:
    """Main class for automating Naukri.com job applications"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.driver = None
        self.applied_jobs = self.load_applied_jobs()
        self.shortlisted_jobs = []
        self.setup_driver()
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_file} not found. Please create it first.")
            raise
    
    def load_applied_jobs(self) -> set:
        """Load previously applied jobs from CSV"""
        applied_jobs = set()
        try:
            with open('applied_jobs.csv', 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:
                        applied_jobs.add(row[0])  # Job URL
        except FileNotFoundError:
            logger.info("No previous applications found. Starting fresh.")
        return applied_jobs
    
    def save_applied_job(self, job_url: str, job_title: str, company: str):
        """Save applied job to CSV"""
        with open('applied_jobs.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Check if file is empty to write header
            if f.tell() == 0:
                writer.writerow(['URL', 'Title', 'Company', 'Applied Date'])
            writer.writerow([job_url, job_title, company, datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Uncomment the next line if you want to run headless
        # chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 10)
    
    def login(self):
        """Login to Naukri.com"""
        try:
            logger.info("Logging into Naukri.com...")
            self.driver.get("https://www.naukri.com/nlogin/login")
            
            # Wait for login form
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            password_field = self.driver.find_element(By.ID, "passwordField")
            
            # Enter credentials
            email_field.clear()
            email_field.send_keys(self.config['email'])
            password_field.clear()
            password_field.send_keys(self.config['password'])
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-name")))
            logger.info("Successfully logged in!")
            time.sleep(3)
            
        except TimeoutException:
            logger.error("Login failed - timeout waiting for elements")
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def search_jobs(self) -> List[JobDetails]:
        """Search for Java backend developer jobs"""
        jobs = []
        try:
            logger.info("Searching for Java backend developer jobs...")
            
            # Navigate to job search
            self.driver.get("https://www.naukri.com/jobs-in-india")
            time.sleep(3)
            
            # Search for Java backend jobs
            search_box = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "suggestor-input")))
            search_box.clear()
            search_box.send_keys("backend java developer spring boot")
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(3)
            
            # Apply experience filter (3+ years)
            try:
                exp_filter = self.driver.find_element(By.XPATH, "//span[contains(text(), '3-5 Yrs') or contains(text(), '3+ Yrs')]")
                exp_filter.click()
                time.sleep(2)
            except NoSuchElementException:
                logger.warning("Experience filter not found, continuing without filter")
            
            # Get job listings
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobTuple")
            
            for card in job_cards[:20]:  # Limit to first 20 jobs
                try:
                    job = self.extract_job_details(card)
                    if job and job.url not in self.applied_jobs:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error extracting job details: {str(e)}")
                    continue
            
            logger.info(f"Found {len(jobs)} new jobs to apply")
            return jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []
    
    def extract_job_details(self, card) -> Optional[JobDetails]:
        """Extract job details from job card element"""
        try:
            # Extract basic information
            title_elem = card.find_element(By.CSS_SELECTOR, ".title")
            title = title_elem.text.strip()
            
            company_elem = card.find_element(By.CSS_SELECTOR, ".subTitle")
            company = company_elem.text.strip()
            
            location_elem = card.find_element(By.CSS_SELECTOR, ".location")
            location = location_elem.text.strip()
            
            # Extract experience
            try:
                exp_elem = card.find_element(By.CSS_SELECTOR, ".experience")
                experience = exp_elem.text.strip()
            except NoSuchElementException:
                experience = "Not specified"
            
            # Extract salary
            try:
                salary_elem = card.find_element(By.CSS_SELECTOR, ".salary")
                salary = salary_elem.text.strip()
            except NoSuchElementException:
                salary = "Not specified"
            
            # Get job URL
            link_elem = card.find_element(By.CSS_SELECTOR, ".title a")
            job_url = link_elem.get_attribute("href")
            
            # Check if it's an external application
            is_external = self.is_external_application(job_url)
            
            return JobDetails(
                title=title,
                company=company,
                location=location,
                experience=experience,
                salary=salary,
                description="",  # Will be filled when applying
                url=job_url,
                is_external=is_external
            )
            
        except Exception as e:
            logger.warning(f"Error extracting job details: {str(e)}")
            return None
    
    def is_external_application(self, job_url: str) -> bool:
        """Check if job application is external (redirects to company website)"""
        try:
            # Check if URL contains external redirect indicators
            external_indicators = [
                'redirect', 'external', 'apply', 'careers', 'jobs'
            ]
            
            # Parse the URL to check domain
            parsed_url = urlparse(job_url)
            domain = parsed_url.netloc.lower()
            
            # If it's not naukri.com domain, it's likely external
            if 'naukri.com' not in domain:
                return True
            
            # Check for external redirect patterns in the URL
            for indicator in external_indicators:
                if indicator in job_url.lower():
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking external application: {str(e)}")
            return False
    
    def apply_to_job(self, job: JobDetails) -> bool:
        """Apply to a specific job"""
        try:
            logger.info(f"Applying to: {job.title} at {job.company}")
            
            # Open job in new tab
            self.driver.execute_script(f"window.open('{job.url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(3)
            
            # Check if it's an external application
            if job.is_external or self.is_external_application(self.driver.current_url):
                logger.info(f"External application detected for {job.title}. Shortlisting for manual application.")
                self.shortlisted_jobs.append(job)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
            
            # Look for apply button
            apply_button = None
            apply_selectors = [
                "//button[contains(text(), 'Apply')]",
                "//a[contains(text(), 'Apply')]",
                "//span[contains(text(), 'Apply')]",
                ".apply-button",
                "#apply-button"
            ]
            
            for selector in apply_selectors:
                try:
                    if selector.startswith("//"):
                        apply_button = self.driver.find_element(By.XPATH, selector)
                    else:
                        apply_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not apply_button:
                logger.warning(f"No apply button found for {job.title}")
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
            
            # Click apply button
            apply_button.click()
            time.sleep(3)
            
            # Handle application form if it appears
            if self.handle_application_form(job):
                # Mark as applied
                job.applied = True
                job.application_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.applied_jobs.add(job.url)
                self.save_applied_job(job.url, job.title, job.company)
                logger.info(f"Successfully applied to {job.title} at {job.company}")
                return True
            else:
                logger.warning(f"Failed to complete application for {job.title}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying to job {job.title}: {str(e)}")
            return False
        finally:
            # Close current tab and switch back to main tab
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
    
    def handle_application_form(self, job: JobDetails) -> bool:
        """Handle job application form filling"""
        try:
            # Wait for form to load
            time.sleep(2)
            
            # Check for additional questions or forms
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, "form, .application-form, .job-application")
            
            if not form_elements:
                # No additional form, application might be direct
                return True
            
            # Handle common form fields
            for form in form_elements:
                # Handle text inputs
                text_inputs = form.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
                for input_field in text_inputs:
                    field_name = input_field.get_attribute("name") or input_field.get_attribute("id") or ""
                    field_name = field_name.lower()
                    
                    if "experience" in field_name and "years" in field_name:
                        input_field.clear()
                        input_field.send_keys("3")
                    elif "notice" in field_name:
                        input_field.clear()
                        input_field.send_keys(self.config.get('notice_period', '30'))
                    elif "expected" in field_name and "salary" in field_name:
                        input_field.clear()
                        input_field.send_keys(self.config.get('expected_salary', '800000'))
                    elif "current" in field_name and "salary" in field_name:
                        input_field.clear()
                        input_field.send_keys(self.config.get('current_salary', '600000'))
                
                # Handle dropdowns
                dropdowns = form.find_elements(By.CSS_SELECTOR, "select")
                for dropdown in dropdowns:
                    try:
                        dropdown_name = dropdown.get_attribute("name") or dropdown.get_attribute("id") or ""
                        dropdown_name = dropdown_name.lower()
                        
                        if "experience" in dropdown_name:
                            # Select appropriate experience option
                            options = dropdown.find_elements(By.TAG_NAME, "option")
                            for option in options:
                                if "3" in option.text and ("year" in option.text.lower() or "yr" in option.text.lower()):
                                    option.click()
                                    break
                    except:
                        continue
                
                # Submit form if submit button exists
                submit_buttons = form.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .submit-btn")
                if submit_buttons:
                    submit_buttons[0].click()
                    time.sleep(3)
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling application form: {str(e)}")
            return False
    
    def save_shortlisted_jobs(self):
        """Save shortlisted jobs to CSV for manual application"""
        if not self.shortlisted_jobs:
            return
        
        filename = f"shortlisted_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Company', 'Location', 'Experience', 'Salary', 'URL', 'Reason'])
            
            for job in self.shortlisted_jobs:
                writer.writerow([
                    job.title,
                    job.company,
                    job.location,
                    job.experience,
                    job.salary,
                    job.url,
                    'External application or requires manual review'
                ])
        
        logger.info(f"Shortlisted {len(self.shortlisted_jobs)} jobs saved to {filename}")
    
    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting Naukri job application automation...")
            
            # Login
            self.login()
            
            # Search for jobs
            jobs = self.search_jobs()
            
            if not jobs:
                logger.info("No new jobs found to apply")
                return
            
            # Apply to jobs
            applied_count = 0
            for job in jobs:
                if self.apply_to_job(job):
                    applied_count += 1
                
                # Add delay between applications
                time.sleep(5)
            
            # Save shortlisted jobs
            self.save_shortlisted_jobs()
            
            logger.info(f"Application process completed. Applied to {applied_count} jobs.")
            logger.info(f"Shortlisted {len(self.shortlisted_jobs)} jobs for manual application.")
            
        except Exception as e:
            logger.error(f"Error in main execution: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function"""
    try:
        applier = NaukriJobApplier()
        applier.run()
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")

if __name__ == "__main__":
    main()