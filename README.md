# Naukri.com Job Application Automation Script

This script automatically applies to backend Java developer jobs on Naukri.com with 3+ years of experience. It intelligently handles external applications by shortlisting them for manual review.

## Features

- 🔍 **Smart Job Search**: Searches for Java backend developer positions with Spring Boot experience
- 🤖 **Automated Applications**: Automatically fills and submits job application forms
- 📋 **External Application Detection**: Identifies and shortlists jobs that require external applications
- 📊 **Application Tracking**: Maintains a record of all applied jobs to avoid duplicates
- 📝 **Detailed Logging**: Comprehensive logging for monitoring and debugging
- ⚙️ **Configurable**: Easy configuration through JSON file

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- Naukri.com account with active profile

## Installation

1. **Clone or download the script files**
   ```bash
   # Make sure you have all files:
   # - naukri_job_applier.py
   # - config.json
   # - requirements.txt
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver**
   ```bash
   # Option 1: Using webdriver-manager (recommended)
   pip install webdriver-manager
   
   # Option 2: Manual installation
   # Download ChromeDriver from https://chromedriver.chromium.org/
   # Add to your PATH
   ```

## Configuration

1. **Edit `config.json`** with your details:
   ```json
   {
     "email": "your_naukri_email@example.com",
     "password": "your_naukri_password",
     "notice_period": "30",
     "current_salary": "600000",
     "expected_salary": "800000",
     "preferred_locations": [
       "Bangalore",
       "Mumbai", 
       "Delhi",
       "Pune",
       "Hyderabad"
     ],
     "job_keywords": [
       "backend java developer",
       "java spring boot",
       "java backend",
       "spring framework",
       "java microservices"
     ],
     "experience_years": 3,
     "max_applications_per_run": 20,
     "delay_between_applications": 5
   }
   ```

2. **Update your Naukri.com profile** to ensure it's complete and up-to-date

## Usage

### Basic Usage
```bash
python naukri_job_applier.py
```

### Running with Custom Config
```bash
python naukri_job_applier.py --config custom_config.json
```

## How It Works

1. **Login**: Automatically logs into your Naukri.com account
2. **Job Search**: Searches for Java backend developer jobs with 3+ years experience
3. **Application Process**:
   - Opens each job posting
   - Checks if it's an external application
   - If external: Shortlists for manual application
   - If internal: Automatically fills and submits the application
4. **Tracking**: Records all applications to avoid duplicates
5. **Reporting**: Generates logs and shortlisted jobs CSV

## Output Files

- `applied_jobs.csv`: Record of all successfully applied jobs
- `shortlisted_jobs_YYYYMMDD_HHMMSS.csv`: Jobs requiring manual application
- `naukri_applications.log`: Detailed application logs

## External Application Detection

The script automatically detects external applications by:
- Checking if the job URL redirects to external websites
- Identifying external redirect patterns in URLs
- Detecting forms that require additional information

External applications are saved to a CSV file for manual review and application.

## Safety Features

- **Rate Limiting**: Built-in delays between applications to avoid being flagged
- **Duplicate Prevention**: Tracks applied jobs to prevent re-application
- **Error Handling**: Comprehensive error handling and logging
- **Resume Capability**: Can be run multiple times safely

## Troubleshooting

### Common Issues

1. **Login Failed**
   - Verify your email and password in config.json
   - Check if your Naukri account is active
   - Ensure 2FA is disabled or handle it manually

2. **ChromeDriver Issues**
   - Update Chrome browser to latest version
   - Reinstall ChromeDriver
   - Use webdriver-manager for automatic driver management

3. **No Jobs Found**
   - Check your search criteria in config.json
   - Verify your Naukri profile is complete
   - Try different job keywords

4. **Application Failures**
   - Check the logs for specific error messages
   - Some jobs may have complex application processes
   - External applications are automatically shortlisted

### Debug Mode

Enable debug logging by modifying the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Legal and Ethical Considerations

- **Terms of Service**: Ensure compliance with Naukri.com's terms of service
- **Rate Limiting**: The script includes delays to avoid overwhelming the server
- **Personal Use**: This script is intended for personal job search use only
- **Data Privacy**: Your credentials and data are stored locally only

## Customization

### Adding New Job Keywords
Edit the `job_keywords` array in `config.json`:
```json
"job_keywords": [
  "backend java developer",
  "java spring boot",
  "your_custom_keyword"
]
```

### Modifying Application Logic
The `handle_application_form()` method can be customized to handle specific form fields or questions.

### Adding New Filters
Modify the `search_jobs()` method to add additional search filters like location, salary range, etc.

## Support

For issues or questions:
1. Check the logs in `naukri_applications.log`
2. Review the troubleshooting section
3. Ensure all dependencies are properly installed
4. Verify your Naukri.com account status

## Disclaimer

This script is for educational and personal use only. Users are responsible for ensuring compliance with Naukri.com's terms of service and applicable laws. The authors are not responsible for any misuse or consequences of using this script.