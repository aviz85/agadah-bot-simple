"""
Agadah WordPress Search Tool

Tool to search agadah.org.il WordPress site for stories.
Uses the existing REST API endpoint.
"""

import json
import logging
import os
from typing import Optional
from urllib.parse import quote, unquote, urlparse

import requests
from crewai.tools.base_tool import BaseTool

# Set up logging
logger = logging.getLogger(__name__)


class AgadahWordPressSearchTool(BaseTool):
    """
    Tool to search agadah.org.il WordPress site for Jewish stories.
    """
    
    name: str = "Agadah WordPress Search Tool"
    description: str = """Search for Jewish stories on agadah.org.il.
    
    Use this tool to find relevant stories based on:
    - Story titles
    - Topics and themes
    - Values (e.g., 'אמונה', 'אחדות', 'חברות')
    - Holidays (e.g., 'פסח', 'סוכות', 'ל"ג בעומר')
    
    Args:
        query: Search term in Hebrew (required). Examples: 'אחדות', 'ירושלים', 'רבי עקיבא'
        limit: Maximum number of results (default: 5, max: 20)
    
    Returns: List of stories with title, link, and excerpt.
    """
    
    def __init__(self, **kwargs):
        """Initialize the WordPress search tool."""
        super().__init__(**kwargs)
        base = os.getenv(
            "AGADAH_API_BASE",
            "https://agadah.org.il/wp-json/wp/v2"
        ).rstrip("/")
        
        if base.endswith("/pages"):
            base = base[:-len("/pages")]
        self._api_base = base
        
        # Search only in stories endpoint
        self._endpoint = "story"
        
        logger.info(
            "Initialized AgadahWordPressSearchTool with base %s (endpoint: %s)",
            self._api_base,
            self._endpoint,
        )
    
    def _run(self, query: str, limit: int = 5) -> str:
        """
        Search for stories on agadah.org.il.
        
        Args:
            query: Search term in Hebrew (required)
            limit: Maximum number of results (default: 5, max: 20)
        
        Returns:
            JSON string with search results
        """
        if not query or not query.strip():
            error_msg = "Search query cannot be empty"
            logger.warning(error_msg)
            return json.dumps({"error": error_msg}, ensure_ascii=False)
        
        # Limit results to reasonable amount
        limit = min(max(1, limit), 20)
        
        logger.info(f"Searching agadah.org.il stories with query: '{query}', limit: {limit}")
        
        try:
            url = (
                f"{self._api_base}/{self._endpoint}"
                f"?per_page={limit}&_fields=id,title,excerpt,link,date,categories,tags"
                f"&search={quote(query)}"
            )
            logger.debug("API URL: %s", url)
            
            response = self._perform_request(url)
            if response is None:
                return json.dumps({"error": "Failed to connect to agadah.org.il"}, ensure_ascii=False)
            
            try:
                results = response.json()
            except json.JSONDecodeError as e:
                logger.warning("Error parsing JSON response: %s", e)
                return json.dumps({"error": "Invalid response from server"}, ensure_ascii=False)
            
            formatted_results = []
            for item in results:
                try:
                    raw_link = item.get("link", "")
                    if not raw_link or not raw_link.strip():
                        logger.debug("Skipping item with empty link")
                        continue

                    # Validate and clean the URL
                    clean_link = self._validate_and_clean_url(raw_link)
                    if not clean_link:
                        logger.warning(f"Skipping item with invalid link: {raw_link}")
                        continue

                    excerpt_raw = item.get("excerpt", {}).get("rendered", "")
                    excerpt_clean = self._clean_html(excerpt_raw) if excerpt_raw else ""

                    result = {
                        "title": item.get("title", {}).get("rendered", ""),
                        "link": clean_link,
                        "excerpt": excerpt_clean,
                        "date": item.get("date", ""),
                        "_note": "Use the 'link' field exactly as provided - it has been validated and decoded",
                    }
                    formatted_results.append(result)
                except Exception as e:
                    logger.warning("Error formatting result item: %s", e)
                    continue
            
            logger.info(f"Found {len(formatted_results)} stories for query '{query}'")
            return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        
        except Exception as e:
            error_msg = f"Unexpected error searching: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return json.dumps({"error": error_msg}, ensure_ascii=False)

    def _perform_request(self, url: str) -> Optional[requests.Response]:
        """Perform HTTP GET with retries and return response or None on failure."""
        max_retries = 3
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Request timeout (attempt %s/%s), retrying in %ss...",
                        attempt + 1, max_retries, retry_delay,
                    )
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Request timed out after multiple retries")
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        "Request error (attempt %s/%s): %s, retrying...",
                        attempt + 1, max_retries, e,
                    )
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Error connecting to API: %s", e)
        return None
    
    def _clean_html(self, html_text: str) -> str:
        """Clean HTML tags and entities from text."""
        import re
        clean = re.sub(r'<[^>]+>', '', html_text)
        clean = re.sub(r'&[^;]+;', ' ', clean)
        clean = ' '.join(clean.split())
        if len(clean) > 500:
            clean = clean[:500] + "..."
        return clean.strip()

    def _validate_and_clean_url(self, url: str) -> Optional[str]:
        """
        Validate and clean URL from agadah.org.il.

        - Decodes URL-encoded characters
        - Validates domain is agadah.org.il
        - Ensures proper format
        - Verifies URL is accessible (returns 200)

        Args:
            url: Raw URL from WordPress API

        Returns:
            Cleaned URL or None if invalid
        """
        if not url or not url.strip():
            return None

        try:
            # Decode URL-encoded characters (like %d7%a2%d7%9c → Hebrew)
            decoded_url = unquote(url.strip())

            # Parse URL to validate
            parsed = urlparse(decoded_url)

            # Validate domain
            if not parsed.netloc or 'agadah.org.il' not in parsed.netloc:
                logger.warning(f"Invalid domain in URL: {url}")
                return None

            # Ensure HTTPS
            if parsed.scheme not in ['http', 'https']:
                logger.warning(f"Invalid scheme in URL: {url}")
                return None

            # Reconstruct clean URL
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            # Add query string if present
            if parsed.query:
                clean_url += f"?{parsed.query}"

            # CRITICAL: Verify URL is accessible (not a 404)
            try:
                head_response = requests.head(clean_url, timeout=3, allow_redirects=True)
                if head_response.status_code == 404:
                    logger.warning(f"URL returns 404 - story not found: {clean_url}")
                    return None
                elif head_response.status_code >= 400:
                    logger.warning(f"URL returns error {head_response.status_code}: {clean_url}")
                    return None

                logger.debug(f"URL validated (HTTP {head_response.status_code}): {clean_url}")
            except requests.RequestException as e:
                logger.warning(f"Cannot verify URL {clean_url}: {e}")
                # Return URL anyway - network issues shouldn't block valid URLs
                # But log it for debugging

            logger.debug(f"Cleaned URL: {url} -> {clean_url}")
            return clean_url

        except Exception as e:
            logger.warning(f"Error validating URL {url}: {e}")
            return None
