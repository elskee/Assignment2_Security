#!/usr/bin/env python3
"""
Vulnerability Analysis Script
Analyzes database entries 26-51, uses GPT-4o-mini to identify vulnerable functions,
fixes applied, and searches GitHub for similar vulnerable code patterns.
"""

import os
import json
import time
import argparse
import pandas as pd
import requests
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict, List
from sqlalchemy import create_engine
from tqdm import tqdm


class VulnerabilityAnalyzer:
    """Analyzes vulnerabilities using GPT-4o-mini and GitHub Search API"""
    
    def __init__(self, test_mode: bool = False, entry_range: str = None):
        """Initialize the analyzer with API credentials
        
        Args:
            test_mode: If True, only process 2 entries for testing (overrides entry_range)
            entry_range: Range of entries to process (e.g., "1-2", "26-50", "All")
                        If None, reads from ENTRY_RANGE env variable (defaults to "26-51")
        """
        load_dotenv()
        
        self.test_mode = test_mode
        
        # Parse entry range from argument or environment variable
        if test_mode:
            self.entry_range = "1-2"  # Override for test mode
        elif entry_range:
            self.entry_range = entry_range
        else:
            self.entry_range = os.getenv('ENTRY_RANGE', '26-51')
        
        # Parse the range
        self.start_entry, self.end_entry, self.limit_entries = self._parse_entry_range(self.entry_range)
        
        # Database configuration
        db_host = os.getenv('POSTGRES_HOST', '127.0.0.1')
        db_port = os.getenv('POSTGRES_PORT', '5432')
        db_name = os.getenv('POSTGRES_DBNAME', 'postgrescvedumper')
        db_user = os.getenv('POSTGRES_USER', 'postgrescvedumper')
        db_password = os.getenv('POSTGRES_PASSWORD')
        
        # Create SQLAlchemy engine
        self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        self.engine = create_engine(self.db_url)
        
        # API keys
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.github_token = os.getenv('GITHUB_TOKEN', '')  # Optional but recommended
        
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=self.openai_api_key)
    
    def _parse_entry_range(self, range_str: str) -> tuple:
        """Parse entry range string into start, end, and limit values
        
        Args:
            range_str: Range string like "1-2", "26-50", or "All"
            
        Returns:
            tuple: (start_index, end_index, limit_count)
        """
        range_str = range_str.strip()
        
        if range_str.lower() == 'all':
            # No limit, no offset
            return 0, None, None
        
        # Parse range like "1-2" or "26-50"
        if '-' in range_str:
            try:
                parts = range_str.split('-')
                start = int(parts[0].strip())
                end = int(parts[1].strip())
                
                if start < 1:
                    raise ValueError("Start entry must be >= 1")
                if end < start:
                    raise ValueError("End entry must be >= start entry")
                
                # Convert to 0-based offset and limit
                offset = start - 1  # Convert to 0-based index
                limit = end - start + 1  # Number of entries to fetch
                
                return offset, end, limit
                
            except (ValueError, IndexError) as e:
                raise ValueError(f"Invalid entry range format: {range_str}. Use format like '1-2', '26-50', or 'All'") from e
        else:
            raise ValueError(f"Invalid entry range format: {range_str}. Use format like '1-2', '26-50', or 'All'")
        
    def get_vulnerability_data(self) -> pd.DataFrame:
        """Fetch entries based on configured range"""
        # Build SQL query with dynamic LIMIT and OFFSET
        base_query = """
            SELECT 
                CONCAT(fx.repo_url, '/commit/', fx.hash) AS commit_url, 
                cv.cve_id, 
                fx.hash, 
                fx.repo_url, 
                f.filename, 
                f.num_lines_added, 
                f.num_lines_deleted, 
                f.code_before, 
                f.code_after, 
                f.diff_parsed, 
                cc.cwe_id 
            FROM file_change f, commits c, fixes fx, cve cv, cwe_classification cc
            WHERE f.hash = c.hash 
            AND c.hash = fx.hash 
            AND fx.cve_id = cv.cve_id 
            AND cv.cve_id = cc.cve_id 
            AND fx.score >= 55
            AND f.programming_language = 'Python'
            AND cc.cwe_id = 'CWE-89'
        """
        
        # Add ORDER BY
        sql_query = f"SELECT * FROM ({base_query}) AS t ORDER BY cve_id"
        
        # Add LIMIT and OFFSET if not "All"
        if self.limit_entries is not None:
            sql_query += f" LIMIT {self.limit_entries} OFFSET {self.start_entry}"
        
        # Display mode information
        if self.entry_range.lower() == 'all':
            mode_str = "Processing ALL entries"
        else:
            start_display = self.start_entry + 1  # Convert back to 1-based for display
            mode_str = f"Processing entries {start_display}-{self.end_entry}"
        
        print(f"Connecting to database... [{mode_str}]")
        
        print("\nExecuting query...")
        df = pd.read_sql_query(sql_query, self.engine)
        print(f"[OK] Query returned {len(df)} rows")
        
        return df
    
    def extract_function_name(self, code_before: str, filename: str) -> str:
        """Use GPT-4o-mini to extract the vulnerable function name"""
        prompt = f"""Analyze this Python code and identify the main function where a SQL injection vulnerability exists.

Filename: {filename}
Code:
```python
{code_before}
```

Respond with ONLY the function name (without parentheses or def keyword). If no function is found, respond with "N/A"."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing vulnerable code. Be concise and precise."},
                    {"role": "user", "content": prompt}
                ],
                # temperature=0.3,
                # max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error extracting function name: {e}")
            return "Error"
    
    def identify_fix(self, code_before: str, code_after: str, filename: str) -> str:
        """Use GPT-4o-mini to identify what fix was applied"""
        prompt = f"""Compare these two versions of Python code and describe what fix was applied to address a SQL injection vulnerability.

