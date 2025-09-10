import os
import re
import argparse
from datetime import datetime
from dotenv import load_dotenv

from src.logger import get_logger
from src.utils import read_file, extract_notion_page_id
from src.claude_client import ClaudeClient
from src.notion_client_wrap import NotionClientWrap

logger = get_logger("insty")

def extract_page_ids_from_text(file_path: str) -> list[str]:

    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()


    raw_ids = re.findall(r'([0-9a-f]{32})', text)
    if not raw_ids:
        raise ValueError("meeting.txt에서 유효한 Notion ID를 찾지 못했습니다.")


    page_ids = [
        f"{raw_id[0:8]}-{raw_id[8:12]}-{raw_id[12:16]}-{raw_id[16:20]}-{raw_id[20:]}"
        for raw_id in raw_ids
    ]

    logger.info(f"Parsed Notion page ids: {page_ids}")
    return page_ids


def run_pipeline(meetingnote_path: str):
    load_dotenv()

    notion_token = os.getenv("NOTION_API_KEY")
    notion_db_id = os.getenv("NOTION_DB_ID")
    if not notion_token or not notion_db_id:
        raise RuntimeError("NOTION_API_KEY, NOTION_DB_ID must be set in .env")

    page_ids = extract_page_ids_from_text(meetingnote_path)

    # # 1) meetingnote.txt에서 노션 페이지 ID 파싱
    # raw = read_file(meetingnote_path)
    # page_id = extract_notion_page_id(raw)
    # logger.info(f"Parsed Notion page id: {page_id}")

    # 2) 노션 페이지의 순수 텍스트 수집
    notion = NotionClientWrap(notion_token)
    claude = ClaudeClient()
    for page_id in page_ids:
        logger.info(f"Processing Notion page: {page_id}")
        try:

            meeting_text = notion.fetch_page_plain_text(page_id)
            logger.info(f"Fetched meeting text length: {len(meeting_text)}")

            # 3) Claude로 업무 항목 추출
            meeting_date_str = datetime.now().strftime("%Y-%m-%d")

            tasks = claude.extract_tasks(meeting_text, meeting_date_str)
            logger.info(f"Extracted tasks: {len(tasks)}")

            if not tasks:
                logger.warning("No tasks extracted. Stop.")
                return

    # 4) Notion DB 업서트 (있으면 update, 없으면 create)
            upserted = notion.upsert_tasks(notion_db_id, tasks)
            logger.info(f"Upsert complete. created={upserted['created']} updated={upserted['updated']}")
        except Exception as e:
            logger.error(f"Error processing page {page_id}: {e}")
def main():
    parser = argparse.ArgumentParser(description="Meeting notes → Claude → Notion DB upsert pipeline")
    parser.add_argument("meetingnote_txt", type=str, help="Path to meetingnote.txt")
    args = parser.parse_args()

    run_pipeline(args.meetingnote_txt)

if __name__ == "__main__":
    main()
