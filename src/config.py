import os
import zoneinfo
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DB_ID = os.getenv("NOTION_DB_ID", "")

TZ_NAME = os.getenv("TIMEZONE", "Asia/Seoul")
try:
    TZ = zoneinfo.ZoneInfo(TZ_NAME)
except Exception:
    TZ = zoneinfo.ZoneInfo("Asia/Seoul")

def validate_env():
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not NOTION_API_KEY:
        missing.append("NOTION_API_KEY")
    if not NOTION_DB_ID:
        missing.append("NOTION_DB_ID")
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
