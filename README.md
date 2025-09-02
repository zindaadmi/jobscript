# Naukri Auto Apply Script

This repository contains a Python script to automatically search and apply for Java backend developer roles (3+ years experience) on Naukri.com.

## Features

* Logs into Naukri using your credentials (email & password)
* Searches predefined keywords:
  * `Backend Developer Java 3 years`
  * `Java Spring Boot Backend Developer`
  * `Backend Java`
* Attempts quick apply on each job posting.
* If a job requires additional information or redirects to an external site, it records the job URL in `shortlist.csv` so that you can apply manually later.

## Prerequisites

* Python 3.8+
* Google Chrome browser and matching [ChromeDriver](https://chromedriver.chromium.org/) in PATH.
* Create `.env` file in project root with:

```
NAUKRI_EMAIL=you@example.com
NAUKRI_PASSWORD=yourpassword
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python apply_naukri_jobs.py
```

The script will display progress in the console and produce `shortlist.csv` with jobs needing manual attention.

## Notes

* Run this sparingly to avoid violating Naukri terms of service.
* Adjust keywords or add filters (location, salary, etc.) in `apply_naukri_jobs.py` as desired.