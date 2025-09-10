# meeting_note.py
import os
import argparse
from datetime import date
from dotenv import load_dotenv
from src.notion_client_wrap import NotionClientWrap
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("insty")


def fetch_tasks_by_field(notion_token: str, database_id: str, field_name: str):
    """
    Notion DB에서 업무영역(field_name) 기준으로 task를 가져옴
    """
    notion = NotionClientWrap(notion_token)
    all_tasks = notion.query_database(database_id)
    filtered = [t for t in all_tasks if t.get("field") == field_name]
    return filtered


def generate_meeting_note(tasks: list):
    """
    tasks 리스트를 기반으로 회의록 초안을 Markdown으로 생성
    """
    today = date.today().isoformat()
    note_lines = [f"### {tasks[0]['field']} 팀 주간 회의록 초안 ({today})\n"]

    # 업데이트 된 업무
    updated_tasks = [t for t in tasks if t.get("진행률", 0) > 0]
    note_lines.append("####  업데이트 된 업무\n> \n")
    for t in updated_tasks:
        note_lines.append(f"- **{t.get('name')}**")
        note_lines.append(f"  - process: {t.get('process','')}")
        note_lines.append(f"  - priority: {t.get('priority','')}")
        note_lines.append(f"  - start: {t.get('start','')}")
        note_lines.append(f"  - end: {t.get('end','')}")
        note_lines.append(f"  - progress: {t.get('progress','')}")
        note_lines.append(f"  - 업데이트 사항:\n    - {t.get('description','')}\n")

    # 신규 업무 (진행률 0 혹은 새로운 task)
    new_tasks = [t for t in tasks if t.get("진행률", 0) == 0]
    if new_tasks:
        note_lines.append("---\n")
        note_lines.append("####  신규 업무\n> 이번 주 새로 생성된 업무 항목\n")
        for t in new_tasks:
            note_lines.append(f"- **{t.get('name','task a')}**")
            note_lines.append(f"  - process: {t.get('process','')}")
            note_lines.append(f"  - priority: {t.get('priority','')}")
            note_lines.append(f"  - start: {t.get('start','')}")
            note_lines.append(f"  - end: {t.get('end','')}")
            note_lines.append(f"  - progress: {t.get('progress','')}")
            note_lines.append(f"  - action:\n    - {t.get('description','')}\n")

    # 추가 논의 사항
    note_lines.append("#### 추가논의 사항\n")

    return "\n".join(note_lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", required=True, help="업무영역 (예: AI, 기획, 개발)")
    args = parser.parse_args()

    load_dotenv()
    notion_token = os.getenv("NOTION_API_KEY")
    database_id = os.getenv("NOTION_DB_ID")
    if not notion_token or not database_id:
        raise RuntimeError("NOTION_API_KEY, NOTION_DB_ID must be set in .env")

    tasks = fetch_tasks_by_field(notion_token, database_id, args.field)
    if not tasks:
        logger.warning(f"No tasks found for field '{args.field}'")
        return

    note_md = generate_meeting_note(tasks)
    output_file = f"meeting_note_{args.field}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(note_md)
    logger.info(f"Meeting note generated: {output_file}")


if __name__ == "__main__":
    main()
