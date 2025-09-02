# Naukri.com Auto Job Apply Script

An automated script to apply for Backend Java Developer positions on Naukri.com with 3+ years experience. The script intelligently handles automatic applications where possible and shortlists jobs requiring manual intervention.

## Features

- **Automated Job Search**: Searches for Java backend developer positions with configurable keywords
- **Smart Application Logic**: Automatically applies to jobs when possible
- **Shortlisting System**: Identifies and saves jobs that require:
  - External website applications
  - Additional questionnaires or details
  - Manual intervention
- **Duplicate Prevention**: Tracks applied jobs to avoid duplicate applications
- **Comprehensive Logging**: Detailed logs of all activities
- **CSV Export**: Exports applied and shortlisted jobs to CSV files for easy tracking

## Prerequisites

- Python 3.7+
- Chrome browser installed
- Naukri.com account

## Installation

1. Clone or download the script files
2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your credentials:
```bash
cp .env.example .env
```

4. Edit `.env` file with your Naukri.com credentials:
```
NAUKRI_EMAIL=your_email@example.com
NAUKRI_PASSWORD=your_password
HEADLESS=false
```

## Configuration

Edit `config.json` to customize your job search preferences:

- **job_keywords**: List of job titles to search for
- **min_experience/max_experience**: Experience range filter
- **locations**: Preferred job locations
- **skills**: Relevant skills for filtering
- **max_applications_per_run**: Maximum applications per execution
- **delay_between_applications**: Delay between applications (seconds)
- **company_blacklist**: Companies to avoid
- **salary_range**: Expected salary range

## Usage

Run the script:
```bash
python naukri_auto_apply.py
```

The script will:
1. Login to your Naukri.com account
2. Search for jobs matching your criteria
3. Automatically apply to suitable jobs
4. Shortlist jobs requiring manual intervention
5. Generate CSV reports

## Output Files

- **applied_jobs.csv**: Jobs successfully applied to
- **shortlisted_jobs.csv**: Jobs requiring manual application
- **naukri_job_apply.log**: Detailed execution log

## Shortlisted Jobs

Jobs are shortlisted for manual application when they:
- Redirect to external company websites
- Require additional questionnaires
- Have complex application processes
- Require cover letters or detailed responses

Review `shortlisted_jobs.csv` and apply to these jobs manually for better success rates.

## Safety Features

- **Rate Limiting**: Built-in delays to avoid being flagged
- **Duplicate Prevention**: Tracks applied jobs
- **Error Handling**: Graceful handling of errors
- **Logging**: Comprehensive activity logging

## Important Notes

1. **Compliance**: Use responsibly and in accordance with Naukri.com's terms of service
2. **Monitoring**: Monitor the script's performance and adjust settings as needed
3. **Manual Review**: Always review shortlisted jobs manually for best results
4. **Profile**: Ensure your Naukri profile is complete and up-to-date

## Troubleshooting

1. **Login Issues**: Verify credentials in `.env` file
2. **Chrome Driver**: Script automatically downloads Chrome driver
3. **Slow Performance**: Increase delays in config.json
4. **No Jobs Found**: Adjust keywords and location filters

## Customization

The script is highly customizable through:
- `config.json`: Job search preferences
- Environment variables: Credentials and settings
- Code modifications: Advanced customizations

## Disclaimer

This script is for educational and personal use. Users are responsible for complying with Naukri.com's terms of service and using the tool ethically. The authors are not responsible for any consequences arising from the use of this script.

## Support

For issues or improvements:
1. Check the log file for error details
2. Verify your configuration settings
3. Ensure your Naukri profile is complete
4. Test with a small number of applications first