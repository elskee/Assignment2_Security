# Assignment 2 - Security Vulnerability Analysis

A security research project that analyzes SQL injection vulnerabilities (CWE-89) in Python code and searches for similar vulnerable patterns in other GitHub repositories.

## Project Structure

### `cve_searcher/`
Automated tool that searches GitHub for vulnerable code patterns similar to those found in CVE databases.

**Features:**
- AI-powered search pattern extraction using GPT
- GitHub code search integration
- Automatic filtering of security scanner projects
- Results ranked by repository stars

### `database_interaction/`
Database analysis tools for extracting and processing vulnerability data from PostgreSQL CVE database.

**Features:**
- SQL query execution and data export
- Vulnerability analysis and reporting
- Excel report generation

## Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key
- GitHub Personal Access Token (recommended)
- PostgreSQL database (for database_interaction only)

### Setup

1. **Install dependencies:**
   ```bash
   # For CVE searcher
   cd cve_searcher
   pip install -r requirements.txt
   
   # For database interaction
   cd database_interaction
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   
   Create a `.env` file in the appropriate directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   GITHUB_TOKEN=your_github_token
   
   # For database_interaction only:
   POSTGRES_HOST=127.0.0.1
   POSTGRES_PORT=5432
   POSTGRES_DBNAME=postgrescvedumper
   POSTGRES_USER=your_username
   POSTGRES_PASSWORD=your_password
   ```

3. **Run the tools:**
   
   **CVE Searcher:**
   ```bash
   cd cve_searcher
   python main.py
   ```
   
   **Database Export:**
   ```bash
   cd database_interaction
   python export_to_excel.py
   ```

## Getting API Keys

**OpenAI API Key:** https://platform.openai.com/api-keys
- Sign in and create a new secret key

**GitHub Token:** https://github.com/settings/tokens
- Generate a classic token with `public_repo` and `read:org` scopes

## Output

Results are saved to Excel files:
- `cve_searcher/dataclean_results.xlsx` - GitHub search results
- `database_interaction/vulnerability_analysis_results.xlsx` - Database analysis

## Notes

- Keep your `.env` files secure and never commit them to version control
- This tool is for security research and educational purposes only

