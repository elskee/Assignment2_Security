"""
GitHub Vulnerability Code Search Tool
Main program that coordinates all modules to find similar vulnerabilities in GitHub repositories.
"""
import os
import sys
from dotenv import load_dotenv
from typing import List, Dict, Any
import time

from excel_handler import ExcelHandler
from gpt5_handler import GPT5Handler
from github_search import GitHubSearcher


class VulnerabilitySearcher:
    """Main class coordinating vulnerability search across GitHub."""
    
    def __init__(self, excel_path: str):
        """
        Initialize the vulnerability searcher.
        
        Args:
            excel_path: Path to the Excel file with vulnerability data
        """
        # Load environment variables
        load_dotenv()
        
        self.excel_path = excel_path
        self.excel_handler = None
        self.gpt5_handler = None
        self.github_searcher = None
        
        # Configuration
        self.max_repos_per_vulnerability = 5
        self.max_search_results_per_query = 10  # Reduced from 30 to speed up searches
        
    def initialize(self) -> bool:
        """
        Initialize all handlers and validate API keys.
        
        Returns:
            True if initialization successful, False otherwise
        """
        print("Initializing Vulnerability Searcher...")
        
        # Check for API keys
        openai_key = os.getenv('OPENAI_API_KEY')
        github_token = os.getenv('GITHUB_TOKEN')
        
        if not openai_key:
            print("ERROR: OPENAI_API_KEY not found in environment variables.")
            print("Please create a .env file with your API key (see env.template)")
            return False
        
        if not github_token:
            print("ERROR: GITHUB_TOKEN not found in environment variables.")
            print("Please create a .env file with your GitHub token (see env.template)")
            return False
        
        try:
            # Initialize handlers
            self.excel_handler = ExcelHandler(self.excel_path)
            self.gpt5_handler = GPT5Handler(openai_key)
            self.github_searcher = GitHubSearcher(github_token)
            
            print("✓ All handlers initialized successfully")
            return True
            
        except Exception as e:
            print(f"ERROR during initialization: {e}")
            return False
    
    def process_vulnerability(self, vuln_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a single vulnerability and find similar code in GitHub.
        
        Args:
            vuln_data: Dictionary containing vulnerability information
        
        Returns:
            List of repositories containing similar vulnerabilities
        """
        # Start timeout timer (5 minutes max per vulnerability)
        start_time = time.time()
        timeout_seconds = 300  # 5 minutes
        
        data = vuln_data['data']
        code_snippet = data.get('code', '')
        vulnerability_type = data.get('Vulnerability', 'Unknown')
        
        if not code_snippet:
            print("  ⚠ No code snippet found, skipping...")
            return []
        
        print(f"  Vulnerability: {vulnerability_type}")
        print(f"  Code length: {len(code_snippet)} characters")
        
        # Step 1: Extract search patterns using GPT-5
        print("  [1/4] Extracting search patterns with GPT-5...")
        search_patterns = self.gpt5_handler.extract_search_patterns(
            code_snippet, vulnerability_type
        )
        
        # Check timeout after GPT call
        if time.time() - start_time > timeout_seconds:
            print(f"  ⚠ Timeout reached ({timeout_seconds}s), stopping early...")
            return []
        
        if not search_patterns:
            print("  ⚠ No search patterns extracted, skipping...")
            return []
        
        print(f"  Found {len(search_patterns)} search patterns")
        
        # Step 2: Search GitHub for matching code
        print("  [2/4] Searching GitHub repositories...")
        repos = self.github_searcher.search_for_vulnerability(
            search_patterns,
            max_results_per_query=self.max_search_results_per_query
        )
        
        # Check timeout after GitHub search
        if time.time() - start_time > timeout_seconds:
            print(f"  ⚠ Timeout reached ({timeout_seconds}s), stopping early...")
            return []
        
        if not repos:
            print("  ⚠ No repositories found")
            return []
        
        print(f"  Found {len(repos)} unique repositories")
        
        # Step 3: Filter out vulnerability scanners
        print("  [3/4] Filtering out vulnerability scanners...")
        filtered_repos = []
        
        for repo in repos:
            # Check timeout during filtering (most time-consuming step)
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout_seconds:
                print(f"  ⚠ Timeout reached ({timeout_seconds}s) during filtering")
                print(f"  Returning {len(filtered_repos)} repositories found so far...")
                break
            
            # Check rate limit
            rate_info = self.github_searcher.check_rate_limit()
            if rate_info['remaining'] < 10:
                print(f"  ⚠ Low API rate limit ({rate_info['remaining']} remaining), pausing...")
                time.sleep(10)
            
            # Get README for scanner detection
            readme = ""
            if repo.get('repo_object'):
                readme = self.github_searcher.get_readme(repo['repo_object'])
            
            is_scanner = self.gpt5_handler.is_vulnerability_scanner(
                repo['repo_name'],
                repo['description'],
                readme
            )
            
            if not is_scanner:
                filtered_repos.append(repo)
            else:
                print(f"    Filtered out scanner: {repo['repo_name']}")
            
            # Limit to top 10 before validation (to save API calls)
            if len(filtered_repos) >= 10:
                break
        
        print(f"  {len(filtered_repos)} repositories after filtering")
        
        if not filtered_repos:
            print("  ⚠ No repositories remaining after filtering")
            return []
        
        # Step 4: Validate code similarity with GPT-5
        print("  [4/4] Validating code similarity with GPT-5...")
        validated_repos = []
        
        for repo in filtered_repos:
            # Check timeout
            if time.time() - start_time > timeout_seconds:
                print(f"  ⚠ Timeout reached during validation")
                break
            
            # Validate that the found code actually contains the same vulnerability
            is_similar = self.gpt5_handler.validate_code_similarity(
                code_snippet,
                repo.get('code_snippet', ''),
                vulnerability_type
            )
            
            if is_similar:
                validated_repos.append(repo)
                print(f"    ✓ Validated: {repo['repo_name']}")
            else:
                print(f"    ✗ Rejected: {repo['repo_name']} (different vulnerability pattern)")
            
            # Stop after we have enough validated results
            if len(validated_repos) >= self.max_repos_per_vulnerability:
                break
        
        print(f"  {len(validated_repos)} repositories validated")
        
        if not validated_repos:
            print("  ⚠ No repositories passed validation")
            return []
        
        # Sort validated repos by stars and take top N
        validated_repos.sort(key=lambda x: x['stars'], reverse=True)
        top_repos = validated_repos[:self.max_repos_per_vulnerability]
        
        # Log processing time
        elapsed_time = time.time() - start_time
        print(f"  Processing time: {elapsed_time:.1f}s")
        
        # Format results with enriched data
        results = []
        for repo in top_repos:
            results.append({
                'repo_name': repo['repo_name'],
                'stars': repo['stars'],
                'url': repo['repo_url'],
                'commit_url': repo.get('commit_url', ''),
                'file_path': repo.get('file_path', ''),
                'code_snippet': repo.get('code_snippet', ''),
                'commit_sha': repo.get('commit_sha', '')
            })
        
        print(f"  ✓ Found {len(results)} matching repositories")
        return results
    
    def run(self) -> None:
        """Run the vulnerability search process."""
        print("\n" + "="*70)
        print("GitHub Vulnerability Code Search Tool")
        print("="*70 + "\n")
        
        if not self.initialize():
            print("\nInitialization failed. Exiting.")
            sys.exit(1)
        
        # Load Excel data
        print(f"\nLoading Excel file: {self.excel_path}")
        try:
            vulnerabilities = self.excel_handler.load()
            print(f"✓ Loaded {len(vulnerabilities)} vulnerability records\n")
        except Exception as e:
            print(f"ERROR loading Excel file: {e}")
            sys.exit(1)
        
        # Process each vulnerability
        total = len(vulnerabilities)
        processed = 0
        updated = 0
        
        # Process all vulnerabilities
        test_limit = None
        if test_limit:
            print(f"\n⚠ TEST MODE: Processing only first {test_limit} entries\n")
            vulnerabilities = vulnerabilities[:test_limit]
            total = len(vulnerabilities)
        
        for idx, vuln in enumerate(vulnerabilities, 1):
            row_index = vuln['row_index']
            data = vuln['data']
            
            print(f"\n[{idx}/{total}] Processing row {row_index}...")
            print(f"  CVE: {data.get('cve_id', 'N/A')}")
            
            try:
                # Check if already processed (disabled in test mode)
                if not test_limit:
                    existing_results = data.get('Found in other projects', '')
                    if existing_results and len(existing_results) > 10:
                        print("  ⚠ Already has results, skipping...")
                        processed += 1
                        continue
                
                # Process vulnerability
                results = self.process_vulnerability(vuln)
                
                if results:
                    # Update Excel - original column
                    self.excel_handler.update_found_in_projects(row_index, results)
                    
                    # Add each result to the new detailed worksheet
                    cve_id = data.get('cve_id', 'N/A')
                    vulnerability_type = data.get('Vulnerability', 'Unknown')
                    for result in results:
                        self.excel_handler.add_result_to_worksheet(
                            cve_id, 
                            vulnerability_type, 
                            result
                        )
                    
                    updated += 1
                    
                    # Display results
                    print(f"\n  Results for row {row_index}:")
                    for r in results:
                        print(f"    - {r['repo_name']} ({r['stars']} stars)")
                        print(f"      {r['url']}")
                        if r.get('commit_url'):
                            print(f"      Commit: {r['commit_url']}")
                        if r.get('file_path'):
                            print(f"      File: {r['file_path']}")
                else:
                    # Write "None found" to the original column
                    self.excel_handler.update_found_in_projects_none(row_index)
                    print(f"  No results found for row {row_index}")
                
                processed += 1
                
                # Save periodically (every 5 vulnerabilities)
                if processed % 5 == 0:
                    print(f"\n  Saving progress ({processed}/{total})...")
                    self.excel_handler.save(backup=True)
                
            except KeyboardInterrupt:
                print("\n\n⚠ Interrupted by user. Saving progress...")
                self.excel_handler.save(backup=True)
                print("Progress saved. Exiting.")
                sys.exit(0)
            except Exception as e:
                print(f"  ERROR processing vulnerability: {e}")
                continue
        
        # Save final results
        print(f"\n\n{'='*70}")
        print("Processing Complete")
        print(f"{'='*70}")
        print(f"Total vulnerabilities processed: {processed}/{total}")
        print(f"Successfully updated: {updated}")
        print(f"\nSaving final results to: {self.excel_path}")
        
        try:
            self.excel_handler.save(backup=True)
            print("✓ Results saved successfully")
            print(f"  (Backup created: {self.excel_path}.bak)")
        except Exception as e:
            print(f"ERROR saving results: {e}")
        
        # Cleanup
        self.excel_handler.close()
        print("\nDone!")


def main():
    """Main entry point."""
    # Default Excel file path
    excel_file = "dataclean_results.xlsx"
    
    # Check if file exists
    if not os.path.exists(excel_file):
        print(f"ERROR: Excel file not found: {excel_file}")
        print("Please ensure the file exists in the current directory.")
        sys.exit(1)
    
    # Create and run searcher
    searcher = VulnerabilitySearcher(excel_file)
    searcher.run()


if __name__ == "__main__":
    main()

