#!/usr/bin/env python3
"""
Enhanced Naukri.com Job Application Automation Script
Advanced version with better external application detection and improved form handling
"""

import time
import json
import csv
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from urllib.parse import urljoin, urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/naukri_applications.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class JobDetails:
    """Enhanced data class to store job information"""
    title: str
    company: str
    location: str
    experience: str
    salary: str
    description: str
    url: str
    job_id: str
    posted_date: str
    is_external: bool = False
    external_reason: str = ""
    applied: bool = False
    application_date: Optional[str] = None
    application_status: str = "pending"

class EnhancedNaukriJobApplier:
    """Enhanced class for automating Naukri.com job applications"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config = self.load_config(config_file)
        self.driver = None
        self.applied_jobs = self.load_applied_jobs()
        self.shortlisted_jobs = []
        self.failed_applications = []
        self.setup_driver()
        
        # External application patterns
        self.external_patterns = [
            r'redirect.*external',
            r'apply.*external',
            r'careers.*company',
            r'jobs.*company',
            r'workday',
            r'greenhouse',
            r'bamboohr',
            r'lever',
            r'ashby',
            r'ats.*apply'
        ]
        
        # Company domains that typically require external applications
        self.external_domains = {
            'workday.com', 'greenhouse.io', 'bamboohr.com', 'lever.co',
            'ashbyhq.com', 'smartrecruiters.com', 'jobvite.com',
            'icims.com', 'taleo.net', 'successfactors.com'
        }
    
    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file {config_file} not found. Please run setup.py first.")
            raise
    
    def load_applied_jobs(self) -> Set[str]:
        """Load previously applied jobs from CSV"""
        applied_jobs = set()
        try:
            with open('output/applied_jobs.csv', 'r', newline='') as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                for row in reader:
                    if row and len(row) > 0:
                        applied_jobs.add(row[0])  # Job URL
        except FileNotFoundError:
            logger.info("No previous applications found. Starting fresh.")
        return applied_jobs
    
    def save_applied_job(self, job: JobDetails):
        """Save applied job to CSV"""
        os.makedirs('output', exist_ok=True)
        with open('output/applied_jobs.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            # Check if file is empty to write header
            if f.tell() == 0:
                writer.writerow(['URL', 'Job ID', 'Title', 'Company', 'Location', 'Applied Date', 'Status'])
            writer.writerow([
                job.url, job.job_id, job.title, job.company, 
                job.location, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 
                job.application_status
            ])
    
    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Faster loading
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Uncomment for headless mode
        # chrome_options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self.wait = WebDriverWait(self.driver, 15)
        self.actions = ActionChains(self.driver)
    
    def login(self):
        """Enhanced login with better error handling"""
        try:
            logger.info("Logging into Naukri.com...")
            self.driver.get("https://www.naukri.com/nlogin/login")
            time.sleep(3)
            
            # Handle potential popups
            self.handle_popups()
            
            # Wait for login form
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            password_field = self.driver.find_element(By.ID, "passwordField")
            
            # Clear and enter credentials
            email_field.clear()
            email_field.send_keys(self.config['email'])
            time.sleep(1)
            
            password_field.clear()
            password_field.send_keys(self.config['password'])
            time.sleep(1)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Login')]")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "user-name")))
            logger.info("Successfully logged in!")
            time.sleep(3)
            
            # Handle post-login popups
            self.handle_popups()
            
        except TimeoutException:
            logger.error("Login failed - timeout waiting for elements")
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise
    
    def handle_popups(self):
        """Handle various popups that may appear"""
        popup_selectors = [
            "//button[contains(text(), 'Skip')]",
            "//button[contains(text(), 'Later')]",
            "//button[contains(text(), 'Not Now')]",
            "//span[contains(@class, 'close')]",
            ".close-popup",
            ".modal-close"
        ]
        
        for selector in popup_selectors:
            try:
                if selector.startswith("//"):
                    popup = self.driver.find_element(By.XPATH, selector)
                else:
                    popup = self.driver.find_element(By.CSS_SELECTOR, selector)
                popup.click()
                time.sleep(1)
            except NoSuchElementException:
                continue
    
    def search_jobs(self) -> List[JobDetails]:
        """Enhanced job search with better filtering"""
        jobs = []
        try:
            logger.info("Searching for Java backend developer jobs...")
            
            # Navigate to job search
            self.driver.get("https://www.naukri.com/jobs-in-india")
            time.sleep(3)
            self.handle_popups()
            
            # Search for Java backend jobs
            search_box = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "suggestor-input")))
            search_box.clear()
            search_box.send_keys("backend java developer spring boot")
            search_box.send_keys(Keys.RETURN)
            
            time.sleep(5)
            self.handle_popups()
            
            # Apply experience filter (3+ years)
            self.apply_experience_filter()
            
            # Apply location filters if specified
            if self.config.get('preferred_locations'):
                self.apply_location_filter()
            
            # Get job listings with pagination
            page = 1
            max_pages = 3  # Limit to first 3 pages
            
            while page <= max_pages and len(jobs) < self.config.get('max_applications_per_run', 20):
                logger.info(f"Scraping page {page}...")
                page_jobs = self.extract_jobs_from_page()
                jobs.extend(page_jobs)
                
                # Go to next page
                if page < max_pages:
                    if self.go_to_next_page():
                        page += 1
                        time.sleep(3)
                    else:
                        break
                else:
                    break
            
            # Filter out already applied jobs
            new_jobs = [job for job in jobs if job.url not in self.applied_jobs]
            
            logger.info(f"Found {len(new_jobs)} new jobs to apply (out of {len(jobs)} total)")
            return new_jobs
            
        except Exception as e:
            logger.error(f"Error searching jobs: {str(e)}")
            return []
    
    def apply_experience_filter(self):
        """Apply experience filter for 3+ years"""
        try:
            # Look for experience filter options
            exp_filters = [
                "//span[contains(text(), '3-5 Yrs')]",
                "//span[contains(text(), '3+ Yrs')]",
                "//span[contains(text(), '3 Yrs')]"
            ]
            
            for filter_xpath in exp_filters:
                try:
                    exp_filter = self.driver.find_element(By.XPATH, filter_xpath)
                    exp_filter.click()
                    time.sleep(2)
                    logger.info("Applied experience filter")
                    break
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not apply experience filter: {str(e)}")
    
    def apply_location_filter(self):
        """Apply location filter if specified"""
        try:
            locations = self.config.get('preferred_locations', [])
            if not locations:
                return
            
            # Look for location filter
            location_input = self.driver.find_element(By.CSS_SELECTOR, ".location-input")
            location_input.click()
            time.sleep(1)
            
            # Select first preferred location
            location_input.send_keys(locations[0])
            time.sleep(2)
            
            # Select from dropdown
            location_option = self.driver.find_element(By.CSS_SELECTOR, ".location-dropdown .option")
            location_option.click()
            time.sleep(2)
            
            logger.info(f"Applied location filter: {locations[0]}")
            
        except Exception as e:
            logger.warning(f"Could not apply location filter: {str(e)}")
    
    def extract_jobs_from_page(self) -> List[JobDetails]:
        """Extract job details from current page"""
        jobs = []
        try:
            # Wait for job cards to load
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jobTuple")))
            
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobTuple")
            
            for card in job_cards:
                try:
                    job = self.extract_job_details(card)
                    if job:
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"Error extracting job details: {str(e)}")
                    continue
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error extracting jobs from page: {str(e)}")
            return []
    
    def extract_job_details(self, card) -> Optional[JobDetails]:
        """Enhanced job details extraction"""
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
            
            # Get job URL and ID
            link_elem = card.find_element(By.CSS_SELECTOR, ".title a")
            job_url = link_elem.get_attribute("href")
            
            # Extract job ID from URL
            job_id = self.extract_job_id(job_url)
            
            # Extract posted date
            try:
                posted_elem = card.find_element(By.CSS_SELECTOR, ".postedDate")
                posted_date = posted_elem.text.strip()
            except NoSuchElementException:
                posted_date = "Not specified"
            
            # Check if it's an external application
            is_external, external_reason = self.is_external_application(job_url)
            
            return JobDetails(
                title=title,
                company=company,
                location=location,
                experience=experience,
                salary=salary,
                description="",  # Will be filled when applying
                url=job_url,
                job_id=job_id,
                posted_date=posted_date,
                is_external=is_external,
                external_reason=external_reason
            )
            
        except Exception as e:
            logger.warning(f"Error extracting job details: {str(e)}")
            return None
    
    def extract_job_id(self, job_url: str) -> str:
        """Extract job ID from URL"""
        try:
            # Common patterns for job IDs in Naukri URLs
            patterns = [
                r'jobid=(\d+)',
                r'jobId=(\d+)',
                r'/job/(\d+)',
                r'id=(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, job_url)
                if match:
                    return match.group(1)
            
            # Fallback: use URL hash
            return str(hash(job_url))[-8:]
            
        except Exception:
            return "unknown"
    
    def is_external_application(self, job_url: str) -> tuple[bool, str]:
        """Enhanced external application detection"""
        try:
            # Check URL patterns
            for pattern in self.external_patterns:
                if re.search(pattern, job_url, re.IGNORECASE):
                    return True, f"URL pattern match: {pattern}"
            
            # Check domain
            parsed_url = urlparse(job_url)
            domain = parsed_url.netloc.lower()
            
            if domain not in ['naukri.com', 'www.naukri.com']:
                return True, f"External domain: {domain}"
            
            # Check for external domains in URL
            for ext_domain in self.external_domains:
                if ext_domain in job_url.lower():
                    return True, f"External ATS domain: {ext_domain}"
            
            # Check for redirect parameters
            query_params = parse_qs(parsed_url.query)
            if 'redirect' in query_params or 'external' in query_params:
                return True, "Redirect parameter detected"
            
            return False, ""
            
        except Exception as e:
            logger.warning(f"Error checking external application: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, ".pagination .next")
            if next_button.is_enabled():
                next_button.click()
                return True
            return False
        except NoSuchElementException:
            return False
    
    def apply_to_job(self, job: JobDetails) -> bool:
        """Enhanced job application with better form handling"""
        try:
            logger.info(f"Applying to: {job.title} at {job.company}")
            
            # Open job in new tab
            self.driver.execute_script(f"window.open('{job.url}', '_blank');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            time.sleep(3)
            
            # Check if it's an external application
            if job.is_external:
                logger.info(f"External application detected for {job.title}. Reason: {job.external_reason}")
                self.shortlisted_jobs.append(job)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
            
            # Double-check for external application after page load
            current_url = self.driver.current_url
            is_external, reason = self.is_external_application(current_url)
            if is_external:
                job.is_external = True
                job.external_reason = reason
                logger.info(f"External application detected after page load: {reason}")
                self.shortlisted_jobs.append(job)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
            
            # Look for apply button with multiple strategies
            apply_button = self.find_apply_button()
            
            if not apply_button:
                logger.warning(f"No apply button found for {job.title}")
                self.failed_applications.append(job)
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                return False
            
            # Click apply button
            try:
                apply_button.click()
            except ElementClickInterceptedException:
                # Try scrolling to button and clicking again
                self.driver.execute_script("arguments[0].scrollIntoView(true);", apply_button)
                time.sleep(1)
                apply_button.click()
            
            time.sleep(3)
            
            # Handle application form
            if self.handle_application_form(job):
                # Mark as applied
                job.applied = True
                job.application_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                job.application_status = "applied"
                self.applied_jobs.add(job.url)
                self.save_applied_job(job)
                logger.info(f"Successfully applied to {job.title} at {job.company}")
                return True
            else:
                logger.warning(f"Failed to complete application for {job.title}")
                job.application_status = "failed"
                self.failed_applications.append(job)
                return False
                
        except Exception as e:
            logger.error(f"Error applying to job {job.title}: {str(e)}")
            job.application_status = "error"
            self.failed_applications.append(job)
            return False
        finally:
            # Close current tab and switch back to main tab
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
    
    def find_apply_button(self):
        """Find apply button using multiple strategies"""
        apply_selectors = [
            "//button[contains(text(), 'Apply')]",
            "//a[contains(text(), 'Apply')]",
            "//span[contains(text(), 'Apply')]",
            "//div[contains(text(), 'Apply')]",
            ".apply-button",
            "#apply-button",
            ".job-apply-btn",
            ".apply-now",
            "[data-testid='apply-button']"
        ]
        
        for selector in apply_selectors:
            try:
                if selector.startswith("//"):
                    button = self.driver.find_element(By.XPATH, selector)
                else:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                
                if button.is_displayed() and button.is_enabled():
                    return button
            except NoSuchElementException:
                continue
        
        return None
    
    def handle_application_form(self, job: JobDetails) -> bool:
        """Enhanced application form handling"""
        try:
            # Wait for form to load
            time.sleep(3)
            
            # Check for external redirect after clicking apply
            current_url = self.driver.current_url
            if self.is_external_application(current_url)[0]:
                logger.info("External redirect detected after clicking apply")
                return False
            
            # Look for application forms
            form_elements = self.driver.find_elements(By.CSS_SELECTOR, "form, .application-form, .job-application, .apply-form")
            
            if not form_elements:
                # Check if application was successful (no form means direct application)
                success_indicators = [
                    "//div[contains(text(), 'Application submitted')]",
                    "//div[contains(text(), 'Applied successfully')]",
                    "//div[contains(text(), 'Thank you for applying')]"
                ]
                
                for indicator in success_indicators:
                    try:
                        self.driver.find_element(By.XPATH, indicator)
                        return True
                    except NoSuchElementException:
                        continue
                
                # No form and no success message - might be direct application
                return True
            
            # Handle form fields
            for form in form_elements:
                if self.fill_application_form(form):
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling application form: {str(e)}")
            return False
    
    def fill_application_form(self, form) -> bool:
        """Fill application form with user data"""
        try:
            # Handle text inputs
            text_inputs = form.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea, input[type='number']")
            for input_field in text_inputs:
                self.fill_text_field(input_field)
            
            # Handle dropdowns
            dropdowns = form.find_elements(By.CSS_SELECTOR, "select")
            for dropdown in dropdowns:
                self.fill_dropdown(dropdown)
            
            # Handle radio buttons
            radio_buttons = form.find_elements(By.CSS_SELECTOR, "input[type='radio']")
            for radio in radio_buttons:
                self.handle_radio_button(radio)
            
            # Handle checkboxes
            checkboxes = form.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
            for checkbox in checkboxes:
                self.handle_checkbox(checkbox)
            
            # Submit form
            return self.submit_form(form)
            
        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            return False
    
    def fill_text_field(self, input_field):
        """Fill text input field based on field type"""
        try:
            field_name = (input_field.get_attribute("name") or 
                         input_field.get_attribute("id") or 
                         input_field.get_attribute("placeholder") or "").lower()
            
            if "experience" in field_name and "years" in field_name:
                input_field.clear()
                input_field.send_keys(str(self.config.get('experience_years', 3)))
            elif "notice" in field_name:
                input_field.clear()
                input_field.send_keys(self.config.get('notice_period', '30'))
            elif "expected" in field_name and "salary" in field_name:
                input_field.clear()
                input_field.send_keys(self.config.get('expected_salary', '800000'))
            elif "current" in field_name and "salary" in field_name:
                input_field.clear()
                input_field.send_keys(self.config.get('current_salary', '600000'))
            elif "mobile" in field_name or "phone" in field_name:
                input_field.clear()
                input_field.send_keys(self.config.get('mobile', ''))
            elif "email" in field_name:
                input_field.clear()
                input_field.send_keys(self.config.get('email', ''))
                
        except Exception as e:
            logger.warning(f"Error filling text field: {str(e)}")
    
    def fill_dropdown(self, dropdown):
        """Fill dropdown field"""
        try:
            dropdown_name = (dropdown.get_attribute("name") or 
                           dropdown.get_attribute("id") or "").lower()
            
            select = Select(dropdown)
            
            if "experience" in dropdown_name:
                # Select appropriate experience option
                for option in select.options:
                    option_text = option.text.lower()
                    if "3" in option_text and ("year" in option_text or "yr" in option_text):
                        select.select_by_visible_text(option.text)
                        break
            elif "notice" in dropdown_name:
                # Select notice period
                for option in select.options:
                    if "30" in option.text or "1 month" in option.text.lower():
                        select.select_by_visible_text(option.text)
                        break
                        
        except Exception as e:
            logger.warning(f"Error filling dropdown: {str(e)}")
    
    def handle_radio_button(self, radio):
        """Handle radio button selection"""
        try:
            radio_name = (radio.get_attribute("name") or 
                         radio.get_attribute("id") or "").lower()
            
            if "experience" in radio_name and "3" in radio.get_attribute("value", ""):
                if not radio.is_selected():
                    radio.click()
            elif "notice" in radio_name and "30" in radio.get_attribute("value", ""):
                if not radio.is_selected():
                    radio.click()
                    
        except Exception as e:
            logger.warning(f"Error handling radio button: {str(e)}")
    
    def handle_checkbox(self, checkbox):
        """Handle checkbox selection"""
        try:
            checkbox_name = (checkbox.get_attribute("name") or 
                           checkbox.get_attribute("id") or "").lower()
            
            # Select relevant checkboxes (e.g., terms and conditions)
            if "terms" in checkbox_name or "agree" in checkbox_name:
                if not checkbox.is_selected():
                    checkbox.click()
                    
        except Exception as e:
            logger.warning(f"Error handling checkbox: {str(e)}")
    
    def submit_form(self, form) -> bool:
        """Submit application form"""
        try:
            # Look for submit buttons
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".submit-btn",
                ".apply-submit",
                "//button[contains(text(), 'Submit')]",
                "//button[contains(text(), 'Apply')]"
            ]
            
            for selector in submit_selectors:
                try:
                    if selector.startswith("//"):
                        submit_btn = form.find_element(By.XPATH, selector)
                    else:
                        submit_btn = form.find_element(By.CSS_SELECTOR, selector)
                    
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        time.sleep(3)
                        return True
                except NoSuchElementException:
                    continue
            
            return True  # No submit button found, might be auto-submit
            
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            return False
    
    def save_shortlisted_jobs(self):
        """Save shortlisted jobs to CSV for manual application"""
        if not self.shortlisted_jobs:
            return
        
        os.makedirs('output', exist_ok=True)
        filename = f"output/shortlisted_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Company', 'Location', 'Experience', 'Salary', 'URL', 'Job ID', 'External Reason'])
            
            for job in self.shortlisted_jobs:
                writer.writerow([
                    job.title,
                    job.company,
                    job.location,
                    job.experience,
                    job.salary,
                    job.url,
                    job.job_id,
                    job.external_reason
                ])
        
        logger.info(f"Shortlisted {len(self.shortlisted_jobs)} jobs saved to {filename}")
    
    def save_failed_applications(self):
        """Save failed applications for review"""
        if not self.failed_applications:
            return
        
        os.makedirs('output', exist_ok=True)
        filename = f"output/failed_applications_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Title', 'Company', 'Location', 'URL', 'Job ID', 'Status', 'Error'])
            
            for job in self.failed_applications:
                writer.writerow([
                    job.title,
                    job.company,
                    job.location,
                    job.url,
                    job.job_id,
                    job.application_status,
                    job.external_reason if hasattr(job, 'external_reason') else 'Unknown'
                ])
        
        logger.info(f"Failed applications saved to {filename}")
    
    def generate_report(self):
        """Generate application report"""
        total_jobs = len(self.applied_jobs) + len(self.shortlisted_jobs) + len(self.failed_applications)
        applied_count = len([job for job in self.applied_jobs if job])
        shortlisted_count = len(self.shortlisted_jobs)
        failed_count = len(self.failed_applications)
        
        report = f"""
        📊 Application Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        ================================================
        Total Jobs Processed: {total_jobs}
        Successfully Applied: {applied_count}
        Shortlisted (External): {shortlisted_count}
        Failed Applications: {failed_count}
        Success Rate: {(applied_count/total_jobs*100):.1f}% (excluding shortlisted)
        ================================================
        """
        
        logger.info(report)
        
        # Save report to file
        os.makedirs('output', exist_ok=True)
        with open(f"output/application_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
            f.write(report)
    
    def run(self):
        """Main execution method"""
        try:
            logger.info("Starting Enhanced Naukri job application automation...")
            
            # Login
            self.login()
            
            # Search for jobs
            jobs = self.search_jobs()
            
            if not jobs:
                logger.info("No new jobs found to apply")
                return
            
            # Apply to jobs
            applied_count = 0
            for i, job in enumerate(jobs, 1):
                logger.info(f"Processing job {i}/{len(jobs)}: {job.title}")
                
                if self.apply_to_job(job):
                    applied_count += 1
                
                # Add delay between applications
                delay = self.config.get('delay_between_applications', 5)
                if i < len(jobs):  # Don't delay after last job
                    time.sleep(delay)
            
            # Save results
            self.save_shortlisted_jobs()
            self.save_failed_applications()
            self.generate_report()
            
            logger.info(f"Application process completed. Applied to {applied_count} jobs.")
            logger.info(f"Shortlisted {len(self.shortlisted_jobs)} jobs for manual application.")
            logger.info(f"Failed applications: {len(self.failed_applications)}")
            
        except Exception as e:
            logger.error(f"Error in main execution: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()

def main():
    """Main function"""
    try:
        applier = EnhancedNaukriJobApplier()
        applier.run()
    except Exception as e:
        logger.error(f"Application failed: {str(e)}")

if __name__ == "__main__":
    main()