import json
import re

def parse_task_json(s: str):
    # 먼저 JSON 배열 탐색
    match = re.search(r"\[.*\]", s, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    # 배열이 없고, 개별 객체만 있는 경우
    objects = re.findall(r"\{[^{}]+\}", s, re.DOTALL)
    tasks = []
    for obj in objects:
        try:
            tasks.append(json.loads(obj))
        except Exception:
            continue

    if tasks:
        return tasks

    print(" JSON 추출 실패")
    return []
