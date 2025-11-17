# Assignment-2_Security

## Vulnerability Analysis Project

This project analyzes SQL injection vulnerabilities (CWE-89) in Python code from a PostgreSQL database of security fixes. It uses AI-powered analysis to identify vulnerable functions, understand fixes, and discover similar vulnerable code patterns in other GitHub repositories.

## Project Files

- **`analyze_vulnerabilities.py`** - Main analysis script that processes database entries 26-51
- **`export_to_excel.py`** - Original script to export SQL query results to Excel
- **`dataclean.sql`** - SQL query to fetch vulnerability data
- **`requirements.txt`** - Python dependencies
- **`SETUP_GUIDE.md`** - Detailed setup and usage instructions

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment variables
Create a `.env` file with your credentials:
```env
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DBNAME=postgrescvedumper
POSTGRES_USER=postgrescvedumper
POSTGRES_PASSWORD=your_password

OPENAI_API_KEY=sk-your-key-here
GITHUB_TOKEN=ghp-your-token-here  # Optional

# Entry range to process (Optional, defaults to "26-51")
# Examples: "1-10", "26-51", "All"
ENTRY_RANGE=26-51
```

### 3. Run the analysis

**Test mode (recommended first run):**
```bash
python analyze_vulnerabilities.py --test
```
Processes only 2 entries (~1 minute) to verify everything works.

**Specific entry range:**
```bash
# Process entries 1-5
python analyze_vulnerabilities.py --range "1-5"

# Process entries 26-50
python analyze_vulnerabilities.py --range "26-50"

# Process all entries
python analyze_vulnerabilities.py --range "All"
```

**Default mode (uses ENTRY_RANGE from .env):**
```bash
python analyze_vulnerabilities.py
```

## Features

The vulnerability analysis script:

1. **Extracts vulnerable function names** - Uses GPT-4o-mini to identify which functions contain SQL injection vulnerabilities
2. **Identifies fixes** - Analyzes code changes to understand what security fixes were applied
3. **Explains vulnerabilities** - Provides clear explanations of how the SQL injection could be exploited
4. **Searches GitHub** - Finds other public repositories with similar vulnerable code patterns
5. **Generates comprehensive reports** - Exports all findings to an Excel file

## Output

Results are saved to `vulnerability_analysis_results.xlsx` with columns:
- Original vulnerability data (CVE ID, commit URL, repo, filename)
- Vulnerable function name
- Fix description
- Vulnerability explanation
- GitHub repositories with similar code
- Analysis of why those repos might be vulnerable

## Documentation

See **`SETUP_GUIDE.md`** for detailed setup instructions, troubleshooting, and cost estimates.

## Requirements

- Python 3.8+
- PostgreSQL database with vulnerability data
- OpenAI API key (required)
- GitHub personal access token (optional, recommended)