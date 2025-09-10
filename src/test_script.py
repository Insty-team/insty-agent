# test_connection.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from notion_client import Client

load_dotenv()
from notion_client import Client
import os

notion = Client(auth=os.getenv("NOTION_API_KEY"))

db = notion.databases.retrieve(database_id=os.getenv("NOTION_DB_ID"))
for k, v in db["properties"].items():
    print(k, "=>", v["id"], v["type"])
