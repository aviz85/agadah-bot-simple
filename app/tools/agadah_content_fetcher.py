"""
Agadah Content Fetcher Tool

Tool to fetch and extract the actual content of a story from agadah.org.il.
"""

import json
import logging
import re
from typing import Optional
from urllib.parse import urlparse, unquote

import requests
from bs4 import BeautifulSoup
from crewai.tools.base_tool import BaseTool

# Set up logging
logger = logging.getLogger(__name__)


class AgadahContentFetcherTool(BaseTool):
    """
    Tool to fetch and extract the actual content of a story from agadah.org.il.
    """
    
    name: str = "Agadah Content Fetcher"
    description: str = """Fetch and extract the actual content of a story from agadah.org.il.
    
    Use this tool to:
    - Get the full text content of a story from its URL
    - Extract the story body text
    - Get the story's main content for analysis
    
    Returns: JSON with story title, content, and metadata.
    """
    
    def __init__(self, **kwargs):
        """Initialize the content fetcher tool."""
        super().__init__(**kwargs)
        logger.info("Initialized AgadahContentFetcherTool")
    
    def _run(self, url: str) -> str:
        """
        Fetch story content from URL.

        Args:
            url: URL to the story on agadah.org.il (required)

        Returns:
            JSON string with story content
        """
        if not url or not url.strip():
            error_msg = "URL cannot be empty"
            logger.warning(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Clean and decode URL (handles URL-encoded Hebrew characters)
        url = unquote(url.strip())

        # Validate URL
        if not url.startswith(('http://', 'https://')):
            error_msg = f"Invalid URL format: {url}"
            logger.warning(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        # Ensure it's from agadah.org.il
        if "agadah.org.il" not in url:
            error_msg = f"URL must be from agadah.org.il, got: {url}"
            logger.warning(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

        logger.debug(f"Decoded URL for fetching: {url}")
        
        # Check if URL is likely a homepage or category page
        url_lower = url.lower()
        invalid_patterns = ['/category/', '/tag/', '/author/', '/page/', '/feed/']
        if any(pattern in url_lower for pattern in invalid_patterns):
            error_msg = f"URL appears to be a category/archive page, not a story: {url}"
            logger.warning(error_msg)
            return json.dumps({
                "error": error_msg,
                "url": url,
                "status": "invalid_url_type"
            }, ensure_ascii=False)
        
        # Check if URL ends with just domain (homepage)
        if url.rstrip('/') in ['https://agadah.org.il', 'http://agadah.org.il']:
            error_msg = f"URL is the homepage, not a story: {url}"
            logger.warning(error_msg)
            return json.dumps({
                "error": error_msg,
                "url": url,
                "status": "homepage"
            }, ensure_ascii=False)
        
        logger.info(f"Fetching content from: {url}")
        
        # Retry logic for network errors
        max_retries = 2
        retry_delay = 1
        response = None
        
        for attempt in range(max_retries):
            try:
                # Fetch the page with shorter timeout for faster iteration
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                # Success - break out of retry loop
                break
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}/{max_retries}), retrying...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    error_msg = f"Timeout after {max_retries} attempts while fetching content from: {url}"
                    logger.error(error_msg)
                    return json.dumps({
                        "error": error_msg,
                        "url": url,
                        "status": "timeout_error"
                    }, ensure_ascii=False)
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Network error fetching {url} (attempt {attempt + 1}/{max_retries}): {e}, retrying...")
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    error_msg = f"Network error after {max_retries} attempts while fetching content from: {url}"
                    logger.error(error_msg)
                    return json.dumps({
                        "error": error_msg,
                        "url": url,
                        "status": "network_error"
                    }, ensure_ascii=False)
        
        # If we got here without a response, something went wrong
        if response is None:
            error_msg = f"Failed to fetch content after {max_retries} attempts: {url}"
            logger.error(error_msg)
            return json.dumps({
                "error": error_msg,
                "url": url,
                "status": "fetch_failed"
            }, ensure_ascii=False)
        
        try:
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('h1') or soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract main content
            # Look for common content containers
            content = ""
            content_selectors = [
                'article',
                '.entry-content',
                '.post-content',
                '.content',
                'main',
                '.story-content',
                '#content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style", "nav", "footer", "header", "aside"]):
                        script.decompose()
                    content = content_elem.get_text(separator='\n', strip=True)
                    if len(content) > 100:  # Ensure we got substantial content
                        break
            
            # If no content found with selectors, try to get body text
            if not content or len(content) < 100:
                body = soup.find('body')
                if body:
                    # Remove script and style
                    for script in body(["script", "style", "nav", "footer", "header", "aside"]):
                        script.decompose()
                    content = body.get_text(separator='\n', strip=True)
            
            # Clean up content
            content = self._clean_text(content)
            
            # Quality checks for story content
            if content:
                # Check if content looks like a navigation/menu page (many links)
                link_count = content.lower().count('http://') + content.lower().count('https://')
                if link_count > 10:
                    error_msg = f"Content contains too many links ({link_count}) - likely a navigation/menu page, not a story"
                    logger.warning(f"{error_msg} for URL: {url}")
                    return json.dumps({
                        "error": error_msg,
                        "url": url,
                        "title": title or "Unknown",
                        "content_length": len(content),
                        "link_count": link_count
                    }, ensure_ascii=False)
                
                # Check if content is mostly navigation text (common menu items)
                # Use STRONG indicators that are very specific to navigation/homepage pages
                strong_nav_keywords = [
                    'דלגו לניווט', 'דלגו לתוכן', 'דלגו לפוטר',  # Skip navigation links
                    'סיפורים עם:', 'מאז ועד היום',  # Category page headers
                    'סרטונים ופודקאסטים',  # Homepage sections
                    'תנאי שימוש', 'הצהרת נגישות',  # Footer legal links
                ]
                
                # Count strong navigation indicators
                strong_nav_score = sum(1 for keyword in strong_nav_keywords if keyword in content)
                
                # If we have multiple strong indicators, it's likely a navigation page
                if strong_nav_score >= 2:
                    error_msg = f"Content appears to be a navigation/menu page (found {strong_nav_score} strong navigation indicators), not a story"
                    logger.warning(f"{error_msg} for URL: {url}")
                    return json.dumps({
                        "error": error_msg,
                        "url": url,
                        "title": title or "Unknown",
                        "content_length": len(content),
                        "navigation_indicators": strong_nav_score
                    }, ensure_ascii=False)
                
                # Additional check: if content is very short AND has navigation elements, likely not a story
                if len(content) < 300 and strong_nav_score >= 1:
                    error_msg = f"Content too short ({len(content)} chars) with navigation elements - likely not a story"
                    logger.warning(f"{error_msg} for URL: {url}")
                    return json.dumps({
                        "error": error_msg,
                        "url": url,
                        "title": title or "Unknown",
                        "content_length": len(content)
                    }, ensure_ascii=False)
            
            # Limit content length (max 5000 characters for analysis)
            if len(content) > 5000:
                content = content[:5000] + "... [content truncated]"
            
            # Require minimum 150 characters for a story (stories should be substantial)
            if not content or len(content) < 150:
                error_msg = f"Content too short ({len(content)} chars) - likely not a full story. Minimum 150 characters required."
                logger.warning(f"{error_msg} for URL: {url}")
                return json.dumps({
                    "error": error_msg,
                    "url": url,
                    "title": title or "Unknown",
                    "content_length": len(content) if content else 0
                }, ensure_ascii=False)
            
            result = {
                "url": url,
                "title": title or "Unknown",
                "content": content,
                "content_length": len(content),
                "status": "success"
            }
            
            logger.info(f"Successfully fetched content from {url}: {len(content)} characters")
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"Unexpected error processing content: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({
                "error": error_msg,
                "url": url,
                "status": "processing_error"
            }, ensure_ascii=False)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)  # Max 2 newlines in a row
        text = re.sub(r' {2,}', ' ', text)  # Max 1 space
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        
        return '\n'.join(lines).strip()

