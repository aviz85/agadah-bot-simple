"""
Simple LLM configuration - OpenRouter with LiteLLM support.
"""
import os
from crewai.llm import LLM
import logging

logger = logging.getLogger(__name__)


def get_llm():
    """
    Get OpenRouter LLM instance configured for CrewAI.

    Uses CrewAI's LLM class with is_litellm=True to force LiteLLM routing.
    This allows using Claude, Gemini, and other models via OpenRouter
    without requiring native provider API keys.

    Returns:
        CrewAI LLM configured for OpenRouter with LiteLLM

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is required. "
            "Please set it in your .env file."
        )

    # Model from env - format: openrouter/provider/model
    # This prefix prevents CrewAI from using native providers
    model = os.getenv("MODEL", "openrouter/anthropic/claude-opus-4.5")

    logger.info(f"Initializing LLM with model: {model} via OpenRouter (LiteLLM)")

    # When model starts with "openrouter/", CrewAI will use LiteLLM automatically
    return LLM(
        model=model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=4000
    )
