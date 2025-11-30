"""
Logging Configuration Module
Sets up comprehensive logging for the vulnerability searcher.
"""
import logging
import os
from datetime import datetime


def setup_logger(name: str = "vulnerability_searcher", log_dir: str = "logs") -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler (detailed logs)
    log_filename = os.path.join(
        log_dir,
        f"vulnerability_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Console handler (important messages only)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized. Log file: {log_filename}")
    
    return logger


def log_api_call(logger: logging.Logger, api_name: str, success: bool, details: str = ""):
    """
    Log an API call with consistent formatting.
    
    Args:
        logger: Logger instance
        api_name: Name of the API (GPT-5, GitHub, etc.)
        success: Whether the call was successful
        details: Additional details
    """
    if success:
        logger.debug(f"{api_name} API call successful. {details}")
    else:
        logger.error(f"{api_name} API call failed. {details}")


def log_rate_limit(logger: logging.Logger, api_name: str, remaining: int, limit: int):
    """
    Log API rate limit status.
    
    Args:
        logger: Logger instance
        api_name: Name of the API
        remaining: Remaining requests
        limit: Total limit
    """
    percentage = (remaining / limit * 100) if limit > 0 else 0
    
    if percentage < 10:
        logger.warning(f"{api_name} rate limit low: {remaining}/{limit} ({percentage:.1f}%)")
    else:
        logger.debug(f"{api_name} rate limit: {remaining}/{limit} ({percentage:.1f}%)")


def log_vulnerability_processing(logger: logging.Logger, row_index: int, cve_id: str, status: str, details: str = ""):
    """
    Log vulnerability processing status.
    
    Args:
        logger: Logger instance
        row_index: Excel row index
        cve_id: CVE identifier
        status: Processing status (started, completed, failed, skipped)
        details: Additional details
    """
    message = f"Row {row_index} (CVE: {cve_id}) - {status}"
    if details:
        message += f" - {details}"
    
    if status.lower() == "failed":
        logger.error(message)
    elif status.lower() == "skipped":
        logger.warning(message)
    else:
        logger.info(message)


def log_search_results(logger: logging.Logger, row_index: int, num_results: int, repos: list = None):
    """
    Log search results summary.
    
    Args:
        logger: Logger instance
        row_index: Excel row index
        num_results: Number of results found
        repos: List of repository names (optional)
    """
    if num_results == 0:
        logger.warning(f"Row {row_index}: No repositories found")
    else:
        logger.info(f"Row {row_index}: Found {num_results} repositories")
        if repos:
            for repo in repos:
                logger.debug(f"  - {repo}")

