"""
Simple LLM configuration - OpenRouter only.
"""
import os
from langchain_openai import ChatOpenAI
import logging

logger = logging.getLogger(__name__)


def get_llm():
    """
    Get OpenRouter LLM instance configured for CrewAI.

    Returns:
        ChatOpenAI configured for OpenRouter with CrewAI compatibility

    Raises:
        ValueError: If OPENROUTER_API_KEY is not set
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY environment variable is required. "
            "Please set it in your .env file."
        )

    # Use openai/gpt-4o-mini for OpenRouter (avoids Anthropic native provider detection)
    model = os.getenv("MODEL", "openai/gpt-4o-mini")

    logger.info(f"Initializing LLM with model: {model} via OpenRouter")

    return ChatOpenAI(
        model=model,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0.7,
        max_tokens=4000,
        model_kwargs={
            "headers": {
                "HTTP-Referer": "https://agadah.org.il",
                "X-Title": "Agadah Bot"
            }
        }
    )
