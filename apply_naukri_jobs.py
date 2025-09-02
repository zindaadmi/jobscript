#!/usr/bin/env python3
"""
Automated script to search and apply for Java Backend developer jobs (3+ yrs exp)
on Naukri.com. Jobs requiring external site application or additional manual
input are saved to a shortlist for manual processing.

Usage:
  1. Fill .env with NAUKRI_EMAIL and NAUKRI_PASSWORD.
  2. pip install -r requirements.txt
  3. python apply_naukri_jobs.py

The script will:
  • Login to Naukri.
  • Search with pre-defined keywords.
  • Iterate over job cards, open and attempt quick apply.
  • If quick apply not possible, add job link to shortlist.csv.
"""
import csv
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

KEYWORDS = [
    "Backend Developer Java 3 years",
    "Java Spring Boot Backend Developer",
    "Backend Java",
]

SHORTLIST_FILE = Path("shortlist.csv")


def init_driver():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=opts)


def login(driver, email: str, password: str):
    driver.get("https://www.naukri.com/")
    login_btn = driver.find_element(By.LINK_TEXT, "Login")
    login_btn.click()
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )
    driver.find_element(By.ID, "usernameField").send_keys(email)
    driver.find_element(By.ID, "passwordField").send_keys(password)
    driver.find_element(By.XPATH, "//button[contains(., 'Login')]" ).click()
    # Wait for login to complete - profile icon visible
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-test-id='accountDropdown']"))
    )
    print("Logged in successfully")


def search_and_apply(driver):
    applied_count = 0
    shortlisted = []
    for kw in KEYWORDS:
        print(f"Searching jobs for: {kw}")
        driver.get("https://www.naukri.com/" + kw.replace(" ", "-") + "-jobs")
        time.sleep(5)
        jobs = driver.find_elements(By.CSS_SELECTOR, "article.jobTuple")
        print(f"Found {len(jobs)} jobs")
        for job in jobs:
            link_el = job.find_element(By.CSS_SELECTOR, "a.title")
            job_url = link_el.get_attribute("href")
            driver.execute_script("window.open(arguments[0])", job_url)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(3)
            try:
                apply_btn = driver.find_element(By.XPATH, "//button[contains(., 'Apply')]" )
                apply_btn.click()
                time.sleep(2)
                # If a quick apply modal appears, finish it
                try:
                    submit_btn = driver.find_element(By.XPATH, "//button[contains(., 'Submit Application') or contains(., 'Submit')]" )
                    submit_btn.click()
                    applied_count += 1
                    print("Applied via quick apply")
                except Exception:
                    # Could not submit; treat as requiring extra input
                    shortlisted.append(job_url)
                    print("Requires additional input, shortlisted")
            except Exception:
                shortlisted.append(job_url)
                print("No direct apply button, shortlisted")
            # Close tab & return
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
    return applied_count, shortlisted


def save_shortlist(urls):
    if not urls:
        return
    write_header = not SHORTLIST_FILE.exists()
    with SHORTLIST_FILE.open("a", newline="") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Job URL"])
        for u in urls:
            writer.writerow([u])
    print(f"Saved {len(urls)} jobs to {SHORTLIST_FILE}")


def main():
    load_dotenv()
    email = os.getenv("NAUKRI_EMAIL")
    password = os.getenv("NAUKRI_PASSWORD")
    if not email or not password:
        print("Please set NAUKRI_EMAIL and NAUKRI_PASSWORD in .env")
        sys.exit(1)

    driver = init_driver()
    try:
        login(driver, email, password)
        applied, shortlist = search_and_apply(driver)
        print(f"Applied to {applied} jobs. Shortlisted {len(shortlist)} jobs.")
        save_shortlist(shortlist)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()