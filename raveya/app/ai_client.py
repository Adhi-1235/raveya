import json
from typing import Any, Dict

from openai import OpenAI

from .config import get_settings


class AIClient:
    """
    Small abstraction over the LLM provider.

    Today this uses OpenAI's Chat Completions API, but callers should not rely on that.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not configured in environment")
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    def generate_json(
        self,
        *,
        system_prompt: str,
        user_payload: Dict[str, Any],
        json_schema_description: str,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Ask the model to return strictly valid JSON according to a textual schema description.
        Performs a couple of retries if JSON parsing fails.
        """
        base_user_message = (
            "You are given the following JSON-like payload from the application:\n\n"
            f"{json.dumps(user_payload, ensure_ascii=False, indent=2)}\n\n"
            "You must respond with **only** a JSON object that follows this schema:\n\n"
            f"{json_schema_description}\n\n"
            "Do not include markdown, comments, or any surrounding text. Only return raw JSON."
        )

        last_error = None
        for _ in range(max_retries + 1):
            completion = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": base_user_message},
                ],
            )
            content = completion.choices[0].message.content or ""
            try:
                # Trim potential markdown fences if present
                cleaned = content.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.strip("`")
                    if cleaned.startswith("json"):
                        cleaned = cleaned[len("json") :].strip()
                return json.loads(cleaned)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                # Retry with explicit correction instruction
                base_user_message = (
                    "You previously returned invalid JSON. "
                    "Return ONLY valid JSON this time. Do not explain.\n\n"
                    f"Original payload:\n{json.dumps(user_payload, ensure_ascii=False, indent=2)}\n\n"
                    f"Schema:\n{json_schema_description}"
                )

        raise ValueError(f"Model did not return valid JSON after retries: {last_error}")