Filename: {filename}

BEFORE (vulnerable):
```python
{code_before}
```

AFTER (fixed):
```python
{code_after}
```

Provide a concise description (2-3 sentences) of the specific fix that was applied."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing vulnerability fixes. Be specific and technical."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error identifying fix: {e}")
            return "Error"
    
    def explain_vulnerability(self, code_before: str, filename: str) -> str:
        """Use GPT-4o-mini to explain the SQL injection vulnerability"""
        prompt = f"""Explain the SQL injection vulnerability in this Python code.

Filename: {filename}
Code:
```python
{code_before}
```

Provide a clear explanation (2-3 sentences) of:
1. What makes this code vulnerable to SQL injection
2. How an attacker could exploit it"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a security expert explaining vulnerabilities. Be clear and educational."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error explaining vulnerability: {e}")
            return "Error"
    
    def extract_search_terms(self, code_before: str, function_name: str) -> List[str]:
        """Extract key code patterns to search on GitHub"""
        # Remove comments and extract key lines
        lines = [line.strip() for line in code_before.split('\n') 
                 if line.strip() and not line.strip().startswith('#')]
        
        search_terms = []
        
        # Look for SQL-related patterns
        for line in lines:
            if any(keyword in line.lower() for keyword in ['execute', 'query', 'cursor', 'select', 'sql']):
                # Clean up the line for searching
                clean_line = line.replace('"', '').replace("'", "").strip()
                if len(clean_line) > 20 and len(clean_line) < 200:
                    search_terms.append(clean_line)
        
        # Add function name if available
        if function_name and function_name != "N/A" and function_name != "Error":
            search_terms.insert(0, f"def {function_name}")
        
        return search_terms[:3]  # Return top 3 search terms
    
    def search_github(self, search_terms: List[str], original_repo: str) -> Dict:
        """Search GitHub for similar code patterns"""
        headers = {
            'Accept': 'application/vnd.github.v3+json'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        all_repos = []
        
        for term in search_terms:
            try:
                # GitHub Code Search API
                search_query = f"{term} language:python"
                url = f"https://api.github.com/search/code?q={requests.utils.quote(search_query)}&per_page=5"
                
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    results = response.json()
                    
                    for item in results.get('items', []):
                        repo_full_name = item['repository']['full_name']
                        # Skip the original repo
                        if original_repo and repo_full_name.lower() in original_repo.lower():
                            continue
                        
                        repo_info = {
                            'repo': repo_full_name,
                            'html_url': item['repository']['html_url'],
                            'file': item['path'],
                            'file_url': item['html_url']
                        }
                        
                        # Avoid duplicates
                        if repo_info not in all_repos:
                            all_repos.append(repo_info)
                
                # Rate limiting - be nice to GitHub API
                time.sleep(2)
                
            except Exception as e:
                print(f"Error searching GitHub for term '{term}': {e}")
                continue
        
        # Get top 5 unique repos
        unique_repos = []
        seen_repos = set()
        for repo_info in all_repos:
            if repo_info['repo'] not in seen_repos:
                unique_repos.append(repo_info)
                seen_repos.add(repo_info['repo'])
            if len(unique_repos) >= 5:
                break
        
        return {
            'repos_found': unique_repos,
            'count': len(unique_repos)
        }
    
    def explain_github_findings(self, repos_found: List[Dict], search_terms: List[str]) -> str:
        """Use GPT to explain why these repos might have similar vulnerabilities"""
        if not repos_found:
            return "No similar code patterns found in other public repositories."
        
        repos_list = "\n".join([f"- {repo['repo']} (file: {repo['file']})" for repo in repos_found])
        
        prompt = f"""These GitHub repositories contain similar code patterns to a known SQL injection vulnerability:

