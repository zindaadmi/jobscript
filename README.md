# Naukri.com Job Application Automation Script

This script automates the job application process on Naukri.com for Java backend developer positions with 3+ years of experience. It automatically applies to eligible jobs and shortlists those requiring manual intervention.

## Features

- **Automated Login**: Logs into your Naukri account
- **Smart Job Search**: Searches for Java backend developer roles with Spring Boot
- **Experience Filter**: Automatically filters for 3+ years experience
- **Intelligent Application**: 
  - Automatically applies to jobs with simple application process
  - Detects and shortlists jobs requiring external applications
  - Identifies jobs needing additional details/questionnaires
- **Results Tracking**: Saves applied, shortlisted, and failed job applications
- **Detailed Logging**: Comprehensive logs for debugging and tracking

## Prerequisites

1. Python 3.8 or higher
2. Google Chrome browser installed
3. ChromeDriver (will be automatically managed by webdriver-manager)

## Installation

1. Clone or download this repository

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Download ChromeDriver (if not using webdriver-manager):
   - Visit https://chromedriver.chromium.org/
   - Download the version matching your Chrome browser
   - Add to PATH or place in project directory

## Configuration

1. Edit `config.json` with your details:
```json
{
  "username": "your_naukri_email@example.com",
  "password": "your_naukri_password",
  "search_keywords": "java backend developer springboot",
  "location": "Bangalore",
  "headless": false,
  "delay_between_applications": 5
}
```

**Configuration Options:**
- `username`: Your Naukri login email
- `password`: Your Naukri password
- `search_keywords`: Keywords for job search
- `location`: Preferred job location (optional)
- `headless`: Set to `true` to run browser in background
- `delay_between_applications`: Seconds to wait between applications

## Usage

Run the script:
```bash
python naukri_job_applier.py
```

The script will:
1. Login to your Naukri account
2. Search for Java backend developer jobs
3. Apply filters for 3+ years experience
4. Automatically apply to eligible jobs
5. Shortlist jobs that require:
   - External website applications
   - Additional questionnaires or details
6. Save results in CSV and JSON formats

## Output Files

The script generates several output files with timestamps:

1. **applied_jobs_[timestamp].csv**: Successfully applied jobs
2. **shortlisted_jobs_[timestamp].csv**: Jobs requiring manual application with reasons
3. **failed_jobs_[timestamp].csv**: Jobs where application failed
4. **application_summary_[timestamp].json**: Summary statistics
5. **naukri_job_application.log**: Detailed execution logs

## Shortlisted Jobs

Jobs are shortlisted for manual application when:
- They require applying through company's external website
- They have screening questions or questionnaires
- They need additional information beyond standard application

Review the `shortlisted_jobs_[timestamp].csv` file to manually apply to these positions.

## Important Notes

1. **Use Responsibly**: This tool is for personal use. Excessive automation may violate Naukri's terms of service.
2. **Captcha**: If Naukri shows captcha, you'll need to solve it manually
3. **Profile Completion**: Ensure your Naukri profile is complete with resume uploaded
4. **Rate Limiting**: The script includes delays to avoid being flagged as a bot
5. **Manual Review**: Always review shortlisted jobs and apply manually where needed

## Troubleshooting

1. **Login Issues**: 
   - Verify credentials in config.json
   - Check if Naukri requires captcha
   - Try logging in manually first

2. **ChromeDriver Issues**:
   - Ensure Chrome browser is updated
   - The script uses webdriver-manager to handle ChromeDriver automatically

3. **Application Failures**:
   - Check logs for specific error messages
   - Some jobs may have changed their application process
   - Verify your Naukri profile is complete

## Customization

You can modify the script to:
- Add more search keywords
- Filter by salary range
- Exclude certain companies
- Apply to different job categories

Edit the relevant sections in `naukri_job_applier.py` to customize behavior.

## Disclaimer

This tool is provided for educational purposes. Users are responsible for complying with Naukri's terms of service and using the tool ethically. The authors are not responsible for any misuse or consequences of using this script.