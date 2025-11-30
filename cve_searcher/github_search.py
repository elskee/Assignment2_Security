"""
GitHub Search Module
Handles GitHub API interactions for code search and repository analysis.
"""
from github import Github, GithubException, RateLimitExceededException
from typing import List, Dict, Any, Optional
import time
import os


class GitHubSearcher:
    """Handles GitHub API searches and repository analysis."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the GitHub searcher.
        
        Args:
            token: GitHub personal access token (if None, reads from environment)
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token not provided. API rate limits will be severely restricted.")
        
        self.github = Github(self.token)
        self.rate_limit_delay = 2  # Seconds to wait between requests
    
    def search_code(self, query: str, max_results: int = 30) -> List[Dict[str, Any]]:
        """
        Search GitHub for code matching the query.
        
        Args:
            query: GitHub code search query
            max_results: Maximum number of results to return
        
        Returns:
            List of code search results with repository information
        """
        results = []
        
        try:
            # Search for code
            search_results = self.github.search_code(query=query)
            
            # Process results
            count = 0
            for code_file in search_results:
                if count >= max_results:
                    break
                
                try:
                    repo = code_file.repository
                    
                    # Get commit SHA for the file
                    commit_sha = None
                    commit_url = None
                    try:
                        # Get the most recent commit for this file
                        commits = repo.get_commits(path=code_file.path)
                        if commits.totalCount > 0:
                            latest_commit = commits[0]
                            commit_sha = latest_commit.sha
                            commit_url = f"https://github.com/{repo.full_name}/commit/{commit_sha}"
                    except Exception as e:
                        print(f"    Warning: Could not get commit info: {e}")
                        # Fallback: use default branch's latest commit
                        try:
                            default_branch = repo.default_branch
                            branch = repo.get_branch(default_branch)
                            commit_sha = branch.commit.sha
                            commit_url = f"https://github.com/{repo.full_name}/commit/{commit_sha}"
                        except:
                            pass
                    
                    result = {
                        'repo_name': repo.full_name,
                        'repo_url': repo.html_url,
                        'stars': repo.stargazers_count,
                        'description': repo.description or "",
                        'file_path': code_file.path,
                        'file_url': code_file.html_url,
                        'code_snippet': self._get_code_content(code_file),
                        'commit_sha': commit_sha,
                        'commit_url': commit_url,
                        'repo_object': repo  # Keep for later use
                    }
                    
                    results.append(result)
                    count += 1
                    
                    # Rate limiting
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    print(f"Error processing search result: {e}")
                    continue
            
        except RateLimitExceededException:
            print("GitHub API rate limit exceeded. Waiting...")
            self._wait_for_rate_limit()
            # Retry once
            return self.search_code(query, max_results)
        except GithubException as e:
            print(f"GitHub API error during search: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error during GitHub search: {e}")
            return []
        
        return results
    
    def _get_code_content(self, code_file) -> str:
        """
        Get the content of a code file.
        
        Args:
            code_file: GitHub code file object
        
        Returns:
            File content as string (truncated to 5000 chars)
        """
        try:
            content = code_file.decoded_content.decode('utf-8')
            # Truncate long files
            return content[:5000]
        except Exception as e:
            print(f"Error getting code content: {e}")
            return ""
    
    def get_readme(self, repo) -> str:
        """
        Get repository README content.
        
        Args:
            repo: GitHub repository object
        
        Returns:
            README content as string (truncated to 3000 chars)
        """
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode('utf-8')
            return content[:3000]  # Truncate for GPT analysis
        except Exception:
            return ""
    
    def aggregate_by_repository(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Aggregate search results by repository (remove duplicates).
        
        Args:
            results: List of code search results
        
        Returns:
            List of unique repositories with their information
        """
        repo_map = {}
        
        for result in results:
            repo_name = result['repo_name']
            
            if repo_name not in repo_map:
                repo_map[repo_name] = {
                    'repo_name': repo_name,
                    'repo_url': result['repo_url'],
                    'stars': result['stars'],
                    'description': result['description'],
                    'code_samples': [result['code_snippet']],
                    'file_urls': [result['file_url']],
                    'file_path': result.get('file_path', ''),
                    'code_snippet': result.get('code_snippet', ''),
                    'commit_sha': result.get('commit_sha', ''),
                    'commit_url': result.get('commit_url', ''),
                    'repo_object': result.get('repo_object')
                }
            else:
                # Add additional code samples from the same repo
                repo_map[repo_name]['code_samples'].append(result['code_snippet'])
                repo_map[repo_name]['file_urls'].append(result['file_url'])
        
        # Convert to list and sort by stars
        repos = list(repo_map.values())
        repos.sort(key=lambda x: x['stars'], reverse=True)
        
        return repos
    
    def filter_and_rank_repositories(self, repos: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Filter and rank repositories by star count.
        
        Args:
            repos: List of repositories
            limit: Maximum number of repositories to return
        
        Returns:
            Top N repositories sorted by stars
        """
        # Already sorted by stars in aggregate_by_repository
        return repos[:limit]
    
    def _wait_for_rate_limit(self) -> None:
        """Wait until GitHub API rate limit resets."""
        try:
            rate_limit = self.github.get_rate_limit()
            reset_time = rate_limit.core.reset
            wait_time = (reset_time - time.time()) + 10  # Add 10 second buffer
            
            if wait_time > 0:
                print(f"Waiting {wait_time:.0f} seconds for rate limit to reset...")
                time.sleep(wait_time)
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            # Default wait time
            time.sleep(60)
    
    def check_rate_limit(self) -> Dict[str, int]:
        """
        Check current GitHub API rate limit status.
        
        Returns:
            Dictionary with remaining requests and reset time
        """
        try:
            rate_limit = self.github.get_rate_limit()
            core = rate_limit.core
            
            return {
                'remaining': core.remaining,
                'limit': core.limit,
                'reset': core.reset.timestamp() if hasattr(core.reset, 'timestamp') else core.reset
            }
        except Exception as e:
            # Silently return default values if rate limit check fails
            return {'remaining': 5000, 'limit': 5000, 'reset': 0}
    
    def search_for_vulnerability(self, search_queries: List[str], max_results_per_query: int = 30) -> List[Dict[str, Any]]:
        """
        Search for vulnerability across multiple queries.
        
        Args:
            search_queries: List of search query strings
            max_results_per_query: Maximum results per query
        
        Returns:
            Aggregated and deduplicated repository results
        """
        all_results = []
        
        for query in search_queries:
            print(f"  Searching: {query[:80]}...")
            results = self.search_code(query, max_results=max_results_per_query)
            all_results.extend(results)
            
            # Small delay between queries
            time.sleep(1)
        
        # Aggregate by repository and sort by stars
        unique_repos = self.aggregate_by_repository(all_results)
        
        return unique_repos