{repos_list}

The search was based on these code patterns:
{chr(10).join(['- ' + term for term in search_terms])}

In 1-2 sentences, explain why these repositories might contain similar SQL injection vulnerabilities."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a security researcher analyzing code patterns across repositories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error explaining GitHub findings: {e}")
            return "Error analyzing findings"
    
    def analyze_entry(self, row: pd.Series, index: int, total: int) -> Dict:
        """Analyze a single vulnerability entry"""
        # Use tqdm.write to print without interfering with progress bar
        tqdm.write(f"\n[Entry {index}/{total}] CVE: {row['cve_id']} | File: {row['filename']}")
        
        result = {
            'commit_url': row['commit_url'],
            'cve_id': row['cve_id'],
            'hash': row['hash'],
            'repo_url': row['repo_url'],
            'filename': row['filename']
        }
        
        # Extract function name
        function_name = self.extract_function_name(row['code_before'], row['filename'])
        result['vulnerable_function'] = function_name
        tqdm.write(f"  [+] Function: {function_name}")
        
        # Identify fix
        fix_description = self.identify_fix(row['code_before'], row['code_after'], row['filename'])
        result['fix_applied'] = fix_description
        tqdm.write("  [+] Fix identified")
        
        # Explain vulnerability
        vulnerability_explanation = self.explain_vulnerability(row['code_before'], row['filename'])
        result['vulnerability_explanation'] = vulnerability_explanation
        tqdm.write("  [+] Vulnerability explained")
        
        # Search GitHub
        search_terms = self.extract_search_terms(row['code_before'], function_name)
        github_results = self.search_github(search_terms, row['repo_url'])
        result['github_repos_found'] = json.dumps(github_results['repos_found'], indent=2)
        result['github_repo_count'] = github_results['count']
        tqdm.write(f"  [+] GitHub search: {github_results['count']} repos found")
        
        # Explain GitHub findings
        github_explanation = self.explain_github_findings(github_results['repos_found'], search_terms)
        result['github_search_explanation'] = github_explanation
        
        return result
    
    def analyze_all(self) -> pd.DataFrame:
        """Analyze all vulnerability entries and return results"""
        if self.test_mode:
            mode_str = "TEST MODE"
        elif self.entry_range.lower() == 'all':
            mode_str = "FULL ANALYSIS (ALL ENTRIES)"
        else:
            start_display = self.start_entry + 1
            mode_str = f"ANALYSIS (Entries {start_display}-{self.end_entry})"
        
        print(f"\n{'='*80}")
        print(f"  {mode_str} - Starting Vulnerability Analysis")
        print(f"{'='*80}\n")
        
        # Get data from database
        df = self.get_vulnerability_data()
        
        if df.empty:
            print("No data found in the specified range")
            return pd.DataFrame()
        
        # Analyze each entry with progress bar
        results = []
        total = len(df)
        
        print(f"\nProcessing {total} entries...\n")
        
        # Use tqdm for progress bar
        for idx, row in tqdm(df.iterrows(), total=total, desc="Analyzing entries", unit="entry"):
            try:
                result = self.analyze_entry(row, idx + 1, total)
                results.append(result)
            except Exception as e:
                tqdm.write(f"\n[ERROR] processing entry {idx + 1}: {e}")
                # Add partial result with error
                results.append({
                    'commit_url': row['commit_url'],
                    'cve_id': row['cve_id'],
                    'hash': row['hash'],
                    'repo_url': row['repo_url'],
                    'filename': row['filename'],
                    'vulnerable_function': 'Error',
                    'fix_applied': 'Error',
                    'vulnerability_explanation': 'Error',
                    'github_repos_found': '[]',
                    'github_repo_count': 0,
                    'github_search_explanation': 'Error'
                })
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        return results_df
    
    def export_results(self, results_df: pd.DataFrame, output_file: str = 'vulnerability_analysis_results.xlsx'):
        """Export results to Excel"""
        print(f"\n{'='*80}")
        print(f"Exporting results to {output_file}...")
        
        results_df.to_excel(output_file, index=False, engine='openpyxl')
        
        print(f"Successfully exported {len(results_df)} analyzed entries to {output_file}")
        print(f"{'='*80}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Analyze SQL injection vulnerabilities using AI and GitHub search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test mode (2 entries only)
  python analyze_vulnerabilities.py --test
  
  # Specific range (from .env or command line)
  python analyze_vulnerabilities.py --range "1-5"
  python analyze_vulnerabilities.py --range "26-50"
  python analyze_vulnerabilities.py --range "All"
  
  # Default mode (uses ENTRY_RANGE from .env, defaults to "26-51")
  python analyze_vulnerabilities.py
  
  # Custom output file
  python analyze_vulnerabilities.py --output my_results.xlsx
        """
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Test mode: only process 2 entries (faster for testing)'
    )
    parser.add_argument(
        '--range',
        type=str,
        default=None,
        help='Entry range to process (e.g., "1-2", "26-50", "All"). Overrides ENTRY_RANGE from .env'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        default='vulnerability_analysis_results.xlsx',
        help='Output Excel file name (default: vulnerability_analysis_results.xlsx)'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer with test mode flag and entry range
        analyzer = VulnerabilityAnalyzer(test_mode=args.test, entry_range=args.range)
        
        # Perform analysis
        results = analyzer.analyze_all()
        
        if not results.empty:
            analyzer.export_results(results, output_file=args.output)
            print(f"\n{'='*80}")
            print("[SUCCESS] Analysis complete!")
            print(f"{'='*80}\n")
            return 0
        else:
            print("\n[ERROR] No results to export")
            return 1
            
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("\nPlease ensure the following environment variables are set:")
        print("  - OPENAI_API_KEY (required)")
        print("  - POSTGRES_PASSWORD (required for database access)")
        print("  - GITHUB_TOKEN (optional, but recommended for higher rate limits)")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

