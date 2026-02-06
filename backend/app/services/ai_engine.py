"""AI engine service for Anthropic Claude integration."""

import json
import logging
import re
from typing import Any, Optional

import anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)


class AIEngine:
    """Core AI service wrapping Anthropic Claude API calls."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the AI engine.

        Args:
            api_key: Anthropic API key. If not provided, uses settings.
        """
        settings = get_settings()
        self.client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self.model = settings.ai_model
        self.default_max_tokens = settings.ai_max_tokens
        self.default_temperature = settings.ai_temperature

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate a text response from Claude.

        Args:
            system_prompt: System prompt defining Claude's role
            user_message: User message to respond to
            context: Additional context to include in system prompt
            temperature: Generation temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        full_system = system_prompt
        if context:
            full_system = f"{system_prompt}\n\nADDITIONAL CONTEXT:\n{context}"

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.default_max_tokens,
                temperature=temperature if temperature is not None else self.default_temperature,
                system=full_system,
                messages=[{"role": "user", "content": user_message}],
            )

            return message.content[0].text

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in AI generation: {e}")
            raise

    async def generate_structured(
        self,
        system_prompt: str,
        user_message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> dict[str, Any]:
        """Generate a structured JSON response from Claude.

        The user_message should include JSON schema/format instructions.

        Args:
            system_prompt: System prompt defining Claude's role
            user_message: User message including JSON format instructions
            context: Additional context
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Parsed JSON response as dictionary
        """
        # Add JSON formatting instruction
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "Do not include any text before or after the JSON object. "
            "Do not use markdown code blocks."
        )

        response = await self.generate(
            system_prompt=system_prompt,
            user_message=user_message + json_instruction,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Parse JSON from Claude's response, handling common issues.

        Args:
            response: Raw response text

        Returns:
            Parsed JSON dictionary
        """
        # Try direct parsing first
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # If all else fails, return a default structure with the raw response
        logger.warning(f"Failed to parse JSON response: {response[:200]}...")
        return {
            "narrative": response,
            "choices": None,
            "mood": "neutral",
            "new_entities": [],
            "knowledge_updates": [],
            "xp_awarded": None,
            "_parse_error": True,
        }

    async def generate_with_retry(
        self,
        system_prompt: str,
        user_message: str,
        context: str = "",
        max_retries: int = 3,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate with automatic retry on transient failures.

        Args:
            system_prompt: System prompt
            user_message: User message
            context: Additional context
            max_retries: Maximum retry attempts
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Returns:
            Generated text
        """
        last_error = None

        for attempt in range(max_retries):
            try:
                return await self.generate(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    context=context,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except anthropic.RateLimitError as e:
                logger.warning(f"Rate limit hit, attempt {attempt + 1}/{max_retries}")
                last_error = e
                # In a real app, you'd implement exponential backoff here
                continue
            except anthropic.APIStatusError as e:
                if e.status_code >= 500:
                    logger.warning(f"Server error, attempt {attempt + 1}/{max_retries}")
                    last_error = e
                    continue
                raise

        raise last_error or Exception("Max retries exceeded")

    async def generate_streaming(
        self,
        system_prompt: str,
        user_message: str,
        context: str = "",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ):
        """Generate a streaming response.

        Args:
            system_prompt: System prompt
            user_message: User message
            context: Additional context
            temperature: Generation temperature
            max_tokens: Maximum tokens

        Yields:
            Text chunks as they are generated
        """
        full_system = system_prompt
        if context:
            full_system = f"{system_prompt}\n\nADDITIONAL CONTEXT:\n{context}"

        with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens or self.default_max_tokens,
            temperature=temperature if temperature is not None else self.default_temperature,
            system=full_system,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                yield text

    async def count_tokens(self, text: str) -> int:
        """Estimate token count for text.

        This is an approximation - Claude uses a similar tokenizer to GPT models.

        Args:
            text: Text to count tokens for

        Returns:
            Estimated token count
        """
        # Rough estimation: ~4 characters per token for English
        return len(text) // 4

    async def check_content_safety(self, content: str) -> dict[str, Any]:
        """Check if content is appropriate.

        Uses Claude to assess content safety.

        Args:
            content: Content to check

        Returns:
            Safety assessment result
        """
        system = """You are a content safety checker. Assess the following content for:
- Violence (1-5 scale)
- Adult content (1-5 scale)
- Harmful instructions (yes/no)
- Appropriate for general RPG (yes/no)

Respond with JSON only."""

        user = f"""Assess this content:

{content}

Respond with:
{{"violence": 1-5, "adult": 1-5, "harmful": true/false, "rpg_appropriate": true/false}}"""

        return await self.generate_structured(
            system_prompt=system,
            user_message=user,
            temperature=0.0,
        )


# Singleton instance
_ai_engine: Optional[AIEngine] = None


def get_ai_engine() -> AIEngine:
    """Get the AI engine singleton."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngine()
    return _ai_engine
