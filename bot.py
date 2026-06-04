"""
KOKAHOUSE â AI Telegram Bot
ÐÐ¾Ñ Ð´Ð»Ñ Ð¾Ð±ÑÐµÐ½Ð¸Ñ Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°Ð¼Ð¸. Claude AI + Notion CRM.

ÐÐ°Ð²Ð¸ÑÐ¸Ð¼Ð¾ÑÑÐ¸: pip install python-telegram-bot anthropic python-dotenv httpx
"""

import os
import logging
import json
import base64
import httpx
import random
from datetime import datetime
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import anthropic
# notion_client ÑÐ´Ð°Ð»ÑÐ½ â Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÐ¼ ÑÐ¾Ð»ÑÐºÐ¾ amoCRM

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ââ ÐÐ¾Ð½ÑÐ¸Ð³ âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
TG_TOKEN        = os.getenv("TG_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
# notion_client ÑÐ´Ð°Ð»ÑÐ½ â Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÐ¼ ÑÐ¾Ð»ÑÐºÐ¾ amoCRM

MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")
CHANNEL_ID      = os.getenv("CHANNEL_ID", "@kokahouse")  # ÐºÐ°Ð½Ð°Ð» Ð´Ð»Ñ Ð¿Ð¾ÑÑÐ¸Ð½Ð³Ð°

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ââ Ð¡Ð¸ÑÑÐµÐ¼Ð½ÑÐ¹ Ð¿ÑÐ¾Ð¼Ð¿Ñ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# ââ ÐÐ°Ð·Ð° Ð·Ð½Ð°Ð½Ð¸Ð¹ (ÑÑÐ°Ð½Ð¸ÑÑÑ Ð² GitHub â Ð¿Ð¾ÑÑÐ¾ÑÐ½Ð½Ð¾) âââââââââââââââââââââââââââââââ
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO   = "yaninve7-commits/altacasa-bot"
KNOWLEDGE_FILE = "custom_knowledge.txt"
_knowledge_cache: str = ""
_knowledge_loaded: bool = False


def github_get_file(path: str):
    """ÐÐ¾Ð»ÑÑÐ¸ÑÑ ÑÐ¾Ð´ÐµÑÐ¶Ð¸Ð¼Ð¾Ðµ ÑÐ°Ð¹Ð»Ð° Ð¸Ð· GitHub. ÐÐµÑÐ½ÑÑÑ (content, sha)."""
    import urllib.request as _req, base64 as _b64
    if not GITHUB_TOKEN:
        return "", ""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    req = _req.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with _req.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return _b64.b64decode(data["content"]).decode("utf-8"), data["sha"]
    except Exception:
        return "", ""


def github_save_file(path: str, content: str, message: str = "Update"):
    """Ð¡Ð¾ÑÑÐ°Ð½Ð¸ÑÑ ÑÐ°Ð¹Ð» Ð² GitHub Ð°Ð²ÑÐ¾Ð¼Ð°ÑÐ¸ÑÐµÑÐºÐ¸."""
    import urllib.request as _req, base64 as _b64
    if not GITHUB_TOKEN:
        return False
    _, sha = github_get_file(path)
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    payload: dict = {
        "message": message,
        "content": _b64.b64encode(content.encode()).decode(),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    req = _req.Request(url, data=json.dumps(payload).encode(), headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }, method="PUT")
    try:
        with _req.urlopen(req, timeout=15) as r:
            logger.info(f"GitHub saved {path}: {r.status}")
            return r.status in [200, 201]
    except Exception as e:
        logger.error(f"GitHub save error: {e}")
        return False


def load_knowledge() -> str:
    """ÐÐ°Ð³ÑÑÐ·Ð¸ÑÑ Ð±Ð°Ð·Ñ Ð·Ð½Ð°Ð½Ð¸Ð¹ Ð¸Ð· GitHub (Ð¿Ð¾ÑÑÐ¾ÑÐ½Ð½Ð¾Ðµ ÑÑÐ°Ð½Ð¸Ð»Ð¸ÑÐµ)."""
    global _knowledge_cache, _knowledge_loaded
    if _knowledge_loaded:
        return _knowledge_cache
    try:
        content, _ = github_get_file(KNOWLEDGE_FILE)
        if content and content.strip():
            _knowledge_cache = (
                f"\n\nâââââââââââââââââââââââââââââââ\n"
                f"ÐÐÐÐÐÐÐÐ¢ÐÐÐ¬ÐÐ«Ð ÐÐÐÐÐÐ¯ (Ð´Ð¾Ð±Ð°Ð²Ð»ÐµÐ½Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐµÐ¼)\n"
                f"âââââââââââââââââââââââââââââââ\n{content.strip()}"
            )
            logger.info(f"ÐÐ°Ð·Ð° Ð·Ð½Ð°Ð½Ð¸Ð¹ Ð·Ð°Ð³ÑÑÐ¶ÐµÐ½Ð° Ð¸Ð· GitHub ({len(content)} ÑÐ¸Ð¼Ð²Ð¾Ð»Ð¾Ð²)")
        elif os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                local = f.read().strip()
            if local:
                _knowledge_cache = f"\n\nâââââââââââââââââââââââââââââââ\nÐÐÐÐÐÐÐÐ¢ÐÐÐ¬ÐÐ«Ð ÐÐÐÐÐÐ¯\nâââââââââââââââââââââââââââââââ\n{local}"
        _knowledge_loaded = True
    except Exception as e:
        logger.error(f"Knowledge load error: {e}")
    return _knowledge_cache


def save_knowledge(entry: str):
    """Ð¡Ð¾ÑÑÐ°Ð½Ð¸ÑÑ Ð·Ð½Ð°Ð½Ð¸Ðµ â Ð»Ð¾ÐºÐ°Ð»ÑÐ½Ð¾ + Ð°Ð²ÑÐ¾Ð¼Ð°ÑÐ¸ÑÐµÑÐºÐ¸ Ð² GitHub."""
    global _knowledge_loaded
    try:
        current, _ = github_get_file(KNOWLEDGE_FILE)
        new_content = (current.strip() + f"\n{entry}").strip()
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        ok = github_save_file(KNOWLEDGE_FILE, new_content, f"Knowledge: {entry[:60]}")
        if ok:
            logger.info(f"ÐÐ½Ð°Ð½Ð¸Ðµ ÑÐ¾ÑÑÐ°Ð½ÐµÐ½Ð¾ Ð² GitHub: {entry[:60]}")
        _knowledge_loaded = False
    except Exception as e:
        logger.error(f"Knowledge save error: {e}")

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()


# ââ Director Mode â AI-Ð´Ð¸ÑÐµÐºÑÐ¾Ñ Ð´Ð»Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° ââââââââââââââââââââââââââââââââ

DIRECTOR_SYSTEM = """Ð¢Ñ â Ð¿ÐµÑÑÐ¾Ð½Ð°Ð»ÑÐ½ÑÐ¹ AI-Ð´Ð¸ÑÐµÐºÑÐ¾Ñ ÐºÐ¾Ð¼Ð¿Ð°Ð½Ð¸Ð¸ KOKAHOUSE.
Ð¢Ñ ÑÐ°Ð·Ð³Ð¾Ð²Ð°ÑÐ¸Ð²Ð°ÐµÑÑ Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐµÐ¼ Ð±Ð¸Ð·Ð½ÐµÑÐ°. ÐÑÐ²ÐµÑÐ°Ð¹ ÐºÐ¾ÑÐ¾ÑÐºÐ¾, Ð¿Ð¾ Ð´ÐµÐ»Ñ, ÐºÐ°Ðº Ð¾Ð¿ÑÑÐ½ÑÐ¹ COO.
ÐÑÐ¿Ð¾Ð»ÑÐ·ÑÐ¹ Ð´Ð°Ð½Ð½ÑÐµ ÐºÐ¾ÑÐ¾ÑÑÐµ Ð¿Ð¾Ð»ÑÑÐ°ÐµÑÑ ÑÐµÑÐµÐ· Ð¸Ð½ÑÑÑÑÐ¼ÐµÐ½ÑÑ.
ÐÑÐµÐ³Ð´Ð° Ð´Ð°Ð²Ð°Ð¹ ÐºÐ¾Ð½ÐºÑÐµÑÐ½ÑÐµ ÑÐ¸ÑÑÑ Ð¸ ÑÐ°ÐºÑÑ, Ð½Ðµ Ð¾Ð±ÑÐ¸Ðµ ÑÐ»Ð¾Ð²Ð°.
ÐÑÐ»Ð¸ Ð½ÑÐ¶Ð½Ð¾ â Ð¿ÑÐµÐ´Ð»Ð°Ð³Ð°Ð¹ Ð´ÐµÐ¹ÑÑÐ²Ð¸Ñ: Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ ÐºÐ»Ð¸ÐµÐ½ÑÑ, ÑÐ¾Ð·Ð´Ð°ÑÑ Ð¿Ð¾ÑÑ, Ð¾ÑÐ¿ÑÐ°Ð²Ð¸ÑÑ ÐÐ.
ÐÑÐ²ÐµÑÐ°Ð¹ Ð½Ð° ÑÑÑÑÐºÐ¾Ð¼.

ÐÐÐÐÐ â ÐµÑÐ»Ð¸ ÑÑ Ð½Ðµ Ð¼Ð¾Ð¶ÐµÑÑ Ð²ÑÐ¿Ð¾Ð»Ð½Ð¸ÑÑ Ð·Ð°Ð¿ÑÐ¾Ñ Ð¿Ð¾ ÑÐµÑÐ½Ð¸ÑÐµÑÐºÐ¸Ð¼ Ð¿ÑÐ¸ÑÐ¸Ð½Ð°Ð¼ (Ð½ÐµÑ Ð½ÑÐ¶Ð½Ð¾Ð³Ð¾ Ð¸Ð½ÑÑÑÑÐ¼ÐµÐ½ÑÐ°, ÑÑÐ½ÐºÑÐ¸Ñ Ð½Ðµ ÑÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½Ð°, Ð´Ð°Ð½Ð½ÑÐµ Ð½ÐµÐ´Ð¾ÑÑÑÐ¿Ð½Ñ):
1. ÐÐ¾ÑÐ¾ÑÐºÐ¾ Ð¾Ð±ÑÑÑÐ½Ð¸ ÑÑÐ¾ Ð¸Ð¼ÐµÐ½Ð½Ð¾ Ð½Ðµ ÑÐ°Ð±Ð¾ÑÐ°ÐµÑ
2. Ð¡ÑÐ°Ð·Ñ Ð¿Ð¾ÑÐ»Ðµ ÑÑÐ¾Ð³Ð¾ Ð´Ð¾Ð±Ð°Ð²Ñ Ð±Ð»Ð¾Ðº Ñ Ð³Ð¾ÑÐ¾Ð²ÑÐ¼ Ð¿ÑÐ¾Ð¼ÑÐ¾Ð¼ Ð´Ð»Ñ ÑÐ°Ð·ÑÐ°Ð±Ð¾ÑÑÐ¸ÐºÐ° Ð² ÑÐ¾ÑÐ¼Ð°ÑÐµ:

---
ð ÐÐÐÐÐ§Ð ÐÐÐ¯ Ð ÐÐÐ ÐÐÐÐ¢Ð§ÐÐÐ:
[Ð§ÑÑÐºÐ¾Ðµ Ð¾Ð¿Ð¸ÑÐ°Ð½Ð¸Ðµ ÑÑÐ¾ Ð½ÑÐ¶Ð½Ð¾ ÑÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°ÑÑ, ÐºÐ°ÐºÐ¸Ðµ Ð´Ð°Ð½Ð½ÑÐµ Ð¿Ð¾Ð»ÑÑÐ°ÑÑ, Ð¾ÑÐºÑÐ´Ð° (Notion/amoCRM/Telegram), ÐºÐ°Ðº Ð¾ÑÐ¾Ð±ÑÐ°Ð¶Ð°ÑÑ ÑÐµÐ·ÑÐ»ÑÑÐ°Ñ. ÐÐ°ÐºÑÐ¸Ð¼Ð°Ð»ÑÐ½Ð¾ ÐºÐ¾Ð½ÐºÑÐµÑÐ½Ð¾, ÐºÐ°Ðº ÑÐµÑÐ½Ð¸ÑÐµÑÐºÐ¾Ðµ Ð·Ð°Ð´Ð°Ð½Ð¸Ðµ.]
---

ÐÑÐ¸Ð¼ÐµÑ: ÐµÑÐ»Ð¸ Ð¿Ð¾Ð»ÑÐ·Ð¾Ð²Ð°ÑÐµÐ»Ñ Ð¿ÑÐ¾ÑÐ¸Ñ "Ð¿Ð¾ÐºÐ°Ð¶Ð¸ ÑÑÐ°ÑÐ¸ÑÑÐ¸ÐºÑ Ð¿ÑÐ¾Ð´Ð°Ð¶ Ð¿Ð¾ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÐ°Ð¼" Ð° Ñ ÑÐµÐ±Ñ Ð½ÐµÑ ÑÐ°ÐºÐ¾Ð³Ð¾ Ð¸Ð½ÑÑÑÑÐ¼ÐµÐ½ÑÐ° â Ð¾Ð±ÑÑÑÐ½Ð¸ ÑÑÐ¾ Ð¸ Ð½Ð°Ð¿Ð¸ÑÐ¸ Ð³Ð¾ÑÐ¾Ð²ÑÐ¹ Ð¿ÑÐ¾Ð¼Ñ Ð´Ð»Ñ ÑÐ°Ð·ÑÐ°Ð±Ð¾ÑÑÐ¸ÐºÐ° ÑÑÐ¾Ð±Ñ Ð¾Ð½ Ð´Ð¾Ð±Ð°Ð²Ð¸Ð» Ð½ÑÐ¶Ð½ÑÑ ÑÑÐ½ÐºÑÐ¸Ñ."""

DIRECTOR_TOOLS = [
    {
        "name": "get_stats",
        "description": "ÐÐ¾Ð»ÑÑÐ¸ÑÑ ÑÑÐ°ÑÐ¸ÑÑÐ¸ÐºÑ Ð»Ð¸Ð´Ð¾Ð² Ð·Ð° Ð¿ÐµÑÐ¸Ð¾Ð´: ÐºÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾, ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ, Ð±ÑÐ´Ð¶ÐµÑÑ, ÐºÐ°Ð½Ð°Ð»Ñ",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "ÐÐ° ÑÐºÐ¾Ð»ÑÐºÐ¾ Ð´Ð½ÐµÐ¹ (Ð½Ð°Ð¿ÑÐ¸Ð¼ÐµÑ 1, 2, 7, 30, 90)"}
            },
            "required": ["days"]
        }
    },
    {
        "name": "find_client",
        "description": "ÐÐ°Ð¹ÑÐ¸ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸, username Ð¸Ð»Ð¸ Telegram ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "ÐÐ¼Ñ, username Ð¸Ð»Ð¸ ID ÐºÐ»Ð¸ÐµÐ½ÑÐ°"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_leads",
        "description": "ÐÐ¾Ð»ÑÑÐ¸ÑÑ ÑÐ¿Ð¸ÑÐ¾Ðº Ð»Ð¸Ð´Ð¾Ð² Ð¿Ð¾ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ð¸",
        "input_schema": {
            "type": "object",
            "properties": {
                "qualification": {
                    "type": "string",
                    "enum": ["ÐÐ¾ÑÑÑÐ¸Ð¹", "Ð¢ÑÐ¿Ð»ÑÐ¹", "Ð¥Ð¾Ð»Ð¾Ð´Ð½ÑÐ¹", "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ", "Ð²ÑÐµ"],
                    "description": "Ð¤Ð¸Ð»ÑÑÑ Ð¿Ð¾ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ð¸"
                },
                "limit": {"type": "integer", "description": "Ð¡ÐºÐ¾Ð»ÑÐºÐ¾ Ð·Ð°Ð¿Ð¸ÑÐµÐ¹ (Ð¼Ð°ÐºÑ 20)"}
            },
            "required": ["qualification"]
        }
    },
    {
        "name": "send_to_client",
        "description": "ÐÑÐ¿ÑÐ°Ð²Ð¸ÑÑ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ ÐºÐ»Ð¸ÐµÐ½ÑÑ: ÑÐµÐºÑÑ, ÑÐ¾ÑÐ¾, ÑÑÑÐ»ÐºÐ¸, ÐºÐ½Ð¾Ð¿ÐºÐ¸",
        "input_schema": {
            "type": "object",
            "properties": {
                "tg_id": {"type": "integer", "description": "Telegram ID ÐºÐ»Ð¸ÐµÐ½ÑÐ°"},
                "text": {"type": "string", "description": "Ð¢ÐµÐºÑÑ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ñ"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ð¡Ð¿Ð¸ÑÐ¾Ðº URL ÑÐ¾ÑÐ¾Ð³ÑÐ°ÑÐ¸Ð¹ ÑÐ¾Ð²Ð°ÑÐ° (Ð´Ð¾ 10 ÑÑÑÐº)"
                },
                "buttons": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "url": {"type": "string"}
                        }
                    },
                    "description": "Inline-ÐºÐ½Ð¾Ð¿ÐºÐ¸: [{text: 'ÐÐ¾Ð´ÑÐ¾Ð±Ð½ÐµÐµ', url: 'https://...'}, ...]"
                }
            },
            "required": ["tg_id", "text"]
        }
    },
    {
        "name": "get_channel_info",
        "description": "ÐÐ¾Ð»ÑÑÐ¸ÑÑ Ð¸Ð½ÑÐ¾ÑÐ¼Ð°ÑÐ¸Ñ Ð¾ ÐºÐ°Ð½Ð°Ð»Ðµ: Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÐ¸ÐºÐ¸, Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ Ð¿Ð¾ÑÑÑ",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reply_to_lead",
        "description": "ÐÐ°Ð¹ÑÐ¸ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸/username Ð¸ Ð¾ÑÐ¿ÑÐ°Ð²Ð¸ÑÑ ÐµÐ¼Ñ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ Ð¾Ñ Ð®Ð»Ð¸. ÐÑÐ¿Ð¾Ð»ÑÐ·ÑÐ¹ ÐºÐ¾Ð³Ð´Ð° Ð²Ð»Ð°Ð´ÐµÐ»ÐµÑ ÑÐ¾ÑÐµÑ Ð¾ÑÐ²ÐµÑÐ¸ÑÑ ÐºÐ»Ð¸ÐµÐ½ÑÑ Ð¸Ð»Ð¸ Ð·Ð°Ð´Ð°ÑÑ ÑÑÐ¾ÑÐ½ÑÑÑÐ¸Ð¹ Ð²Ð¾Ð¿ÑÐ¾Ñ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "ÐÐ¼Ñ Ð¸Ð»Ð¸ username ÐºÐ»Ð¸ÐµÐ½ÑÐ° (Ð¸Ð· ÑÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ñ)"},
                "message": {"type": "string", "description": "Ð§ÑÐ¾ Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ ÐºÐ»Ð¸ÐµÐ½ÑÑ Ð¾Ñ Ð®Ð»Ð¸"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Ð¤Ð¾ÑÐ¾ ÑÐ¾Ð²Ð°ÑÐ¾Ð² Ð´Ð»Ñ Ð¾ÑÐ¿ÑÐ°Ð²ÐºÐ¸ (Ð¾Ð¿ÑÐ¸Ð¾Ð½Ð°Ð»ÑÐ½Ð¾)"
                },
                "buttons": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"text": {"type": "string"}, "url": {"type": "string"}}},
                    "description": "ÐÐ½Ð¾Ð¿ÐºÐ¸-ÑÑÑÐ»ÐºÐ¸ (Ð¾Ð¿ÑÐ¸Ð¾Ð½Ð°Ð»ÑÐ½Ð¾)"
                }
            },
            "required": ["client_name", "message"]
        }
    },
    {
        "name": "update_deal",
        "description": "ÐÐ±Ð½Ð¾Ð²Ð¸ÑÑ ÑÐ´ÐµÐ»ÐºÑ Ð² amoCRM: Ð¸Ð·Ð¼ÐµÐ½Ð¸ÑÑ ÑÑÐ°ÑÑÑ, ÑÑÐ¼Ð¼Ñ, Ð´Ð¾Ð±Ð°Ð²Ð¸ÑÑ Ð¿ÑÐ¸Ð¼ÐµÑÐ°Ð½Ð¸Ðµ",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "ID ÑÐ´ÐµÐ»ÐºÐ¸ Ð² amoCRM"},
                "status": {
                    "type": "string",
                    "enum": ["Ð½Ð¾Ð²Ð°Ñ", "Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÑ", "ÐºÐ¿_Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾", "ÑÐ¾Ð³Ð»Ð°ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ", "ÑÑÐ¿ÐµÑÐ½Ð¾", "Ð¾ÑÐºÐ°Ð·"],
                    "description": "ÐÐ¾Ð²ÑÐ¹ ÑÑÐ°ÑÑÑ ÑÐ´ÐµÐ»ÐºÐ¸"
                },
                "price": {"type": "integer", "description": "ÐÐ¾Ð²Ð°Ñ ÑÑÐ¼Ð¼Ð° ÑÐ´ÐµÐ»ÐºÐ¸ Ð² ÑÑÐ±Ð»ÑÑ"},
                "note": {"type": "string", "description": "ÐÑÐ¸Ð¼ÐµÑÐ°Ð½Ð¸Ðµ Ðº ÑÐ´ÐµÐ»ÐºÐµ"}
            },
            "required": ["deal_id"]
        }
    },
    {
        "name": "create_deal",
        "description": "Ð¡Ð¾Ð·Ð´Ð°ÑÑ Ð½Ð¾Ð²ÑÑ ÑÐ´ÐµÐ»ÐºÑ Ð² amoCRM Ð¸Ð· Telegram-Ð»Ð¸Ð´Ð°",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "ÐÐ°Ð·Ð²Ð°Ð½Ð¸Ðµ ÑÐ´ÐµÐ»ÐºÐ¸"},
                "client_name": {"type": "string", "description": "ÐÐ¼Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°"},
                "price": {"type": "integer", "description": "Ð¡ÑÐ¼Ð¼Ð° ÑÐ´ÐµÐ»ÐºÐ¸ Ð² ÑÑÐ±Ð»ÑÑ"},
                "note": {"type": "string", "description": "ÐÐ¿Ð¸ÑÐ°Ð½Ð¸Ðµ / Ð¿ÐµÑÐ²Ð¾Ðµ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ ÐºÐ»Ð¸ÐµÐ½ÑÐ°"}
            },
            "required": ["name", "client_name"]
        }
    },
    {
        "name": "search_deals",
        "description": "ÐÐ°Ð¹ÑÐ¸ ÑÐ´ÐµÐ»ÐºÐ¸ Ð² amoCRM Ð¿Ð¾ Ð½Ð°Ð·Ð²Ð°Ð½Ð¸Ñ Ð¸Ð»Ð¸ ÐºÐ»Ð¸ÐµÐ½ÑÑ",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "ÐÐ¾Ð¸ÑÐºÐ¾Ð²ÑÐ¹ Ð·Ð°Ð¿ÑÐ¾Ñ (Ð¸Ð¼Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð¸Ð»Ð¸ Ð½Ð°Ð·Ð²Ð°Ð½Ð¸Ðµ ÑÐ´ÐµÐ»ÐºÐ¸)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_revenue_stats",
        "description": "ÐÐ¾Ð»ÑÑÐ¸ÑÑ ÑÑÐ°ÑÐ¸ÑÑÐ¸ÐºÑ Ð²ÑÑÑÑÐºÐ¸ Ð¸ ÑÐ´ÐµÐ»Ð¾Ðº: ÑÑÐ¼Ð¼Ñ, ÐºÐ¾Ð»Ð¸ÑÐµÑÑÐ²Ð¾, ÑÑÐµÐ´Ð½Ð¸Ð¹ ÑÐµÐº, Ð¿Ð¾ ÑÑÐ°Ð´Ð¸ÑÐ¼ Ð¸ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÐ°Ð¼. Ð¡ÑÐ°Ð²Ð½ÐµÐ½Ð¸Ðµ Ñ Ð¿ÑÐµÐ´ÑÐ´ÑÑÐ¸Ð¼ Ð¿ÐµÑÐ¸Ð¾Ð´Ð¾Ð¼.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "ÐÐµÑÐ¸Ð¾Ð´ Ð² Ð´Ð½ÑÑ (1, 7, 30, 90)"},
                "group_by": {
                    "type": "string",
                    "enum": ["Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑ", "ÑÑÐ°Ð´Ð¸Ñ", "Ð¸ÑÐ¾Ð³Ð¾"],
                    "description": "ÐÑÑÐ¿Ð¿Ð¸ÑÐ¾Ð²ÐºÐ° ÑÐµÐ·ÑÐ»ÑÑÐ°ÑÐ¾Ð²"
                }
            },
            "required": ["days"]
        }
    }
]


