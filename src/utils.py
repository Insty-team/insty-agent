import re
from typing import Optional

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

UUID_RE = re.compile(r"[0-9a-fA-F]{32}|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

def extract_notion_page_id(text: str) -> str:
    """
    Notion URL/텍스트에서 페이지 ID 추출.
    - 32자리 hex 또는 UUID 형태 지원
    - URL 내 포함된 경우도 자동 추출
    """
    # notion의 canonical url 내 마지막 하이픈 이후 32hex가 오는 경우 처리

    m = re.search(r"([0-9a-fA-F]{32})(?![0-9a-fA-F])", text)
    if m:
        return m.group(1)

    # 일반 UUID 포맷도 시도
    m2 = UUID_RE.search(text)
    if m2:
        return m2.group(0).replace("-", "")

    raise ValueError("Failed to parse Notion page id from meetingnote.txt")
