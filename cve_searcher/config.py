"""
Configuration Module
Central configuration for the vulnerability searcher.
"""


class Config:
    """Configuration settings for the vulnerability searcher."""
    
    # Excel file settings
    EXCEL_FILE_PATH = "dataclean_results.xlsx"
    CREATE_BACKUP = True
    
    # Search settings
    MAX_REPOS_PER_VULNERABILITY = 5
    MAX_SEARCH_RESULTS_PER_QUERY = 30
    
    # GitHub API settings
    GITHUB_RATE_LIMIT_DELAY = 2  # Seconds between requests
    GITHUB_MIN_STARS = 0  # Minimum stars for a repo to be included
    
    # GPT settings
    GPT_MODEL = "gpt-5-mini" 
    # GPT_TEMPERATURE = 0.3 Not in use for GPT-5
    GPT_MAX_TOKENS = 500
    
    # Validation settings
    VALIDATE_CODE_SIMILARITY = False  # Set to True to enable GPT validation (costs more)
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # Seconds
    
    # Progress settings
    SAVE_INTERVAL = 5  # Save every N vulnerabilities
    
    # Logging settings
    LOG_DIRECTORY = "logs"
    LOG_LEVEL = "INFO"
    
    # Filtering settings
    EXCLUDE_FORKS = True  # Exclude forked repositories
    EXCLUDE_ARCHIVED = True  # Exclude archived repositories


def get_config():
    """Get the configuration instance."""
    return Config()

