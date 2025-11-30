"""
GPT-5 Integration Module
Handles all GPT-5 API interactions for pattern analysis and filtering.
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import os


class GPT5Handler:
    """Handles GPT-5 API interactions for vulnerability analysis."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the GPT-5 handler.
        
        Args:
            api_key: OpenAI API key (if None, reads from environment)
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = OpenAI(api_key=self.api_key)
        # Using gpt-4o (update to gpt-5 when available)
        self.model = "gpt-5-mini"
    
    def extract_search_patterns(self, code_snippet: str, vulnerability_type: str) -> List[str]:
        """
        Extract searchable patterns from a vulnerability code snippet.
        
        Args:
            code_snippet: The vulnerable code snippet
            vulnerability_type: Type/name of the vulnerability
        
        Returns:
            List of search query strings for GitHub
        """
        prompt = f"""You are a security researcher analyzing vulnerable code patterns to find SIMILAR SECURITY VULNERABILITIES.

Vulnerability Type: {vulnerability_type}

Code Snippet:
```python
{code_snippet}
```

Task: Extract 3-5 SPECIFIC search patterns that identify THE VULNERABILITY ITSELF, not just similar variable names or function calls.

CRITICAL Requirements:
1. Focus on the SECURITY FLAW pattern - what makes this code vulnerable?
2. For SQL injection: look for string concatenation/formatting with user input in SQL queries
3. For XSS: look for unescaped output rendering
4. For path traversal: look for unsanitized file paths
5. For command injection: look for shell command execution with user input
6. DO NOT match generic variable assignments or common function names
7. Match the DANGEROUS OPERATION in the code (e.g., execute() with %, os.system with +, etc.)
8. Each pattern should be a valid GitHub code search query focusing on the vulnerability

Return ONLY a JSON array of search query strings that identify the SECURITY VULNERABILITY.
Example format: ["execute(\"%s\" % user_input)", "os.system(cmd +"]
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert specializing in code vulnerability analysis. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.choices[0].message.content
            if not content:
                print(f"Warning: GPT returned empty response")
                return []
            
            content = content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith('```'):
                # Extract JSON from code block
                lines = content.split('\n')
                content = '\n'.join(lines[1:-1]) if len(lines) > 2 else content
                if content.startswith('json'):
                    content = content[4:].strip()
            
            # Parse JSON response
            patterns = json.loads(content)
            
            if isinstance(patterns, list):
                return [str(p) for p in patterns[:5]]  # Limit to 5 patterns
            else:
                return []
                
        except json.JSONDecodeError as e:
            # Fallback: extract patterns from response text
            print(f"Warning: Could not parse JSON from GPT response. Error: {e}")
            print(f"Raw response: {content[:200]}")
            return []
        except Exception as e:
            print(f"Error extracting search patterns: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def is_vulnerability_scanner(self, repo_name: str, description: str, readme_content: str = "") -> bool:
        """
        Determine if a repository is a vulnerability scanner/security tool.
        
        Args:
            repo_name: Repository name
            description: Repository description
            readme_content: README content (optional, first 2000 chars)
        
        Returns:
            True if the repo is a vulnerability scanner, False otherwise
        """
        # Truncate readme to save tokens
        readme_sample = readme_content[:2000] if readme_content else ""
        
        prompt = f"""Determine if this GitHub repository is a vulnerability scanner, security analysis tool, or penetration testing framework.

Repository: {repo_name}
Description: {description}

README Sample:
{readme_sample}

A repository IS a scanner/security tool if it:
- Scans code for vulnerabilities
- Is a security testing framework
- Is a penetration testing tool
- Is explicitly designed to find security issues in other code

A repository is NOT a scanner if it:
- Is a regular application that happens to have vulnerabilities
- Is a web framework, library, or tool with security issues
- Is a real-world project that contains vulnerable code patterns

Answer with ONLY "YES" if it's a scanner/security tool, or "NO" if it's not. No explanation."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert analyzing GitHub repositories. Answer only YES or NO."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return answer == "YES"
            
        except Exception as e:
            print(f"Error checking if scanner: {e}")
            # If error, be conservative and assume it's not a scanner
            return False
    
    def validate_code_similarity(self, original_vuln: str, found_code: str, vulnerability_type: str) -> bool:
        """
        Validate if found code truly matches the vulnerability pattern.
        
        Args:
            original_vuln: Original vulnerable code snippet
            found_code: Code found in GitHub search
            vulnerability_type: Type of vulnerability
        
        Returns:
            True if the code patterns match, False otherwise
        """
        prompt = f"""Compare these two Python code snippets to determine if they contain the SAME SECURITY VULNERABILITY.

Vulnerability Type: {vulnerability_type}

Original Vulnerable Code:
```python
{original_vuln}
```

Found Code:
```python
{found_code}
```

Question: Does the "Found Code" contain the SAME SECURITY VULNERABILITY as the "Original Vulnerable Code"?

STRICT Requirements - Answer YES only if:
1. SAME type of vulnerability (e.g., both SQL injection, both XSS, etc.)
2. SAME dangerous operation (e.g., both use .execute() with % formatting)
3. SAME security flaw mechanism (e.g., both concatenate user input into SQL)
4. The "Found Code" is ACTUALLY VULNERABLE, not just using similar variable names

Answer NO if:
- Just similar variable/function names but different context
- One is vulnerable but the other is safe
- Different types of vulnerabilities
- The "Found Code" is documentation, comments, or test files
- Different programming languages

Answer with ONLY "YES" if they share the EXACT SAME VULNERABILITY TYPE, or "NO" otherwise. No explanation."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a security expert comparing vulnerability patterns. Answer only YES or NO."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.choices[0].message.content.strip().upper()
            return answer == "YES"
            
        except Exception as e:
            print(f"Error validating similarity: {e}")
            # If error, be conservative and accept the match
            return True
    
    def generate_github_search_query(self, pattern: str) -> str:
        """
        Generate a GitHub code search query from a pattern.
        
        Args:
            pattern: Search pattern
        
        Returns:
            Formatted GitHub search query
        """
        # Add language filter for Python
        if "language:python" not in pattern.lower():
            return f"{pattern} language:python"
        return pattern

