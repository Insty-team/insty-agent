from datetime import datetime, timezone
import os

def build_user_prompt(meeting_text: str, meeting_date_str: str) -> str:
    """
    한국어 시스템 요구사항 기반 + Few-shot 3개 포함
    결과는 JSON 배열로만 출력하도록 유도 (extractor에서 파싱)
    """
    today = meeting_date_str
    return f"""
당신은 회의록에서 업무 항목을 추출하고 분석하는 전문가입니다.

# 역할
- 회의록 내용을 분석하여 구체적인 업무 항목들을 식별
- 누락된 정보는 문맥과 상식을 바탕으로 추론하여 보완
- 각 업무의 priority와 예상 일정을 합리적으로 판단

# 추출해야 할 정보 (출력 키)
1. name: 업무 제목 / 액션 가능한 구체적 업무명 
2. field: AI, BE, FE, 개발, 디자인, 기획, 마케팅, 운영, 기타 중 하나 (업무 성격에 따라 추론)
3. process: 계획 / 진행중 / 완료 / 보류 / 취소
4. function: 신규개발 / 버그수정 / 개선 / 유지보수 / 분석 / 기타
5. start: YYYY-MM-DD (없으면 회의 날짜)
6. end: YYYY-MM-DD (없으면 합리적 추정)
7. description: 업무 상세 설명
8. priority: 높음 / 보통 / 낮음 (없으면 마감기간 임박한 순으로 산정)
9. progress: 0-100 

# 추론 규칙
- field는 AI, BE, FE, 개발, 디자인, 기획, 마케팅, 운영, 기타 중 하나. 아니면 name에 업무 제목으로 넣어줘야함.
- 명시되지 않은 정보는 업무의 성격과 문맥을 고려하여 추론
- end이 없으면 업무 복잡도를 고려하여 합리적 기간 설정
- priority는 중요도+긴급성 고려
- start 기본값은 명시되지 않았으면 '{today}'

# 출력 규칙 (매우 중요)
- 반드시 **순수 JSON 배열**만 출력하세요.
- JSON 외의 텍스트, bullet point, 설명 문구는 절대 쓰지 마세요.
- 배열 바깥에 어떠한 주석, 설명, 서문도 쓰지 마세요.- 각 원소는 위 9개 키를 모두 포함.

# Few-shot 예시 (정답 JSON 일부)
[
  {{
    "name": "태그 알림 기능 마무리",
    "field": "개발",
    "process": "진행중",
    "end": "{today}",
    "priority": "높음",
    "function": "개선",
    "description": "태그 알림 기능 잔여 작업 마무리 및 QA.",
    "start": "{today}",
    "progress": 50
  }},
  {{
    "name": "네이버 클라우드 제안서 완성",
    "field": "기획",
    "process": "진행중",
    "end": "{today}",
    "priority": "보통",
    "function": "분석",
    "description": "스토리텔링 6개 완료, 정량 근거 7개 중 3개 작성. 마무리 및 컨택.",
    "start": "{today}",
    "progress": 69
  }},
  {{
    "name": "크리에이터 컨택 200명 진행",
    "field": "마케팅",
    "process": "진행중",
    "end": "{today}",
    "priority": "보통",
    "function": "운영",
    "description": "리스트업 200명, 메일 10명 발송, 커피챗 1건 예정. 목표 진척.",
    "start": "{today}",
    "progress": 25
  }}
]

# 실제 회의록
{meeting_text}
"""