def director_get_stats(days: int) -> dict:
    """Ð¡ÑÐ°ÑÐ¸ÑÑÐ¸ÐºÐ° Ð»Ð¸Ð´Ð¾Ð² Ð·Ð° Ð¿ÐµÑÐ¸Ð¾Ð´ â Ð¸Ð· amoCRM Ñ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸ÑÐ¼Ð¸."""
    leads = amo_get_leads(days, limit=250)

    QUAL_MAP = {
        86187794: "Ð¥Ð¾Ð»Ð¾Ð´Ð½ÑÐ¹",
        86187798: "Ð¥Ð¾Ð»Ð¾Ð´Ð½ÑÐ¹",
        86187802: "Ð¢ÑÐ¿Ð»ÑÐ¹",
        86187806: "Ð¢ÑÐ¿Ð»ÑÐ¹",
        86187810: "ÐÐ¾ÑÑÑÐ¸Ð¹",
        86187814: "ÐÐ¾ÑÑÑÐ¸Ð¹",
        86187818: "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ",
        86187822: "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ",
        142: "Ð£ÑÐ¿ÐµÑÐ½Ð¾",
        143: "ÐÑÐºÐ°Ð·",
    }

    stats = {
        "total": len(leads),
        "by_qual": {},
        "total_budget": 0,
        "hot": [],
        "source": "amoCRM",
        "period_days": days
    }

    for l in leads:
        status_id = l.get("status_id", 0)
        qual = QUAL_MAP.get(status_id, "ÐÐµÐ¸Ð·Ð²ÐµÑÑÐ½Ð¾")
        price = l.get("price") or 0

        if qual not in stats["by_qual"]:
            stats["by_qual"][qual] = {"count": 0, "budget": 0}
        stats["by_qual"][qual]["count"] += 1
        stats["by_qual"][qual]["budget"] += price
        stats["total_budget"] += price

        if qual in ("ÐÐ¾ÑÑÑÐ¸Ð¹", "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ"):
            contacts = (l.get("_embedded") or {}).get("contacts", [])
            client = contacts[0].get("name", "â") if contacts else "â"
            stats["hot"].append({
                "name": client,
                "budget": price,
                "lead_id": l.get("id"),
                "qual": qual
            })

    return stats
