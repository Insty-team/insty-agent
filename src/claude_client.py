import os
import backoff
from typing import List, Dict, Any
from anthropic import Anthropic, APIStatusError
from .prompt_builder import build_user_prompt
from .extractor import parse_task_json
from .logger import get_logger
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")

SYSTEM_PROMPT = "You extract actionable tasks from meeting notes and respond ONLY with JSON."

logger = get_logger("insty")


class ClaudeClient:
    def __init__(self, api_key: str = ANTHROPIC_API_KEY):
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY must be set in .env")
        self.client = Anthropic(api_key=api_key)

    @backoff.on_exception(backoff.expo, (APIStatusError, TimeoutError), max_time=90)
    def extract_tasks(self, meeting_text: str, meeting_date_str: str) -> List[Dict[str, Any]]:
        user_prompt = build_user_prompt(meeting_text, meeting_date_str)
        resp = self.client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            temperature=0.2,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(part.text for part in resp.content if hasattr(part, "text"))
        # 🔹 여기서 로그 찍기
        logger.info(f"Claude raw response:\n{text[:2000]}")  # 앞 2000자만
        from .extractor import parse_task_json
        tasks = parse_task_json(text)

        logger.info(f"Extracted {len(tasks)} tasks from Claude response")
        return parse_task_json(text)
