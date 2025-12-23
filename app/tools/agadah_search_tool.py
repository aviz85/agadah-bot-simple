"""
Agadah WordPress Search Tool

Tool to search agadah.org.il WordPress site for stories.
Uses the existing REST API endpoint.
"""

import json
import logging
import os
from typing import Optional
from urllib.parse import quote

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
                    link = item.get("link", "")
                    if not link or not link.strip():
                        continue
                    
                    excerpt_raw = item.get("excerpt", {}).get("rendered", "")
                    excerpt_clean = self._clean_html(excerpt_raw) if excerpt_raw else ""
                    
                    result = {
                        "title": item.get("title", {}).get("rendered", ""),
                        "link": link.strip(),
                        "excerpt": excerpt_clean,
                        "date": item.get("date", ""),
                        "_note": "Use the 'link' field exactly as provided when fetching content",
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
