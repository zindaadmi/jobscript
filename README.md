### Naukri Auto-Apply Script

Automates applying to Naukri jobs for backend Java roles (3+ years) and shortlists jobs that require detailed forms or redirect to external sites so you can apply manually later.

### Features

- **Search queries**: backend developer java, java spring boot, backend java
- **Experience filter**: minimum years (default 3)
- **Auto-apply**: Attempts in-site one-click applies
- **Shortlist**: If the application asks extra details or opens company site
- **CSV outputs**: `output/applied.csv`, `output/shortlist.csv`

### Requirements

- Python 3.9+

### Setup

1) Create a virtualenv and install deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install --with-deps chromium
```

2) Configure environment variables (copy and edit `.env.example`)

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
NAUKRI_EMAIL=your_email@example.com
NAUKRI_PASSWORD=your_password
# Optional: absolute path to your resume
RESUME_PATH=/absolute/path/to/resume.pdf
```

### Usage

Run the script (non-headless for visibility):

```bash
source .venv/bin/activate
python scripts/naukri_auto_apply.py --headless false
```

Common flags:

- `--queries/-q`: search queries (space-separated)
- `--locations/-l`: locations (optional)
- `--min-exp`: minimum experience (default 3)
- `--max-jobs`: stop after N jobs processed (default 40)
- `--headless`: run headless browser
- `--output-dir`: output directory (default `./output`)

Example:

```bash
python scripts/naukri_auto_apply.py -q "backend developer java" "java spring boot" -l Bangalore Pune --min-exp 3 --max-jobs 60
```

### Notes

- Sites change frequently; selectors include fallbacks but may need updates.
- Avoid running too fast; delays are randomized to mimic human behavior.
- Jobs that redirect to external sites or present detailed forms are added to `shortlist.csv`.

