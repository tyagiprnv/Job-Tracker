"""DeepSeek API client for job email analysis."""

import json
from typing import Dict, Optional
import requests

from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_MODEL


class DeepSeekClient:
    """Client for DeepSeek API."""

    def __init__(self):
        """Initialize DeepSeek client."""
        self.api_key = DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = DEEPSEEK_MODEL or "deepseek-chat"

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
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at analyzing job application emails. Extract structured information accurately.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1,  # Low temperature for consistency
                },
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return json.loads(content)
            else:
                print(f"API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"Error calling DeepSeek API: {e}")
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
