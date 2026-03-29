import json
import re
import pandas as pd
from google import genai
from config import Config       # ← get GEMINI_MODEL from Config


class GeminiClient:

    def __init__(self, client, model=Config.GEMINI_MODEL):  # ← use Config
        self._client = client
        self._model = model

    def ask(self, system_prompt: str, user_message: str) -> str:
        full_prompt = f"{system_prompt}\n\n---\n\n{user_message}"
        response = self._client.models.generate_content(
            model=self._model,
            contents=full_prompt,
        )
        return response.text

    def ask_json(self, system_prompt: str, user_message: str):
        raw = self.ask(system_prompt, user_message)
        cleaned = re.sub(r"```json\s*", "", raw)
        cleaned = re.sub(r"```\s*", "", cleaned).strip()
        return json.loads(cleaned)
