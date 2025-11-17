# Vulnerability Analysis Script - Setup Guide

## Overview
This script analyzes SQL injection vulnerabilities (CWE-89) from database entries 26-51, using GPT-4o-mini for analysis and GitHub Search API to find similar vulnerable code patterns in other repositories.

## Prerequisites

1. **Python 3.8+** installed
2. **PostgreSQL database** with vulnerability data
3. **OpenAI API key** (required)
4. **GitHub personal access token** (optional, but recommended)

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root with the following configuration:

```env
# Database Configuration
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DBNAME=postgrescvedumper
POSTGRES_USER=postgrescvedumper
POSTGRES_PASSWORD=your_database_password_here

# OpenAI API Configuration (Required)
OPENAI_API_KEY=sk-your-openai-api-key-here

# GitHub Token (Optional but recommended)
GITHUB_TOKEN=ghp_your_github_token_here

# Entry Range Configuration (Optional)
# Specify which entries to process from the database
# Options:
#   - Specific range: "1-2", "26-51", "1-100", etc.
#   - All entries: "All"
# If not specified, defaults to "26-51"
ENTRY_RANGE=26-51
```

### 3. Get API Keys

#### OpenAI API Key (Required)
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Generate a new API key
4. Copy the key to your `.env` file

#### GitHub Personal Access Token (Optional)
1. Visit [GitHub Token Settings](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Give it a descriptive name (e.g., "Vulnerability Analysis")
4. Select scope: `public_repo` (read-only access)
5. Click "Generate token"
6. Copy the token to your `.env` file

**Note:** Without a GitHub token, you're limited to 60 API requests per hour. With a token, you get 5,000 requests per hour.

## Usage

### Test Mode (Recommended First Run)

For a quick test with just 2 entries (~1 minute):

```bash
python analyze_vulnerabilities.py --test
```

### Specific Entry Range

You can specify entry ranges in two ways:

**Method 1: Via .env file**
Set `ENTRY_RANGE` in your `.env` file:
```env
ENTRY_RANGE=1-10       # Process entries 1-10
ENTRY_RANGE=26-51      # Process entries 26-51 (default)
ENTRY_RANGE=All        # Process all entries in the database
```

Then run:
```bash
python analyze_vulnerabilities.py
```

**Method 2: Via command-line argument**
Override the .env setting with `--range`:
```bash
# Process entries 1-5
python analyze_vulnerabilities.py --range "1-5"

# Process entries 26-50
python analyze_vulnerabilities.py --range "26-50"

# Process all entries
python analyze_vulnerabilities.py --range "All"
```

### Custom Output File

```bash
python analyze_vulnerabilities.py --output custom_results.xlsx
```

### Combined Options

```bash
# Process entries 10-20 and save to custom file
python analyze_vulnerabilities.py --range "10-20" --output results_10_20.xlsx
```

### Command-Line Options

```bash
python analyze_vulnerabilities.py --help
```

The script will:
1. Connect to the PostgreSQL database
2. Fetch entries 26-51 from the vulnerability dataset
3. For each entry, analyze:
   - Vulnerable function name
   - Fix that was applied
   - Explanation of the vulnerability
   - Similar code patterns in other GitHub repositories
4. Export results to `vulnerability_analysis_results.xlsx`

## Output Format

The Excel file will contain the following columns:

| Column | Description |
|--------|-------------|
| `commit_url` | URL to the commit that fixed the vulnerability |
| `cve_id` | CVE identifier |
| `hash` | Git commit hash |
| `repo_url` | Repository URL |
| `filename` | File that was changed |
| `vulnerable_function` | Name of the function containing the vulnerability |
| `fix_applied` | Description of the fix |
| `vulnerability_explanation` | Explanation of the SQL injection vulnerability |
| `github_repos_found` | JSON list of repositories with similar code |
| `github_repo_count` | Number of repositories found |
| `github_search_explanation` | Analysis of why these repos might be vulnerable |

## Expected Runtime

- Each entry takes approximately 15-30 seconds to analyze
- Total time for 26 entries: **7-13 minutes**
- Progress is displayed in real-time

## Troubleshooting

### "OPENAI_API_KEY not found"
- Ensure your `.env` file exists in the project root
- Check that the API key is correctly formatted (starts with `sk-`)

### "Database error: connection refused"
- Verify PostgreSQL is running
- Check database credentials in `.env`
- Ensure the database contains the required tables

### GitHub Rate Limit Errors
- Add a `GITHUB_TOKEN` to your `.env` file
- Wait for the rate limit to reset (typically 1 hour for unauthenticated requests)

### Empty Results
- Verify the database has entries in the range 26-51
- Check that entries match the filters (Python, CWE-89, score >= 55)

## Cost Estimation

### OpenAI API Costs (GPT-4o-mini)
- **Input:** ~500 tokens per entry × 26 entries = 13,000 tokens
- **Output:** ~300 tokens per entry × 26 entries = 7,800 tokens
- **Estimated cost:** $0.03 - $0.05 USD (very affordable!)

### GitHub API
- Free with or without token
- No cost for code search requests

## Support

If you encounter any issues, check:
1. Environment variables are correctly set
2. Database connection is working
3. API keys are valid and have sufficient quota
4. Internet connection is stable

