import os
from typing import Dict, Any, List, Tuple
from notion_client import Client
from .logger import get_logger
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logger = get_logger("insty")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY must be set in .env")


class NotionClientWrap:
    def __init__(self, token: str):
        self.client = Client(auth=token)
        self.oai_client = OpenAI(api_key=api_key)


    def get_embedding(self, text: str) -> list[float]:
        if not text:
            return []
        resp = self.oai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return resp.data[0].embedding

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        a, b = np.array(a), np.array(b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


    def upsert_tasks(self, database_id: str, tasks: List[Dict[str, Any]]) -> Dict[str, int]:
        title_prop_name, name_to_id = self._get_db_schema(database_id)
        created, updated = 0, 0


        existing_pages = self.client.databases.query(database_id=database_id).get("results", [])
        existing_tasks = []
        for page in existing_pages:
            props = page["properties"]
            title_val = props[title_prop_name]["title"][0]["plain_text"] if props[title_prop_name]["title"] else ""
            embedding = self.get_embedding(title_val)
            existing_tasks.append({
                "page_id": page["id"],
                "name": title_val,
                "embedding": embedding
            })

        for task in tasks:
            try:
                normalized_name = task.get("name")
                if not normalized_name:
                    logger.warning("Skip a task without 'name'")
                    continue

                #  신규 task name 임베딩
                new_emb = self.get_embedding(normalized_name)

                #  가장 유사한 기존 task 찾기
                best_match, best_score = None, 0
                for et in existing_tasks:
                    if not et["embedding"]:
                        continue
                    sim = self.cosine_similarity(new_emb, et["embedding"])
                    if sim > best_score:
                        best_match, best_score = et, sim

                #기준치 이상 업데이트 아니면 신규 생성
                if best_match and best_score >= 0.9:
                    props = self._build_properties(name_to_id, task)
                    self.client.pages.update(page_id=best_match["page_id"], properties=props)
                    updated += 1
                    logger.info(f"Updated (similarity={best_score:.2f}): {normalized_name} ≈ {best_match['name']}")
                else:
                    props = self._build_properties(name_to_id, task)
                    self.client.pages.create(parent={"database_id": database_id}, properties=props)
                    created += 1
                    logger.info(f"Created new task: {normalized_name}")

            except Exception as e:
                logger.error(f"Failed upsert '{task.get('name', '(no-name)')}': {e}")

        return {"created": created, "updated": updated}


    def fetch_page_plain_text(self, page_id: str) -> str:
        """
        페이지 블록을 순회하면서 텍스트 추출
        """
        texts = []
        def walk(block_id: str):
            children = self.client.blocks.children.list(block_id).get("results", [])
            for b in children:
                t = self._block_to_text(b)
                if t:
                    texts.append(t)
                if b.get("has_children"):
                    walk(b["id"])

        # page_id는 블록 API에 그대로 사용 가능
        walk(page_id)
        return "\n".join(texts)

    def _block_to_text(self, block: Dict[str, Any]) -> str:
        t = block.get("type")
        data = block.get(t, {})
        rich = data.get("rich_text", [])
        text = "".join([rt["plain_text"] for rt in rich if "plain_text" in rt])
        if t in ("heading_1", "heading_2", "heading_3"):
            return f"# {text}"
        return text

    # ---------- DB 업서트 ----------
    def _get_db_schema(self, database_id: str) -> Tuple[str, Dict[str, str]]:
        """
        returns: (title_property_name_for_filter, name->id map)
        - Notion filter에는 'property'에 이름 문자열을 써야 함
        """
        db = self.client.databases.retrieve(database_id=database_id)
        props = db["properties"]
        name_to_id = {k: v["id"] for k, v in props.items()}

        # title property 이름 찾기
        title_prop_name = None
        for k, v in props.items():
            if v["type"] == "title":
                title_prop_name = k
                break
        if not title_prop_name:
            raise RuntimeError("No title property found in database")

        return title_prop_name, name_to_id

    def _build_properties(self, name_to_id: Dict[str, str], task: Dict[str, Any]) -> Dict[str, Any]:
        pid = name_to_id

        def safe_select(key: str, default: str = "기타"):
            return {"select": {"name": task.get(key, default)}}

        def safe_date(key: str):
            val = task.get(key)
            return {"date": {"start": val}} if val else {"date": None}

        return {
            pid["name"]: {"title": [{"text": {"content": task.get("name", "Untitled")}}]},
            pid["field"]: safe_select("field"),
            pid["process"]: safe_select("process", "계획"),
            pid["function"]: safe_select("function", "기타"),
            pid["start"]: safe_date("start"),
            pid["end"]: safe_date("end"),
            pid["description"]: {
                "rich_text": [{"text": {"content": (task.get("description") or "")[:2000]}}]
            },
            pid["priority"]: safe_select("priority", "보통"),
            pid["progress"]: {"number": int(task.get("progress", 0))},
        }

    def _find_existing_page(self, database_id: str, title_property_name: str, task_name: str):
        """
        같은 제목(name)이 이미 있는지 검색 (정확 일치해야만,,)
        """
        q = self.client.databases.query(
            database_id=database_id,
            filter={
                "property": title_property_name,
                "title": {"equals": task_name}
            },
            page_size=1
        )
        results = q.get("results", [])
        return results[0]["id"] if results else None
