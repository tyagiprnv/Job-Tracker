"""LLM client supporting multiple providers via LiteLLM."""

import json
import os
from typing import Dict, Optional
import litellm

from config.settings import (
    LLM_PROVIDER,
    LLM_MODEL,
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    GOOGLE_API_KEY,
    DEEPSEEK_API_KEY,
)


class LLMClient:
    """Client for LLM analysis supporting multiple providers."""

    def __init__(self):
        """Initialize LLM client."""
        self.provider = LLM_PROVIDER
        self.model = LLM_MODEL

        # Set API key in environment for LiteLLM
        self._configure_api_key()

        # Configure LiteLLM settings
        litellm.drop_params = True  # Drop unsupported params gracefully
        litellm.set_verbose = False  # Disable debug logging

        # Provider-specific JSON mode configuration
        self.json_mode_config = self._get_json_mode_config()

    def _configure_api_key(self):
        """Configure API key for LiteLLM based on provider."""
        key_map = {
            "openai": ("OPENAI_API_KEY", OPENAI_API_KEY),
            "anthropic": ("ANTHROPIC_API_KEY", ANTHROPIC_API_KEY),
            "google": ("GOOGLE_API_KEY", GOOGLE_API_KEY),
            "deepseek": ("DEEPSEEK_API_KEY", DEEPSEEK_API_KEY),
        }

        if self.provider in key_map:
            env_var, key_value = key_map[self.provider]
            os.environ[env_var] = key_value

    def _get_json_mode_config(self) -> dict:
        """Get JSON mode configuration for provider.

        Returns:
            dict: Provider-specific JSON mode parameters
        """
        # LiteLLM automatically handles JSON mode for different providers
        # We use response_format for OpenAI/DeepSeek/Google
        # For Anthropic (no native JSON mode), we rely on prompt engineering
        if self.provider in ["openai", "deepseek", "google"]:
            return {"response_format": {"type": "json_object"}}
        else:
            # Anthropic - no JSON mode, rely on prompt
            return {}

    def analyze_email(
        self, subject: str, body: str, sender: str
    ) -> Optional[Dict]:
        """Analyze email using LLM.

        Args:
            subject: Email subject
            body: Email body (truncated to 2000 chars)
            sender: Sender email address

        Returns:
            dict: Parsed JSON response or None if error
        """
        # Truncate body to avoid token limits
        body_sample = body[:2000]

        prompt = self._build_prompt(subject, body_sample, sender)

        try:
            # Build messages
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing job application emails. Extract structured information accurately. Always respond with valid JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            # Call LiteLLM with provider-specific config
            response = litellm.completion(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistency
                timeout=30,
                **self.json_mode_config
            )

            # Extract content from response
            content = response.choices[0].message.content

            # Parse JSON
            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            if 'content' in locals():
                print(f"Response content: {content[:200]}...")
            return None
        except Exception as e:
            print(f"Error calling {self.provider.upper()} API: {e}")
            return None

    def _build_prompt(self, subject: str, body: str, sender: str) -> str:
        """Build analysis prompt.

        Args:
            subject: Email subject
            body: Email body sample
            sender: Sender email address

        Returns:
            str: Formatted prompt
        """
        from llm.prompts import EMAIL_ANALYSIS_PROMPT

        return EMAIL_ANALYSIS_PROMPT.format(
            subject=subject, body=body, sender=sender
        )
