# Quick Reference Guide

## Installation
```bash
pip install -r requirements.txt
```

## Configuration (.env file)

```env
# Database
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DBNAME=postgrescvedumper
POSTGRES_USER=postgrescvedumper
POSTGRES_PASSWORD=your_password

# APIs (Required)
OPENAI_API_KEY=sk-your-key-here

# APIs (Optional)
GITHUB_TOKEN=ghp-your-token-here

# Entry Range (Optional, defaults to "26-51")
ENTRY_RANGE=26-51
```

## Common Commands

### Test Mode (2 entries, ~1 min)
```bash
python analyze_vulnerabilities.py --test
```

### Specific Ranges
```bash
# First 5 entries
python analyze_vulnerabilities.py --range "1-5"

# Assignment range (26-51)
python analyze_vulnerabilities.py --range "26-51"

# Custom range
python analyze_vulnerabilities.py --range "10-20"

# All entries
python analyze_vulnerabilities.py --range "All"
```

### Using .env Configuration
```bash
# Uses ENTRY_RANGE from .env (defaults to "26-51")
python analyze_vulnerabilities.py
```

### Custom Output File
```bash
python analyze_vulnerabilities.py --output my_results.xlsx
python analyze_vulnerabilities.py --range "1-10" --output test.xlsx
```

### Help
```bash
python analyze_vulnerabilities.py --help
```

## Entry Range Formats

| Format | Example | Description |
|--------|---------|-------------|
| `X-Y` | `1-10` | Process entries X through Y (inclusive) |
| `All` | `All` | Process all database entries |

## Time Estimates

| Entries | Time | Command |
|---------|------|---------|
| 2 | 1 min | `--test` or `--range "1-2"` |
| 5 | 2-3 min | `--range "1-5"` |
| 10 | 5 min | `--range "1-10"` |
| 26 | 13 min | `--range "26-51"` (default) |
| 100 | 50 min | `--range "1-100"` |

## Output Columns

| Column | Description |
|--------|-------------|
| `commit_url` | URL to the fix commit |
| `cve_id` | CVE identifier |
| `hash` | Git commit hash |
| `repo_url` | Repository URL |
| `filename` | File that was changed |
| `vulnerable_function` | Function with vulnerability |
| `fix_applied` | Description of the fix |
| `vulnerability_explanation` | How the vulnerability works |
| `github_repos_found` | JSON list of similar repos |
| `github_repo_count` | Number of repos found |
| `github_search_explanation` | Why repos might be vulnerable |

## Troubleshooting

### "OPENAI_API_KEY not found"
- Create `.env` file in project root
- Add `OPENAI_API_KEY=sk-your-key-here`

### Database connection error
- Check PostgreSQL is running
- Verify credentials in `.env`

### Rate limit errors (GitHub)
- Add `GITHUB_TOKEN` to `.env`
- Or wait for rate limit reset

### Invalid range format
- Use format: `"1-10"` or `"All"`
- Start must be >= 1
- End must be >= start

## Examples

```bash
# Quick test
python analyze_vulnerabilities.py --test

# Assignment requirement
python analyze_vulnerabilities.py --range "26-51"

# First 10 entries with custom output
python analyze_vulnerabilities.py --range "1-10" --output first_10.xlsx

# Process all entries in database
python analyze_vulnerabilities.py --range "All"

# Use .env configuration
echo "ENTRY_RANGE=1-20" >> .env
python analyze_vulnerabilities.py
```

