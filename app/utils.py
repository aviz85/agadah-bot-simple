"""
Utility functions for agadah-bot-simple
"""

import json
import logging
import re
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain additional content.

    Handles cases where LLM adds text before/after the JSON.

    Args:
        text: Raw text output from agent

    Returns:
        Parsed JSON dict or None if not found
    """
    if not text or not text.strip():
        logger.warning("Empty text provided to extract_json_from_text")
        return None

    # Try direct JSON parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object using regex
    # Look for { ... } pattern, handling nested objects
    json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    matches = re.finditer(json_pattern, text, re.DOTALL)

    for match in matches:
        try:
            json_str = match.group(0)
            parsed = json.loads(json_str)
            logger.info("Successfully extracted JSON from text using regex")
            return parsed
        except json.JSONDecodeError:
            continue

    logger.warning("Could not extract valid JSON from text")
    logger.debug(f"Text content: {text[:500]}")  # Log first 500 chars
    return None


def validate_story_url(url: str, strict: bool = True) -> bool:
    """
    Validate that a story URL is accessible and returns HTTP 200.

    Args:
        url: URL to validate
        strict: If True, only accept HTTP 200. If False, accept 2xx codes.

    Returns:
        True if URL is valid and accessible, False otherwise
    """
    if not url or not url.strip():
        logger.warning("Empty URL provided to validate_story_url")
        return False

    url = url.strip()

    # Check domain
    if "agadah.org.il" not in url:
        logger.warning(f"URL is not from agadah.org.il: {url}")
        return False

    # Check HTTP(S)
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"URL missing http/https scheme: {url}")
        return False

    # Try HEAD request to check accessibility
    try:
        response = requests.head(url, timeout=3, allow_redirects=False)

        if strict:
            # Only accept 200
            if response.status_code == 200:
                logger.debug(f"URL validated (HTTP 200): {url}")
                return True
            else:
                logger.warning(f"URL returned HTTP {response.status_code}, not 200: {url}")
                return False
        else:
            # Accept any 2xx
            if 200 <= response.status_code < 300:
                logger.debug(f"URL validated (HTTP {response.status_code}): {url}")
                return True
            else:
                logger.warning(f"URL returned HTTP {response.status_code}: {url}")
                return False

    except requests.RequestException as e:
        logger.warning(f"Failed to validate URL {url}: {e}")
        return False


def validate_story_urls_in_activity(activity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate all story URLs in activity report and log warnings for invalid ones.

    Args:
        activity_data: ActivityReport dict

    Returns:
        Same activity_data (validation is for logging only, doesn't modify)
    """
    if not activity_data:
        return activity_data

    # Check story_references list
    story_refs = activity_data.get("story_references", [])
    for idx, story in enumerate(story_refs):
        url = story.get("url", "")
        if url:
            is_valid = validate_story_url(url, strict=True)
            if not is_valid:
                logger.error(
                    f"⚠️⚠️⚠️ INVALID URL in story_references[{idx}]: {url}"
                )
                logger.error(
                    f"   Story title: {story.get('title', 'Unknown')}"
                )

    # Check sections for story_reference.url
    sections = activity_data.get("sections", [])
    for idx, section in enumerate(sections):
        story_ref = section.get("story_reference")
        if story_ref:
            url = story_ref.get("url", "")
            if url:
                is_valid = validate_story_url(url, strict=True)
                if not is_valid:
                    logger.error(
                        f"⚠️⚠️⚠️ INVALID URL in sections[{idx}].story_reference: {url}"
                    )
                    logger.error(
                        f"   Section: {section.get('section_name', 'Unknown')}"
                    )

    return activity_data
