# Quick Start Guide - Naukri Job Application Automation

## 🚀 Get Started in 3 Steps

### Step 1: Setup
```bash
python setup.py
```
This will:
- Install all required packages
- Create necessary directories
- Guide you through configuration setup

### Step 2: Configure
Edit `config.json` with your details:
```json
{
  "email": "your_naukri_email@example.com",
  "password": "your_password",
  "notice_period": "30",
  "current_salary": "600000",
  "expected_salary": "800000"
}
```

### Step 3: Run
```bash
python run.py
```

## 📋 What the Script Does

1. **Logs into Naukri.com** using your credentials
2. **Searches for Java backend jobs** with 3+ years experience
3. **Automatically applies** to suitable positions
4. **Shortlists external applications** for manual review
5. **Tracks all applications** to avoid duplicates

## 📊 Output Files

- `output/applied_jobs.csv` - Successfully applied jobs
- `output/shortlisted_jobs_*.csv` - Jobs requiring manual application
- `output/failed_applications_*.csv` - Failed applications for review
- `logs/naukri_applications.log` - Detailed logs

## ⚙️ Advanced Usage

### Run Basic Version
```bash
python run.py --version basic
```

### Run Enhanced Version (Default)
```bash
python run.py --version enhanced
```

### Custom Config
```bash
python run.py --config my_config.json
```

## 🔧 Troubleshooting

### Common Issues

1. **"Chrome browser not found"**
   - Install Google Chrome browser
   - Download from: https://www.google.com/chrome/

2. **"Login failed"**
   - Check your email/password in config.json
   - Ensure your Naukri account is active
   - Disable 2FA if enabled

3. **"No jobs found"**
   - Check your search criteria
   - Ensure your Naukri profile is complete
   - Try different job keywords

### Debug Mode
Enable detailed logging by editing the script:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Important Notes

- **Rate Limiting**: Script includes delays to avoid being flagged
- **External Applications**: Automatically detected and shortlisted
- **Duplicate Prevention**: Tracks applied jobs to prevent re-application
- **Safe to Re-run**: Can be executed multiple times safely

## 🆘 Need Help?

1. Check the logs in `logs/naukri_applications.log`
2. Review the full README.md for detailed documentation
3. Ensure all requirements are installed: `pip install -r requirements.txt`

## ⚖️ Legal Notice

This script is for personal use only. Ensure compliance with Naukri.com's terms of service.