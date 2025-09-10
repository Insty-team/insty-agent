from typing import List, Dict, Any
from dateutil import parser as dateparser
from datetime import datetime
from .config import TZ

VALID_AREA = {"개발","디자인","기획","마케팅","운영","기타","AI","BE","FE"}
VALID_STATUS = {"계획","진행중","완료","보류","취소"}
VALID_TYPE = {"신규개발","버그수정","개선","유지보수","분석","기타"}
VALID_PRIORITY = {"높음","보통","낮음"}

def _as_date_str(s: str, fallback: datetime) -> str:
    try:
        dt = dateparser.parse(s)
        return dt.date().isoformat()
    except Exception:
        return fallback.date().isoformat()

def _as_int_progress(v) -> int:
    # "69.3%" or "9/13" or number
    try:
        if isinstance(v, (int, float)):
            return max(0, min(100, int(round(float(v)))))
        s = str(v).strip()
        if "/" in s:
            a, b = s.split("/", 1)
            return max(0, min(100, int(round((float(a)/float(b))*100))))
        if s.endswith("%"):
            return max(0, min(100, int(round(float(s[:-1])))))
        return max(0, min(100, int(round(float(s)))))
    except Exception:
        return 0

def _coerce_select(value: str, valid: set, default: str) -> str:
    if value in valid:
        return value
    # 간단 매핑 (유사어)
    mapping = {
        "진행중입니다": "진행중",
        "planning": "계획",
        "done": "완료",
        "bugfix": "버그수정",
        "improve": "개선",
        "analysis": "분석",
        "high": "높음",
        "medium": "보통",
        "low": "낮음",
    }
    v = mapping.get(str(value).lower(), default)
    return v if v in valid else default

def normalize_tasks(tasks: List[Dict[str, Any]], meeting_date: datetime) -> List[Dict[str, Any]]:
    normed = []
    for t in tasks:
        name = str(t.get("name", "")).strip()
        if not name:
            continue

        area = _coerce_select(str(t.get("field", "기타")).strip(), VALID_AREA, "기타")
        status = _coerce_select(str(t.get("process", "계획")).strip(), VALID_STATUS, "계획")
        ftype = _coerce_select(str(t.get("function", "기타")).strip(), VALID_TYPE, "기타")
        priority = _coerce_select(str(t.get("priority", "보통")).strip(), VALID_PRIORITY, "보통")

        start_raw = t.get("start") or meeting_date.date().isoformat()
        due_raw = t.get("end") or meeting_date.date().isoformat()

        start = _as_date_str(str(start_raw), meeting_date)
        due = _as_date_str(str(due_raw), meeting_date)
        desc = str(t.get("description", "")).strip()
        progress = _as_int_progress(t.get("progress", 0))

        normed.append({
            "name": name,
            "field": area,
            "process": status,
            "function": ftype,
            "start": start,
            "end": due,
            "description": desc,
            "priority": priority,
            "progress": progress,
        })
    return normed