def director_find_client(query: str) -> list:
    """ÐÐ°Ð¹ÑÐ¸ ÐºÐ»Ð¸ÐµÐ½ÑÐ°."""
    results = []
    # ÐÐ¾Ð¸ÑÐº Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸
    try:
        r = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "Name", "title": {"contains": query}}
        )
        results.extend(r.get("results", []))
    except Exception:
        pass
    # ÐÐ¾Ð¸ÑÐº Ð¿Ð¾ TG ID ÐµÑÐ»Ð¸ ÑÐ¸ÑÐ»Ð¾
    if query.lstrip("-").isdigit():
        try:
            r = notion.databases.query(
                database_id=NOTION_DB_ID,
                filter={"property": "Telegram ID", "number": {"equals": int(query)}}
            )
            results.extend(r.get("results", []))
        except Exception:
            pass
    clients = []
    for p in results[:5]:
        props = p.get("properties", {})
        name_arr = props.get("Name", {}).get("title", [])
        name = name_arr[0]["plain_text"] if name_arr else "â"
        qual = (props.get("ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ", {}).get("select") or {}).get("name", "â")
        interest = (props.get("ÐÐ½ÑÐµÑÐµÑ", {}).get("select") or {}).get("name", "â")
        budget = props.get("ÐÑÐ´Ð¶ÐµÑ â½", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        tg_url = props.get("Telegram", {}).get("url", "â")
        dialog = (props.get("ÐÐ¸Ð°Ð»Ð¾Ð³ Ñ Ð±Ð¾ÑÐ¾Ð¼", {}).get("rich_text") or [{}])
        dialog_text = dialog[0].get("plain_text", "")[-300:] if dialog else ""
        clients.append({
            "name": name, "qual": qual, "interest": interest,
            "budget": budget, "tg_id": tg_id, "tg_url": tg_url,
            "dialog_preview": dialog_text
        })
    return clients


DEALS_DB_ID = "36e698e7193a8092b378eeb45a969b84"  # ÐÐ¾ÑÐ¾Ð½ÐºÐ° ÑÐ´ÐµÐ»Ð¾Ðº (Notion)
AMO_TOKEN   = os.getenv("AMO_LONG_TOKEN", "")
AMO_DOMAIN  = "yaninve7.amocrm.ru"
AMO_API     = "yaninve7.amocrm.ru"   # Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÐ¼ subdomain â Ð¾Ð½ Ð¿ÑÐ¸Ð½Ð¸Ð¼Ð°ÐµÑ ÑÐ¾ÐºÐµÐ½


def amo_get_leads(days: int, limit: int = 250) -> list:
    """ÐÐ¾Ð»ÑÑÐ¸ÑÑ ÑÐ´ÐµÐ»ÐºÐ¸ Ð¸Ð· amoCRM Ð·Ð° Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ N Ð´Ð½ÐµÐ¹."""
    import time
    if not AMO_TOKEN:
        return []
    since_ts = int(time.time()) - days * 86400
    headers = {"Authorization": f"Bearer {AMO_TOKEN}"}
    url = f"https://{AMO_DOMAIN}/api/v4/leads"
    params = {
        "limit": limit,
        "filter[created_at][from]": since_ts,
        "with": "contacts,loss_reason",
        "order[created_at]": "desc"
    }
    try:
        import urllib.request, urllib.parse
        full_url = url + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("_embedded", {}).get("leads", [])
    except Exception as e:
        logger.error(f"amoCRM API error: {e}")
        return []


# ââ amoCRM CRM Sync âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
# ÐÐµÑ: tg_id â {"contact_id": int, "lead_id": int}
_amo_client_cache: dict[int, dict] = {}
# ÐÐ»Ð¸ÐµÐ½ÑÑ Ð¿Ð¾ ÐºÐ¾ÑÐ¾ÑÑÐ¼ ÑÐ¶Ðµ Ð±ÑÐ»Ð¾ ÑÑÐºÐ°Ð»Ð°ÑÐ¸Ð¾Ð½Ð½Ð¾Ðµ ÑÐ²ÐµÐ´Ð¾Ð¼Ð»ÐµÐ½Ð¸Ðµ
_escalated_clients: set = set()
# ÐÐµÑÑÐ¸ÑÑÐµÐ½ÑÐ½ÑÐ¹ Ð¼Ð°Ð¿Ð¿Ð¸Ð½Ð³ tg_id â amo_contact_id (Ð·Ð°ÑÐ¸ÑÐ° Ð¾Ñ Ð´ÑÐ±Ð»ÐµÐ¹ Ð¿ÑÐ¸ ÑÐµÑÑÐ°ÑÑÐµ)
AMO_MAP_FILE = "amo_id_map.json"

def _load_amo_map() -> dict:
    """ÐÐ°Ð³ÑÑÐ·Ð¸ÑÑ Ð¼Ð°Ð¿Ð¿Ð¸Ð½Ð³ tg_id â {contact_id, lead_id} Ð¸Ð· ÑÐ°Ð¹Ð»Ð°."""
    if os.path.exists(AMO_MAP_FILE):
        try:
            with open(AMO_MAP_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def _save_amo_map(tg_id: int, contact_id: int, lead_id: int):
    """Ð¡Ð¾ÑÑÐ°Ð½Ð¸ÑÑ Ð¼Ð°Ð¿Ð¿Ð¸Ð½Ð³ Ð¿ÐµÑÑÐ¸ÑÑÐµÐ½ÑÐ½Ð¾."""
    data = _load_amo_map()
    data[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
    try:
        with open(AMO_MAP_FILE, "w") as f:
            json.dump({str(k): v for k, v in data.items()}, f)
    except Exception as e:
        logger.error(f"amo_map save error: {e}")

# ÐÐ°Ð³ÑÑÐ¶Ð°ÐµÐ¼ Ð¼Ð°Ð¿Ð¿Ð¸Ð½Ð³ Ð¿ÑÐ¸ ÑÑÐ°ÑÑÐµ
_amo_client_cache = _load_amo_map()

# ÐÐ°Ð¿Ð¿Ð¸Ð½Ð³ ÑÑÐ°ÑÑÑÐ¾Ð² â ID Ð² Ð²Ð¾ÑÐ¾Ð½ÐºÐµ amoCRM (ÑÑÐ°Ð½Ð´Ð°ÑÑÐ½ÑÐµ)
AMO_STATUS_MAP = {
        "Ð½Ð¾Ð²ÑÐ¹_Ð»Ð¸Ð´":     86187794,  # ÐÐ¾Ð²ÑÐ¹ Ð»Ð¸Ð´
            "ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ":  86187798,  # ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ
                "Ð¿Ð¾Ð´Ð±Ð¾Ñ":        86187802,  # ÐÐ¾Ð´Ð±Ð¾Ñ ÑÐ¾Ð²Ð°ÑÐ°
                    "ÐºÐ¿_Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾": 86187806,  # ÐÐ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾
                        "Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÑ":    86187810,  # ÐÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÑ
                            "Ð¾Ð¶Ð¸Ð´Ð°Ð½Ð¸Ðµ":      86187814,  # ÐÐ¶Ð¸Ð´Ð°Ð½Ð¸Ðµ Ð¾Ð¿Ð»Ð°ÑÑ
                                "Ð¾Ð¿Ð»Ð°ÑÐµÐ½Ð¾":      86187818,  # ÐÐ¿Ð»Ð°ÑÐµÐ½Ð¾
                                    "Ð´Ð¾ÑÑÐ°Ð²ÐºÐ°":      86187822,  # ÐÐ¾ÑÑÐ°Ð²ÐºÐ°
                                        "ÑÑÐ¿ÐµÑÐ½Ð¾":       142,       # Ð£ÑÐ¿ÐµÑÐ½Ð¾ ÑÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½Ð¾ (system)
                                            "Ð¾ÑÐºÐ°Ð·":         143,       # ÐÐ°ÐºÑÑÑÐ¾ Ð¸ Ð½Ðµ ÑÐµÐ°Ð»Ð¸Ð·Ð¾Ð²Ð°Ð½Ð¾ (system)
                                            }
AMO_WON_STATUS  = 142  # Won (Ð¿Ð¾Ð±ÐµÐ´Ð°)
AMO_LOST_STATUS = 143  # Lost (Ð¾ÑÐºÐ°Ð·)


def amo_request(method: str, path: str, data: dict = None) -> dict:
    """Ð£Ð½Ð¸Ð²ÐµÑÑÐ°Ð»ÑÐ½ÑÐ¹ Ð·Ð°Ð¿ÑÐ¾Ñ Ðº amoCRM API."""
    import urllib.request, urllib.error
    if not AMO_TOKEN:
        logger.error("amoCRM: AMO_LONG_TOKEN Ð½Ðµ Ð½Ð°ÑÑÑÐ¾ÐµÐ½")
        return {"error": "AMO_LONG_TOKEN Ð½Ðµ Ð½Ð°ÑÑÑÐ¾ÐµÐ½"}
    # ÐÑÐ¿Ð¾Ð»ÑÐ·ÑÐµÐ¼ ÑÐµÐ°Ð»ÑÐ½ÑÐ¹ API Ð´Ð¾Ð¼ÐµÐ½ (Ð½Ðµ subdomain ÐºÐ¾ÑÐ¾ÑÑÐ¹ Ð´ÐµÐ»Ð°ÐµÑ ÑÐµÐ´Ð¸ÑÐµÐºÑ)
    url = f"https://{AMO_API}/api/v4/{path}"
    headers = {
        "Authorization": f"Bearer {AMO_TOKEN}",
        "Content-Type": "application/json"
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            logger.info(f"amoCRM {method} {path} â {r.status}")
            return json.loads(raw) if raw else {"status": "ok"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        logger.error(f"amoCRM HTTP {e.code} {method} {path}: {err_body}")
        return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        logger.error(f"amoCRM error {method} {path}: {e}")
        return {"error": str(e)}


def amo_get_pipeline_statuses() -> dict:
    """ÐÐ¾Ð»ÑÑÐ¸ÑÑ ID ÑÑÐ°ÑÑÑÐ¾Ð² Ð¸Ð· Ð¿ÐµÑÐ²Ð¾Ð¹ Ð²Ð¾ÑÐ¾Ð½ÐºÐ¸."""
    r = amo_request("GET", "leads/pipelines")
    pipelines = r.get("_embedded", {}).get("pipelines", [])
    if not pipelines:
        return {}
    statuses = {}
    for s in pipelines[0].get("_embedded", {}).get("statuses", []):
        statuses[s["name"].lower()] = s["id"]
    return {"pipeline_id": pipelines[0]["id"], "statuses": statuses}


def director_update_deal(deal_id: int, status: str = None, price: int = None, note: str = None) -> dict:
    """ÐÐ±Ð½Ð¾Ð²Ð¸ÑÑ ÑÐ´ÐµÐ»ÐºÑ Ð² amoCRM."""
    payload = {}

    if status:
        # ÐÐ¾Ð»ÑÑÐ°ÐµÐ¼ ÑÐµÐ°Ð»ÑÐ½ÑÐµ ID ÑÑÐ°ÑÑÑÐ¾Ð²
        pipe_info = amo_get_pipeline_statuses()
        statuses = pipe_info.get("statuses", {})
        # ÐÑÐµÐ¼ Ð½ÑÐ¶Ð½ÑÐ¹ ÑÑÐ°ÑÑÑ
        status_id = None
        status_map = {
            "Ð½Ð¾Ð²Ð°Ñ": ["Ð¿ÐµÑÐ²Ð¸ÑÐ½ÑÐ¹", "Ð½Ð¾Ð²Ð°Ñ", "new"],
            "Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÑ": ["Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾Ñ", "discuss"],
            "ÐºÐ¿_Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾": ["ÐºÐ¿", "Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ", "Ð¿ÑÐ¸Ð½Ð¸Ð¼Ð°ÑÑ"],
            "ÑÐ¾Ð³Ð»Ð°ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ": ["ÑÐ¾Ð³Ð»Ð°ÑÐ¾Ð²Ð°Ð½", "decision"],
            "ÑÑÐ¿ÐµÑÐ½Ð¾": ["ÑÑÐ¿ÐµÑÐ½Ð¾", "won", "Ð·Ð°ÐºÑÑÑ"],
            "Ð¾ÑÐºÐ°Ð·": ["Ð¾ÑÐºÐ°Ð·", "lost", "Ð¿ÑÐ¾Ð²Ð°Ð»"]
        }
        for key, keywords in status_map.items():
            if status == key:
                for sname, sid in statuses.items():
                    if any(kw in sname for kw in keywords):
                        status_id = sid
                        break
        if status_id:
            payload["status_id"] = status_id
        if pipe_info.get("pipeline_id"):
            payload["pipeline_id"] = pipe_info["pipeline_id"]

    if price is not None:
        payload["price"] = price

    result = amo_request("PATCH", f"leads/{deal_id}", [{"id": deal_id, **payload}])

    # ÐÐ¾Ð±Ð°Ð²Ð»ÑÐµÐ¼ Ð¿ÑÐ¸Ð¼ÐµÑÐ°Ð½Ð¸Ðµ
    if note:
        amo_request("POST", "notes", [{"entity_id": deal_id, "note_type": "common", "params": {"text": note}, "entity_type": "leads"}])

    return {"deal_id": deal_id, "updated": payload, "result": result}


def director_create_deal(name: str, client_name: str, price: int = 0, note: str = "") -> dict:
    """Ð¡Ð¾Ð·Ð´Ð°ÑÑ Ð½Ð¾Ð²ÑÑ ÑÐ´ÐµÐ»ÐºÑ Ð² amoCRM."""
    pipe_info = amo_get_pipeline_statuses()

    deal_data = [{
        "name": name,
        "price": price,
        "_embedded": {
            "contacts": [{"name": client_name}]
        }
    }]
    if pipe_info.get("pipeline_id"):
        deal_data[0]["pipeline_id"] = pipe_info["pipeline_id"]

    result = amo_request("POST", "leads/complex", deal_data)
    leads = result if isinstance(result, list) else result.get("_embedded", {}).get("leads", [])
    if note and leads:
            deal_id = leads[0]["id"]
            amo_request("POST", "notes", [{"entity_id": deal_id, "note_type": "common", "params": {"text": note}, "entity_type": "leads"}])

    return result


def director_search_deals(query: str) -> list:
    """ÐÐ°Ð¹ÑÐ¸ ÑÐ´ÐµÐ»ÐºÐ¸ Ð¿Ð¾ Ð·Ð°Ð¿ÑÐ¾ÑÑ."""
    r = amo_request("GET", f"leads?query={query}&limit=10&with=contacts")
    leads = r.get("_embedded", {}).get("leads", [])
    result = []
    for l in leads:
        contacts = l.get("_embedded", {}).get("contacts", [])
        client = contacts[0].get("name", "â") if contacts else "â"
        result.append({
            "id": l.get("id"),
            "name": l.get("name"),
            "price": l.get("price"),
            "status_id": l.get("status_id"),
            "client": client,
            "created_at": l.get("created_at")
        })
    return result


def amo_get_or_create_contact(tg_id: int, name: str, tg_username: str = "") -> int:
    """ÐÐ°Ð¹ÑÐ¸ Ð¸Ð»Ð¸ ÑÐ¾Ð·Ð´Ð°ÑÑ ÐºÐ¾Ð½ÑÐ°ÐºÑ Ð² amoCRM. ÐÐµÑÐ½ÑÑÑ contact_id."""
    import urllib.parse as _urlparse
    if not AMO_TOKEN:
        return 0

    # 1. ÐÑÐµÐ¼ Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸ â Ñ Ð¿ÑÐ°Ð²Ð¸Ð»ÑÐ½ÑÐ¼ URL-encode
    params = _urlparse.urlencode({"query": name, "limit": 5})
    r = amo_request("GET", f"contacts?{params}")
    contacts = r.get("_embedded", {}).get("contacts", [])
    for c in contacts:
        if c.get("name") == name:
            return c["id"]

    # 2. Ð¢Ð°ÐºÐ¶Ðµ Ð¸ÑÐµÐ¼ Ð¿Ð¾ tg_id ÐµÑÐ»Ð¸ ÐµÑÑÑ
    if not contacts and tg_username:
        params2 = _urlparse.urlencode({"query": tg_username, "limit": 3})
        r2 = amo_request("GET", f"contacts?{params2}")
        for c in r2.get("_embedded", {}).get("contacts", []):
            if c.get("name") == name:
                return c["id"]

    # 3. Ð¡Ð¾Ð·Ð´Ð°ÑÐ¼ Ð½Ð¾Ð²Ð¾Ð³Ð¾ â ÑÐ¾Ð»ÑÐºÐ¾ ÑÑÐ°Ð½Ð´Ð°ÑÑÐ½ÑÐµ Ð¿Ð¾Ð»Ñ Ð±ÐµÐ· ÐºÐ°ÑÑÐ¾Ð¼Ð½ÑÑ field_code
    note_text = f"Telegram ID: {tg_id}"
    if tg_username:
        note_text += f"\n@{tg_username}"

    data = [{"name": name}]  # Ð¼Ð¸Ð½Ð¸Ð¼Ð°Ð»ÑÐ½ÑÐ¹ payload Ð±ÐµÐ· ÐºÐ°ÑÑÐ¾Ð¼Ð½ÑÑ Ð¿Ð¾Ð»ÐµÐ¹
    r = amo_request("POST", "contacts", data)
    new_contacts = r.get("_embedded", {}).get("contacts", [])
    if not new_contacts:
        logger.error(f"amoCRM: Ð½Ðµ ÑÐ´Ð°Ð»Ð¾ÑÑ ÑÐ¾Ð·Ð´Ð°ÑÑ ÐºÐ¾Ð½ÑÐ°ÐºÑ Ð´Ð»Ñ {name}: {r}")
        return 0
    contact_id = new_contacts[0]["id"]

    # 4. ÐÐ¾Ð±Ð°Ð²Ð»ÑÐµÐ¼ Telegram Ð´Ð°Ð½Ð½ÑÐµ ÐºÐ°Ðº Ð¿ÑÐ¸Ð¼ÐµÑÐ°Ð½Ð¸Ðµ (Ð½Ð°Ð´ÑÐ¶Ð½ÐµÐµ ÑÐµÐ¼ ÐºÐ°ÑÑÐ¾Ð¼Ð½ÑÐµ Ð¿Ð¾Ð»Ñ)
    amo_request("POST", "contacts/notes", [{
        "entity_id": contact_id,
        "note_type": "common",
        "params": {"text": note_text}
    }])
    logger.info(f"amoCRM: ÑÐ¾Ð·Ð´Ð°Ð½ ÐºÐ¾Ð½ÑÐ°ÐºÑ {name} (id={contact_id})")
    return contact_id


def amo_get_or_create_lead(tg_id: int, contact_id: int, name: str) -> int:
    """ÐÐ°Ð¹ÑÐ¸ Ð°ÐºÑÐ¸Ð²Ð½ÑÑ ÑÐ´ÐµÐ»ÐºÑ ÐºÐ¾Ð½ÑÐ°ÐºÑÐ° Ð¸Ð»Ð¸ ÑÐ¾Ð·Ð´Ð°ÑÑ Ð½Ð¾Ð²ÑÑ. ÐÐµÑÐ½ÑÑÑ lead_id."""
    if not AMO_TOKEN or not contact_id:
        return 0
    # ÐÑÐµÐ¼ ÑÐ´ÐµÐ»ÐºÐ¸ ÐºÐ¾Ð½ÑÐ°ÐºÑÐ°
    r = amo_request("GET", f"leads?filter[contact_id]={contact_id}&limit=5")
    leads = r.get("_embedded", {}).get("leads", [])
    # ÐÐµÑÑÐ¼ Ð¿Ð¾ÑÐ»ÐµÐ´Ð½ÑÑ Ð½ÐµÐ·Ð°ÐºÑÑÑÑÑ
    for l in leads:
        if l.get("status_id") not in [142, 143]:  # Ð½Ðµ Won/Lost
            return l["id"]
    # Ð¡Ð¾Ð·Ð´Ð°ÑÐ¼ Ð½Ð¾Ð²ÑÑ
    pipe_info = amo_get_pipeline_statuses()
    data = [{
        "name": f"ÐÐ°Ð¿ÑÐ¾Ñ Ð¾Ñ {name}",
        "price": 0,
        "_embedded": {"contacts": [{"id": contact_id}]}
    }]
    if pipe_info.get("pipeline_id"):
        data[0]["pipeline_id"] = pipe_info["pipeline_id"]
    r = amo_request("POST", "leads/complex", data)
    leads = r.get("_embedded", {}).get("leads", [])
    return leads[0]["id"] if leads else 0


def amo_add_note(lead_id: int, text: str, note_type: str = "common"):
    """ÐÐ¾Ð±Ð°Ð²Ð¸ÑÑ ÐºÐ¾Ð¼Ð¼ÐµÐ½ÑÐ°ÑÐ¸Ð¹ Ðº ÑÐ´ÐµÐ»ÐºÐµ."""
    if not AMO_TOKEN or not lead_id:
        return
    amo_request("POST", "leads/notes", [{
        "entity_id": lead_id,
        "note_type": note_type,
        "params": {"text": text[:1000]}
    }])


def amo_move_pipeline(lead_id: int, qualification: str, interest: str = None, budget: int = None):
    """ÐÐ²Ð¸Ð½ÑÑÑ ÑÐ´ÐµÐ»ÐºÑ Ð¿Ð¾ Ð²Ð¾ÑÐ¾Ð½ÐºÐµ Ð½Ð° Ð¾ÑÐ½Ð¾Ð²Ðµ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ð¸."""
    if not AMO_TOKEN or not lead_id:
        return
    pipe_info = amo_get_pipeline_statuses()
    statuses = pipe_info.get("statuses", {})
    pipeline_id = pipe_info.get("pipeline_id")

    # ÐÐ°ÑÐ¾Ð´Ð¸Ð¼ Ð½ÑÐ¶Ð½ÑÐ¹ ÑÑÐ°ÑÑÑ Ð¿Ð¾ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ð¸
    target_status = None
    if qualification == "ÐÐ¾ÑÑÑÐ¸Ð¹":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾Ñ", "ÐºÐ¿", "Ð¿ÑÐ¸Ð½Ð¸Ð¼Ð°ÑÑ", "discuss"]):
                target_status = sid
                break
    elif qualification == "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["ÐºÐ¿", "Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾", "Ð¾Ð¶Ð¸Ð´Ð°Ð½"]):
                target_status = sid
                break

    payload: dict = {}
    if target_status:
        payload["status_id"] = target_status
    if pipeline_id:
        payload["pipeline_id"] = pipeline_id
    if budget:
        payload["price"] = budget

    if payload:
        amo_request("PATCH", "leads", [{"id": lead_id, **payload}])


def sync_to_amo(tg_id: int, name: str, username: str,
                message_text: str, bot_reply: str,
                qualification: str = None, interest: str = None, budget: int = None):
    """ÐÐ»Ð°Ð²Ð½Ð°Ñ ÑÑÐ½ÐºÑÐ¸Ñ ÑÐ¸Ð½ÑÑÐ¾Ð½Ð¸Ð·Ð°ÑÐ¸Ð¸ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð° Ñ amoCRM."""
    if not AMO_TOKEN:
        return

    try:
        # ÐÐ¾Ð»ÑÑÐ°ÐµÐ¼ Ð¸Ð· ÐºÐµÑÐ° Ð¸Ð»Ð¸ ÑÐ¾Ð·Ð´Ð°ÑÐ¼
        if tg_id not in _amo_client_cache:
            contact_id = amo_get_or_create_contact(tg_id, name, username)
            if not contact_id:
                return

            # ÐÐ»Ñ Ð³Ð¾ÑÑÑÐµÐ³Ð¾ Ð»Ð¸Ð´Ð° â ÑÐ¾Ð·Ð´Ð°ÑÐ¼ Ð¸Ð¼ÐµÐ½Ð¾Ð²Ð°Ð½Ð½ÑÑ ÑÐ´ÐµÐ»ÐºÑ
            if qualification == "ÐÐ¾ÑÑÑÐ¸Ð¹" and interest:
                lead_name = f"{name} â {interest}"
            else:
                lead_name = f"ÐÐ°Ð¿ÑÐ¾Ñ Ð¾Ñ {name}"

            lead_id = amo_get_or_create_lead(tg_id, contact_id, lead_name)
            _amo_client_cache[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
            _save_amo_map(tg_id, contact_id, lead_id)  # Ð¿ÐµÑÑÐ¸ÑÑÐµÐ½ÑÐ½Ð¾
        else:
            lead_id = _amo_client_cache[tg_id].get("lead_id", 0)

            # ÐÐ±Ð½Ð¾Ð²Ð»ÑÐµÐ¼ Ð½Ð°Ð·Ð²Ð°Ð½Ð¸Ðµ ÑÐ´ÐµÐ»ÐºÐ¸ ÐµÑÐ»Ð¸ ÑÑÐ°Ð» Ð³Ð¾ÑÑÑÐ¸Ð¼
            if qualification == "ÐÐ¾ÑÑÑÐ¸Ð¹" and interest and lead_id:
                amo_request("PATCH", "leads", [{"id": lead_id, "name": f"{name} â {interest}"}])

        if not lead_id:
            return

        # ÐÐ¾Ð±Ð°Ð²Ð»ÑÐµÐ¼ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ ÐºÐ»Ð¸ÐµÐ½ÑÐ° ÐºÐ°Ðº ÐºÐ¾Ð¼Ð¼ÐµÐ½ÑÐ°ÑÐ¸Ð¹
        note = f"ð¤ {name}: {message_text}\nð¤ Ð®Ð»Ñ: {bot_reply[:300]}"
        if interest:
            note += f"\nð¦ ÐÐ½ÑÐµÑÐµÑ: {interest}"
        if budget:
            note += f"\nð° ÐÑÐ´Ð¶ÐµÑ: {budget:,} â½".replace(",", " ")
        if qualification:
            note += f"\nð Ð¡ÑÐ°ÑÑÑ: {qualification}"
        amo_add_note(lead_id, note)

        # ÐÐ²Ð¸Ð³Ð°ÐµÐ¼ Ð¿Ð¾ Ð²Ð¾ÑÐ¾Ð½ÐºÐµ + Ð¾Ð±Ð½Ð¾Ð²Ð»ÑÐµÐ¼ ÑÑÐ¼Ð¼Ñ ÐµÑÐ»Ð¸ Ð¸Ð·Ð²ÐµÑÑÐµÐ½ Ð±ÑÐ´Ð¶ÐµÑ
        if qualification in ("ÐÐ¾ÑÑÑÐ¸Ð¹", "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ"):
            amo_move_pipeline(lead_id, qualification, interest, budget)

        logger.info(f"amoCRM sync: tg={tg_id} lead={lead_id} qual={qualification}")
    except Exception as e:
        logger.error(f"amoCRM sync error: {e}")


def director_get_revenue_stats(days: int, group_by: str = "Ð¸ÑÐ¾Ð³Ð¾") -> dict:
    """Ð¡ÑÐ°ÑÐ¸ÑÑÐ¸ÐºÐ° Ð²ÑÑÑÑÐºÐ¸. ÐÑÑÐ¾ÑÐ½Ð¸Ðº: amoCRM (Ð¾ÑÐ½Ð¾Ð²Ð½Ð¾Ð¹) Ð¸Ð»Ð¸ Notion (fallback)."""

    # ââ amoCRM ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    if AMO_TOKEN:
        leads = amo_get_leads(days)
        prev_leads = amo_get_leads(days * 2)
        # prev_leads Ð²ÐºÐ»ÑÑÐ°ÐµÑ ÑÐµÐºÑÑÐ¸Ð¹ Ð¿ÐµÑÐ¸Ð¾Ð´ â ÑÐ±Ð¸ÑÐ°ÐµÐ¼
        import time
        since_ts = int(time.time()) - days * 86400
        prev_leads = [l for l in prev_leads if l.get("created_at", 0) < since_ts]

        def calc_amo(deals):
            total = 0
            count = 0
            by_status = {}
            by_manager = {}
            for d in deals:
                price = d.get("price") or 0
                total += price
                count += 1
                status = d.get("status_id", "?")
                by_status[str(status)] = by_status.get(str(status), {"count": 0, "sum": 0})
                by_status[str(status)]["count"] += 1
                by_status[str(status)]["sum"] += price
                # ÐÐµÐ½ÐµÐ´Ð¶ÐµÑ
                embedded = d.get("_embedded", {})
                users = embedded.get("users", []) if isinstance(embedded, dict) else []
                manager = users[0].get("name", "ÐÐµ Ð½Ð°Ð·Ð½Ð°ÑÐµÐ½") if users else "ÐÐµ Ð½Ð°Ð·Ð½Ð°ÑÐµÐ½"
                by_manager[manager] = by_manager.get(manager, {"count": 0, "sum": 0})
                by_manager[manager]["count"] += 1
                by_manager[manager]["sum"] += price
            return {"count": count, "total": total, "avg": total // count if count else 0,
                    "by_status": by_status, "by_manager": by_manager}

        cur = calc_amo(leads)
        prv = calc_amo(prev_leads)
        delta = cur["total"] - prv["total"]
        delta_pct = round(delta / prv["total"] * 100) if prv["total"] else None

        return {
            "source": "amoCRM",
            "period_days": days,
            "current": cur,
            "previous": prv,
            "delta": delta,
            "delta_pct": delta_pct,
            "group_by": group_by
        }

    # ââ Notion fallback âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    from datetime import timedelta
    now = datetime.utcnow()
    since = (now - timedelta(days=days)).date().isoformat()
    try:
        r = notion.databases.query(
            database_id=DEALS_DB_ID,
            filter={"property": "ÐÐµÐ´Ð»Ð°Ð¹Ð½", "date": {"on_or_after": since}}
        )
        deals = r.get("results", [])
    except Exception:
        r = notion.databases.query(database_id=DEALS_DB_ID, page_size=100)
        deals = r.get("results", [])

    total_rub = sum(d.get("properties", {}).get("Ð¡ÑÐ¼Ð¼Ð° â½", {}).get("number") or 0 for d in deals)
    count = len(deals)

    by_stage = {}
    for d in deals:
        props = d.get("properties", {})
        stage = (props.get("Ð¡ÑÐ°Ð´Ð¸Ñ", {}).get("status") or {}).get("name", "â")
        rub = props.get("Ð¡ÑÐ¼Ð¼Ð° â½", {}).get("number") or 0
        by_stage[stage] = by_stage.get(stage, {"count": 0, "sum_rub": 0})
        by_stage[stage]["count"] += 1
        by_stage[stage]["sum_rub"] += rub

    return {
        "source": "Notion (amoCRM ÑÐ¾ÐºÐµÐ½ Ð½Ðµ Ð°ÐºÑÐ¸Ð²ÐµÐ½)",
        "period_days": days,
        "current": {"count": count, "total": total_rub, "avg": total_rub // count if count else 0, "by_stage": by_stage},
        "previous": {},
        "delta": None,
        "delta_pct": None,
    }


def director_list_leads(qualification: str, limit: int = 10) -> list:
    """Ð¡Ð¿Ð¸ÑÐ¾Ðº Ð»Ð¸Ð´Ð¾Ð² â Ð¸Ð· amoCRM (Ð¾ÑÐ½Ð¾Ð²Ð½Ð¾Ð¹) Ð¸Ð»Ð¸ Notion (fallback)."""

    # ââ amoCRM ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    if AMO_TOKEN:
        import urllib.parse
        # ÐÐ°Ð¿Ð¿Ð¸Ð½Ð³ ÐºÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ð¸ â ÑÑÐ°ÑÑÑ amoCRM (Ð¿ÑÐ¸Ð¼ÐµÑÐ½ÑÐ¹)
        status_filter = ""
        if qualification == "ÐÐ¾ÑÑÑÐ¸Ð¹":
            # ÐÑÐµÐ¼ Ð»Ð¸Ð´Ñ Ð² ÑÑÐ°Ð´Ð¸Ð¸ Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÐ¾Ð²/ÐÐ
            pass  # ÑÐ¸Ð»ÑÑÑÑÐµÐ¼ Ð¿Ð¾ pipeline stage Ð¿Ð¾Ð·Ð¶Ðµ

        r = amo_request("GET", f"leads?limit={min(limit,50)}&with=contacts&order[created_at]=desc")
        raw_leads = r.get("_embedded", {}).get("leads", [])

        leads = []
        for l in raw_leads:
            contacts = l.get("_embedded", {}).get("contacts", []) if isinstance(l.get("_embedded"), dict) else []
            client = contacts[0].get("name", "â") if contacts else "â"
            price = l.get("price") or 0
            created = l.get("created_at", 0)
            from datetime import datetime as _dt
            created_str = _dt.fromtimestamp(created).strftime("%d.%m.%Y %H:%M") if created else "â"
            leads.append({
                "id": l.get("id"),
                "name": l.get("name", "â"),
                "client": client,
                "price": price,
                "status_id": l.get("status_id"),
                "created_at": created_str,
                "source": "amoCRM"
            })

        # Ð¤Ð¸Ð»ÑÑÑÐ°ÑÐ¸Ñ Ð¿Ð¾ qualification ÐµÑÐ»Ð¸ Ð½ÑÐ¶Ð½Ð¾
        if qualification == "ÐÐ¾ÑÑÑÐ¸Ð¹":
            # ÐÐ¾ÑÑÑÐ¸Ðµ â Ð½Ðµ Ð·Ð°ÐºÑÑÑÑÐµ Ð¸ Ñ ÑÑÐ¼Ð¼Ð¾Ð¹ > 0
            leads = [l for l in leads if l.get("price", 0) > 0][:limit]
        elif qualification != "Ð²ÑÐµ":
            leads = leads[:limit]

        return leads if leads else [{"note": "Ð amoCRM Ð½ÐµÑ Ð»Ð¸Ð´Ð¾Ð² Ð·Ð° Ð¿Ð¾ÑÐ»ÐµÐ´Ð½ÐµÐµ Ð²ÑÐµÐ¼Ñ"}]

    # ââ Notion fallback âââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    try:
        if qualification != "Ð²ÑÐµ":
            r = notion.databases.query(
                database_id=NOTION_DB_ID,
                filter={"property": "ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ", "select": {"equals": qualification}},
                page_size=min(limit, 20)
            )
        else:
            r = notion.databases.query(database_id=NOTION_DB_ID, page_size=min(limit, 20))
    except Exception as e:
        return [{"error": f"ÐÑÐ¸Ð±ÐºÐ° Notion: {e}"}]

    leads = []
    for p in r.get("results", []):
        props = p.get("properties", {})
        name_arr = props.get("Name", {}).get("title", [])
        name = name_arr[0]["plain_text"] if name_arr else "â"
        qual = (props.get("ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ", {}).get("select") or {}).get("name", "â")
        interest = (props.get("ÐÐ½ÑÐµÑÐµÑ", {}).get("select") or {}).get("name", "â")
        budget = props.get("ÐÑÐ´Ð¶ÐµÑ â½", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        leads.append({"name": name, "qual": qual, "interest": interest,
                      "budget": budget, "tg_id": tg_id, "source": "Notion"})
    return leads


async def handle_owner_director(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Director Mode â Ð²Ð»Ð°Ð´ÐµÐ»ÐµÑ Ð·Ð°Ð´Ð°ÑÑ Ð²Ð¾Ð¿ÑÐ¾ÑÑ Ð¾ Ð±Ð¸Ð·Ð½ÐµÑÐµ."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    messages = [{"role": "user", "content": text}]
    bot_ref = context.bot

    # Ð¦Ð¸ÐºÐ» tool_use
    for _ in range(5):  # Ð¼Ð°ÐºÑÐ¸Ð¼ÑÐ¼ 5 Ð²ÑÐ·Ð¾Ð²Ð¾Ð² Ð¸Ð½ÑÑÑÑÐ¼ÐµÐ½ÑÐ¾Ð²
        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=DIRECTOR_SYSTEM,
            tools=DIRECTOR_TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Ð¤Ð¸Ð½Ð°Ð»ÑÐ½ÑÐ¹ Ð¾ÑÐ²ÐµÑ
            reply = "".join(b.text for b in response.content if hasattr(b, "text"))
            await update.message.reply_text(reply)
            return

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool = block.name
                inp = block.input
                result = None

                try:
                    if tool == "get_stats":
                        result = director_get_stats(inp.get("days", 7))
                    elif tool == "find_client":
                        result = director_find_client(inp.get("query", ""))
                    elif tool == "list_leads":
                        result = director_list_leads(
                            inp.get("qualification", "Ð²ÑÐµ"),
                            inp.get("limit", 10)
                        )
                    elif tool == "send_to_client":
                        tg_id = inp["tg_id"]
                        text = inp["text"]

                        # ââ ÐÐ°Ð»Ð¸Ð´Ð°ÑÐ¸Ñ ÑÐ¾Ð²Ð°ÑÐ° Ð¿ÐµÑÐµÐ´ Ð¾ÑÐ¿ÑÐ°Ð²ÐºÐ¾Ð¹ âââââââââââââââââ
                        photo_urls_check = inp.get("photo_urls", [])
                        buttons_check = inp.get("buttons", [])
                        all_urls = photo_urls_check + [b.get("url","") for b in buttons_check]
                        altacasa_urls = [u for u in all_urls if "kokahouse.ru" in u]

                        if altacasa_urls:
                            # ÐÐ·Ð²Ð»ÐµÐºÐ°ÐµÐ¼ product key Ð¸Ð· URL Ð¸Ð»Ð¸ ÑÐµÐºÑÑÐ°
                            import re as _re
                            product_key = None
                            for url in altacasa_urls:
                                m = _re.search(r'product(\d*)', url)
                                if m:
                                    product_key = url.split("/")[-1].replace(".html","")

                            # ÐÐ¾Ð»ÑÑÐ°ÐµÐ¼ Ð¸Ð½ÑÐµÑÐµÑ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð¸Ð· ÐºÐµÑÐ° Ð´Ð¸Ð°Ð»Ð¾Ð³Ð¾Ð²
                            client_history = dialogs.get(tg_id, [])
                            client_interests = []
                            for msg in client_history[-10:]:
                                content = msg.get("content","") if isinstance(msg.get("content"), str) else ""
                                for cat in ["Ð´Ð¸Ð²Ð°Ð½","ÐºÑÐµÑÐ»Ð¾","ÐºÑÐ¾Ð²Ð°ÑÑ","ÑÑÐ¾Ð»","ÑÑÑÐ»","ÑÐºÐ°Ñ","ÑÑÐ¼Ð±Ð°","Ð³Ð°ÑÐ´ÐµÑÐ¾Ð±"]:
                                    if cat in content.lower():
                                        client_interests.append(cat)

                            # ÐÐ°ÑÐµÐ³Ð¾ÑÐ¸Ñ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÑÐµÐ¼Ð¾Ð³Ð¾ ÑÐ¾Ð²Ð°ÑÐ° Ð¸Ð· ÑÐµÐºÑÑÐ°
                            sending_cats = []
                            for cat in ["Ð´Ð¸Ð²Ð°Ð½","ÐºÑÐµÑÐ»Ð¾","ÐºÑÐ¾Ð²Ð°ÑÑ","ÑÑÐ¾Ð»","ÑÑÑÐ»","ÑÐºÐ°Ñ","ÑÑÐ¼Ð±Ð°","Ð³Ð°ÑÐ´ÐµÑÐ¾Ð±"]:
                                if cat in text.lower() or any(cat in u.lower() for u in all_urls):
                                    sending_cats.append(cat)

                            # ÐÑÐ»Ð¸ Ð¸Ð½ÑÐµÑÐµÑÑ Ð¸Ð·Ð²ÐµÑÑÐ½Ñ Ð¸ ÑÐ¾Ð²Ð°Ñ Ð½Ðµ ÑÐ¾Ð²Ð¿Ð°Ð´Ð°ÐµÑ â WARNING
                            if client_interests and sending_cats:
                                mismatch = not any(c in client_interests for c in sending_cats)
                                if mismatch:
                                    warning_msg = (
                                        f"â ï¸ ÐÐÐÐÐÐÐÐ!\n"
                                        f"ÐÐ»Ð¸ÐµÐ½Ñ Ð¸Ð½ÑÐµÑÐµÑÐ¾Ð²Ð°Ð»ÑÑ: {', '.join(set(client_interests))}\n"
                                        f"ÐÑ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÑÐµÑÐµ: {', '.join(set(sending_cats))}\n\n"
                                        f"Ð­ÑÐ¾ Ð½Ð°Ð¼ÐµÑÐµÐ½Ð½Ð¾? Ð¡Ð¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ Ð²ÑÑ ÑÐ°Ð²Ð½Ð¾ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾."
                                    )
                                    await bot_ref.send_message(
                                        chat_id=int(MANAGER_CHAT_ID),
                                        text=warning_msg
                                    )
                        # ââ ÐºÐ¾Ð½ÐµÑ Ð²Ð°Ð»Ð¸Ð´Ð°ÑÐ¸Ð¸ âââââââââââââââââââââââââââââââââââ
                        photo_urls = inp.get("photo_urls", [])
                        buttons = inp.get("buttons", [])

                        # Ð¡ÑÑÐ¾Ð¸Ð¼ inline-ÐºÐ»Ð°Ð²Ð¸Ð°ÑÑÑÑ ÐµÑÐ»Ð¸ ÐµÑÑÑ ÐºÐ½Ð¾Ð¿ÐºÐ¸
                        reply_markup = None
                        if buttons:
                            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                            keyboard = [[InlineKeyboardButton(b["text"], url=b["url"])] for b in buttons if b.get("url")]
                            if keyboard:
                                reply_markup = InlineKeyboardMarkup(keyboard)

                        if photo_urls:
                            if len(photo_urls) == 1:
                                # ÐÐ´Ð½Ð¾ ÑÐ¾ÑÐ¾ Ñ Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÑ
                                await bot_ref.send_photo(
                                    chat_id=tg_id,
                                    photo=photo_urls[0],
                                    caption=text[:1024],
                                    reply_markup=reply_markup
                                )
                            else:
                                # ÐÐµÑÐºÐ¾Ð»ÑÐºÐ¾ ÑÐ¾ÑÐ¾ â media group
                                from telegram import InputMediaPhoto
                                media = [InputMediaPhoto(media=url, caption=text[:1024] if i == 0 else None)
                                         for i, url in enumerate(photo_urls[:10])]
                                await bot_ref.send_media_group(chat_id=tg_id, media=media)
                                if reply_markup:
                                    await bot_ref.send_message(chat_id=tg_id, text="ð ÐÐ¾ÑÐ¼Ð¾ÑÑÐ¸ÑÐµ Ð²Ð°ÑÐ¸Ð°Ð½ÑÑ Ð²ÑÑÐµ", reply_markup=reply_markup)
                        else:
                            # Ð¢Ð¾Ð»ÑÐºÐ¾ ÑÐµÐºÑÑ Ñ ÐºÐ½Ð¾Ð¿ÐºÐ°Ð¼Ð¸
                            await bot_ref.send_message(
                                chat_id=tg_id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode="Markdown"
                            )
                        result = {"status": "sent", "tg_id": tg_id, "photos": len(photo_urls), "buttons": len(buttons)}
                    elif tool == "get_channel_info":
                        result = {"channel": CHANNEL_ID, "note": "ÐÐ°Ð½Ð½ÑÐµ ÐºÐ°Ð½Ð°Ð»Ð° Ð´Ð¾ÑÑÑÐ¿Ð½Ñ ÑÐµÑÐµÐ· Telegram API"}
                    elif tool == "reply_to_lead":
                        # ÐÑÐµÐ¼ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð² Notion Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸
                        clients = director_find_client(inp["client_name"])
                        if not clients:
                            result = {"error": f"ÐÐ»Ð¸ÐµÐ½Ñ '{inp['client_name']}' Ð½Ðµ Ð½Ð°Ð¹Ð´ÐµÐ½ Ð² Ð±Ð°Ð·Ðµ"}
                        else:
                            client = clients[0]
                            tg_id = client.get("tg_id")
                            if not tg_id:
                                result = {"error": f"Ð£ ÐºÐ»Ð¸ÐµÐ½ÑÐ° {client['name']} Ð½ÐµÑ Telegram ID"}
                            else:
                                msg = inp["message"]
                                photo_urls = inp.get("photo_urls", [])
                                buttons = inp.get("buttons", [])
                                reply_markup = None
                                if buttons:
                                    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                                    keyboard = [[InlineKeyboardButton(b["text"], url=b["url"])] for b in buttons if b.get("url")]
                                    if keyboard:
                                        reply_markup = InlineKeyboardMarkup(keyboard)
                                if photo_urls:
                                    await bot_ref.send_photo(chat_id=tg_id, photo=photo_urls[0], caption=msg[:1024], reply_markup=reply_markup)
                                else:
                                    await bot_ref.send_message(chat_id=tg_id, text=msg, reply_markup=reply_markup)
                                # ÐÐ¾Ð±Ð°Ð²Ð»ÑÐµÐ¼ Ð² amoCRM ÐºÐ°Ðº Ð¸ÑÑÐ¾Ð´ÑÑÐµÐµ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ
                                if tg_id in _amo_client_cache:
                                    lead_id = _amo_client_cache[tg_id].get("lead_id", 0)
                                    amo_add_note(lead_id, f"ð¤ ÐÑÑÐ¾Ð´ÑÑÐµÐµ Ð¾Ñ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÐ° â {client['name']}:\n{msg}")
                                result = {"status": "sent", "client": client["name"], "tg_id": tg_id}
                    elif tool == "update_deal":
                        result = director_update_deal(
                            inp["deal_id"],
                            inp.get("status"),
                            inp.get("price"),
                            inp.get("note")
                        )
                    elif tool == "create_deal":
                        result = director_create_deal(
                            inp["name"],
                            inp["client_name"],
                            inp.get("price", 0),
                            inp.get("note", "")
                        )
                    elif tool == "search_deals":
                        result = director_search_deals(inp["query"])
                    elif tool == "get_revenue_stats":
                        result = director_get_revenue_stats(
                            inp.get("days", 30),
                            inp.get("group_by", "Ð¸ÑÐ¾Ð³Ð¾")
                        )
                except Exception as e:
                    result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str)
                })

            messages.append({"role": "user", "content": tool_results})

    await update.message.reply_text("ÐÐµ ÑÐ´Ð°Ð»Ð¾ÑÑ Ð¿Ð¾Ð»ÑÑÐ¸ÑÑ Ð´Ð°Ð½Ð½ÑÐµ. ÐÐ¾Ð¿ÑÐ¾Ð±ÑÐ¹ Ð¿ÐµÑÐµÑÐ¾ÑÐ¼ÑÐ»Ð¸ÑÐ¾Ð²Ð°ÑÑ.")


# ââ Ð¥ÑÐ°Ð½Ð¸Ð»Ð¸ÑÐµ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð¾Ð² ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
dialogs: dict[int, list[dict]] = {}
MAX_HISTORY = 12


# ââ Notion helpers ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def get_or_create_client(tg_id: int, name: str, username: str) -> str:
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "Telegram ID", "number": {"equals": tg_id}}
    )
    if results["results"]:
        page = results["results"][0]
        page_id = page["id"]
        # ÐÐ°Ð³ÑÑÐ¶Ð°ÐµÐ¼ Ð¸ÑÑÐ¾ÑÐ¸Ñ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð° Ð¸Ð· Notion Ð² Ð¿Ð°Ð¼ÑÑÑ
        try:
            history_raw = page["properties"].get("ÐÑÑÐ¾ÑÐ¸Ñ JSON", {}).get("rich_text", [])
            if history_raw:
                history_json = history_raw[0]["plain_text"]
                loaded = json.loads(history_json)
                if loaded and tg_id not in dialogs:
                    dialogs[tg_id] = loaded
                    logger.info(f"ÐÑÑÐ¾ÑÐ¸Ñ Ð·Ð°Ð³ÑÑÐ¶ÐµÐ½Ð° Ð´Ð»Ñ {tg_id}: {len(loaded)} ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ð¹")
        except Exception as e:
            logger.error(f"History load error: {e}")
        return page_id

    tg_url = f"https://t.me/{username}" if username else None
    props = {
        "Name":        {"title": [{"text": {"content": name}}]},
        "Telegram ID": {"number": tg_id},
        "ÐÐ°Ð½Ð°Ð»":       {"select": {"name": "Telegram"}},
        "ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ":{"select": {"name": "Ð¥Ð¾Ð»Ð¾Ð´Ð½ÑÐ¹"}},
        "Ð¯Ð·ÑÐº":        {"select": {"name": "RU"}},
        "ÐÐ°ÑÐ°":        {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    if tg_url:
        props["Telegram"] = {"url": tg_url}
    page = notion.pages.create(parent={"database_id": NOTION_DB_ID}, properties=props)
    logger.info(f"ÐÐ¾Ð²ÑÐ¹ ÐºÐ»Ð¸ÐµÐ½Ñ: {name} ({tg_id})")
    return page["id"]


def update_client(page_id: str, dialog_text: str, history: list = None,
                  qualification: str = None, interest: str = None,
                  budget: float = None, escalate: bool = False):
    # Ð¡Ð¾ÑÑÐ°Ð½ÑÐµÐ¼ Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 20 ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ð¹ ÐºÐ°Ðº JSON (ÑÐ¾Ð»ÑÐºÐ¾ ÑÐµÐºÑÑÐ¾Ð²ÑÐµ)
    history_json = ""
    if history:
        text_only = [m for m in history if isinstance(m.get("content"), str)][-20:]
        history_json = json.dumps(text_only, ensure_ascii=False)

    props = {
        "ÐÐ¸Ð°Ð»Ð¾Ð³ Ñ Ð±Ð¾ÑÐ¾Ð¼": {"rich_text": [{"text": {"content": dialog_text[-2000:]}}]},
    }
    if history_json:
        props["ÐÑÑÐ¾ÑÐ¸Ñ JSON"] = {"rich_text": [{"text": {"content": history_json[:2000]}}]}
    if qualification:
        props["ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ"] = {"select": {"name": qualification}}
    if interest:
        props["ÐÐ½ÑÐµÑÐµÑ"] = {"select": {"name": interest}}
    if budget:
        props["ÐÑÐ´Ð¶ÐµÑ â½"] = {"number": budget}
    if escalate:
        props["Ð­ÑÐºÐ°Ð»Ð¸ÑÐ¾Ð²Ð°ÑÑ"] = {"checkbox": True}
        props["ÐÐ²Ð°Ð»Ð¸ÑÐ¸ÐºÐ°ÑÐ¸Ñ"] = {"select": {"name": "ÐÐµÑÐµÐ´Ð°Ð½ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ"}}
    notion.pages.update(page_id=page_id, properties=props)


# ââ AI Ð»Ð¾Ð³Ð¸ÐºÐ° âââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def ask_claude(chat_id: int, user_message: str, image_data: dict = None, extra_system: str = "") -> dict:
    history = dialogs.get(chat_id, [])

    if image_data:
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": image_data["media_type"], "data": image_data["data"]}},
            {"type": "text", "text": user_message or "ÐÐ»Ð¸ÐµÐ½Ñ Ð¿ÑÐ¸ÑÐ»Ð°Ð» Ð¸Ð·Ð¾Ð±ÑÐ°Ð¶ÐµÐ½Ð¸Ðµ. ÐÐ¿Ð¸ÑÐ¸ ÑÑÐ¾ Ð½Ð° Ð½ÑÐ¼ Ð¸ ÐºÐ°Ðº ÑÑÐ¾ ÑÐ²ÑÐ·Ð°Ð½Ð¾ Ñ Ð¼ÐµÐ±ÐµÐ»ÑÑ."}
        ]
        history.append({"role": "user", "content": content})
    else:
        history.append({"role": "user", "content": user_message})

    # Ð£Ð¿ÑÐ¾ÑÐ°ÐµÐ¼ Ð¸ÑÑÐ¾ÑÐ¸Ñ Ð´Ð»Ñ API (ÑÐ¾Ð»ÑÐºÐ¾ ÑÐµÐºÑÑ)
    api_history = []
    for m in history[-MAX_HISTORY:]:
        if isinstance(m["content"], list):
            api_history.append(m)
        else:
            api_history.append({"role": m["role"], "content": m["content"]})

    system_text = get_system_prompt() + extra_system
    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=[{"type":"text","text":system_text,"cache_control":{"type":"ephemeral"}}],
        messages=api_history
    )

    raw = response.content[0].text
    history.append({"role": "assistant", "content": raw})
    dialogs[chat_id] = history[-MAX_HISTORY:]

    result = {"reply": raw, "qualification": None, "interest": None, "budget": None, "escalate": False}

    if "```json" in raw:
        try:
            text_before_json = raw.split("```json")[0].strip()
            json_part = raw.split("```json")[1].split("```")[0].strip()
            meta = json.loads(json_part)
            json_reply = meta.get("reply", "")
            if json_reply and len(json_reply) > 30:
                result["reply"] = json_reply
            elif text_before_json and len(text_before_json) > 10:
                result["reply"] = text_before_json
            result["qualification"] = meta.get("qualification")
            result["interest"]      = meta.get("interest")
            result["budget"]        = meta.get("budget")
            result["escalate"]      = meta.get("escalate", False)
        except Exception:
            pass

    return result


async def download_photo(bot, file_id: str) -> dict:
    """Ð¡ÐºÐ°ÑÐ°ÑÑ ÑÐ¾ÑÐ¾ Ð¸Ð· Telegram Ð¸ Ð²ÐµÑÐ½ÑÑÑ base64."""
    file = await bot.get_file(file_id)
    url  = file.file_path
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    data = base64.standard_b64encode(resp.content).decode()
    return {"data": data, "media_type": "image/jpeg"}


# ââ ÐÐ°ÑÐ°Ð»Ð¾Ð³ ÑÐ¾Ð²Ð°ÑÐ¾Ð² (Ð´Ð»Ñ deep links Ñ ÑÐ°Ð¹ÑÐ°) âââââââââââââââââââââââââââââââââ
PRODUCTS = {
    # ÐÐ¸Ð²Ð°Ð½Ñ
    "mc_a68": {
        "name": "ÐÐ¸Ð²Ð°Ð½ MC-A68",
        "desc": "ÐÑÐ°Ð»ÑÑÐ½ÑÐºÐ°Ñ Ð½Ð°ÑÑÑÐ°Ð»ÑÐ½Ð°Ñ ÐºÐ¾Ð¶Ð° oil-wax, Ð³ÑÑÐ¸Ð½ÑÐ¹ Ð¿ÑÑ, Ð»Ð¸ÑÑÐ²ÐµÐ½Ð½Ð¸ÑÐ°. 3-Ð¼ÐµÑÑÐ½ÑÐ¹ 230Ã97Ã92 ÑÐ¼.",
        "price": "Ð¾Ñ 235 224 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "fort": {
        "name": "ÐÐ¸Ð²Ð°Ð½ FORT",
        "desc": "ÐÑÐµÑ/ÑÑÐµÐ½Ñ + Ð²ÐµÐ»ÑÑ, Ð²ÑÑÐ¾ÐºÐ¾Ð¿Ð»Ð¾ÑÐ½ÑÐ¹ Ð¿Ð¾ÑÐ¾Ð»Ð¾Ð½. 2â4 Ð¼ÐµÑÑÐ½ÑÐ¹.",
        "price": "Ð¾Ñ 99 634 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "pr701": {
        "name": "ÐÐ¸Ð²Ð°Ð½ PR701 Â«ÐÐ±Ð»Ð°ÐºÐ¾Â»",
        "desc": "ÐÐ¾Ð´ÑÐ»ÑÐ½ÑÐ¹. Ð¥Ð»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, Ð³ÑÑÐ¸Ð½ÑÐ¹ Ð¿ÑÑ, Ð»Ð¸ÑÑÐ²ÐµÐ½Ð½Ð¸ÑÐ°. 3â4 Ð¼ÐµÑÑÐ° + Ð¿ÑÑ.",
        "price": "Ð¾Ñ 219 109 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "mk_sofa01": {
        "name": "ÐÐ¸Ð²Ð°Ð½ MK-SOFA01",
        "desc": "ÐÐ½Ð¸Ð»Ð¸Ð½Ð¾Ð²Ð°Ñ/Ð·Ð°Ð¼ÑÐµÐ²Ð°Ñ ÐºÐ¾Ð¶Ð°, Ð¾ÑÐµÑ, Ð»Ð¸ÑÑÐ²ÐµÐ½Ð½Ð¸ÑÐ°. 2â3 Ð¼ÐµÑÑÐ°.",
        "price": "Ð¾Ñ 272 833 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "qmw2023": {
        "name": "ÐÐ¸Ð²Ð°Ð½ QMW-2023",
        "desc": "ÐÑÐ°Ð»ÑÑÐ½ÑÐºÐ°Ñ Ð½Ð°ÑÑÑÐ°Ð»ÑÐ½Ð°Ñ ÐºÐ¾Ð¶Ð°, Ð½ÐµÑÐ¶Ð°Ð²ÐµÑÑÐ°Ñ ÑÑÐ°Ð»Ñ. 1â4 Ð¼ÐµÑÑÐ°.",
        "price": "Ð¾Ñ 59 895 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    # ÐÑÐµÑÐ»Ð°
    "lanyue": {
        "name": "ÐÑÐµÑÐ»Ð¾ Â«ÐÐ°Ð½ÑÑÑÂ» ZX-LY3",
        "desc": "Ð¡ÐµÐ².-Ð°Ð¼ÐµÑÐ¸ÐºÐ°Ð½ÑÐºÐ¸Ð¹ Ð¾ÑÐµÑ, ÑÐ»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, Ð¿Ð¾ÑÐ¾Ð»Ð¾Ð½ + ÑÐ¾Ð»Ð»Ð¾ÑÐ°Ð¹Ð±ÐµÑ. 64Ã102Ã74 ÑÐ¼.",
        "price": "118 921 â½",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "mercer": {
        "name": "ÐÑÐµÑÐ»Ð¾ MERCER",
        "desc": "ÐÑÐµÑ/ÑÑÐµÐ½Ñ, Ð¿ÑÐµÐ¼Ð¸Ð°Ð»ÑÐ½ÑÐ¹ ÑÐ»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, Ð²ÑÑÐ¾ÐºÐ¾Ð¿Ð»Ð¾ÑÐ½ÑÐ¹ Ð¿Ð¾ÑÐ¾Ð»Ð¾Ð½. 70Ã96Ã95 ÑÐ¼.",
        "price": "Ð¾Ñ 127 490 â½",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "florence": {
        "name": "ÐÑÐµÑÐ»Ð¾ Lounge Florence",
        "desc": "ÐÐ¾Ð¶Ð° full-grain, ÐºÐ°ÑÐºÐ°Ñ Ð¸Ð· Ð¾ÑÐµÑÐ¾Ð²Ð¾Ð³Ð¾ Ð´ÐµÑÐµÐ²Ð°. Ð¡ÑÐ¸Ð»Ñ mid-century modern.",
        "price": "Ð¾Ñ 47 500 â½",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "2 ÑÑ",
    },
    # ÐÑÐ¾Ð²Ð°ÑÐ¸
    "roma": {
        "name": "ÐÑÐ¾Ð²Ð°ÑÑ Roma Platform",
        "desc": "ÐÐ°ÑÑÐ¸Ð² Ð´ÑÐ±Ð°, Ð¼ÑÐ³ÐºÐ¾Ðµ Ð¸Ð·Ð³Ð¾Ð»Ð¾Ð²ÑÐµ, Ð¿Ð¾Ð´ÑÑÐ¼Ð½ÑÐ¹ Ð¼ÐµÑÐ°Ð½Ð¸Ð·Ð¼. Ð Ð°Ð·Ð¼ÐµÑÑ 160/180/200.",
        "price": "Ð¾Ñ 62 000 â½",
        "ÑÑÐ¾Ðº": "5â7 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    # Ð¡ÑÐ¾Ð»Ð¸ÐºÐ¸
    "cj106": {
        "name": "ÐÑÑÐ½Ð°Ð»ÑÐ½ÑÐ¹ ÑÑÐ¾Ð»Ð¸Ðº MK-CJ106",
        "desc": "ÐÐ°ÑÑÐ¸Ð² ÑÐµÐ².-Ð°Ð¼ÐµÑÐ¸ÐºÐ°Ð½ÑÐºÐ¾Ð³Ð¾ Ð¾ÑÐµÑÐ°. 135Ã75Ã36 ÑÐ¼.",
        "price": "98 593 â½",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "palazzo": {
        "name": "ÐÐ±ÐµÐ´ÐµÐ½Ð½ÑÐ¹ ÑÑÐ¾Ð» Palazzo",
        "desc": "Ð¡ÑÐ¾Ð»ÐµÑÐ½Ð¸ÑÐ° Ð¸Ð· Ð¸ÑÐ°Ð»ÑÑÐ½ÑÐºÐ¾Ð³Ð¾ Ð¼ÑÐ°Ð¼Ð¾ÑÐ° Calacatta, Ð½ÐµÑÐ¶Ð°Ð²ÐµÑÑÐ°Ñ ÑÑÐ°Ð»Ñ. Ã120/140/160 ÑÐ¼.",
        "price": "Ð¾Ñ 118 000 â½",
        "ÑÑÐ¾Ðº": "7â10 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "2 ÑÑ",
    },
    # ÐÑÐ¸Ñ
    "executive": {
        "name": "Ð¡ÑÐ¾Ð» Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÐ½ÑÐ¹ Executive",
        "desc": "Ð¨Ð¿Ð¾Ð½ Ð°Ð¼ÐµÑÐ¸ÐºÐ°Ð½ÑÐºÐ¾Ð³Ð¾ Ð¾ÑÐµÑÐ°, ÑÑÐ¾Ð¼. 3.6â6.0 Ð¼. ÐÑÑÑÐ¾ÐµÐ½Ð½ÑÐµ ÐºÐ°Ð±ÐµÐ»Ñ-ÐºÐ°Ð½Ð°Ð»Ñ.",
        "price": "Ð¾Ñ 210 000 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "1 ÑÑ",
    },
    "cabinet_pro": {
        "name": "ÐÐ°ÑÐ´ÐµÑÐ¾Ð±Ð½Ð°Ñ ÑÐ¸ÑÑÐµÐ¼Ð° Cabinet Pro",
        "desc": "ÐÐ°ÑÐ¾Ð²ÑÐ¹ Ð»Ð°Ðº + Ð½Ð°ÑÑÑÐ°Ð»ÑÐ½ÑÐ¹ ÑÐ¿Ð¾Ð½, Ð°Ð»ÑÐ¼Ð¸Ð½Ð¸ÐµÐ²ÑÐµ Ð¿ÑÐ¾ÑÐ¸Ð»Ð¸. ÐÐ¾Ð´ ÑÐ°Ð·Ð¼ÐµÑ Ð¿Ð¾Ð¼ÐµÑÐµÐ½Ð¸Ñ.",
        "price": "Ð¾Ñ 94 000 â½",
        "ÑÑÐ¾Ðº": "6â8 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "ÐºÐ°ÑÑÐ¾Ð¼",
    },
    # ÐÑÐµÐ»Ñ
    "grand_hotel": {
        "name": "Ð ÐµÑÐµÐ¿ÑÐ½-ÑÑÐ¾Ð¹ÐºÐ° Grand Hotel",
        "desc": "ÐÐ°ÑÑÑÐ°Ð»ÑÐ½ÑÐ¹ ÑÑÐ°Ð²ÐµÑÑÐ¸Ð½/Ð¼ÑÐ°Ð¼Ð¾Ñ + ÐºÐ²Ð°ÑÑ. ÐÐ¾Ð´ÑÐ²ÐµÑÐºÐ° Ð² Ð±Ð°Ð·Ðµ. ÐÐ¾Ð»Ð½Ð¾ÑÑÑÑ Ð¿Ð¾Ð´ ÑÐ°Ð·Ð¼ÐµÑ Ð»Ð¾Ð±Ð±Ð¸.",
        "price": "Ð¾Ñ 157 200 â½",
        "ÑÑÐ¾Ðº": "8â12 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "ÐºÐ°ÑÑÐ¾Ð¼",
    },
    "chateau": {
        "name": "ÐÐ°Ð½ÐºÐµÑÐ½ÑÐ¹ ÑÑÑÐ» Chateau",
        "desc": "ÐÑÐº + ÑÐºÐ°Ð½Ñ/ÐºÐ¾Ð¶Ð°. Ð¨ÑÐ°Ð±ÐµÐ»Ð¸ÑÑÐµÐ¼ÑÐ¹. 50+ ÑÐ°ÑÑÐ²ÐµÑÐ¾Ðº. Ð¡ÐµÑÑÐ¸ÑÐ¸ÐºÐ°Ñ EN 16139.",
        "price": "Ð¾Ñ 4 200 â½/ÑÑ",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "50 ÑÑ",
    },
    "milano": {
        "name": "ÐÑÐ¸ÐºÑÐ¾Ð²Ð°ÑÐ½Ð°Ñ ÑÑÐ¼Ð±Ð° Milano",
        "desc": "ÐÐ°ÐºÐ¸ÑÐ¾Ð²Ð°Ð½Ð½ÑÐ¹ ÐÐÐ¤ 18 ÑÐ²ÐµÑÐ¾Ð², Ð»Ð°ÑÑÐ½Ñ Ð¼Ð°ÑÐ¾Ð²Ð°Ñ/Ð³Ð»ÑÐ½ÐµÑ. ÐÑÐ´Ð²Ð¸Ð¶Ð½Ð¾Ð¹ ÑÑÐ¸Ðº Ð½Ð° Ð´Ð¾Ð²Ð¾Ð´ÑÐ¸ÐºÐµ.",
        "price": "Ð¾Ñ 18 400 â½",
        "ÑÑÐ¾Ðº": "4â6 Ð½ÐµÐ´ÐµÐ»Ñ",
        "moq": "4 ÑÑ",
    },
}

def get_product_context(product_key: str) -> str:
    """ÐÐµÑÐ½ÑÑÑ ÑÐµÐºÑÑ Ñ Ð¾Ð¿Ð¸ÑÐ°Ð½Ð¸ÐµÐ¼ ÑÐ¾Ð²Ð°ÑÐ° Ð´Ð»Ñ ÑÐ¸ÑÑÐµÐ¼Ð½Ð¾Ð³Ð¾ Ð¿ÑÐ¾Ð¼Ð¿ÑÐ°."""
    p = PRODUCTS.get(product_key.lower().replace("-", "_").replace(" ", "_"))
    if not p:
        return ""
    return (
        f"\n\nâââââââââââââââââââââââââââââââ\n"
        f"ÐÐÐÐÐÐ¢ ÐÐ ÐÐ¨ÐÐ Ð¡ ÐÐÐ Ð¢ÐÐ§ÐÐ Ð¢ÐÐÐÐ Ð\n"
        f"âââââââââââââââââââââââââââââââ\n"
        f"Ð¢Ð¾Ð²Ð°Ñ: {p['name']}\n"
        f"ÐÐ¿Ð¸ÑÐ°Ð½Ð¸Ðµ: {p['desc']}\n"
        f"Ð¦ÐµÐ½Ð°: {p['price']}\n"
        f"Ð¡ÑÐ¾Ðº Ð¿ÑÐ¾Ð¸Ð·Ð²Ð¾Ð´ÑÑÐ²Ð°: {p['ÑÑÐ¾Ðº']}\n"
        f"ÐÐ¸Ð½Ð¸Ð¼Ð°Ð»ÑÐ½ÑÐ¹ Ð·Ð°ÐºÐ°Ð·: {p['moq']}\n\n"
        f"ÐÐ°ÑÐ½Ð¸ Ñ Ð¿ÑÐ¸Ð²ÐµÑÑÑÐ²Ð¸Ñ Ð¸ ÑÑÐ°Ð·Ñ ÑÐ¿Ð¾Ð¼ÑÐ½Ð¸ ÑÑÐ¾Ñ ÑÐ¾Ð²Ð°Ñ Ð¿Ð¾ Ð¸Ð¼ÐµÐ½Ð¸. "
        f"Ð¡Ð¿ÑÐ¾ÑÐ¸ ÑÑÐ¾ Ð¸Ð¼ÐµÐ½Ð½Ð¾ ÐºÐ»Ð¸ÐµÐ½Ñ ÑÐ¾ÑÐµÑ ÑÑÐ¾ÑÐ½Ð¸ÑÑ."
    )


# ââ Telegram handlers âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dialogs[user.id] = []

    # Ð§Ð¸ÑÐ°ÐµÐ¼ Ð¿Ð°ÑÐ°Ð¼ÐµÑÑ deep link (product key)
    product_key = context.args[0] if context.args else None
    product_ctx = get_product_context(product_key) if product_key else ""

    # amoCRM ÑÐ¾Ð·Ð´Ð°ÑÑ ÐºÐ¾Ð½ÑÐ°ÐºÑ Ð¿ÑÐ¸ Ð¿ÐµÑÐ²Ð¾Ð¼ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ð¸

    if product_ctx:
        # ÐÑÑÑ ÐºÐ¾Ð½ÑÐµÐºÑÑ ÑÐ¾Ð²Ð°ÑÐ° â Ð¿ÑÐ¾ÑÐ¸Ð¼ Claude Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð¿ÐµÑÑÐ¾Ð½Ð°Ð»Ð¸Ð·Ð¸ÑÐ¾Ð²Ð°Ð½Ð½Ð¾Ðµ Ð¿ÑÐ¸Ð²ÐµÑÑÑÐ²Ð¸Ðµ
        result = ask_claude(
            user.id,
            f"[Ð¡ÐÐ¡Ð¢ÐÐÐ: ÐºÐ»Ð¸ÐµÐ½Ñ Ð¿ÐµÑÐµÑÑÐ» Ñ ÐºÐ°ÑÑÐ¾ÑÐºÐ¸ ÑÐ¾Ð²Ð°ÑÐ°. ÐÐ¾Ð¿ÑÐ¸Ð²ÐµÑÑÑÐ²ÑÐ¹ Ð¸ Ð·Ð°Ð´Ð°Ð¹ Ð¿ÐµÑÐ²ÑÐ¹ Ð²Ð¾Ð¿ÑÐ¾Ñ.]{product_ctx}",
            extra_system=product_ctx
        )
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(
            "ÐÐ´ÑÐ°Ð²ÑÑÐ²ÑÐ¹ÑÐµ! ÐÐµÐ½Ñ Ð·Ð¾Ð²ÑÑ Ð®Ð»Ñ.\n\n"
            "Ð¯ Ð¿Ð¾Ð¼Ð¾Ð³Ñ Ð²Ð°Ð¼ Ð¿Ð¾Ð´Ð¾Ð±ÑÐ°ÑÑ ÐºÐ°ÑÐµÑÑÐ²ÐµÐ½Ð½ÑÑ Ð¼ÐµÐ±ÐµÐ»Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ, "
            "ÑÐ°ÑÑÑÐ¸ÑÐ°ÑÑ ÑÑÐ¾Ð¸Ð¼Ð¾ÑÑÑ Ð¸ Ð¿Ð¾Ð´Ð¾Ð±ÑÐ°ÑÑ Ð¾Ð¿ÑÐ¸Ð¼Ð°Ð»ÑÐ½ÑÐ¹ Ð²Ð°ÑÐ¸Ð°Ð½Ñ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸.\n\n"
            "ÐÐ¾Ð´ÑÐºÐ°Ð¶Ð¸ÑÐµ, Ð¿Ð¾Ð¶Ð°Ð»ÑÐ¹ÑÑÐ°, ÐºÐ°ÐºÑÑ Ð¼ÐµÐ±ÐµÐ»Ñ Ð²Ñ ÑÐ°ÑÑÐ¼Ð°ÑÑÐ¸Ð²Ð°ÐµÑÐµ: "
            "Ð´Ð»Ñ Ð´Ð¾Ð¼Ð°, Ð¾ÑÐ¸ÑÐ°, ÑÐµÑÑÐ¾ÑÐ°Ð½Ð°, Ð¾ÑÐµÐ»Ñ Ð¸Ð»Ð¸ Ð´ÑÑÐ³Ð¾Ð³Ð¾ Ð¿ÑÐ¾ÐµÐºÑÐ°?"
        )


async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÐ¾Ð±Ð°Ð²Ð¸ÑÑ Ð·Ð½Ð°Ð½Ð¸Ñ Ð² Ð±Ð°Ð·Ñ. Ð¢Ð¾Ð»ÑÐºÐ¾ Ð´Ð»Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ°."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    text = update.message.text.replace("/teach", "").strip()
    if not text:
        await update.message.reply_text(
            "ð *ÐÐ°Ðº Ð´Ð¾Ð±Ð°Ð²Ð¸ÑÑ Ð·Ð½Ð°Ð½Ð¸Ðµ:*\n\n"
            "`/teach Ð²Ð¾Ð¿ÑÐ¾Ñ: ÑÐºÐ¾Ð»ÑÐºÐ¾ ÑÑÐ¾Ð¸Ñ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ°?\nÐ¾ÑÐ²ÐµÑ: Ð¾Ñ 3000 â½ Ð´Ð¾ ÐÐ¾ÑÐºÐ²Ñ`\n\n"
            "ÐÐ»Ð¸ Ð¿ÑÐ¾ÑÑÐ¾:\n"
            "`/teach ÐÑÐ»Ð¸ ÐºÐ»Ð¸ÐµÐ½Ñ ÑÐ¿ÑÐ°ÑÐ¸Ð²Ð°ÐµÑ Ð¿ÑÐ¾ ÑÐ°ÑÑÑÐ¾ÑÐºÑ â Ð¾ÑÐ²ÐµÑÐ°Ð¹ ÑÑÐ¾ ÑÐ°Ð±Ð¾ÑÐ°ÐµÐ¼ Ñ Ð±Ð°Ð½ÐºÐ¾Ð¼ Ð¢Ð¸Ð½ÑÐºÐ¾ÑÑ, ÑÐ°ÑÑÑÐ¾ÑÐºÐ° 0% Ð½Ð° 12 Ð¼ÐµÑÑÑÐµÐ²`",
            parse_mode="Markdown"
        )
        return

    entry = f"[{datetime.now():%d.%m.%Y}] {text}"
    save_knowledge(entry)
    logger.info(f"Knowledge added: {text[:80]}")
    await update.message.reply_text(f"â ÐÐ¾Ð±Ð°Ð²Ð»ÐµÐ½Ð¾ Ð² Ð±Ð°Ð·Ñ Ð·Ð½Ð°Ð½Ð¸Ð¹ Ð®Ð»Ð¸:\n\n_{text[:200]}_", parse_mode="Markdown")


async def cmd_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÐ¾ÐºÐ°Ð·Ð°ÑÑ ÑÐµÐºÑÑÑÑ Ð±Ð°Ð·Ñ Ð·Ð½Ð°Ð½Ð¸Ð¹. Ð¢Ð¾Ð»ÑÐºÐ¾ Ð´Ð»Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ°."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    knowledge = load_knowledge()
    if not knowledge:
        await update.message.reply_text("ÐÐ°Ð·Ð° Ð·Ð½Ð°Ð½Ð¸Ð¹ Ð¿ÑÑÑÐ°. ÐÑÐ¿Ð¾Ð»ÑÐ·ÑÐ¹ /teach ÑÑÐ¾Ð±Ñ Ð´Ð¾Ð±Ð°Ð²Ð¸ÑÑ.")
    else:
        await update.message.reply_text(f"ð *ÐÐ°Ð·Ð° Ð·Ð½Ð°Ð½Ð¸Ð¹:*\n\n{knowledge[:3000]}", parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialogs[update.effective_user.id] = []
    await update.message.reply_text("ÐÐ¸Ð°Ð»Ð¾Ð³ ÑÐ±ÑÐ¾ÑÐµÐ½.")


def detect_owner_intent(text: str) -> str | None:
    """ÐÐ¿ÑÐµÐ´ÐµÐ»Ð¸ÑÑ Ð½Ð°Ð¼ÐµÑÐµÐ½Ð¸Ðµ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° Ð¸Ð· ÑÐ²Ð¾Ð±Ð¾Ð´Ð½Ð¾Ð³Ð¾ ÑÐµÐºÑÑÐ°. ÐÐµÑÐ½ÑÑÑ ÑÐ¸Ð¿ Ð¸Ð»Ð¸ None."""
    t = text.lower().strip()

    # ÐÐ°Ð¼ÐµÑÐµÐ½Ð¸Ðµ: Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð¸ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ Ð¿Ð¾ÑÑ
    post_triggers = [
        "Ð½Ð°Ð¿Ð¸ÑÐ¸ Ð¿Ð¾ÑÑ", "ÑÐ´ÐµÐ»Ð°Ð¹ Ð¿Ð¾ÑÑ", "Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹ Ð¿Ð¾ÑÑ", "Ð·Ð°Ð¿Ð¾ÑÑÐ¸", "Ð¿Ð¾ÑÑ Ð¿ÑÐ¾",
        "Ð¿Ð¾ÑÑ Ð¾ ", "Ð½Ð°Ð¿Ð¸ÑÐ¸ Ð¾ ", "Ð½Ð°Ð¿Ð¸ÑÐ¸ Ð¿ÑÐ¾ ", "ÑÐ´ÐµÐ»Ð°Ð¹ Ð°Ð½Ð¾Ð½Ñ", "Ð½Ð°Ð¿Ð¸ÑÐ¸ Ð°Ð½Ð¾Ð½Ñ",
        "ÑÐ´ÐµÐ»Ð°Ð¹ Ð¾Ð±ÑÑÐ²Ð»ÐµÐ½Ð¸Ðµ", "Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹:", "Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹ ÑÐµÐºÑÑ", "Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð¿Ð¾ÑÑ",
        "ÑÐ¾Ð·Ð´Ð°Ð¹ Ð¿Ð¾ÑÑ", "Ð½Ð¾Ð²ÑÐ¹ Ð¿Ð¾ÑÑ"
    ]
    if any(t.startswith(tr) or tr in t for tr in post_triggers):
        return "post"

    # ÐÐ°Ð¼ÐµÑÐµÐ½Ð¸Ðµ: Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ Ð³Ð¾ÑÐ¾Ð²ÑÐ¹ ÑÐµÐºÑÑ Ð½Ð°Ð¿ÑÑÐ¼ÑÑ
    direct_triggers = ["Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹: ", "Ð² ÐºÐ°Ð½Ð°Ð»: ", "Ð¿Ð¾ÑÑ: "]
    if any(t.startswith(tr) for tr in direct_triggers):
        return "direct_post"

    # ÐÐ°Ð¼ÐµÑÐµÐ½Ð¸Ðµ: Ð¾Ð±ÑÑÐ¸ÑÑ Ð±Ð¾ÑÐ°
    teach_triggers = [
        "Ð·Ð°Ð¿Ð¾Ð¼Ð½Ð¸:", "Ð·Ð°Ð¿Ð¾Ð¼Ð½Ð¸,", "Ð·Ð°Ð¿Ð¾Ð¼Ð½Ð¸ ÑÑÐ¾", "Ð´Ð¾Ð±Ð°Ð²Ñ Ð² Ð±Ð°Ð·Ñ", "Ð¾Ð±ÑÑÐ¸",
        "ÑÐ»Ñ Ð´Ð¾Ð»Ð¶Ð½Ð° Ð·Ð½Ð°ÑÑ", "ÑÐ»Ñ Ð¾ÑÐ²ÐµÑÐ°ÐµÑ", "ÐµÑÐ»Ð¸ ÑÐ¿ÑÐ¾ÑÑÑ Ð¿ÑÐ¾",
        "Ð¾ÑÐ²ÐµÑ Ð½Ð° Ð²Ð¾Ð¿ÑÐ¾Ñ", "Ñaq:", "Ð²Ð¾Ð¿ÑÐ¾Ñ:", "ÑÐºÐ°Ð¶Ð¸ ÐºÐ»Ð¸ÐµÐ½ÑÐ°Ð¼"
    ]
    if any(t.startswith(tr) or tr in t for tr in teach_triggers):
        return "teach"

    return None




def load_history_from_amo(tg_id: int) -> bool:
    """ÐÐ°Ð³ÑÑÐ·Ð¸ÑÑ Ð¸ÑÑÐ¾ÑÐ¸Ñ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð° Ð¸Ð· amoCRM Ð¿ÑÐ¸ ÑÐµÑÑÐ°ÑÑÐµ Ð±Ð¾ÑÐ°."""
    if tg_id in dialogs and dialogs[tg_id]:
        return False
    cache = _amo_client_cache.get(tg_id)
    if not cache:
        return False
    lead_id = cache.get("lead_id", 0)
    if not lead_id:
        return False
    try:
        r = amo_request("GET", f"leads/{lead_id}/notes?limit=30&order[id]=desc")
        notes = r.get("_embedded", {}).get("notes", [])
        history = []
        for note in reversed(notes):
            text = note.get("params", {}).get("text", "")
            if not text:
                continue
            for line in text.strip().split("\n"):
                if "ð¤" in line[:5] and ": " in line:
                    c = line.split(": ", 1)[1].strip()
                    if c:
                        history.append({"role": "user", "content": c})
                elif "ð¤ Ð®Ð»Ñ: " in line[:12]:
                    c = line.split("Ð®Ð»Ñ: ", 1)[-1].strip()
                    if c:
                        history.append({"role": "assistant", "content": c})
        if history:
            dialogs[tg_id] = history[-MAX_HISTORY:]
            logger.info(f"ÐÑÑÐ¾ÑÐ¸Ñ Ð¸Ð· amoCRM Ð´Ð»Ñ {tg_id}: {len(history)} ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ð¹")
            return True
    except Exception as e:
        logger.error(f"load_history_from_amo error: {e}")
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    name = user.full_name or "ÐÐ»Ð¸ÐµÐ½Ñ"

    logger.info(f"[{user.id}] {name}: {text}")

    # ââ ÐÐ»Ð°Ð´ÐµÐ»ÐµÑ: ÑÐ°ÑÐ¿Ð¾Ð·Ð½Ð°ÑÐ¼ Ð½Ð°Ð¼ÐµÑÐµÐ½Ð¸Ðµ Ð±ÐµÐ· ÐºÐ¾Ð¼Ð°Ð½Ð´ ââââââââââââââââââââââââââââââ
    if is_owner(user):
        intent = detect_owner_intent(text)

        if intent == "post":
            # ÐÐµÐ½ÐµÑÐ¸ÑÑÐµÐ¼ Ð¿Ð¾ÑÑ ÑÐµÑÐµÐ· AI Ð¸ Ð¿ÑÐ±Ð»Ð¸ÐºÑÐµÐ¼
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            prompt = f"""ÐÐ°Ð¿Ð¸ÑÐ¸ Ð¿ÑÐ¾Ð´Ð°ÑÑÐ¸Ð¹ Ð¿Ð¾ÑÑ Ð´Ð»Ñ Telegram-ÐºÐ°Ð½Ð°Ð»Ð° KOKAHOUSE.
Ð¢ÐµÐ¼Ð°: {text}
Ð¢ÑÐµÐ±Ð¾Ð²Ð°Ð½Ð¸Ñ: 3-4 Ð°Ð±Ð·Ð°ÑÐ°, Ð¶Ð¸Ð²Ð¾Ð¹ ÑÑÐ¸Ð»Ñ, ÑÐµÐ½Ñ ÐµÑÐ»Ð¸ Ð·Ð½Ð°ÐµÑÑ, Ð² ÐºÐ¾Ð½ÑÐµ Ð¿ÑÐ¸Ð·ÑÐ² Ð¿Ð¸ÑÐ°ÑÑ @kokahouse_Yulia.
2-3 emoji ÑÐ¼ÐµÑÑÐ½Ð¾. Ð¤Ð¾ÑÐ¼Ð°ÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ Markdown. ÐÐµÐ· ÑÑÑÑÐµÐ³Ð¾Ð².
ÐÐµÑÐ½Ð¸ Ð¢ÐÐÐ¬ÐÐ ÑÐµÐºÑÑ Ð¿Ð¾ÑÑÐ°."""
            response = ai.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            post_text = response.content[0].text.strip()
            context.user_data["pending_post"] = post_text
            await update.message.reply_text(
                f"ð ÐÑÐµÐ²ÑÑ Ð¿Ð¾ÑÑÐ°:\n\n{post_text}\n\n"
                f"ÐÐ°Ð¿Ð¸ÑÐ¸ 'Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹' Ð¸Ð»Ð¸ /confirm ÑÑÐ¾Ð±Ñ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ Ð² ÐºÐ°Ð½Ð°Ð»."
            )
            return

        if intent == "direct_post":
            # ÐÑÐ±Ð»Ð¸ÐºÑÐµÐ¼ ÑÐµÐºÑÑ Ð½Ð°Ð¿ÑÑÐ¼ÑÑ
            for prefix in ["Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹: ", "Ð² ÐºÐ°Ð½Ð°Ð»: ", "Ð¿Ð¾ÑÑ: "]:
                if text.lower().startswith(prefix):
                    post_text = text[len(prefix):]
                    break
            else:
                post_text = text
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                await update.message.reply_text("â ÐÐ¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½Ð¾ Ð² ÐºÐ°Ð½Ð°Ð»Ðµ!")
            except Exception as e:
                await update.message.reply_text(f"â ÐÑÐ¸Ð±ÐºÐ°: {e}")
            return

        if intent == "teach":
            entry = f"[{datetime.now():%d.%m.%Y}] {text}"
            save_knowledge(entry)
            await update.message.reply_text(f"â ÐÐ°Ð¿Ð¾Ð¼Ð½Ð¸Ð»Ð°:\n\n{text[:200]}")
            return

        # ÐÐ»Ð°Ð´ÐµÐ»ÐµÑ Ð½Ð°Ð¿Ð¸ÑÐ°Ð» "Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹" â Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ¶Ð´ÐµÐ½Ð¸Ðµ pending Ð¿Ð¾ÑÑÐ°
        if text.lower().strip() in ["Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹", "Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ´Ð¸", "Ð¾Ðº Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹", "Ð´Ð° Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹", "Ð¿ÑÐ±Ð»Ð¸ÐºÑÐ¹!"]:
            post_text = context.user_data.get("pending_post")
            if post_text:
                try:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("â ÐÐ¾ÑÑ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½ Ð² ÐºÐ°Ð½Ð°Ð»Ðµ!")
                except Exception:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("â ÐÐ¾ÑÑ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½!")
            else:
                await update.message.reply_text("ÐÐµÑ Ð¿Ð¾ÑÑÐ° Ð´Ð»Ñ Ð¿ÑÐ±Ð»Ð¸ÐºÐ°ÑÐ¸Ð¸. Ð¡Ð½Ð°ÑÐ°Ð»Ð° Ð¿Ð¾Ð¿ÑÐ¾ÑÐ¸ Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð¿Ð¾ÑÑ.")
            return

        # ââ Director Mode â Ð²ÑÑ Ð¾ÑÑÐ°Ð»ÑÐ½Ð¾Ðµ Ð¾Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° Ð¸Ð´ÑÑ Ðº AI-Ð´Ð¸ÑÐµÐºÑÐ¾ÑÑ ââââââ
        await handle_owner_director(update, context, text)
        return

    # ââ ÐÑÐ¾Ð²ÐµÑÐºÐ° Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ¶Ð´ÐµÐ½Ð¸Ñ ÐÐ Ð¾Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ° ââââââââââââââââââââââââââââââââââ
    if user.id in pending_kp and text.strip().lower() in [
        "Ð´Ð°", "Ð´Ð°!", "yes", "Ð¿Ð¾Ð´ÑÐ¾Ð´Ð¸Ñ", "ÑÐ¾Ð³Ð»Ð°ÑÐµÐ½", "ÑÐ¾Ð³Ð»Ð°ÑÐ½Ð°",
        "Ð¾ÑÐ»Ð¸ÑÐ½Ð¾", "ÑÐ¾ÑÐ¾ÑÐ¾", "Ð±ÐµÑÑÐ¼", "Ð±ÐµÑÐµÐ¼", "Ð¾Ðº", "ok", "ð"
    ]:
        kp_data = pending_kp[user.id]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")
        try:
            client_name = user.full_name or "ÐÐ»Ð¸ÐµÐ½Ñ"
            pdf_bytes = await generate_kp_pdf(kp_data, client_name)
            filename = f"ÐÐ_ALTA_CASA_{datetime.now().strftime('%d%m%Y')}.pdf"

            # ÐÑÐ¿ÑÐ°Ð²Ð»ÑÐµÐ¼ PDF ÐºÐ»Ð¸ÐµÐ½ÑÑ
            from telegram import InputFile
            import io
            await context.bot.send_document(
                chat_id=user.id,
                document=InputFile(io.BytesIO(pdf_bytes), filename=filename),
                caption=f"ÐÐ¾Ð¼Ð¼ÐµÑÑÐµÑÐºÐ¾Ðµ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ KOKAHOUSE\n{kp_data['product']}\nÐÑÐ¾Ð³Ð¾: {kp_data['total']:,} â½".replace(',', ' ')
            )

            # Ð£Ð²ÐµÐ´Ð¾Ð¼Ð»ÑÐµÐ¼ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÐ°
            if kp_data.get("manager_id"):
                await context.bot.send_message(
                    chat_id=kp_data["manager_id"],
                    text=f"â ÐÐ»Ð¸ÐµÐ½Ñ {client_name} (ID: {user.id}) Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ´Ð¸Ð» ÐÐ!\nÐÐ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾."
                )

            del pending_kp[user.id]
            logger.info(f"ÐÐ PDF Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½ ÐºÐ»Ð¸ÐµÐ½ÑÑ {user.id}")
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            await update.message.reply_text(
                "ÐÑÐ»Ð¸ÑÐ½Ð¾! ÐÐµÑÐµÐ´Ð°Ñ Ð²Ð°ÑÑ Ð·Ð°ÑÐ²ÐºÑ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÑ â Ð¾Ð½ ÑÐ²ÑÐ¶ÐµÑÑÑ Ñ Ð²Ð°Ð¼Ð¸ Ð² Ð±Ð»Ð¸Ð¶Ð°Ð¹ÑÐµÐµ Ð²ÑÐµÐ¼Ñ."
            )
        return
    import re
    urls_in_text = re.findall(r'https?://[^\s]+', text)
    has_external_link = any(
        "kokahouse.ru" not in url and "t.me" not in url and "max.ru" not in url
        for url in urls_in_text
    )
    # ÐÑÐ»Ð¸ ÐµÑÑÑ Ð²Ð½ÐµÑÐ½ÑÑ ÑÑÑÐ»ÐºÐ° â Ð´Ð¾Ð±Ð°Ð²Ð¸Ð¼ Ð¿Ð¾Ð´ÑÐºÐ°Ð·ÐºÑ Ð² Ð¿ÑÐ¾Ð¼Ñ Ð´Ð»Ñ Claude
    extra_context = ""
    if has_external_link:
        extra_context = "\n[Ð¡ÐÐ¡Ð¢ÐÐÐ: ÐºÐ»Ð¸ÐµÐ½Ñ Ð¿ÑÐ¸ÑÐ»Ð°Ð» ÑÑÑÐ»ÐºÑ ÐÐ Ñ Ð½Ð°ÑÐµÐ³Ð¾ ÑÐ°Ð¹ÑÐ°. ÐÑÐ¸Ð¼ÐµÐ½ÑÐ¹ Ð¿ÑÐ°Ð²Ð¸Ð»Ð¾ ÑÑÐºÐ°Ð»Ð°ÑÐ¸Ð¸ Ð´Ð»Ñ Ð²Ð½ÐµÑÐ½Ð¸Ñ ÑÑÑÐ»Ð¾Ðº.]"

    # ââ ÐÐ±ÑÑÐ½ÑÐ¹ ÐºÐ»Ð¸ÐµÐ½Ñ âââââââââââââââââââââââââââââââââââââââââââââââââââââââââ


    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    load_history_from_amo(user.id)
    result = ask_claude(user.id, text + extra_context)

    # ÐÑÐ»Ð¸ Ð²Ð½ÐµÑÐ½ÑÑ ÑÑÑÐ»ÐºÐ° â ÑÐ¸ÑÐ¾ ÑÐ¾ÑÐ²Ð°ÑÐ´Ð¸Ð¼ ÑÐµÐ±Ðµ (Ð±ÐµÐ· ÑÑÐºÐ°Ð»Ð°ÑÐ¸Ð¸ Ð² ÑÐ°Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°)
    if has_external_link and MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=(
                    f"ð ÐÐ»Ð¸ÐµÐ½Ñ {user.full_name} Ð¿ÑÐ¸ÑÐ»Ð°Ð» Ð²Ð½ÐµÑÐ½ÑÑ ÑÑÑÐ»ÐºÑ:\n\n"
                    f"{text[:500]}\n\n"
                    f"ÐÑÐ²ÐµÑÑ ÑÐµÑÐµÐ·: `Ð¾ÑÐ²ÐµÑÑ {user.full_name} [ÑÐ²Ð¾Ð¹ ÑÐµÐºÑÑ]`"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
        # ÐÐ ÑÑÐ°Ð²Ð¸Ð¼ escalate=True â Ð®Ð»Ñ Ð¿ÑÐ¾Ð´Ð¾Ð»Ð¶Ð°ÐµÑ Ð²ÐµÑÑÐ¸ Ð´Ð¸Ð°Ð»Ð¾Ð³

    await _send_and_update(update, context, user, result, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÐ±ÑÐ°Ð±Ð¾ÑÐºÐ° ÑÐ¾ÑÐ¾ Ð¾Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°."""
    user = update.effective_user
    name = user.full_name or "ÐÐ»Ð¸ÐµÐ½Ñ"
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [Ð¤ÐÐ¢Ð] {caption}")



    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # ÐÐµÑÑÐ¼ Ð½Ð°Ð¸Ð±Ð¾Ð»ÑÑÐµÐµ ÑÐ°Ð·ÑÐµÑÐµÐ½Ð¸Ðµ ÑÐ¾ÑÐ¾
        photo = update.message.photo[-1]
        image_data = await download_photo(context.bot, photo.file_id)
        prompt = caption if caption else "ÐÐ»Ð¸ÐµÐ½Ñ Ð¿ÑÐ¸ÑÐ»Ð°Ð» ÑÐ¾ÑÐ¾ ÑÐ¾Ð²Ð°ÑÐ° ÐºÐ¾ÑÐ¾ÑÑÐ¹ ÑÐ¾ÑÐµÑ Ð½Ð°Ð¹ÑÐ¸ Ð¸Ð»Ð¸ ÐºÑÐ¿Ð¸ÑÑ. ÐÑÐ²ÐµÑÑ ÑÐ¾Ð³Ð»Ð°ÑÐ½Ð¾ Ð¿ÑÐ°Ð²Ð¸Ð»Ð°Ð¼ ÑÐ°Ð±Ð¾ÑÑ Ñ ÑÐ¾ÑÐ¾."
        load_history_from_amo(user.id)
        result = ask_claude(user.id, prompt, image_data=image_data)
        # Ð¤Ð¾ÑÐ¾ Ð¾Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð²ÑÐµÐ³Ð´Ð° ÑÑÐºÐ°Ð»Ð¸ÑÑÐµÐ¼ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÑ
        result["escalate"] = True
    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        result = {"reply": "ÐÐ¾Ð»ÑÑÐ¸Ð»Ð° Ð²Ð°ÑÐµ ÑÐ¾ÑÐ¾! Ð£ÑÐ¾ÑÐ½Ð¸ÑÐµ, ÑÑÐ¾ Ð¸Ð¼ÐµÐ½Ð½Ð¾ Ð²Ð°Ñ Ð¸Ð½ÑÐµÑÐµÑÑÐµÑ?",
                  "qualification": None, "interest": None, "budget": None, "escalate": False}

    await _send_and_update(update, context, user, result, f"[Ð¤ÐÐ¢Ð] {caption}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÐ±ÑÐ°Ð±Ð¾ÑÐºÐ° Ð´Ð¾ÐºÑÐ¼ÐµÐ½ÑÐ¾Ð²/ÑÐ°Ð¹Ð»Ð¾Ð²."""
    user = update.effective_user
    name = user.full_name or "ÐÐ»Ð¸ÐµÐ½Ñ"
    doc  = update.message.document
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [Ð¤ÐÐÐ] {doc.file_name}")



    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"ÐÐ»Ð¸ÐµÐ½Ñ Ð¿ÑÐ¸ÑÐ»Ð°Ð» ÑÐ°Ð¹Ð» '{doc.file_name}'"
    if caption:
        prompt += f" Ñ Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÑ: {caption}"
    prompt += ". ÐÑÐ²ÐµÑÑ ÐºÐ°Ðº Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑ â ÑÑÐ¾ÑÐ½Ð¸ ÑÑÐ¾ ÑÑÐ¾ Ð¸ ÐºÐ°Ðº Ð¼Ð¾Ð¶ÐµÑÑ Ð¿Ð¾Ð¼Ð¾ÑÑ."

    load_history_from_amo(user.id)
    result = ask_claude(user.id, prompt)
    await _send_and_update(update, context, user, result, f"[Ð¤ÐÐÐ] {doc.file_name}")


async def _send_and_update(update, context, user, result, original_text):
    """ÐÑÐ¿ÑÐ°Ð²Ð¸ÑÑ Ð¾ÑÐ²ÐµÑ ÐºÐ»Ð¸ÐµÐ½ÑÑ Ð¸ Ð¾Ð±Ð½Ð¾Ð²Ð¸ÑÑ Notion."""
    # Ð£Ð²ÐµÐ´Ð¾Ð¼Ð¸ÑÑ Ð¼ÐµÐ½ÐµÐ´Ð¶ÐµÑÐ° Ð¿ÑÐ¸ ÑÑÐºÐ°Ð»Ð°ÑÐ¸Ð¸ â Ð¢ÐÐÐ¬ÐÐ ÐÐÐÐ Ð ÐÐ Ð½Ð° ÐºÐ»Ð¸ÐµÐ½ÑÐ°
    if result["escalate"] and MANAGER_CHAT_ID and user.id not in _escalated_clients:
        try:
            # Ð¡Ð¾Ð±Ð¸ÑÐ°ÐµÐ¼ Ð¸ÑÑÐ¾ÑÐ¸Ñ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð° Ð´Ð»Ñ ÐºÐ¾Ð½ÑÐµÐºÑÑÐ°
            history = dialogs.get(user.id, [])
            def clean_msg(text: str) -> str:
                """Ð£Ð±ÑÐ°ÑÑ JSON Ð±Ð»Ð¾ÐºÐ¸ Ð¸Ð· ÑÐµÐºÑÑÐ°."""
                import re as _re
                text = _re.sub(r'```json.*?```', '', text, flags=_re.DOTALL)
                return text.strip()[:150]

            dialog_summary = "\n".join(
                f"{'ð¤' if m['role'] == 'user' else 'ð¤'} {clean_msg(m['content']) if isinstance(m['content'], str) else '[Ð¼ÐµÐ´Ð¸Ð°]'}"
                for m in history[-6:]
                if isinstance(m.get('content'), str) and m['content'].strip()
            )
            interest = result.get("interest") or "Ð½Ðµ ÑÐºÐ°Ð·Ð°Ð½"
            budget = f"{int(result['budget']):,} â½".replace(",", " ") if result.get("budget") else "Ð½Ðµ ÑÐºÐ°Ð·Ð°Ð½"
            qualification = result.get("qualification") or "ÐÐ¾ÑÑÑÐ¸Ð¹"

            msg = (
                f"ð¥ ÐÐ¾ÑÑÑÐ¸Ð¹ Ð»Ð¸Ð´!\n\n"
                f"ð¤ ÐÐ»Ð¸ÐµÐ½Ñ: {user.full_name}\n"
                f"ð± TG: @{user.username or 'Ð½ÐµÑ'} | ID: {user.id}\n"
                f"ð ÐÐ½ÑÐµÑÐµÑ: {interest}\n"
                f"ð° ÐÑÐ´Ð¶ÐµÑ: {budget}\n"
                f"ð Ð¡ÑÐ°ÑÑÑ: {qualification}\nð amoCRM: https://yaninve7.amocrm.ru/leads/detail/{_amo_client_cache.get(user.id, {}).get('lead_id', '?')}\n\n"
                f"ð ÐÑÐ¸ÑÐ¸Ð½Ð°:\n{result.get('reply','')[:200]}\n\nð¬ ÐÐ¸Ð°Ð»Ð¾Ð³:\n{dialog_summary}"
            )
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=msg
            )
            # ÐÐ¾Ð¼ÐµÑÐ°ÐµÐ¼ ÑÑÐ¾ ÑÐ¶Ðµ ÑÐ²ÐµÐ´Ð¾Ð¼Ð¸Ð»Ð¸ â Ð½Ðµ Ð±ÑÐ´ÐµÐ¼ ÑÐ¿Ð°Ð¼Ð¸ÑÑ
            _escalated_clients.add(user.id)
        except Exception as e:
            logger.error(f"Escalation notify error: {e}")



    # Ð¡Ð¸Ð½ÑÑÐ¾Ð½Ð¸Ð·Ð°ÑÐ¸Ñ Ñ amoCRM
    if not is_owner(user):
        try:
            sync_to_amo(
                tg_id=user.id,
                name=user.full_name or "ÐÐ»Ð¸ÐµÐ½Ñ",
                username=user.username or "",
                message_text=original_text[:500],
                bot_reply=result["reply"][:500],
                qualification=result.get("qualification"),
                interest=result.get("interest"),
                budget=int(result["budget"]) if result.get("budget") else None
            )
        except Exception as e:
            logger.error(f"amoCRM sync exception: {e}")

    # ÐÑÐ²ÐµÑÐ¸ÑÑ ÐºÐ»Ð¸ÐµÐ½ÑÑ
    await update.message.reply_text(result["reply"])


# ââ ÐÐ°Ð½Ð°Ð»: ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° ââââââââââââââââââââââââââââââââââââââââââââââââââ

def is_owner(user) -> bool:
    return str(user.id) == str(MANAGER_CHAT_ID)


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/post <ÑÐµÐºÑÑ> â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ ÑÐµÐºÑÑ Ð² ÐºÐ°Ð½Ð°Ð»."""
    if not is_owner(update.effective_user):
        return

    text = update.message.text.replace("/post", "").strip()
    if not text:
        await update.message.reply_text(
            "ð¢ *ÐÐ¾Ð¼Ð°Ð½Ð´Ñ Ð´Ð»Ñ ÐºÐ°Ð½Ð°Ð»Ð°:*\n\n"
            "`/post Ð¢ÐµÐºÑÑ Ð¿Ð¾ÑÑÐ°` â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ ÑÐµÐºÑÑ\n"
            "`/post_photo` + Ð¿ÑÐ¸ÐºÑÐµÐ¿Ð¸ ÑÐ¾ÑÐ¾ Ñ Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÑ â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ ÑÐ¾ÑÐ¾\n"
            "`/ai_post Ð¢ÐµÐ¼Ð°` â Claude ÑÐ°Ð¼ Ð½Ð°Ð¿Ð¸ÑÐµÑ Ð¿Ð¾ÑÑ Ð¿Ð¾ ÑÐµÐ¼Ðµ\n"
            "`/forward` â Ð¿ÐµÑÐµÑÐ»Ð¸ Ð»ÑÐ±Ð¾Ðµ ÑÐ¾Ð¾Ð±ÑÐµÐ½Ð¸Ðµ Ð±Ð¾ÑÑ Ð¸ Ð¾ÑÐ²ÐµÑÑ /forward\n"
            "`/channel` â Ð¿Ð¾ÐºÐ°Ð·Ð°ÑÑ ID ÐºÐ°Ð½Ð°Ð»Ð°",
            parse_mode="Markdown"
        )
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
        await update.message.reply_text(f"â ÐÐ¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½Ð¾ Ð² {CHANNEL_ID}\n[ÐÐ¾ÑÐ¼Ð¾ÑÑÐµÑÑ](https://t.me/{CHANNEL_ID.lstrip('@')}/{msg.message_id})", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"â ÐÑÐ¸Ð±ÐºÐ°: {e}")


async def cmd_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ai_post <ÑÐµÐ¼Ð°> â Claude Ð¿Ð¸ÑÐµÑ Ð¿Ð¾ÑÑ Ð¸ Ð¿ÑÐ±Ð»Ð¸ÐºÑÐµÑ Ð² ÐºÐ°Ð½Ð°Ð»."""
    if not is_owner(update.effective_user):
        return

    topic = update.message.text.replace("/ai_post", "").strip()
    if not topic:
        await update.message.reply_text("Ð£ÐºÐ°Ð¶Ð¸ ÑÐµÐ¼Ñ: `/ai_post Ð´Ð¸Ð²Ð°Ð½ MC-A68 Ð¸Ð· Ð¸ÑÐ°Ð»ÑÑÐ½ÑÐºÐ¾Ð¹ ÐºÐ¾Ð¶Ð¸`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"""ÐÐ°Ð¿Ð¸ÑÐ¸ Ð¿ÑÐ¾Ð´Ð°ÑÑÐ¸Ð¹ Ð¿Ð¾ÑÑ Ð´Ð»Ñ Telegram-ÐºÐ°Ð½Ð°Ð»Ð° Ð¼ÐµÐ±ÐµÐ»ÑÐ½Ð¾Ð¹ ÐºÐ¾Ð¼Ð¿Ð°Ð½Ð¸Ð¸ KOKAHOUSE.

Ð¢ÐµÐ¼Ð°/ÑÐ¾Ð²Ð°Ñ: {topic}

Ð¢ÑÐµÐ±Ð¾Ð²Ð°Ð½Ð¸Ñ:
â 3-5 Ð°Ð±Ð·Ð°ÑÐµÐ², Ð¶Ð¸Ð²Ð¾Ð¹ ÑÑÐ¸Ð»Ñ
â Ð£Ð¿Ð¾Ð¼ÑÐ½Ð¸ Ð¼Ð°ÑÐµÑÐ¸Ð°Ð»Ñ, Ð¿ÑÐ¾Ð¸Ð·Ð²Ð¾Ð´ÑÑÐ²Ð¾ Ð² ÐÐ¸ÑÐ°Ðµ, ÑÐµÐ½Ñ ÐµÑÐ»Ð¸ Ð·Ð½Ð°ÐµÑÑ
â Ð ÐºÐ¾Ð½ÑÐµ: Ð¿ÑÐ¸Ð·ÑÐ² Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð² Ð»Ð¸ÑÐºÑ Ð±Ð¾ÑÑ @kokahouse_Yulia
â Emoji ÑÐ¼ÐµÑÑÐ½Ð¾ (1-3 ÑÑÑÐºÐ¸)
â ÐÐµÐ· ÑÑÑÑÐµÐ³Ð¾Ð²
â Ð¤Ð¾ÑÐ¼Ð°ÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ Markdown (Ð¶Ð¸ÑÐ½ÑÐ¹, ÐºÑÑÑÐ¸Ð²)

ÐÐµÑÐ½Ð¸ Ð¢ÐÐÐ¬ÐÐ ÑÐµÐºÑÑ Ð¿Ð¾ÑÑÐ°, Ð±ÐµÐ· Ð¿Ð¾ÑÑÐ½ÐµÐ½Ð¸Ð¹."""

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    post_text = response.content[0].text.strip()

    # Ð¡Ð½Ð°ÑÐ°Ð»Ð° Ð¿Ð¾ÐºÐ°Ð·ÑÐ²Ð°ÐµÐ¼ Ð¿ÑÐµÐ²ÑÑ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÑ (Ð±ÐµÐ· parse_mode ÑÑÐ¾Ð±Ñ Ð½Ðµ ÑÐ»Ð¾Ð¼Ð°ÑÑ)
    await update.message.reply_text(
        f"ð ÐÑÐµÐ²ÑÑ Ð¿Ð¾ÑÑÐ°:\n\n{post_text}\n\n"
        f"ÐÑÐ¿ÑÐ°Ð²Ñ /confirm ÑÑÐ¾Ð±Ñ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ, Ð¸Ð»Ð¸ /post <ÑÐµÐºÑÑ> ÑÑÐ¾Ð±Ñ Ð¸Ð·Ð¼ÐµÐ½Ð¸ÑÑ"
    )
    # Ð¡Ð¾ÑÑÐ°Ð½ÑÐµÐ¼ Ð² ÐºÐ¾Ð½ÑÐµÐºÑÑ Ð´Ð»Ñ Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ¶Ð´ÐµÐ½Ð¸Ñ
    context.user_data["pending_post"] = post_text


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/confirm â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ð¹ ai_post."""
    if not is_owner(update.effective_user):
        return

    post_text = context.user_data.get("pending_post")
    if not post_text:
        await update.message.reply_text("ÐÐµÑ Ð¿Ð¾ÑÑÐ° Ð´Ð»Ñ Ð¿ÑÐ±Ð»Ð¸ÐºÐ°ÑÐ¸Ð¸. Ð¡Ð½Ð°ÑÐ°Ð»Ð° Ð¸ÑÐ¿Ð¾Ð»ÑÐ·ÑÐ¹ /ai_post.")
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        context.user_data.pop("pending_post", None)
        await update.message.reply_text(f"â ÐÐ¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½Ð¾!", parse_mode="Markdown")
    except Exception as e:
        # ÐÑÐ»Ð¸ Markdown ÑÐ»Ð¾Ð¼Ð°Ð½ â Ð¿ÑÐ±Ð»Ð¸ÐºÑÐµÐ¼ Ð±ÐµÐ· ÑÐ¾ÑÐ¼Ð°ÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¸Ñ
        try:
            msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            context.user_data.pop("pending_post", None)
            await update.message.reply_text("â ÐÐ¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½Ð¾ (Ð±ÐµÐ· Markdown).")
        except Exception as e2:
            await update.message.reply_text(f"â ÐÑÐ¸Ð±ÐºÐ°: {e2}")


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/channel â Ð¿Ð¾ÐºÐ°Ð·Ð°ÑÑ ÑÐµÐºÑÑÐ¸Ð¹ ÐºÐ°Ð½Ð°Ð»."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(f"ð¢ Ð¢ÐµÐºÑÑÐ¸Ð¹ ÐºÐ°Ð½Ð°Ð»: `{CHANNEL_ID}`", parse_mode="Markdown")


async def handle_owner_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÑÐ»Ð¸ Ð²Ð»Ð°Ð´ÐµÐ»ÐµÑ Ð¿ÑÐ¸ÑÑÐ»Ð°ÐµÑ ÑÐ¾ÑÐ¾ Ñ Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÑ /post_photo â Ð¿ÑÐ±Ð»Ð¸ÐºÑÐµÐ¼ Ð² ÐºÐ°Ð½Ð°Ð»."""
    user = update.effective_user
    caption = update.message.caption or ""

    if is_owner(user) and "/post_photo" in caption:
        real_caption = caption.replace("/post_photo", "").strip()
        try:
            photo = update.message.photo[-1]
            msg = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo.file_id,
                caption=real_caption,
                parse_mode="Markdown"
            )
            await update.message.reply_text(f"â Ð¤Ð¾ÑÐ¾ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½Ð¾ Ð² {CHANNEL_ID}!", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"â ÐÑÐ¸Ð±ÐºÐ°: {e}")
        return

    # ÐÐ½Ð°ÑÐµ â Ð¾Ð±ÑÑÐ½Ð°Ñ Ð¾Ð±ÑÐ°Ð±Ð¾ÑÐºÐ° ÑÐ¾ÑÐ¾ Ð¾Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°
    await handle_photo(update, context)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÐÐµÐ½Ñ ÐºÐ¾Ð¼Ð°Ð½Ð´ Ð´Ð»Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ°."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(
        "ð *ÐÐ¾Ð¼Ð°Ð½Ð´Ñ KOKAHOUSE Bot*\n\n"
        "*ð¥ ÐÐ»Ð¸ÐµÐ½ÑÑ:*\n"
        "`/start` â Ð½Ð°ÑÐ°ÑÑ Ð´Ð¸Ð°Ð»Ð¾Ð³\n"
        "`/reset` â ÑÐ±ÑÐ¾ÑÐ¸ÑÑ Ð¸ÑÑÐ¾ÑÐ¸Ñ Ð´Ð¸Ð°Ð»Ð¾Ð³Ð°\n\n"
        "*ð ÐÐ±ÑÑÐµÐ½Ð¸Ðµ Ð®Ð»Ð¸:*\n"
        "`/teach <ÑÐµÐºÑÑ>` â Ð´Ð¾Ð±Ð°Ð²Ð¸ÑÑ Ð·Ð½Ð°Ð½Ð¸Ðµ\n"
        "`/knowledge` â Ð¿Ð¾ÐºÐ°Ð·Ð°ÑÑ Ð±Ð°Ð·Ñ Ð·Ð½Ð°Ð½Ð¸Ð¹\n\n"
        "*ð¢ ÐÐ°Ð½Ð°Ð»:*\n"
        "`/post <ÑÐµÐºÑÑ>` â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ ÑÐµÐºÑÑ\n"
        "`/post_photo` â Ð¿ÑÐ¸ÐºÑÐµÐ¿Ð¸ ÑÐ¾ÑÐ¾ Ñ ÑÑÐ¾Ð¹ Ð¿Ð¾Ð´Ð¿Ð¸ÑÑÑ\n"
        "`/ai_post <ÑÐµÐ¼Ð°>` â Claude Ð½Ð°Ð¿Ð¸ÑÐµÑ Ð¿Ð¾ÑÑ\n"
        "`/confirm` â Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°ÑÑ ai_post\n"
        "`/channel` â Ð¿Ð¾ÐºÐ°Ð·Ð°ÑÑ ÐºÐ°Ð½Ð°Ð»\n\n"
        "*â¹ï¸ Ð¡Ð¿ÑÐ°Ð²ÐºÐ°:*\n"
        "`/menu` â ÑÑÐ¾ Ð¼ÐµÐ½Ñ",
        parse_mode="Markdown"
    )


# ââ ÐÐ (ÐÐ¾Ð¼Ð¼ÐµÑÑÐµÑÐºÐ¾Ðµ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ) ââââââââââââââââââââââââââââââââââââââââââââ

# Ð¥ÑÐ°Ð½Ð¸Ð»Ð¸ÑÐµ Ð¾Ð¶Ð¸Ð´Ð°ÑÑÐ¸Ñ Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ¶Ð´ÐµÐ½Ð¸Ñ ÐÐ: {client_tg_id: {Ð´Ð°Ð½Ð½ÑÐµ ÐÐ}}
pending_kp: dict[int, dict] = {}


async def cmd_kp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /kp <tg_id ÐºÐ»Ð¸ÐµÐ½ÑÐ°> <ÑÐ¾Ð²Ð°Ñ> <ÑÐµÐ½Ð°â½> [Ð´Ð¾ÑÑÐ°Ð²ÐºÐ°â½]
    ÐÑÐ¸Ð¼ÐµÑ: /kp 283951945 "ÐÐ¸Ð²Ð°Ð½ MC-A68 3-Ð¼ÐµÑÑÐ½ÑÐ¹ ÐºÐ¾Ð¶Ð°" 235000 8000
    """
    if not is_owner(update.effective_user):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "ð *ÐÐ°Ðº Ð¾ÑÐ¿ÑÐ°Ð²Ð¸ÑÑ ÐÐ:*\n\n"
            "`/kp <ID_ÐºÐ»Ð¸ÐµÐ½ÑÐ°> <ÑÐ¾Ð²Ð°Ñ> <ÑÐµÐ½Ð°> [Ð´Ð¾ÑÑÐ°Ð²ÐºÐ°]`\n\n"
            "ÐÑÐ¸Ð¼ÐµÑ:\n"
            "`/kp 283951945 ÐÐ¸Ð²Ð°Ð½ MC-A68 3-Ð¼ÐµÑÑÐ½ÑÐ¹ 235000 8000`\n\n"
            "ID ÐºÐ»Ð¸ÐµÐ½ÑÐ° ÑÐ·Ð½Ð°ÑÑ: Ð¿Ð¾Ð¿ÑÐ¾ÑÐ¸ ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð½Ð°Ð¿Ð¸ÑÐ°ÑÑ Ð±Ð¾ÑÑ, "
            "Ð¸Ð»Ð¸ Ð¿Ð¾ÑÐ¼Ð¾ÑÑÐ¸ Ð² Notion â Telegram ID",
            parse_mode="Markdown"
        )
        return

    client_id = int(args[0])
    price = int(args[-2]) if len(args) >= 4 else int(args[-1])
    delivery = int(args[-1]) if len(args) >= 4 else 0
    product = " ".join(args[1:-2]) if len(args) >= 4 else " ".join(args[1:-1])
    total = price + delivery

    # Ð¡Ð¾ÑÑÐ°Ð½ÑÐµÐ¼ Ð² Ð¾Ð¶Ð¸Ð´Ð°Ð½Ð¸Ðµ
    pending_kp[client_id] = {
        "product": product,
        "price": price,
        "delivery": delivery,
        "total": total,
        "manager_id": update.effective_user.id,
        "created_at": datetime.now().isoformat(),
    }

    # ÐÑÐ¿ÑÐ°Ð²Ð»ÑÐµÐ¼ ÐºÐ»Ð¸ÐµÐ½ÑÑ
    try:
        msg = (
            f"ÐÐ´ÑÐ°Ð²ÑÑÐ²ÑÐ¹ÑÐµ!\n\n"
            f"ÐÑ Ð¿Ð¾Ð´Ð³Ð¾ÑÐ¾Ð²Ð¸Ð»Ð¸ ÑÐ°ÑÑÑÑ Ð¿Ð¾ Ð²Ð°ÑÐµÐ¼Ñ Ð·Ð°Ð¿ÑÐ¾ÑÑ:\n\n"
            f"ð¦ *{product}*\n"
            f"ð° Ð¡ÑÐ¾Ð¸Ð¼Ð¾ÑÑÑ: {price:,} â½\n"
        )
        if delivery:
            msg += f"ð ÐÐ¾ÑÑÐ°Ð²ÐºÐ°: {delivery:,} â½\n"
        msg += (
            f"ââââââââââââââ\n"
            f"ðµ *ÐÑÐ¾Ð³Ð¾: {total:,} â½*\n\n"
            f"ÐÐ°Ñ ÑÑÑÑÐ°Ð¸Ð²Ð°ÑÑ ÑÑÐ»Ð¾Ð²Ð¸Ñ? ÐÑÐ²ÐµÑÑÑÐµ *Â«ÐÐ°Â»* â Ð¸ Ñ Ð¿ÑÐ¸ÑÐ»Ñ Ð¿Ð¾Ð»Ð½Ð¾Ðµ ÐºÐ¾Ð¼Ð¼ÐµÑÑÐµÑÐºÐ¾Ðµ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ."
        )
        msg = msg.replace(",", " ")

        await context.bot.send_message(
            chat_id=client_id,
            text=msg,
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            f"â Ð Ð°ÑÑÑÑ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½ ÐºÐ»Ð¸ÐµÐ½ÑÑ (ID: {client_id})\n"
            f"Ð¢Ð¾Ð²Ð°Ñ: {product}\n"
            f"ÐÑÐ¾Ð³Ð¾: {total:,} â½\n\n"
            f"ÐÐ´Ñ Ð¿Ð¾Ð´ÑÐ²ÐµÑÐ¶Ð´ÐµÐ½Ð¸Ñ Ð¾Ñ ÐºÐ»Ð¸ÐµÐ½ÑÐ°...".replace(",", " ")
        )
        logger.info(f"ÐÐ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½Ð¾ ÐºÐ»Ð¸ÐµÐ½ÑÑ {client_id}: {product} {total}â½")
    except Exception as e:
        await update.message.reply_text(f"â ÐÑÐ¸Ð±ÐºÐ° Ð¾ÑÐ¿ÑÐ°Ð²ÐºÐ¸: {e}")


async def generate_kp_pdf(data: dict, client_name: str) -> bytes:
    """ÐÐµÐ½ÐµÑÐ¸ÑÐ¾Ð²Ð°ÑÑ PDF ÐºÐ¾Ð¼Ð¼ÐµÑÑÐµÑÐºÐ¾Ð³Ð¾ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ñ."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    story = []

    # ÐÐ°Ð³Ð¾Ð»Ð¾Ð²Ð¾Ðº
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
                                  fontSize=20, textColor=colors.HexColor('#1a1a2e'),
                                  spaceAfter=6, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=11, textColor=colors.grey, spaceAfter=20)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=11, spaceAfter=8, leading=16)

    story.append(Paragraph("KOKAHOUSE", title_style))
    story.append(Paragraph("ÐÐ¾Ð¼Ð¼ÐµÑÑÐµÑÐºÐ¾Ðµ Ð¿ÑÐµÐ´Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.5*cm))

    # ÐÐ»Ð¸ÐµÐ½Ñ Ð¸ Ð´Ð°ÑÐ°
    story.append(Paragraph(f"<b>ÐÐ»Ñ:</b> {client_name}", body_style))
    story.append(Paragraph(f"<b>ÐÐ°ÑÐ°:</b> {datetime.now().strftime('%d.%m.%Y')}", body_style))
    story.append(Spacer(1, 0.5*cm))

    # Ð¢Ð°Ð±Ð»Ð¸ÑÐ° Ñ ÑÐ¾Ð²Ð°ÑÐ¾Ð¼
    table_data = [
        ['ÐÐ°Ð¸Ð¼ÐµÐ½Ð¾Ð²Ð°Ð½Ð¸Ðµ', 'Ð¡ÑÐ¾Ð¸Ð¼Ð¾ÑÑÑ'],
        [data['product'], f"{data['price']:,} â½".replace(',', ' ')],
    ]
    if data['delivery']:
        table_data.append(['ÐÐ¾ÑÑÐ°Ð²ÐºÐ°', f"{data['delivery']:,} â½".replace(',', ' ')])
    table_data.append(['ÐÐ¢ÐÐÐ', f"{data['total']:,} â½".replace(',', ' ')])

    table = Table(table_data, colWidths=[12*cm, 4*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0e0e0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#fafafa')]),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(table)
    story.append(Spacer(1, 1*cm))

    # Ð£ÑÐ»Ð¾Ð²Ð¸Ñ
    story.append(Paragraph("<b>Ð£ÑÐ»Ð¾Ð²Ð¸Ñ:</b>", body_style))
    story.append(Paragraph("â¢ ÐÑÐ¾Ð¸Ð·Ð²Ð¾Ð´ÑÑÐ²Ð¾: 6â8 Ð½ÐµÐ´ÐµÐ»Ñ", body_style))
    story.append(Paragraph("â¢ ÐÐ¿Ð»Ð°ÑÐ°: 30% Ð¿ÑÐµÐ´Ð¾Ð¿Ð»Ð°ÑÐ°, 70% Ð¿ÐµÑÐµÐ´ Ð¾ÑÐ¿ÑÐ°Ð²ÐºÐ¾Ð¹", body_style))
    story.append(Paragraph("â¢ ÐÐ°ÑÐ°Ð½ÑÐ¸Ñ: 12 Ð¼ÐµÑÑÑÐµÐ²", body_style))
    story.append(Paragraph("â¢ ÐÐµÐ»Ð°Ñ ÑÐ°Ð¼Ð¾Ð¶Ð½Ñ, Ð´Ð¾ÑÑÐ°Ð²ÐºÐ° Ð¿Ð¾Ð´ ÐºÐ»ÑÑ", body_style))
    story.append(Spacer(1, 1*cm))

    # ÐÐ¾Ð½ÑÐ°ÐºÑÑ
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("KOKAHOUSE | kokahouse.ru | @kokahouse_Yulia", sub_style))

    doc.build(story)
    return buffer.getvalue()


# ââ ÐÐ¶ÐµÐ´Ð½ÐµÐ²Ð½ÑÐ¹ Ð¾ÑÑÑÑ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

async def daily_report(bot):
    """ÐÐ¶ÐµÐ´Ð½ÐµÐ²Ð½ÑÐ¹ Ð¾ÑÑÑÑ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÑ Ð² 9:00 ÐÐ¡Ð."""
    if not MANAGER_CHAT_ID:
        return
    try:
        # ÐÐ¾Ð»ÑÑÐ°ÐµÐ¼ Ð»Ð¸Ð´Ñ Ð¸Ð· amoCRM Ð·Ð° Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 24 ÑÐ°ÑÐ°
        import time as _time
        since = int(_time.time()) - 86400
        r_new = amo_request("GET", f"leads?filter[created_at][from]={since}&limit=50")
        new_leads = r_new.get("_embedded", {}).get("leads", [])

        # ÐÑÐµ Ð°ÐºÑÐ¸Ð²Ð½ÑÐµ Ð»Ð¸Ð´Ñ
        r_all = amo_request("GET", "leads?limit=50&order[created_at]=desc")
        all_leads = r_all.get("_embedded", {}).get("leads", [])

        # ÐÐ¾ÑÑÑÐ¸Ðµ (Ñ ÑÐµÐ½Ð¾Ð¹ > 0 Ð¸ Ð½Ðµ Ð·Ð°ÐºÑÑÑÑÐµ)
        hot = [l for l in all_leads if (l.get("price") or 0) > 0 and l.get("status_id") not in [142, 143]]
        # ÐÐ°Ð²Ð¸ÑÑÐ¸Ðµ (Ð½Ðµ Ð¾Ð±Ð½Ð¾Ð²Ð»ÑÐ»Ð¸ÑÑ 3+ Ð´Ð½Ñ)
        stale_ts = int(_time.time()) - 259200
        stale = [l for l in all_leads if (l.get("updated_at") or 0) < stale_ts and l.get("status_id") not in [142, 143]]

        total_sum = sum(l.get("price", 0) or 0 for l in all_leads if l.get("status_id") not in [142, 143])

        msg = (
            f"âï¸ *ÐÐ¾Ð±ÑÐ¾Ðµ ÑÑÑÐ¾! ÐÑÑÑÑ KOKAHOUSE*\n\n"
            f"ð ÐÐ° Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ðµ 24 ÑÐ°ÑÐ°:\n"
            f"â¢ ÐÐ¾Ð²ÑÑ Ð»Ð¸Ð´Ð¾Ð²: {len(new_leads)}\n"
            f"â¢ ÐÐ¾ÑÑÑÐ¸Ñ Ð² ÑÐ°Ð±Ð¾ÑÐµ: {len(hot)}\n"
            f"â¢ Ð¡ÑÐ¼Ð¼Ð° Ð² ÑÐ°Ð±Ð¾ÑÐµ: {total_sum:,} â½\n\n".replace(",", " ")
        )

        if stale:
            msg += f"â ï¸ ÐÐ°Ð²Ð¸ÑÐ»Ð¸ (3+ Ð´Ð½Ñ Ð±ÐµÐ· Ð°ÐºÑÐ¸Ð²Ð½Ð¾ÑÑÐ¸):\n"
            for l in stale[:5]:
                contacts = l.get("_embedded", {}).get("contacts", [])
                client = contacts[0].get("name", "â") if contacts else "â"
                msg += f"â¢ {client} â {l.get('name', '?')}\n"
            msg += "\n"

        msg += "ÐÐ°Ð¿Ð¸ÑÐ¸ Ð¼Ð½Ðµ ÑÑÐ¾ Ð½ÑÐ¶Ð½Ð¾ ÑÐ´ÐµÐ»Ð°ÑÑ ÑÐµÐ³Ð¾Ð´Ð½Ñ Ð¸Ð»Ð¸ ÑÐ¿ÑÐ¾ÑÐ¸ ÑÑÐ°ÑÐ¸ÑÑÐ¸ÐºÑ."

        await bot.send_message(chat_id=int(MANAGER_CHAT_ID), text=msg, parse_mode="Markdown")
        logger.info("ð ÐÐ¶ÐµÐ´Ð½ÐµÐ²Ð½ÑÐ¹ Ð¾ÑÑÑÑ Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½")
    except Exception as e:
        logger.error(f"daily_report error: {e}")


# ââ Follow-up Ð°Ð²ÑÐ¾Ð¼Ð°ÑÐ¸ÐºÐ° ââââââââââââââââââââââââââââââââââââââââââââââââââââââ

# Ð¥ÑÐ°Ð½Ð¸Ð¼ ÐºÐ¾Ð³Ð´Ð° Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÑÐ»Ð¸ follow-up: {lead_id: [timestamp1, timestamp2]}
_followup_sent: dict[int, list] = {}

FOLLOWUP_MESSAGES = [
    "ÐÐ¾Ð±ÑÑÐ¹ Ð´ÐµÐ½Ñ! ÐÐ¾Ð·Ð²ÑÐ°ÑÐ°ÑÑÑ Ðº Ð²Ð°ÑÐµÐ¼Ñ Ð·Ð°Ð¿ÑÐ¾ÑÑ. Ð¥Ð¾ÑÐ¸ÑÐµ, Ñ Ð¿Ð¾Ð´Ð±ÐµÑÑ Ð½ÐµÑÐºÐ¾Ð»ÑÐºÐ¾ Ð²Ð°ÑÐ¸Ð°Ð½ÑÐ¾Ð² Ð¿Ð¾Ð´ Ð²Ð°Ñ Ð±ÑÐ´Ð¶ÐµÑ Ð¸ ÑÑÐ¸Ð»Ñ?",
    "ÐÐ´ÑÐ°Ð²ÑÑÐ²ÑÐ¹ÑÐµ! Ð¥Ð¾ÑÐµÐ»(Ð°) ÑÑÐ¾ÑÐ½Ð¸ÑÑ â Ð¾ÑÑÐ°Ð»ÑÑ Ð»Ð¸ Ð¸Ð½ÑÐµÑÐµÑ Ðº Ð½Ð°ÑÐµÐ¹ Ð¼ÐµÐ±ÐµÐ»Ð¸? ÐÐ¾ÑÐ¾Ð²Ð° Ð¾ÑÐ²ÐµÑÐ¸ÑÑ Ð½Ð° Ð»ÑÐ±ÑÐµ Ð²Ð¾Ð¿ÑÐ¾ÑÑ.",
]

async def followup_check(bot):
    """ÐÑÐ¾Ð²ÐµÑÑÐµÐ¼ ÑÑÐ¿Ð»ÑÑ/Ð³Ð¾ÑÑÑÐ¸Ñ Ð»Ð¸Ð´Ð¾Ð² ÐºÐ¾ÑÐ¾ÑÑÐµ Ð¼Ð¾Ð»ÑÐ°Ñ 2+ Ð´Ð½Ñ."""
    import time as _time
    now = int(_time.time())
    cutoff_2d = now - 172800  # 2 Ð´Ð½Ñ
    cutoff_5d = now - 432000  # 5 Ð´Ð½ÐµÐ¹
    cutoff_7d = now - 604800  # 7 Ð´Ð½ÐµÐ¹

    # Ð¢Ð¾Ð»ÑÐºÐ¾ Ð´Ð½ÑÐ¼ (9-20 ÐÐ¡Ð = 6-17 UTC)
    hour_utc = datetime.utcnow().hour
    if not (6 <= hour_utc <= 17):
        return

    try:
        r = amo_request("GET", "leads?limit=100&order[updated_at]=asc")
        leads = r.get("_embedded", {}).get("leads", [])

        for lead in leads:
            lead_id = lead.get("id")
            status_id = lead.get("status_id")
            updated = lead.get("updated_at", 0) or 0
            price = lead.get("price") or 0

            # Ð¢Ð¾Ð»ÑÐºÐ¾ Ð°ÐºÑÐ¸Ð²Ð½ÑÐµ ÑÑÐ¿Ð»ÑÐµ/Ð³Ð¾ÑÑÑÐ¸Ðµ
            if status_id in [142, 143]:  # Won/Lost
                continue
            if price == 0:  # Ð¥Ð¾Ð»Ð¾Ð´Ð½ÑÐ¹ â Ð¿ÑÐ¾Ð¿ÑÑÐºÐ°ÐµÐ¼
                continue

            sent = _followup_sent.get(lead_id, [])
            contacts = lead.get("_embedded", {}).get("contacts", []) if isinstance(lead.get("_embedded"), dict) else []
            client_name = contacts[0].get("name", "ÐÐ»Ð¸ÐµÐ½Ñ") if contacts else "ÐÐ»Ð¸ÐµÐ½Ñ"

            # ÐÑÐµÐ¼ tg_id ÐºÐ»Ð¸ÐµÐ½ÑÐ° Ð² ÐºÐµÑÐµ
            tg_id = None
            for tid, data in _amo_client_cache.items():
                if data.get("lead_id") == lead_id:
                    tg_id = tid
                    break

            if not tg_id:
                continue

            # 2 Ð´Ð½Ñ â Ð¿ÐµÑÐ²ÑÐ¹ follow-up
            if updated < cutoff_2d and len(sent) == 0:
                msg = FOLLOWUP_MESSAGES[0]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id] = [now]
                amo_add_note(lead_id, f"ð¤ Follow-up #1 Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½: {msg[:100]}")
                logger.info(f"Follow-up #1 â lead {lead_id} ({client_name})")

            # 5 Ð´Ð½ÐµÐ¹ â Ð²ÑÐ¾ÑÐ¾Ð¹ follow-up
            elif updated < cutoff_5d and len(sent) == 1:
                msg = FOLLOWUP_MESSAGES[1]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id].append(now)
                amo_add_note(lead_id, f"ð¤ Follow-up #2 Ð¾ÑÐ¿ÑÐ°Ð²Ð»ÐµÐ½")
                logger.info(f"Follow-up #2 â lead {lead_id} ({client_name})")

            # 7 Ð´Ð½ÐµÐ¹ â Ð·Ð°Ð´Ð°ÑÐ° Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÑ
            elif updated < cutoff_7d and len(sent) == 2:
                if MANAGER_CHAT_ID:
                    await bot.send_message(
                        chat_id=int(MANAGER_CHAT_ID),
                        text=f"â ï¸ *{client_name}* Ð½Ðµ Ð¾ÑÐ²ÐµÑÐ°ÐµÑ 7 Ð´Ð½ÐµÐ¹.\nÐ¡Ð´ÐµÐ»ÐºÐ°: {lead.get('name', '?')}\nÐÑÐ¾Ð²ÐµÑÑÑÐµ Ð²ÑÑÑÐ½ÑÑ."
                    )
                _followup_sent[lead_id].append(now)
                logger.info(f"Follow-up #3 Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÑ â lead {lead_id}")

    except Exception as e:
        logger.error(f"followup_check error: {e}")


# ââ ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑÑ Ð² ÐºÐ°Ð½Ð°Ð» ââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

# Ð¢ÐµÐ¼Ñ Ð´Ð»Ñ Ð°Ð²ÑÐ¾-Ð¿Ð¾ÑÑÐ¾Ð² â ÑÐ¾ÑÐ°ÑÐ¸Ñ
AUTO_POST_TOPICS = [
    # ââ Ð¢Ð¾Ð²Ð°ÑÑ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "Ð´Ð¸Ð²Ð°Ð½ MC-A68 â Ð¸ÑÐ°Ð»ÑÑÐ½ÑÐºÐ°Ñ ÐºÐ¾Ð¶Ð° oil-wax, 3-Ð¼ÐµÑÑÐ½ÑÐ¹, Ð¾Ñ 235 000 â½. ÐÐ¾ÑÐµÐ¼Ñ ÐºÐ¾Ð¶Ð° oil-wax Ð»ÑÑÑÐµ Ð¾Ð±ÑÑÐ½Ð¾Ð¹ ÐºÐ¾Ð¶Ð¸",
    "Ð´Ð¸Ð²Ð°Ð½ FORT â Ð¾ÑÐµÑ Ð¸ Ð²ÐµÐ»ÑÑ, ÐºÐ»Ð°ÑÑÐ¸ÐºÐ° Ð´Ð»Ñ Ð³Ð¾ÑÑÐ¸Ð½Ð¾Ð¹, Ð¾Ñ 99 634 â½. ÐÐ¾ÑÐµÐ¼Ñ Ð½Ð°ÑÑÑÐ°Ð»ÑÐ½Ð¾Ðµ Ð´ÐµÑÐµÐ²Ð¾ Ð² ÐºÐ°ÑÐºÐ°ÑÐµ Ð²Ð°Ð¶Ð½Ð¾",
    "ÐºÑÐµÑÐ»Ð¾ ÐÐ°Ð½ÑÑÑ â ÑÐµÐ²ÐµÑÐ¾-Ð°Ð¼ÐµÑÐ¸ÐºÐ°Ð½ÑÐºÐ¸Ð¹ Ð¾ÑÐµÑ, ÑÐ»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, 118 921 â½. ÐÐ´ÐµÐ°Ð»ÑÐ½Ð¾Ðµ ÐºÑÐµÑÐ»Ð¾ Ð´Ð»Ñ Ð´Ð¾Ð¼Ð°ÑÐ½ÐµÐ³Ð¾ Ð¾ÑÐ¸ÑÐ°",
    "ÐºÑÐ¾Ð²Ð°ÑÑ Roma Platform â Ð¼Ð°ÑÑÐ¸Ð² Ð´ÑÐ±Ð°, Ð¿Ð¾Ð´ÑÑÐ¼Ð½ÑÐ¹ Ð¼ÐµÑÐ°Ð½Ð¸Ð·Ð¼, Ð¾Ñ 62 000 â½. ÐÐ°Ðº Ð²ÑÐ±ÑÐ°ÑÑ ÐºÑÐ¾Ð²Ð°ÑÑ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",
    "Ð¾Ð±ÐµÐ´ÐµÐ½Ð½ÑÐ¹ ÑÑÐ¾Ð» Palazzo â Ð¼ÑÐ°Ð¼Ð¾Ñ Calacatta Ð¸ Ð½ÐµÑÐ¶Ð°Ð²ÐµÑÑÐ°Ñ ÑÑÐ°Ð»Ñ, Ð¾Ñ 118 000 â½. ÐÑÐ°Ð¼Ð¾Ñ Ð² Ð¸Ð½ÑÐµÑÑÐµÑÐµ ÑÑÐ¾Ð»Ð¾Ð²Ð¾Ð¹",
    "Ð´Ð¸Ð²Ð°Ð½ PR701 ÐÐ±Ð»Ð°ÐºÐ¾ â Ð¼Ð¾Ð´ÑÐ»ÑÐ½ÑÐ¹, Ð³ÑÑÐ¸Ð½ÑÐ¹ Ð¿ÑÑ, ÑÐ»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, Ð¾Ñ 219 000 â½. ÐÐ¾ÑÐµÐ¼Ñ Ð³ÑÑÐ¸Ð½ÑÐ¹ Ð¿ÑÑ Ð»ÑÑÑÐµ Ð¿Ð¾ÑÐ¾Ð»Ð¾Ð½Ð°",
    "Ð³Ð°ÑÐ´ÐµÑÐ¾Ð±Ð½Ð°Ñ Cabinet Pro â Ð¼Ð°ÑÐ¾Ð²ÑÐ¹ Ð»Ð°Ðº Ð¸ ÑÐ¿Ð¾Ð½, Ð¿Ð¾Ð´ ÑÐ°Ð·Ð¼ÐµÑ Ð¿Ð¾Ð¼ÐµÑÐµÐ½Ð¸Ñ, Ð¾Ñ 94 000 â½. ÐÐ°ÑÐ´ÐµÑÐ¾Ð±Ð½Ð°Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ Ð¿Ð¾Ð´ ÐºÐ»ÑÑ",
    "ÑÐµÑÐµÐ¿ÑÐ½-ÑÑÐ¾Ð¹ÐºÐ° Grand Hotel â ÑÑÐ°Ð²ÐµÑÑÐ¸Ð½/Ð¼ÑÐ°Ð¼Ð¾Ñ, Ð¿Ð¾Ð´ÑÐ²ÐµÑÐºÐ°, Ð¾Ñ 157 000 â½. ÐÐµÐ±ÐµÐ»Ñ Ð´Ð»Ñ Ð¾ÑÐµÐ»ÐµÐ¹ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",
    "ÐºÑÐµÑÐ»Ð¾ MERCER â Ð¾ÑÐµÑ/ÑÑÐµÐ½Ñ, ÑÐ»Ð¾Ð¿Ð¾Ðº-Ð»ÑÐ½, Ð¾Ñ 127 000 â½. ÐÐ°Ðº ÑÐ¾ÑÐµÑÐ°ÑÑ ÐºÑÐµÑÐ»Ð° Ñ Ð´Ð¸Ð²Ð°Ð½Ð¾Ð¼",
    "Ð´Ð¸Ð²Ð°Ð½ MK-SOFA01 â Ð°Ð½Ð¸Ð»Ð¸Ð½Ð¾Ð²Ð°Ñ ÐºÐ¾Ð¶Ð°, Ð¾ÑÐµÑ, Ð¾Ñ 273 000 â½. Ð§ÑÐ¾ ÑÐ°ÐºÐ¾Ðµ Ð°Ð½Ð¸Ð»Ð¸Ð½Ð¾Ð²Ð°Ñ ÐºÐ¾Ð¶Ð° Ð¸ Ð·Ð°ÑÐµÐ¼ Ð¾Ð½Ð° Ð½ÑÐ¶Ð½Ð°",
    "Ð±Ð°Ð½ÐºÐµÑÐ½ÑÐ¹ ÑÑÑÐ» Chateau â Ð±ÑÐº, ÑÐºÐ°Ð½Ñ/ÐºÐ¾Ð¶Ð°, Ð¾Ñ 4 200 â½/ÑÑ. ÐÐ¾ÑÐµÐ¼Ñ ÑÐµÑÑÐ¾ÑÐ°Ð½Ñ Ð²ÑÐ±Ð¸ÑÐ°ÑÑ Ð¼ÐµÐ±ÐµÐ»Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",

    # ââ ÐÐ±ÑÐ°Ð·Ð¾Ð²Ð°ÑÐµÐ»ÑÐ½ÑÐ¹ ÐºÐ¾Ð½ÑÐµÐ½Ñ ââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÐ°Ðº Ð¾ÑÐ»Ð¸ÑÐ¸ÑÑ ÐºÐ°ÑÐµÑÑÐ²ÐµÐ½Ð½ÑÑ ÐºÐ¾Ð¶Ñ Ð¾Ñ Ð´ÐµÑÑÐ²Ð¾Ð¹ â 5 Ð¿ÑÐ¸Ð·Ð½Ð°ÐºÐ¾Ð² ÐºÐ¾ÑÐ¾ÑÑÐµ Ð¼Ð¾Ð¶Ð½Ð¾ Ð¿ÑÐ¾Ð²ÐµÑÐ¸ÑÑ Ð¿ÑÑÐ¼Ð¾ Ð² Ð¼Ð°Ð³Ð°Ð·Ð¸Ð½Ðµ",
    "ÐÐ¾ÑÐµÐ¼Ñ Ð¼Ð°ÑÑÐ¸Ð² Ð´ÐµÑÐµÐ²Ð° Ð»ÑÑÑÐµ ÐÐÐ¤ â ÑÐ°Ð·Ð±Ð¸ÑÐ°ÐµÐ¼ ÑÐ¾ÑÑÐ°Ð² ÐºÐ°ÑÐºÐ°ÑÐ° Ð´Ð¸Ð²Ð°Ð½Ð° Ð¸ Ð¿Ð¾ÑÐµÐ¼Ñ ÑÑÐ¾ Ð²Ð°Ð¶Ð½Ð¾",
    "ÐÐ° ÑÑÐ¾ ÑÐ¼Ð¾ÑÑÐµÑÑ Ð¿ÑÐ¸ Ð²ÑÐ±Ð¾ÑÐµ Ð´Ð¸Ð²Ð°Ð½Ð° â Ð¼Ð°ÑÐµÑÐ¸Ð°Ð», ÐºÐ°ÑÐºÐ°Ñ, Ð½Ð°Ð¿Ð¾Ð»Ð½Ð¸ÑÐµÐ»Ñ, ÑÐ°Ð·Ð¼ÐµÑ. ÐÐ¾Ð»Ð½ÑÐ¹ Ð³Ð°Ð¹Ð´",
    "ÐÑÑÐ¸Ð½ÑÐ¹ Ð¿ÑÑ vs Ð¿Ð¾ÑÐ¾Ð»Ð¾Ð½ vs ÑÐ¾Ð»Ð»Ð¾ÑÐ°Ð¹Ð±ÐµÑ â Ð¸Ð· ÑÐµÐ³Ð¾ Ð»ÑÑÑÐµ Ð´ÐµÐ»Ð°ÑÑ Ð¿Ð¾Ð´ÑÑÐºÐ¸ Ð´Ð¸Ð²Ð°Ð½Ð°",
    "ÐÑÐ°Ð»ÑÑÐ½ÑÐºÐ¸Ðµ ÑÐºÐ°Ð½Ð¸ Ð² ÐºÐ¸ÑÐ°Ð¹ÑÐºÐ¾Ð¹ Ð¼ÐµÐ±ÐµÐ»Ð¸ â ÐºÐ°Ðº ÑÑÐ¾ ÑÐ°Ð±Ð¾ÑÐ°ÐµÑ Ð¸ Ð¿Ð¾ÑÐµÐ¼Ñ ÑÑÐ¾ Ð½Ðµ Ð¼Ð°ÑÐºÐµÑÐ¸Ð½Ð³",
    "ÐÐ°Ðº Ð²ÑÐ±ÑÐ°ÑÑ Ð¾Ð±ÐµÐ´ÐµÐ½Ð½ÑÐ¹ ÑÑÐ¾Ð» Ð´Ð»Ñ ÑÐµÐ¼ÑÐ¸ â ÑÐ°Ð·Ð¼ÐµÑ, Ð¼Ð°ÑÐµÑÐ¸Ð°Ð», ÑÐ¾ÑÐ¼Ð°. Ð Ð°Ð·Ð±Ð¸ÑÐ°ÐµÐ¼ Ð¾ÑÐ¸Ð±ÐºÐ¸",
    "ÐÑÐ°Ð¼Ð¾Ñ Ð² Ð¸Ð½ÑÐµÑÑÐµÑÐµ â Ð½Ð°ÑÑÑÐ°Ð»ÑÐ½ÑÐ¹ vs Ð¸ÑÐºÑÑÑÑÐ²ÐµÐ½Ð½ÑÐ¹. ÐÐ°Ðº Ð½Ðµ Ð¿ÐµÑÐµÐ¿Ð»Ð°ÑÐ¸ÑÑ Ð¸ Ð½Ðµ Ð¾ÑÐ¸Ð±Ð¸ÑÑÑÑ",
    "Ð¡ÐºÐ¾Ð»ÑÐºÐ¾ ÑÐ»ÑÐ¶Ð¸Ñ Ð´Ð¸Ð²Ð°Ð½ Ð¸Ð· ÐÐ¸ÑÐ°Ñ â ÑÐµÑÑÐ½ÑÐ¹ ÑÐ°Ð·Ð³Ð¾Ð²Ð¾Ñ Ð¾ ÑÑÐ¾ÐºÐ°Ñ Ð¸ ÐºÐ°ÑÐµÑÑÐ²Ðµ",

    # ââ ÐÐ° ÐºÑÐ»Ð¸ÑÐ°Ð¼Ð¸ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÐ°Ðº Ð¼Ñ Ð¿ÑÐ¾Ð²ÐµÑÑÐµÐ¼ ÑÐ°Ð±ÑÐ¸ÐºÐ¸ Ð¿ÐµÑÐµÐ´ Ð·Ð°ÐºÐ»ÑÑÐµÐ½Ð¸ÐµÐ¼ ÐºÐ¾Ð½ÑÑÐ°ÐºÑÐ° â Ð½Ð°Ñ Ð¿ÑÐ¾ÑÐµÑÑ Ð¾ÑÐ±Ð¾ÑÐ° Ð¿Ð¾ÑÑÐ°Ð²ÑÐ¸ÐºÐ¾Ð²",
    "Ð§ÑÐ¾ Ð¿ÑÐ¾Ð¸ÑÑÐ¾Ð´Ð¸Ñ Ð½Ð° ÑÐ°Ð±ÑÐ¸ÐºÐµ Ð·Ð° 6 Ð½ÐµÐ´ÐµÐ»Ñ Ð´Ð¾ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸ â Ð¿ÑÐ¾Ð¸Ð·Ð²Ð¾Ð´ÑÑÐ²Ð¾ Ð¼ÐµÐ±ÐµÐ»Ð¸ Ð¸Ð·Ð½ÑÑÑÐ¸",
    "ÐÐ°Ðº Ð²ÑÐ³Ð»ÑÐ´Ð¸Ñ ÐºÐ¾Ð½ÑÑÐ¾Ð»Ñ ÐºÐ°ÑÐµÑÑÐ²Ð° Ð½Ð° ÐºÐ¸ÑÐ°Ð¹ÑÐºÐ¾Ð¹ ÑÐ°Ð±ÑÐ¸ÐºÐµ â Ð²Ð¸Ð´ÐµÐ¾-ÐºÐ¾Ð½ÑÑÐ¾Ð»Ñ, ÑÐ¾ÑÐ¾ Ð¿ÐµÑÐµÐ´ ÑÐ¿Ð°ÐºÐ¾Ð²ÐºÐ¾Ð¹",
    "Ð¤Ð¾ÑÐ°Ð½Ñ vs ÐÑÐ°Ð½ÑÐ¶Ð¾Ñ â Ð² ÑÑÐ¼ ÑÐ°Ð·Ð½Ð¸ÑÐ° Ð¸ Ð¾ÑÐºÑÐ´Ð° Ð¼Ñ Ð·Ð°ÐºÐ°Ð·ÑÐ²Ð°ÐµÐ¼ ÑÐ°Ð·Ð½ÑÐµ ÐºÐ°ÑÐµÐ³Ð¾ÑÐ¸Ð¸ Ð¼ÐµÐ±ÐµÐ»Ð¸",
    "ÐÐ°Ðº Ð¼Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÐ¼ Ñ 340 ÑÐ°Ð±ÑÐ¸ÐºÐ°Ð¼Ð¸ â ÑÐ¸ÑÑÐµÐ¼Ð° Ð¾ÑÐ±Ð¾ÑÐ°, ÑÐµÐ¹ÑÐ¸Ð½Ð³Ð¸, ÑÐºÑÐºÐ»ÑÐ·Ð¸Ð²Ð½ÑÐµ ÐºÐ¾Ð½ÑÑÐ°ÐºÑÑ",

    # ââ ÐÐµÐ¹ÑÑ Ð¸ Ð¿ÑÐ¾ÐµÐºÑÑ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÐ¾Ð¼Ð¿Ð»ÐµÐºÑÐ¾Ð²Ð°Ð»Ð¸ ÑÐµÑÑÐ¾ÑÐ°Ð½ â 40 Ð±Ð°Ð½ÐºÐµÑÐ½ÑÑ ÑÑÑÐ»ÑÐµÐ² Ð¸ 10 ÑÑÐ¾Ð»Ð¾Ð² Ð¸Ð· Ð¤Ð¾ÑÐ°Ð½Ñ Ð·Ð° 5 Ð½ÐµÐ´ÐµÐ»Ñ. ÐÑÑÐ¾ÑÐ¸Ñ Ð¿ÑÐ¾ÐµÐºÑÐ°",
    "ÐÐ¾ÑÑÐ¸Ð½Ð°Ñ Ð¿Ð¾Ð´ ÐºÐ»ÑÑ Ñ Ð±ÑÐ´Ð¶ÐµÑÐ¾Ð¼ 300 000 â½ â ÑÑÐ¾ Ð²ÑÐ¾Ð´Ð¸Ñ Ð¸ ÐºÐ°Ðº ÑÑÐ¾ Ð²ÑÐ³Ð»ÑÐ´Ð¸Ñ",
    "ÐÑÐµÐ»Ñ Ð½Ð° 30 Ð½Ð¾Ð¼ÐµÑÐ¾Ð² â ÐºÐ°Ðº Ð¼Ñ ÐºÐ¾Ð¼Ð¿Ð»ÐµÐºÑÐ¾Ð²Ð°Ð»Ð¸ Ð¼ÐµÐ±ÐµÐ»Ñ Ð¾Ñ ÐºÑÐ¾Ð²Ð°ÑÐµÐ¹ Ð´Ð¾ ÑÐµÑÐµÐ¿ÑÐ½Ð°",
    "ÐÑÐ¸Ñ Ð´Ð»Ñ IT-ÐºÐ¾Ð¼Ð¿Ð°Ð½Ð¸Ð¸ â Ð¿ÐµÑÐµÐ³Ð¾Ð²Ð¾ÑÐ½ÑÐ¹ ÑÑÐ¾Ð» Executive 5 Ð¼ÐµÑÑÐ¾Ð² Ð¸ ÑÐ°Ð±Ð¾ÑÐ¸Ðµ Ð·Ð¾Ð½Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",

    # ââ ÐÐ°Ð¹ÑÑÑÐ°Ð¹Ð» Ð¸ Ð¸Ð½ÑÐµÑÑÐµÑ âââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÐ°Ðº Ð¾Ð±ÑÑÑÑÐ¾Ð¸ÑÑ Ð´Ð¾Ð¼Ð°ÑÐ½Ð¸Ð¹ Ð¾ÑÐ¸Ñ Ñ Ð±ÑÐ´Ð¶ÐµÑÐ¾Ð¼ 150 000 â½ â ÑÑÐ¾Ð», ÐºÑÐµÑÐ»Ð¾, ÑÑÐµÐ»Ð»Ð°Ð¶Ð¸ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",
    "Japandi ÑÑÐ¸Ð»Ñ Ð² Ð¸Ð½ÑÐµÑÑÐµÑÐµ â Ð¾ÑÐµÑ, Ð»ÑÐ½, Ð¼Ð¸Ð½Ð¸Ð¼Ð°Ð»Ð¸Ð·Ð¼. ÐÐ°ÐºÑÑ Ð¼ÐµÐ±ÐµÐ»Ñ Ð²ÑÐ±ÑÐ°ÑÑ",
    "ÐÐ¾ÑÑÐ¸Ð½Ð°Ñ Ð² ÑÑÐ¸Ð»Ðµ mid-century modern â Ð´Ð¸Ð²Ð°Ð½Ñ Ð¸ ÐºÑÐµÑÐ»Ð° ÐºÐ¾ÑÐ¾ÑÑÐµ ÑÐ¾Ð·Ð´Ð°ÑÑ Ð°ÑÐ¼Ð¾ÑÑÐµÑÑ",
    "ÐÐ¾Ð´ÑÐ»ÑÐ½ÑÐ¹ Ð´Ð¸Ð²Ð°Ð½ vs Ð¾Ð±ÑÑÐ½ÑÐ¹ â ÑÑÐ¾ Ð»ÑÑÑÐµ Ð´Ð»Ñ Ð±Ð¾Ð»ÑÑÐ¾Ð¹ Ð³Ð¾ÑÑÐ¸Ð½Ð¾Ð¹",
    "Ð¡Ð¿Ð°Ð»ÑÐ½Ñ Ð¼ÐµÑÑÑ Ñ Ð±ÑÐ´Ð¶ÐµÑÐ¾Ð¼ 200 000 â½ â ÐºÑÐ¾Ð²Ð°ÑÑ, ÑÑÐ¼Ð±Ð¾ÑÐºÐ¸, Ð³Ð°ÑÐ´ÐµÑÐ¾Ð±Ð½Ð°Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ",

    # ââ ÐÐ¾ÑÑÐ°Ð²ÐºÐ° Ð¸ Ð»Ð¾Ð³Ð¸ÑÑÐ¸ÐºÐ° âââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÐ°Ðº ÑÐ°Ð±Ð¾ÑÐ°ÐµÑ Ð±ÐµÐ»Ð°Ñ ÑÐ°Ð¼Ð¾Ð¶Ð½Ñ â Ð¿Ð¾ÑÐµÐ¼Ñ ÑÑÐ¾ Ð²Ð°Ð¶Ð½Ð¾ Ð¸ ÐºÐ°Ðº Ð¼Ñ ÑÑÐ¾ Ð´ÐµÐ»Ð°ÐµÐ¼",
    "Ð¡ÐºÐ¾Ð»ÑÐºÐ¾ Ð¸Ð´ÑÑ Ð¼ÐµÐ±ÐµÐ»Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ â ÑÐµÐ°Ð»ÑÐ½ÑÐµ ÑÑÐ¾ÐºÐ¸ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸ Ð¿Ð¾ ÑÑÑÐ°Ð½Ð°Ð¼",
    "ÐÐ°Ðº ÑÐ¿Ð°ÐºÐ¾Ð²Ð°Ð½Ð° Ð¼ÐµÐ±ÐµÐ»Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ â ÑÑÐ¾ Ð·Ð°ÑÐ¸ÑÐ°ÐµÑ ÐµÑ Ð² Ð¿ÑÑÐ¸ Ð½Ð° 8 000 ÐºÐ¼",
    "ÐÐ¾ÑÑÐ°Ð²ÐºÐ° Ð² ÐÐ°Ð·Ð°ÑÑÑÐ°Ð½, ÐÐ¸ÑÐ³Ð¸Ð·Ð¸Ñ, ÐÐÐ­ â ÐºÐ°Ðº Ð¼Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÐ¼ Ñ ÑÐ°Ð·Ð½ÑÐ¼Ð¸ ÑÑÑÐ°Ð½Ð°Ð¼Ð¸",

    # ââ Ð¡ÑÐ°Ð²Ð½ÐµÐ½Ð¸Ñ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "ÐÑÐ°Ð»ÑÑÐ½ÑÐºÐ°Ñ Ð¼ÐµÐ±ÐµÐ»Ñ vs ÐÐ¸ÑÐ°Ð¹ â Ð² ÑÑÐ¼ ÑÐµÐ°Ð»ÑÐ½Ð°Ñ ÑÐ°Ð·Ð½Ð¸ÑÐ° Ð¿ÑÐ¸ Ð¾Ð´Ð¸Ð½Ð°ÐºÐ¾Ð²Ð¾Ð¹ ÑÐµÐ½Ðµ",
    "ÐÐµÐ±ÐµÐ»Ñ Ð¸Ð· ÐÐ¸ÑÐ°Ñ vs ÑÐ¾ÑÑÐ¸Ð¹ÑÐºÐ¸Ðµ Ð¼Ð°Ð³Ð°Ð·Ð¸Ð½Ñ â ÑÑÐ°Ð²Ð½Ð¸Ð²Ð°ÐµÐ¼ ÑÐµÐ½Ñ Ð½Ð° Ð¾Ð´Ð¸Ð½Ð°ÐºÐ¾Ð²ÑÐµ Ð¿Ð¾Ð·Ð¸ÑÐ¸Ð¸",
    "Ð¤Ð°Ð±ÑÐ¸ÑÐ½Ð°Ñ ÑÐµÐ½Ð° EXW vs ÑÐ¾Ð·Ð½Ð¸ÑÐ° Ð² Ð Ð¾ÑÑÐ¸Ð¸ â Ð¿Ð¾ÑÐµÐ¼Ñ ÑÐ°Ð·Ð½Ð¸ÑÐ° Ð² 2-3 ÑÐ°Ð·Ð° ÑÑÐ¾ Ð½Ð¾ÑÐ¼Ð°",

    # ââ Ð Ð°Ð±Ð¾ÑÐ° Ñ Ð½Ð°Ð¼Ð¸ ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
    "340+ ÑÐ°Ð±ÑÐ¸Ðº Ð¤Ð¾ÑÐ°Ð½Ñ Ð¸ ÐÑÐ°Ð½ÑÐ¶Ð¾Ñ â ÐºÐ°Ðº Ð¼Ñ Ð²ÑÐ±Ð¸ÑÐ°ÐµÐ¼ Ð¿Ð¾ÑÑÐ°Ð²ÑÐ¸ÐºÐ¾Ð² Ð¸ ÐºÐ¾Ð½ÑÑÐ¾Ð»Ð¸ÑÑÐµÐ¼ ÐºÐ°ÑÐµÑÑÐ²Ð¾",
    "ÐÐ°Ðº ÑÐ´ÐµÐ»Ð°ÑÑ Ð·Ð°ÐºÐ°Ð· Ð² KOKAHOUSE â Ð¾Ñ Ð·Ð°Ð¿ÑÐ¾ÑÐ° Ð´Ð¾ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸. ÐÐ¾ÑÐ°Ð³Ð¾Ð²ÑÐ¹ Ð¿ÑÐ¾ÑÐµÑÑ",
    "ÐÐ¾Ð¼Ð¿Ð»ÐµÐºÑÐ°ÑÐ¸Ñ Ð¾Ð±ÑÐµÐºÑÐ¾Ð² â Ð¾ÑÐµÐ»Ð¸, ÑÐµÑÑÐ¾ÑÐ°Ð½Ñ, Ð¾ÑÐ¸ÑÑ, Ð°Ð¿Ð°ÑÑÐ°Ð¼ÐµÐ½ÑÑ. ÐÐ°Ðº Ð¼Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÐ¼",
    "ÐÐ¿Ð»Ð°ÑÐ° Ð² ÑÑÐ±Ð»ÑÑ, Ð´Ð¾Ð»Ð»Ð°ÑÐ°Ñ, ÐºÑÐ¸Ð¿ÑÐµ â ÐºÐ°Ðº Ð¼Ñ ÑÐ°Ð±Ð¾ÑÐ°ÐµÐ¼ Ñ ÑÐ°Ð·Ð½ÑÐ¼Ð¸ ÑÑÐµÐ¼Ð°Ð¼Ð¸ Ð¾Ð¿Ð»Ð°ÑÑ",
]

_last_topic_index = -1


async def auto_post_to_channel(bot):
    """ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑ Ð² ÐºÐ°Ð½Ð°Ð» â Ð·Ð°Ð¿ÑÑÐºÐ°ÐµÑÑÑ Ð¿Ð¾ ÑÐ°ÑÐ¿Ð¸ÑÐ°Ð½Ð¸Ñ."""
    global _last_topic_index
    try:
        # ÐÑÐ±Ð¸ÑÐ°ÐµÐ¼ ÑÐµÐ¼Ñ â Ð¿Ð¾ Ð¾ÑÐµÑÐµÐ´Ð¸, Ð½Ðµ Ð¿Ð¾Ð²ÑÐ¾ÑÑÐµÐ¼
        _last_topic_index = (_last_topic_index + 1) % len(AUTO_POST_TOPICS)
        topic = AUTO_POST_TOPICS[_last_topic_index]

        logger.info(f"ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑ: {topic[:50]}...")

        prompt = f"""ÐÐ°Ð¿Ð¸ÑÐ¸ Ð¿ÑÐ¾Ð´Ð°ÑÑÐ¸Ð¹ Ð¿Ð¾ÑÑ Ð´Ð»Ñ Telegram-ÐºÐ°Ð½Ð°Ð»Ð° KOKAHOUSE.

Ð¢ÐµÐ¼Ð°: {topic}

Ð¢ÑÐµÐ±Ð¾Ð²Ð°Ð½Ð¸Ñ:
â 3-4 Ð°Ð±Ð·Ð°ÑÐ°, Ð¶Ð¸Ð²Ð¾Ð¹ ÑÑÐ¸Ð»Ñ Ð±ÐµÐ· ÐºÐ°Ð½ÑÐµÐ»ÑÑÑÐ¸Ð½Ñ
â Ð£Ð¿Ð¾Ð¼ÑÐ½Ð¸ ÐºÐ¾Ð½ÐºÑÐµÑÐ½ÑÐµ Ð¼Ð°ÑÐµÑÐ¸Ð°Ð»Ñ Ð¸ Ð¿ÑÐµÐ¸Ð¼ÑÑÐµÑÑÐ²Ð°
â Ð¦ÐµÐ½Ð¾Ð²Ð¾Ð¹ Ð¾ÑÐ¸ÐµÐ½ÑÐ¸Ñ ÐµÑÐ»Ð¸ ÐµÑÑÑ
â Ð ÐºÐ¾Ð½ÑÐµ: "ÐÐ¾Ð´ÑÐ¾Ð±Ð½ÐµÐµ Ð¸ ÑÐ°ÑÑÑÑ Ð´Ð¾ÑÑÐ°Ð²ÐºÐ¸ â @kokahouse_Yulia"
â 2-3 emoji ÑÐ¼ÐµÑÑÐ½Ð¾
â Ð¤Ð¾ÑÐ¼Ð°ÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¸Ðµ Markdown (Ð¶Ð¸ÑÐ½ÑÐ¹, ÐºÑÑÑÐ¸Ð²)
â ÐÐµÐ· ÑÑÑÑÐµÐ³Ð¾Ð²

ÐÐµÑÐ½Ð¸ Ð¢ÐÐÐ¬ÐÐ ÑÐµÐºÑÑ Ð¿Ð¾ÑÑÐ°."""

        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        post_text = response.content[0].text.strip()

        # ÐÑÐ±Ð»Ð¸ÐºÑÐµÐ¼ Ð² ÐºÐ°Ð½Ð°Ð»
        await bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        logger.info("â ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½")

    except Exception as e:
        # ÐÑÐ»Ð¸ Markdown ÑÐ»Ð¾Ð¼Ð°Ð½ â Ð¿ÑÐ¾Ð±ÑÐµÐ¼ Ð±ÐµÐ· ÑÐ¾ÑÐ¼Ð°ÑÐ¸ÑÐ¾Ð²Ð°Ð½Ð¸Ñ
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            logger.info("â ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑ Ð¾Ð¿ÑÐ±Ð»Ð¸ÐºÐ¾Ð²Ð°Ð½ (Ð±ÐµÐ· Markdown)")
        except Exception as e2:
            logger.error(f"ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑ Ð¾ÑÐ¸Ð±ÐºÐ°: {e2}")


# ââ ÐÐ°Ð¿ÑÑÐº ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()

    # ÐÐ»Ð¸ÐµÐ½ÑÑÐºÐ¸Ðµ ÐºÐ¾Ð¼Ð°Ð½Ð´Ñ
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("reset",     cmd_reset))

    # ÐÐ¾Ð¼Ð°Ð½Ð´Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° â Ð¾Ð±ÑÑÐµÐ½Ð¸Ðµ
    app.add_handler(CommandHandler("teach",     cmd_teach))
    app.add_handler(CommandHandler("knowledge", cmd_knowledge))

    # ÐÐ¾Ð¼Ð°Ð½Ð´Ð° ÐÐ
    app.add_handler(CommandHandler("kp", cmd_kp))

    # Ð¢ÐµÑÑ amoCRM
    async def cmd_test_amo(update, context):
        if not is_owner(update.effective_user):
            return
        await update.message.reply_text("ð Ð¢ÐµÑÑÐ¸ÑÑÑ Ð¿Ð¾Ð´ÐºÐ»ÑÑÐµÐ½Ð¸Ðµ Ðº amoCRM...")
        r = amo_request("GET", "account")
        if "error" in r:
            await update.message.reply_text(f"â amoCRM Ð¾ÑÐ¸Ð±ÐºÐ°: {r['error']}")
        else:
            name = r.get("name", "?")
            await update.message.reply_text(
                f"â amoCRM Ð¿Ð¾Ð´ÐºÐ»ÑÑÑÐ½!\n"
                f"ÐÐºÐºÐ°ÑÐ½Ñ: {name}\n"
                f"ÐÐ¾Ð¼ÐµÐ½: {AMO_DOMAIN}\n"
                f"API: {AMO_API}"
            )
    app.add_handler(CommandHandler("test_amo", cmd_test_amo))

    # ÐÐ¾Ð¼Ð°Ð½Ð´Ñ Ð²Ð»Ð°Ð´ÐµÐ»ÑÑÐ° â ÐºÐ°Ð½Ð°Ð»
    app.add_handler(CommandHandler("post",      cmd_post))
    app.add_handler(CommandHandler("ai_post",   cmd_ai_post))
    app.add_handler(CommandHandler("confirm",   cmd_confirm))
    app.add_handler(CommandHandler("channel",   cmd_channel))
    app.add_handler(CommandHandler("menu",      cmd_menu))

    # ÐÐµÐ´Ð¸Ð° (ÑÐ¾ÑÐ¾ ÑÐ½Ð°ÑÐ°Ð»Ð° â ÑÑÐ¾Ð±Ñ /post_photo Ð¿ÐµÑÐµÑÐ²Ð°ÑÐ¸ÑÑ)
    app.add_handler(MessageHandler(filters.PHOTO, handle_owner_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Ð¢ÐµÐºÑÑ â Ð¿Ð¾ÑÐ»ÐµÐ´Ð½Ð¸Ð¼
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ÐÐ»Ð°Ð½Ð¸ÑÐ¾Ð²ÑÐ¸Ðº Ð·Ð°Ð¿ÑÑÐºÐ°ÐµÑÑÑ Ð¿Ð¾ÑÐ»Ðµ ÑÑÐ°ÑÑÐ° asyncio loop
    async def post_init(application):
        scheduler = AsyncIOScheduler(timezone="UTC")

        # ÐÐ²ÑÐ¾-Ð¿Ð¾ÑÑÑ Ð¿Ð½/ÑÑ/Ð¿Ñ Ð² 10:00 ÐÐ¡Ð (UTC+3 = 07:00 UTC)
        scheduler.add_job(
            auto_post_to_channel,
            CronTrigger(day_of_week="mon,wed,fri", hour=7, minute=0),
            args=[application.bot], id="auto_post"
        )

        # ÐÐ¶ÐµÐ´Ð½ÐµÐ²Ð½ÑÐ¹ Ð¾ÑÑÑÑ Ð² 9:00 ÐÐ¡Ð (06:00 UTC)
        scheduler.add_job(
            daily_report, CronTrigger(hour=6, minute=0),
            args=[application.bot], id="daily_report"
        )

        # Follow-up ÐºÐ°Ð¶Ð´ÑÐµ 6 ÑÐ°ÑÐ¾Ð² â Ð¿ÑÐ¾Ð²ÐµÑÑÐµÐ¼ Ð·Ð°Ð²Ð¸ÑÑÐ¸Ñ Ð»Ð¸Ð´Ð¾Ð²
        scheduler.add_job(
            followup_check, CronTrigger(hour="6,12,18", minute=0),
            args=[application.bot], id="followup"
        )

        scheduler.start()
        logger.info("ð ÐÐ»Ð°Ð½Ð¸ÑÐ¾Ð²ÑÐ¸Ðº Ð·Ð°Ð¿ÑÑÐµÐ½: Ð¿Ð¾ÑÑÑ + Ð¾ÑÑÑÑ + follow-up")

    app.post_init = post_init

    logger.info("ð¤ KOKAHOUSE Bot Ð·Ð°Ð¿ÑÑÐµÐ½")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
