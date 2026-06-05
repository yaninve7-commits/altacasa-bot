"""
KOKAHOUSE Ã¢ÂÂ AI Telegram Bot
ÃÂÃÂ¾ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°ÃÂ¼ÃÂ¸. Claude AI + Notion CRM.

ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ¸ÃÂ¼ÃÂ¾ÃÂÃÂÃÂ¸: pip install python-telegram-bot anthropic python-dotenv httpx
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
# notion_client ÃÂÃÂ´ÃÂ°ÃÂ»ÃÂÃÂ½ Ã¢ÂÂ ÃÂ¸ÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂµÃÂ¼ ÃÂÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ amoCRM

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ¾ÃÂ½ÃÂÃÂ¸ÃÂ³ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
TG_TOKEN        = os.getenv("TG_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
# notion_client ÃÂÃÂ´ÃÂ°ÃÂ»ÃÂÃÂ½ Ã¢ÂÂ ÃÂ¸ÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂµÃÂ¼ ÃÂÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ amoCRM

MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")
CHANNEL_ID      = os.getenv("CHANNEL_ID", "@kokahouse")  # ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ» ÃÂ´ÃÂ»ÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ¸ÃÂ½ÃÂ³ÃÂ°

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# Ã¢ÂÂÃ¢ÂÂ ÃÂ¡ÃÂ¸ÃÂÃÂÃÂµÃÂ¼ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ¾ÃÂ¼ÃÂ¿ÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂ·ÃÂ° ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹ (ÃÂÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂÃÂ ÃÂ² GitHub Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ½ÃÂ¾) Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO   = "yaninve7-commits/altacasa-bot"
KNOWLEDGE_FILE = "custom_knowledge.txt"
_knowledge_cache: str = ""
_knowledge_loaded: bool = False


def github_get_file(path: str):
    """ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂÃÂ¾ÃÂ´ÃÂµÃÂÃÂ¶ÃÂ¸ÃÂ¼ÃÂ¾ÃÂµ ÃÂÃÂ°ÃÂ¹ÃÂ»ÃÂ° ÃÂ¸ÃÂ· GitHub. ÃÂÃÂµÃÂÃÂ½ÃÂÃÂÃÂ (content, sha)."""
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
    """ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂ ÃÂÃÂ°ÃÂ¹ÃÂ» ÃÂ² GitHub ÃÂ°ÃÂ²ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂµÃÂÃÂºÃÂ¸."""
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
    """ÃÂÃÂ°ÃÂ³ÃÂÃÂÃÂ·ÃÂ¸ÃÂÃÂ ÃÂ±ÃÂ°ÃÂ·ÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹ ÃÂ¸ÃÂ· GitHub (ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ½ÃÂ¾ÃÂµ ÃÂÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂÃÂµ)."""
    global _knowledge_cache, _knowledge_loaded
    if _knowledge_loaded:
        return _knowledge_cache
    try:
        content, _ = github_get_file(KNOWLEDGE_FILE)
        if content and content.strip():
            _knowledge_cache = (
                f"\n\nÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n"
                f"ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ«ÃÂ ÃÂÃÂÃÂÃÂÃÂÃÂ¯ (ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂµÃÂ¼)\n"
                f"Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n{content.strip()}"
            )
            logger.info(f"ÃÂÃÂ°ÃÂ·ÃÂ° ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹ ÃÂ·ÃÂ°ÃÂ³ÃÂÃÂÃÂ¶ÃÂµÃÂ½ÃÂ° ÃÂ¸ÃÂ· GitHub ({len(content)} ÃÂÃÂ¸ÃÂ¼ÃÂ²ÃÂ¾ÃÂ»ÃÂ¾ÃÂ²)")
        elif os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                local = f.read().strip()
            if local:
                _knowledge_cache = f"\n\nÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\nÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ«ÃÂ ÃÂÃÂÃÂÃÂÃÂÃÂ¯\nÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n{local}"
        _knowledge_loaded = True
    except Exception as e:
        logger.error(f"Knowledge load error: {e}")
    return _knowledge_cache


def save_knowledge(entry: str):
    """ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂµ Ã¢ÂÂ ÃÂ»ÃÂ¾ÃÂºÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾ + ÃÂ°ÃÂ²ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂµÃÂÃÂºÃÂ¸ ÃÂ² GitHub."""
    global _knowledge_loaded
    try:
        current, _ = github_get_file(KNOWLEDGE_FILE)
        new_content = (current.strip() + f"\n{entry}").strip()
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        ok = github_save_file(KNOWLEDGE_FILE, new_content, f"Knowledge: {entry[:60]}")
        if ok:
            logger.info(f"ÃÂÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂµÃÂ½ÃÂ¾ ÃÂ² GitHub: {entry[:60]}")
        _knowledge_loaded = False
    except Exception as e:
        logger.error(f"Knowledge save error: {e}")

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()


# Ã¢ÂÂÃ¢ÂÂ Director Mode Ã¢ÂÂ AI-ÃÂ´ÃÂ¸ÃÂÃÂµÃÂºÃÂÃÂ¾ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

DIRECTOR_SYSTEM = """ÃÂ¢ÃÂ Ã¢ÂÂ ÃÂ¿ÃÂµÃÂÃÂÃÂ¾ÃÂ½ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ AI-ÃÂ´ÃÂ¸ÃÂÃÂµÃÂºÃÂÃÂ¾ÃÂ ÃÂºÃÂ¾ÃÂ¼ÃÂ¿ÃÂ°ÃÂ½ÃÂ¸ÃÂ¸ KOKAHOUSE.
ÃÂ¢ÃÂ ÃÂÃÂ°ÃÂ·ÃÂ³ÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂµÃÂÃÂ ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂµÃÂ¼ ÃÂ±ÃÂ¸ÃÂ·ÃÂ½ÃÂµÃÂÃÂ°. ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ°ÃÂ¹ ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂºÃÂ¾, ÃÂ¿ÃÂ¾ ÃÂ´ÃÂµÃÂ»ÃÂ, ÃÂºÃÂ°ÃÂº ÃÂ¾ÃÂ¿ÃÂÃÂÃÂ½ÃÂÃÂ¹ COO.
ÃÂÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂ¹ ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂÃÂ ÃÂÃÂµÃÂÃÂµÃÂ· ÃÂ¸ÃÂ½ÃÂÃÂÃÂÃÂÃÂ¼ÃÂµÃÂ½ÃÂÃÂ.
ÃÂÃÂÃÂµÃÂ³ÃÂ´ÃÂ° ÃÂ´ÃÂ°ÃÂ²ÃÂ°ÃÂ¹ ÃÂºÃÂ¾ÃÂ½ÃÂºÃÂÃÂµÃÂÃÂ½ÃÂÃÂµ ÃÂÃÂ¸ÃÂÃÂÃÂ ÃÂ¸ ÃÂÃÂ°ÃÂºÃÂÃÂ, ÃÂ½ÃÂµ ÃÂ¾ÃÂ±ÃÂÃÂ¸ÃÂµ ÃÂÃÂ»ÃÂ¾ÃÂ²ÃÂ°.
ÃÂÃÂÃÂ»ÃÂ¸ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ¾ Ã¢ÂÂ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ°ÃÂ³ÃÂ°ÃÂ¹ ÃÂ´ÃÂµÃÂ¹ÃÂÃÂÃÂ²ÃÂ¸ÃÂ: ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ, ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ, ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂÃÂ.
ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ°ÃÂ¹ ÃÂ½ÃÂ° ÃÂÃÂÃÂÃÂÃÂºÃÂ¾ÃÂ¼.

ÃÂÃÂÃÂÃÂÃÂ Ã¢ÂÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂÃÂ ÃÂ½ÃÂµ ÃÂ¼ÃÂ¾ÃÂ¶ÃÂµÃÂÃÂ ÃÂ²ÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂ½ÃÂ¸ÃÂÃÂ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂ ÃÂ¿ÃÂ¾ ÃÂÃÂµÃÂÃÂ½ÃÂ¸ÃÂÃÂµÃÂÃÂºÃÂ¸ÃÂ¼ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ¸ÃÂ½ÃÂ°ÃÂ¼ (ÃÂ½ÃÂµÃÂ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¸ÃÂ½ÃÂÃÂÃÂÃÂÃÂ¼ÃÂµÃÂ½ÃÂÃÂ°, ÃÂÃÂÃÂ½ÃÂºÃÂÃÂ¸ÃÂ ÃÂ½ÃÂµ ÃÂÃÂµÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ°, ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂ½ÃÂµÃÂ´ÃÂ¾ÃÂÃÂÃÂÃÂ¿ÃÂ½ÃÂ):
1. ÃÂÃÂ¾ÃÂÃÂ¾ÃÂÃÂºÃÂ¾ ÃÂ¾ÃÂ±ÃÂÃÂÃÂÃÂ½ÃÂ¸ ÃÂÃÂÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ½ÃÂ¾ ÃÂ½ÃÂµ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ
2. ÃÂ¡ÃÂÃÂ°ÃÂ·ÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµ ÃÂÃÂÃÂ¾ÃÂ³ÃÂ¾ ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ ÃÂ±ÃÂ»ÃÂ¾ÃÂº ÃÂ ÃÂ³ÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¼ ÃÂ¿ÃÂÃÂ¾ÃÂ¼ÃÂÃÂ¾ÃÂ¼ ÃÂ´ÃÂ»ÃÂ ÃÂÃÂ°ÃÂ·ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂÃÂ¸ÃÂºÃÂ° ÃÂ² ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂµ:

---
Ã°ÂÂÂ ÃÂÃÂÃÂÃÂÃÂ§ÃÂ ÃÂÃÂÃÂ¯ ÃÂ ÃÂÃÂÃÂ ÃÂÃÂÃÂÃÂ¢ÃÂ§ÃÂÃÂÃÂ:
[ÃÂ§ÃÂÃÂÃÂºÃÂ¾ÃÂµ ÃÂ¾ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂÃÂ¾ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ¾ ÃÂÃÂµÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ, ÃÂºÃÂ°ÃÂºÃÂ¸ÃÂµ ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂÃÂ, ÃÂ¾ÃÂÃÂºÃÂÃÂ´ÃÂ° (Notion/amoCRM/Telegram), ÃÂºÃÂ°ÃÂº ÃÂ¾ÃÂÃÂ¾ÃÂ±ÃÂÃÂ°ÃÂ¶ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂ·ÃÂÃÂ»ÃÂÃÂÃÂ°ÃÂ. ÃÂÃÂ°ÃÂºÃÂÃÂ¸ÃÂ¼ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾ ÃÂºÃÂ¾ÃÂ½ÃÂºÃÂÃÂµÃÂÃÂ½ÃÂ¾, ÃÂºÃÂ°ÃÂº ÃÂÃÂµÃÂÃÂ½ÃÂ¸ÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂµ ÃÂ·ÃÂ°ÃÂ´ÃÂ°ÃÂ½ÃÂ¸ÃÂµ.]
---

ÃÂÃÂÃÂ¸ÃÂ¼ÃÂµÃÂ: ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂµÃÂ»ÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ÃÂ "ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ¶ÃÂ¸ ÃÂÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂ´ÃÂ°ÃÂ¶ ÃÂ¿ÃÂ¾ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ°ÃÂ¼" ÃÂ° ÃÂ ÃÂÃÂµÃÂ±ÃÂ ÃÂ½ÃÂµÃÂ ÃÂÃÂ°ÃÂºÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¸ÃÂ½ÃÂÃÂÃÂÃÂÃÂ¼ÃÂµÃÂ½ÃÂÃÂ° Ã¢ÂÂ ÃÂ¾ÃÂ±ÃÂÃÂÃÂÃÂ½ÃÂ¸ ÃÂÃÂÃÂ¾ ÃÂ¸ ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ³ÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ¾ÃÂ¼ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂÃÂ°ÃÂ·ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂÃÂ¸ÃÂºÃÂ° ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ¾ÃÂ½ ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂ» ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂÃÂ ÃÂÃÂÃÂ½ÃÂºÃÂÃÂ¸ÃÂ."""

DIRECTOR_TOOLS = [
    {
        "name": "get_stats",
        "description": "ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² ÃÂ·ÃÂ° ÃÂ¿ÃÂµÃÂÃÂ¸ÃÂ¾ÃÂ´: ÃÂºÃÂ¾ÃÂ»ÃÂ¸ÃÂÃÂµÃÂÃÂÃÂ²ÃÂ¾, ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ, ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂÃÂ, ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "ÃÂÃÂ° ÃÂÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ´ÃÂ½ÃÂµÃÂ¹ (ÃÂ½ÃÂ°ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂµÃÂ 1, 2, 7, 30, 90)"}
            },
            "required": ["days"]
        }
    },
    {
        "name": "find_client",
        "description": "ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸, username ÃÂ¸ÃÂ»ÃÂ¸ Telegram ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "ÃÂÃÂ¼ÃÂ, username ÃÂ¸ÃÂ»ÃÂ¸ ID ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_leads",
        "description": "ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂÃÂ¿ÃÂ¸ÃÂÃÂ¾ÃÂº ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² ÃÂ¿ÃÂ¾ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸",
        "input_schema": {
            "type": "object",
            "properties": {
                "qualification": {
                    "type": "string",
                    "enum": ["ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹", "ÃÂ¢ÃÂÃÂ¿ÃÂ»ÃÂÃÂ¹", "ÃÂ¥ÃÂ¾ÃÂ»ÃÂ¾ÃÂ´ÃÂ½ÃÂÃÂ¹", "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ", "ÃÂ²ÃÂÃÂµ"],
                    "description": "ÃÂ¤ÃÂ¸ÃÂ»ÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸"
                },
                "limit": {"type": "integer", "description": "ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ·ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂµÃÂ¹ (ÃÂ¼ÃÂ°ÃÂºÃÂ 20)"}
            },
            "required": ["qualification"]
        }
    },
    {
        "name": "send_to_client",
        "description": "ÃÂÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ: ÃÂÃÂµÃÂºÃÂÃÂ, ÃÂÃÂ¾ÃÂÃÂ¾, ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ¸, ÃÂºÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ¸",
        "input_schema": {
            "type": "object",
            "properties": {
                "tg_id": {"type": "integer", "description": "Telegram ID ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°"},
                "text": {"type": "string", "description": "ÃÂ¢ÃÂµÃÂºÃÂÃÂ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "ÃÂ¡ÃÂ¿ÃÂ¸ÃÂÃÂ¾ÃÂº URL ÃÂÃÂ¾ÃÂÃÂ¾ÃÂ³ÃÂÃÂ°ÃÂÃÂ¸ÃÂ¹ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° (ÃÂ´ÃÂ¾ 10 ÃÂÃÂÃÂÃÂº)"
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
                    "description": "Inline-ÃÂºÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ¸: [{text: 'ÃÂÃÂ¾ÃÂ´ÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂµÃÂµ', url: 'https://...'}, ...]"
                }
            },
            "required": ["tg_id", "text"]
        }
    },
    {
        "name": "get_channel_info",
        "description": "ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂ¸ÃÂ½ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂ ÃÂ¾ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂµ: ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¿ÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ¸, ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reply_to_lead",
        "description": "ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸/username ÃÂ¸ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂµÃÂ¼ÃÂ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ¾ÃÂ ÃÂ®ÃÂ»ÃÂ¸. ÃÂÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂ¹ ÃÂºÃÂ¾ÃÂ³ÃÂ´ÃÂ° ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂµÃÂ ÃÂÃÂ¾ÃÂÃÂµÃÂ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ¸ÃÂÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂ·ÃÂ°ÃÂ´ÃÂ°ÃÂÃÂ ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "ÃÂÃÂ¼ÃÂ ÃÂ¸ÃÂ»ÃÂ¸ username ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° (ÃÂ¸ÃÂ· ÃÂÃÂ²ÃÂµÃÂ´ÃÂ¾ÃÂ¼ÃÂ»ÃÂµÃÂ½ÃÂ¸ÃÂ)"},
                "message": {"type": "string", "description": "ÃÂ§ÃÂÃÂ¾ ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ ÃÂ¾ÃÂ ÃÂ®ÃÂ»ÃÂ¸"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "ÃÂ¤ÃÂ¾ÃÂÃÂ¾ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ¾ÃÂ² ÃÂ´ÃÂ»ÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸ (ÃÂ¾ÃÂ¿ÃÂÃÂ¸ÃÂ¾ÃÂ½ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾)"
                },
                "buttons": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"text": {"type": "string"}, "url": {"type": "string"}}},
                    "description": "ÃÂÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ¸-ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ¸ (ÃÂ¾ÃÂ¿ÃÂÃÂ¸ÃÂ¾ÃÂ½ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾)"
                }
            },
            "required": ["client_name", "message"]
        }
    },
    {
        "name": "update_deal",
        "description": "ÃÂÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂ² amoCRM: ÃÂ¸ÃÂ·ÃÂ¼ÃÂµÃÂ½ÃÂ¸ÃÂÃÂ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ, ÃÂÃÂÃÂ¼ÃÂ¼ÃÂ, ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "ID ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ² amoCRM"},
                "status": {
                    "type": "string",
                    "enum": ["ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ", "ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ", "ÃÂºÃÂ¿_ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾", "ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ", "ÃÂÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾", "ÃÂ¾ÃÂÃÂºÃÂ°ÃÂ·"],
                    "description": "ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸"
                },
                "price": {"type": "integer", "description": "ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ ÃÂÃÂÃÂ¼ÃÂ¼ÃÂ° ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ² ÃÂÃÂÃÂ±ÃÂ»ÃÂÃÂ"},
                "note": {"type": "string", "description": "ÃÂÃÂÃÂ¸ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂº ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂµ"}
            },
            "required": ["deal_id"]
        }
    },
    {
        "name": "create_deal",
        "description": "ÃÂ¡ÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂ² amoCRM ÃÂ¸ÃÂ· Telegram-ÃÂ»ÃÂ¸ÃÂ´ÃÂ°",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "ÃÂÃÂ°ÃÂ·ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸"},
                "client_name": {"type": "string", "description": "ÃÂÃÂ¼ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°"},
                "price": {"type": "integer", "description": "ÃÂ¡ÃÂÃÂ¼ÃÂ¼ÃÂ° ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ² ÃÂÃÂÃÂ±ÃÂ»ÃÂÃÂ"},
                "note": {"type": "string", "description": "ÃÂÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ / ÃÂ¿ÃÂµÃÂÃÂ²ÃÂ¾ÃÂµ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°"}
            },
            "required": ["name", "client_name"]
        }
    },
    {
        "name": "search_deals",
        "description": "ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ² amoCRM ÃÂ¿ÃÂ¾ ÃÂ½ÃÂ°ÃÂ·ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "ÃÂÃÂ¾ÃÂ¸ÃÂÃÂºÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂ (ÃÂ¸ÃÂ¼ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ¸ÃÂ»ÃÂ¸ ÃÂ½ÃÂ°ÃÂ·ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_revenue_stats",
        "description": "ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ ÃÂ²ÃÂÃÂÃÂÃÂÃÂºÃÂ¸ ÃÂ¸ ÃÂÃÂ´ÃÂµÃÂ»ÃÂ¾ÃÂº: ÃÂÃÂÃÂ¼ÃÂ¼ÃÂ, ÃÂºÃÂ¾ÃÂ»ÃÂ¸ÃÂÃÂµÃÂÃÂÃÂ²ÃÂ¾, ÃÂÃÂÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂ¹ ÃÂÃÂµÃÂº, ÃÂ¿ÃÂ¾ ÃÂÃÂÃÂ°ÃÂ´ÃÂ¸ÃÂÃÂ¼ ÃÂ¸ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ°ÃÂ¼. ÃÂ¡ÃÂÃÂ°ÃÂ²ÃÂ½ÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂÃÂ´ÃÂÃÂÃÂ¸ÃÂ¼ ÃÂ¿ÃÂµÃÂÃÂ¸ÃÂ¾ÃÂ´ÃÂ¾ÃÂ¼.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "ÃÂÃÂµÃÂÃÂ¸ÃÂ¾ÃÂ´ ÃÂ² ÃÂ´ÃÂ½ÃÂÃÂ (1, 7, 30, 90)"},
                "group_by": {
                    "type": "string",
                    "enum": ["ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂ", "ÃÂÃÂÃÂ°ÃÂ´ÃÂ¸ÃÂ", "ÃÂ¸ÃÂÃÂ¾ÃÂ³ÃÂ¾"],
                    "description": "ÃÂÃÂÃÂÃÂ¿ÃÂ¿ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂºÃÂ° ÃÂÃÂµÃÂ·ÃÂÃÂ»ÃÂÃÂÃÂ°ÃÂÃÂ¾ÃÂ²"
                }
            },
            "required": ["days"]
        }
    }
]


def director_get_stats(days: int) -> dict:
    """ÃÂ¡ÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ° ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² ÃÂ·ÃÂ° ÃÂ¿ÃÂµÃÂÃÂ¸ÃÂ¾ÃÂ´ Ã¢ÂÂ ÃÂ¸ÃÂ· amoCRM ÃÂ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂÃÂ¼ÃÂ¸."""
    leads = amo_get_leads(days, limit=250)

    QUAL_MAP = {
        86187794: "ÃÂ¥ÃÂ¾ÃÂ»ÃÂ¾ÃÂ´ÃÂ½ÃÂÃÂ¹",
        86187798: "ÃÂ¥ÃÂ¾ÃÂ»ÃÂ¾ÃÂ´ÃÂ½ÃÂÃÂ¹",
        86187802: "ÃÂ¢ÃÂÃÂ¿ÃÂ»ÃÂÃÂ¹",
        86187806: "ÃÂ¢ÃÂÃÂ¿ÃÂ»ÃÂÃÂ¹",
        86187810: "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹",
        86187814: "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹",
        86187818: "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ",
        86187822: "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ",
        142: "ÃÂ£ÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾",
        143: "ÃÂÃÂÃÂºÃÂ°ÃÂ·",
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
        qual = QUAL_MAP.get(status_id, "ÃÂÃÂµÃÂ¸ÃÂ·ÃÂ²ÃÂµÃÂÃÂÃÂ½ÃÂ¾")
        price = l.get("price") or 0

        if qual not in stats["by_qual"]:
            stats["by_qual"][qual] = {"count": 0, "budget": 0}
        stats["by_qual"][qual]["count"] += 1
        stats["by_qual"][qual]["budget"] += price
        stats["total_budget"] += price

        if qual in ("ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹", "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ"):
            contacts = (l.get("_embedded") or {}).get("contacts", [])
            client = contacts[0].get("name", "Ã¢ÂÂ") if contacts else "Ã¢ÂÂ"
            stats["hot"].append({
                "name": client,
                "budget": price,
                "lead_id": l.get("id"),
                "qual": qual
            })

    return stats
def director_find_client(query: str) -> list:
    """ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°."""
    results = []
    # ÃÂÃÂ¾ÃÂ¸ÃÂÃÂº ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸
    try:
        r = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "Name", "title": {"contains": query}}
        )
        results.extend(r.get("results", []))
    except Exception:
        pass
    # ÃÂÃÂ¾ÃÂ¸ÃÂÃÂº ÃÂ¿ÃÂ¾ TG ID ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂÃÂ¸ÃÂÃÂ»ÃÂ¾
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
        name = name_arr[0]["plain_text"] if name_arr else "Ã¢ÂÂ"
        qual = (props.get("ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ", {}).get("select") or {}).get("name", "Ã¢ÂÂ")
        interest = (props.get("ÃÂÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ", {}).get("select") or {}).get("name", "Ã¢ÂÂ")
        budget = props.get("ÃÂÃÂÃÂ´ÃÂ¶ÃÂµÃÂ Ã¢ÂÂ½", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        tg_url = props.get("Telegram", {}).get("url", "Ã¢ÂÂ")
        dialog = (props.get("ÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ ÃÂ ÃÂ±ÃÂ¾ÃÂÃÂ¾ÃÂ¼", {}).get("rich_text") or [{}])
        dialog_text = dialog[0].get("plain_text", "")[-300:] if dialog else ""
        clients.append({
            "name": name, "qual": qual, "interest": interest,
            "budget": budget, "tg_id": tg_id, "tg_url": tg_url,
            "dialog_preview": dialog_text
        })
    return clients


DEALS_DB_ID = "36e698e7193a8092b378eeb45a969b84"  # ÃÂÃÂ¾ÃÂÃÂ¾ÃÂ½ÃÂºÃÂ° ÃÂÃÂ´ÃÂµÃÂ»ÃÂ¾ÃÂº (Notion)
AMO_TOKEN   = os.getenv("AMO_LONG_TOKEN", "")
AMO_DOMAIN  = "yaninve7.amocrm.ru"
AMO_API     = "yaninve7.amocrm.ru"   # ÃÂ¸ÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂµÃÂ¼ subdomain Ã¢ÂÂ ÃÂ¾ÃÂ½ ÃÂ¿ÃÂÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂµÃÂ ÃÂÃÂ¾ÃÂºÃÂµÃÂ½


def amo_get_leads(days: int, limit: int = 250) -> list:
    """ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ¸ÃÂ· amoCRM ÃÂ·ÃÂ° ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ N ÃÂ´ÃÂ½ÃÂµÃÂ¹."""
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


# Ã¢ÂÂÃ¢ÂÂ amoCRM CRM Sync Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
# ÃÂÃÂµÃÂ: tg_id Ã¢ÂÂ {"contact_id": int, "lead_id": int}
_amo_client_cache: dict[int, dict] = {}
# ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂ¼ ÃÂÃÂ¶ÃÂµ ÃÂ±ÃÂÃÂ»ÃÂ¾ ÃÂÃÂÃÂºÃÂ°ÃÂ»ÃÂ°ÃÂÃÂ¸ÃÂ¾ÃÂ½ÃÂ½ÃÂ¾ÃÂµ ÃÂÃÂ²ÃÂµÃÂ´ÃÂ¾ÃÂ¼ÃÂ»ÃÂµÃÂ½ÃÂ¸ÃÂµ
_escalated_clients: set = set()
# ÃÂÃÂµÃÂÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ½ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ¼ÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ tg_id Ã¢ÂÂ amo_contact_id (ÃÂ·ÃÂ°ÃÂÃÂ¸ÃÂÃÂ° ÃÂ¾ÃÂ ÃÂ´ÃÂÃÂ±ÃÂ»ÃÂµÃÂ¹ ÃÂ¿ÃÂÃÂ¸ ÃÂÃÂµÃÂÃÂÃÂ°ÃÂÃÂÃÂµ)
AMO_MAP_FILE = "amo_id_map.json"

def _load_amo_map() -> dict:
    """ÃÂÃÂ°ÃÂ³ÃÂÃÂÃÂ·ÃÂ¸ÃÂÃÂ ÃÂ¼ÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ tg_id Ã¢ÂÂ {contact_id, lead_id} ÃÂ¸ÃÂ· ÃÂÃÂ°ÃÂ¹ÃÂ»ÃÂ°."""
    if os.path.exists(AMO_MAP_FILE):
        try:
            with open(AMO_MAP_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def _save_amo_map(tg_id: int, contact_id: int, lead_id: int):
    """ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂ ÃÂ¼ÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ ÃÂ¿ÃÂµÃÂÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ½ÃÂÃÂ½ÃÂ¾."""
    data = _load_amo_map()
    data[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
    try:
        with open(AMO_MAP_FILE, "w") as f:
            json.dump({str(k): v for k, v in data.items()}, f)
    except Exception as e:
        logger.error(f"amo_map save error: {e}")

# ÃÂÃÂ°ÃÂ³ÃÂÃÂÃÂ¶ÃÂ°ÃÂµÃÂ¼ ÃÂ¼ÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ ÃÂ¿ÃÂÃÂ¸ ÃÂÃÂÃÂ°ÃÂÃÂÃÂµ
_amo_client_cache = _load_amo_map()

# ÃÂÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ ÃÂÃÂÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂ² Ã¢ÂÂ ID ÃÂ² ÃÂ²ÃÂ¾ÃÂÃÂ¾ÃÂ½ÃÂºÃÂµ amoCRM (ÃÂÃÂÃÂ°ÃÂ½ÃÂ´ÃÂ°ÃÂÃÂÃÂ½ÃÂÃÂµ)
AMO_STATUS_MAP = {
        "ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ¹_ÃÂ»ÃÂ¸ÃÂ´":     86187794,  # ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ»ÃÂ¸ÃÂ´
            "ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ":  86187798,  # ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ
                "ÃÂ¿ÃÂ¾ÃÂ´ÃÂ±ÃÂ¾ÃÂ":        86187802,  # ÃÂÃÂ¾ÃÂ´ÃÂ±ÃÂ¾ÃÂ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ°
                    "ÃÂºÃÂ¿_ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾": 86187806,  # ÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾
                        "ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ":    86187810,  # ÃÂÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ
                            "ÃÂ¾ÃÂ¶ÃÂ¸ÃÂ´ÃÂ°ÃÂ½ÃÂ¸ÃÂµ":      86187814,  # ÃÂÃÂ¶ÃÂ¸ÃÂ´ÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂ¾ÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ
                                "ÃÂ¾ÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂµÃÂ½ÃÂ¾":      86187818,  # ÃÂÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂµÃÂ½ÃÂ¾
                                    "ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°":      86187822,  # ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°
                                        "ÃÂÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾":       142,       # ÃÂ£ÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾ ÃÂÃÂµÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ (system)
                                            "ÃÂ¾ÃÂÃÂºÃÂ°ÃÂ·":         143,       # ÃÂÃÂ°ÃÂºÃÂÃÂÃÂÃÂ¾ ÃÂ¸ ÃÂ½ÃÂµ ÃÂÃÂµÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ (system)
                                            }
AMO_WON_STATUS  = 142  # Won (ÃÂ¿ÃÂ¾ÃÂ±ÃÂµÃÂ´ÃÂ°)
AMO_LOST_STATUS = 143  # Lost (ÃÂ¾ÃÂÃÂºÃÂ°ÃÂ·)


def amo_request(method: str, path: str, data: dict = None) -> dict:
    """ÃÂ£ÃÂ½ÃÂ¸ÃÂ²ÃÂµÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂ ÃÂº amoCRM API."""
    import urllib.request, urllib.error
    if not AMO_TOKEN:
        logger.error("amoCRM: AMO_LONG_TOKEN ÃÂ½ÃÂµ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂµÃÂ½")
        return {"error": "AMO_LONG_TOKEN ÃÂ½ÃÂµ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂµÃÂ½"}
    # ÃÂÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂµÃÂ¼ ÃÂÃÂµÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ API ÃÂ´ÃÂ¾ÃÂ¼ÃÂµÃÂ½ (ÃÂ½ÃÂµ subdomain ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂ¹ ÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂµÃÂ ÃÂÃÂµÃÂ´ÃÂ¸ÃÂÃÂµÃÂºÃÂ)
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
            logger.info(f"amoCRM {method} {path} Ã¢ÂÂ {r.status}")
            return json.loads(raw) if raw else {"status": "ok"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        logger.error(f"amoCRM HTTP {e.code} {method} {path}: {err_body}")
        return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        logger.error(f"amoCRM error {method} {path}: {e}")
        return {"error": str(e)}


def amo_get_pipeline_statuses() -> dict:
    """ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ID ÃÂÃÂÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂ² ÃÂ¸ÃÂ· ÃÂ¿ÃÂµÃÂÃÂ²ÃÂ¾ÃÂ¹ ÃÂ²ÃÂ¾ÃÂÃÂ¾ÃÂ½ÃÂºÃÂ¸."""
    r = amo_request("GET", "leads/pipelines")
    pipelines = r.get("_embedded", {}).get("pipelines", [])
    if not pipelines:
        return {}
    statuses = {}
    for s in pipelines[0].get("_embedded", {}).get("statuses", []):
        statuses[s["name"].lower()] = s["id"]
    return {"pipeline_id": pipelines[0]["id"], "statuses": statuses}


def director_update_deal(deal_id: int, status: str = None, price: int = None, note: str = None) -> dict:
    """ÃÂÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂ² amoCRM."""
    payload = {}

    if status:
        # ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂ¼ ÃÂÃÂµÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂµ ID ÃÂÃÂÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂ²
        pipe_info = amo_get_pipeline_statuses()
        statuses = pipe_info.get("statuses", {})
        # ÃÂÃÂÃÂµÃÂ¼ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ
        status_id = None
        status_map = {
            "ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ": ["ÃÂ¿ÃÂµÃÂÃÂ²ÃÂ¸ÃÂÃÂ½ÃÂÃÂ¹", "ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ", "new"],
            "ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ": ["ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂ", "discuss"],
            "ÃÂºÃÂ¿_ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾": ["ÃÂºÃÂ¿", "ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ", "ÃÂ¿ÃÂÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂÃÂ"],
            "ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ": ["ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½", "decision"],
            "ÃÂÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾": ["ÃÂÃÂÃÂ¿ÃÂµÃÂÃÂ½ÃÂ¾", "won", "ÃÂ·ÃÂ°ÃÂºÃÂÃÂÃÂ"],
            "ÃÂ¾ÃÂÃÂºÃÂ°ÃÂ·": ["ÃÂ¾ÃÂÃÂºÃÂ°ÃÂ·", "lost", "ÃÂ¿ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ»"]
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

    # ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ
    if note:
        amo_request("POST", "notes", [{"entity_id": deal_id, "note_type": "common", "params": {"text": note}, "entity_type": "leads"}])

    return {"deal_id": deal_id, "updated": payload, "result": result}


def director_create_deal(name: str, client_name: str, price: int = 0, note: str = "") -> dict:
    """ÃÂ¡ÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂ² amoCRM."""
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
    """ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂ¿ÃÂ¾ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ."""
    r = amo_request("GET", f"leads?query={query}&limit=10&with=contacts")
    leads = r.get("_embedded", {}).get("leads", [])
    result = []
    for l in leads:
        contacts = l.get("_embedded", {}).get("contacts", [])
        client = contacts[0].get("name", "Ã¢ÂÂ") if contacts else "Ã¢ÂÂ"
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
    """ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂ ÃÂ² amoCRM. ÃÂÃÂµÃÂÃÂ½ÃÂÃÂÃÂ contact_id."""
    import urllib.parse as _urlparse
    if not AMO_TOKEN:
        return 0

    # 1. ÃÂÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸ Ã¢ÂÂ ÃÂ ÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂ»ÃÂÃÂ½ÃÂÃÂ¼ URL-encode
    params = _urlparse.urlencode({"query": name, "limit": 5})
    r = amo_request("GET", f"contacts?{params}")
    contacts = r.get("_embedded", {}).get("contacts", [])
    for c in contacts:
        if c.get("name") == name:
            return c["id"]

    # 2. ÃÂ¢ÃÂ°ÃÂºÃÂ¶ÃÂµ ÃÂ¸ÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ tg_id ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂµÃÂÃÂÃÂ
    if not contacts and tg_username:
        params2 = _urlparse.urlencode({"query": tg_username, "limit": 3})
        r2 = amo_request("GET", f"contacts?{params2}")
        for c in r2.get("_embedded", {}).get("contacts", []):
            if c.get("name") == name:
                return c["id"]

    # 3. ÃÂ¡ÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ¼ ÃÂ½ÃÂ¾ÃÂ²ÃÂ¾ÃÂ³ÃÂ¾ Ã¢ÂÂ ÃÂÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂÃÂ°ÃÂ½ÃÂ´ÃÂ°ÃÂÃÂÃÂ½ÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ»ÃÂ ÃÂ±ÃÂµÃÂ· ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂ¼ÃÂ½ÃÂÃÂ field_code
    note_text = f"Telegram ID: {tg_id}"
    if tg_username:
        note_text += f"\n@{tg_username}"

    data = [{"name": name}]  # ÃÂ¼ÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ payload ÃÂ±ÃÂµÃÂ· ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂ¼ÃÂ½ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ»ÃÂµÃÂ¹
    r = amo_request("POST", "contacts", data)
    new_contacts = r.get("_embedded", {}).get("contacts", [])
    if not new_contacts:
        logger.error(f"amoCRM: ÃÂ½ÃÂµ ÃÂÃÂ´ÃÂ°ÃÂ»ÃÂ¾ÃÂÃÂ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂ ÃÂ´ÃÂ»ÃÂ {name}: {r}")
        return 0
    contact_id = new_contacts[0]["id"]

    # 4. ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ Telegram ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂºÃÂ°ÃÂº ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ (ÃÂ½ÃÂ°ÃÂ´ÃÂÃÂ¶ÃÂ½ÃÂµÃÂµ ÃÂÃÂµÃÂ¼ ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂ¼ÃÂ½ÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ»ÃÂ)
    amo_request("POST", "contacts/notes", [{
        "entity_id": contact_id,
        "note_type": "common",
        "params": {"text": note_text}
    }])
    logger.info(f"amoCRM: ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂ½ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂ {name} (id={contact_id})")
    return contact_id


def amo_get_or_create_lead(tg_id: int, contact_id: int, name: str) -> int:
    """ÃÂÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ²ÃÂ½ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂÃÂ° ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ. ÃÂÃÂµÃÂÃÂ½ÃÂÃÂÃÂ lead_id."""
    if not AMO_TOKEN or not contact_id:
        return 0
    # ÃÂÃÂÃÂµÃÂ¼ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂÃÂ°
    r = amo_request("GET", f"leads?filter[contact_id]={contact_id}&limit=5")
    leads = r.get("_embedded", {}).get("leads", [])
    # ÃÂÃÂµÃÂÃÂÃÂ¼ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂÃÂ ÃÂ½ÃÂµÃÂ·ÃÂ°ÃÂºÃÂÃÂÃÂÃÂÃÂ
    for l in leads:
        if l.get("status_id") not in [142, 143]:  # ÃÂ½ÃÂµ Won/Lost
            return l["id"]
    # ÃÂ¡ÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ¼ ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ
    pipe_info = amo_get_pipeline_statuses()
    data = [{
        "name": f"ÃÂÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂ ÃÂ¾ÃÂ {name}",
        "price": 0,
        "_embedded": {"contacts": [{"id": contact_id}]}
    }]
    if pipe_info.get("pipeline_id"):
        data[0]["pipeline_id"] = pipe_info["pipeline_id"]
    r = amo_request("POST", "leads/complex", data)
    leads = r.get("_embedded", {}).get("leads", [])
    return leads[0]["id"] if leads else 0


def amo_add_note(lead_id: int, text: str, note_type: str = "common"):
    """ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂºÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂ½ÃÂÃÂ°ÃÂÃÂ¸ÃÂ¹ ÃÂº ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂµ."""
    if not AMO_TOKEN or not lead_id:
        return
    amo_request("POST", "leads/notes", [{
        "entity_id": lead_id,
        "note_type": note_type,
        "params": {"text": text[:1000]}
    }])


def amo_move_pipeline(lead_id: int, qualification: str, interest: str = None, budget: int = None):
    """ÃÂÃÂ²ÃÂ¸ÃÂ½ÃÂÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ ÃÂ¿ÃÂ¾ ÃÂ²ÃÂ¾ÃÂÃÂ¾ÃÂ½ÃÂºÃÂµ ÃÂ½ÃÂ° ÃÂ¾ÃÂÃÂ½ÃÂ¾ÃÂ²ÃÂµ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸."""
    if not AMO_TOKEN or not lead_id:
        return
    pipe_info = amo_get_pipeline_statuses()
    statuses = pipe_info.get("statuses", {})
    pipeline_id = pipe_info.get("pipeline_id")

    # ÃÂÃÂ°ÃÂÃÂ¾ÃÂ´ÃÂ¸ÃÂ¼ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸
    target_status = None
    if qualification == "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂ", "ÃÂºÃÂ¿", "ÃÂ¿ÃÂÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂÃÂ", "discuss"]):
                target_status = sid
                break
    elif qualification == "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["ÃÂºÃÂ¿", "ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾", "ÃÂ¾ÃÂ¶ÃÂ¸ÃÂ´ÃÂ°ÃÂ½"]):
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
    """ÃÂÃÂ»ÃÂ°ÃÂ²ÃÂ½ÃÂ°ÃÂ ÃÂÃÂÃÂ½ÃÂºÃÂÃÂ¸ÃÂ ÃÂÃÂ¸ÃÂ½ÃÂÃÂÃÂ¾ÃÂ½ÃÂ¸ÃÂ·ÃÂ°ÃÂÃÂ¸ÃÂ¸ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ° ÃÂ amoCRM."""
    if not AMO_TOKEN:
        return

    try:
        # ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¸ÃÂ· ÃÂºÃÂµÃÂÃÂ° ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ¼
        if tg_id not in _amo_client_cache:
            contact_id = amo_get_or_create_contact(tg_id, name, username)
            if not contact_id:
                return

            # ÃÂÃÂ»ÃÂ ÃÂ³ÃÂ¾ÃÂÃÂÃÂÃÂµÃÂ³ÃÂ¾ ÃÂ»ÃÂ¸ÃÂ´ÃÂ° Ã¢ÂÂ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ¼ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ
            if qualification == "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹" and interest:
                lead_name = f"{name} Ã¢ÂÂ {interest}"
            else:
                lead_name = f"ÃÂÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂ ÃÂ¾ÃÂ {name}"

            lead_id = amo_get_or_create_lead(tg_id, contact_id, lead_name)
            _amo_client_cache[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
            _save_amo_map(tg_id, contact_id, lead_id)  # ÃÂ¿ÃÂµÃÂÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ½ÃÂÃÂ½ÃÂ¾
        else:
            lead_id = _amo_client_cache[tg_id].get("lead_id", 0)

            # ÃÂÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂ½ÃÂ°ÃÂ·ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂ´ÃÂµÃÂ»ÃÂºÃÂ¸ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂÃÂÃÂ°ÃÂ» ÃÂ³ÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¼
            if qualification == "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹" and interest and lead_id:
                amo_request("PATCH", "leads", [{"id": lead_id, "name": f"{name} Ã¢ÂÂ {interest}"}])

        if not lead_id:
            return

        # ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂºÃÂ°ÃÂº ÃÂºÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂ½ÃÂÃÂ°ÃÂÃÂ¸ÃÂ¹
        note = f"Ã°ÂÂÂ¤ {name}: {message_text}\nÃ°ÂÂ¤Â ÃÂ®ÃÂ»ÃÂ: {bot_reply[:300]}"
        if interest:
            note += f"\nÃ°ÂÂÂ¦ ÃÂÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ: {interest}"
        if budget:
            note += f"\nÃ°ÂÂÂ° ÃÂÃÂÃÂ´ÃÂ¶ÃÂµÃÂ: {budget:,} Ã¢ÂÂ½".replace(",", " ")
        if qualification:
            note += f"\nÃ°ÂÂÂ ÃÂ¡ÃÂÃÂ°ÃÂÃÂÃÂ: {qualification}"
        amo_add_note(lead_id, note)

        # ÃÂÃÂ²ÃÂ¸ÃÂ³ÃÂ°ÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ ÃÂ²ÃÂ¾ÃÂÃÂ¾ÃÂ½ÃÂºÃÂµ + ÃÂ¾ÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂÃÂÃÂ¼ÃÂ¼ÃÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ¸ÃÂ·ÃÂ²ÃÂµÃÂÃÂÃÂµÃÂ½ ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂ
        if qualification in ("ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹", "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ"):
            amo_move_pipeline(lead_id, qualification, interest, budget)

        logger.info(f"amoCRM sync: tg={tg_id} lead={lead_id} qual={qualification}")
    except Exception as e:
        logger.error(f"amoCRM sync error: {e}")


def director_get_revenue_stats(days: int, group_by: str = "ÃÂ¸ÃÂÃÂ¾ÃÂ³ÃÂ¾") -> dict:
    """ÃÂ¡ÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ° ÃÂ²ÃÂÃÂÃÂÃÂÃÂºÃÂ¸. ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ¸ÃÂº: amoCRM (ÃÂ¾ÃÂÃÂ½ÃÂ¾ÃÂ²ÃÂ½ÃÂ¾ÃÂ¹) ÃÂ¸ÃÂ»ÃÂ¸ Notion (fallback)."""

    # Ã¢ÂÂÃ¢ÂÂ amoCRM Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if AMO_TOKEN:
        leads = amo_get_leads(days)
        prev_leads = amo_get_leads(days * 2)
        # prev_leads ÃÂ²ÃÂºÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂ ÃÂÃÂµÃÂºÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ¿ÃÂµÃÂÃÂ¸ÃÂ¾ÃÂ´ Ã¢ÂÂ ÃÂÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼
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
                # ÃÂÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂ
                embedded = d.get("_embedded", {})
                users = embedded.get("users", []) if isinstance(embedded, dict) else []
                manager = users[0].get("name", "ÃÂÃÂµ ÃÂ½ÃÂ°ÃÂ·ÃÂ½ÃÂ°ÃÂÃÂµÃÂ½") if users else "ÃÂÃÂµ ÃÂ½ÃÂ°ÃÂ·ÃÂ½ÃÂ°ÃÂÃÂµÃÂ½"
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

    # Ã¢ÂÂÃ¢ÂÂ Notion fallback Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    from datetime import timedelta
    now = datetime.utcnow()
    since = (now - timedelta(days=days)).date().isoformat()
    try:
        r = notion.databases.query(
            database_id=DEALS_DB_ID,
            filter={"property": "ÃÂÃÂµÃÂ´ÃÂ»ÃÂ°ÃÂ¹ÃÂ½", "date": {"on_or_after": since}}
        )
        deals = r.get("results", [])
    except Exception:
        r = notion.databases.query(database_id=DEALS_DB_ID, page_size=100)
        deals = r.get("results", [])

    total_rub = sum(d.get("properties", {}).get("ÃÂ¡ÃÂÃÂ¼ÃÂ¼ÃÂ° Ã¢ÂÂ½", {}).get("number") or 0 for d in deals)
    count = len(deals)

    by_stage = {}
    for d in deals:
        props = d.get("properties", {})
        stage = (props.get("ÃÂ¡ÃÂÃÂ°ÃÂ´ÃÂ¸ÃÂ", {}).get("status") or {}).get("name", "Ã¢ÂÂ")
        rub = props.get("ÃÂ¡ÃÂÃÂ¼ÃÂ¼ÃÂ° Ã¢ÂÂ½", {}).get("number") or 0
        by_stage[stage] = by_stage.get(stage, {"count": 0, "sum_rub": 0})
        by_stage[stage]["count"] += 1
        by_stage[stage]["sum_rub"] += rub

    return {
        "source": "Notion (amoCRM ÃÂÃÂ¾ÃÂºÃÂµÃÂ½ ÃÂ½ÃÂµ ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ²ÃÂµÃÂ½)",
        "period_days": days,
        "current": {"count": count, "total": total_rub, "avg": total_rub // count if count else 0, "by_stage": by_stage},
        "previous": {},
        "delta": None,
        "delta_pct": None,
    }


def director_list_leads(qualification: str, limit: int = 10) -> list:
    """ÃÂ¡ÃÂ¿ÃÂ¸ÃÂÃÂ¾ÃÂº ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² Ã¢ÂÂ ÃÂ¸ÃÂ· amoCRM (ÃÂ¾ÃÂÃÂ½ÃÂ¾ÃÂ²ÃÂ½ÃÂ¾ÃÂ¹) ÃÂ¸ÃÂ»ÃÂ¸ Notion (fallback)."""

    # Ã¢ÂÂÃ¢ÂÂ amoCRM Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if AMO_TOKEN:
        import urllib.parse
        # ÃÂÃÂ°ÃÂ¿ÃÂ¿ÃÂ¸ÃÂ½ÃÂ³ ÃÂºÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸ Ã¢ÂÂ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ amoCRM (ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂµÃÂÃÂ½ÃÂÃÂ¹)
        status_filter = ""
        if qualification == "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹":
            # ÃÂÃÂÃÂµÃÂ¼ ÃÂ»ÃÂ¸ÃÂ´ÃÂ ÃÂ² ÃÂÃÂÃÂ°ÃÂ´ÃÂ¸ÃÂ¸ ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ¾ÃÂ²/ÃÂÃÂ
            pass  # ÃÂÃÂ¸ÃÂ»ÃÂÃÂÃÂÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ pipeline stage ÃÂ¿ÃÂ¾ÃÂ·ÃÂ¶ÃÂµ

        r = amo_request("GET", f"leads?limit={min(limit,50)}&with=contacts&order[created_at]=desc")
        raw_leads = r.get("_embedded", {}).get("leads", [])

        leads = []
        for l in raw_leads:
            contacts = l.get("_embedded", {}).get("contacts", []) if isinstance(l.get("_embedded"), dict) else []
            client = contacts[0].get("name", "Ã¢ÂÂ") if contacts else "Ã¢ÂÂ"
            price = l.get("price") or 0
            created = l.get("created_at", 0)
            from datetime import datetime as _dt
            created_str = _dt.fromtimestamp(created).strftime("%d.%m.%Y %H:%M") if created else "Ã¢ÂÂ"
            leads.append({
                "id": l.get("id"),
                "name": l.get("name", "Ã¢ÂÂ"),
                "client": client,
                "price": price,
                "status_id": l.get("status_id"),
                "created_at": created_str,
                "source": "amoCRM"
            })

        # ÃÂ¤ÃÂ¸ÃÂ»ÃÂÃÂÃÂÃÂ°ÃÂÃÂ¸ÃÂ ÃÂ¿ÃÂ¾ qualification ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ¾
        if qualification == "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹":
            # ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂµ Ã¢ÂÂ ÃÂ½ÃÂµ ÃÂ·ÃÂ°ÃÂºÃÂÃÂÃÂÃÂÃÂµ ÃÂ¸ ÃÂ ÃÂÃÂÃÂ¼ÃÂ¼ÃÂ¾ÃÂ¹ > 0
            leads = [l for l in leads if l.get("price", 0) > 0][:limit]
        elif qualification != "ÃÂ²ÃÂÃÂµ":
            leads = leads[:limit]

        return leads if leads else [{"note": "ÃÂ amoCRM ÃÂ½ÃÂµÃÂ ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² ÃÂ·ÃÂ° ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂµÃÂµ ÃÂ²ÃÂÃÂµÃÂ¼ÃÂ"}]

    # Ã¢ÂÂÃ¢ÂÂ Notion fallback Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    try:
        if qualification != "ÃÂ²ÃÂÃÂµ":
            r = notion.databases.query(
                database_id=NOTION_DB_ID,
                filter={"property": "ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ", "select": {"equals": qualification}},
                page_size=min(limit, 20)
            )
        else:
            r = notion.databases.query(database_id=NOTION_DB_ID, page_size=min(limit, 20))
    except Exception as e:
        return [{"error": f"ÃÂÃÂÃÂ¸ÃÂ±ÃÂºÃÂ° Notion: {e}"}]

    leads = []
    for p in r.get("results", []):
        props = p.get("properties", {})
        name_arr = props.get("Name", {}).get("title", [])
        name = name_arr[0]["plain_text"] if name_arr else "Ã¢ÂÂ"
        qual = (props.get("ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ", {}).get("select") or {}).get("name", "Ã¢ÂÂ")
        interest = (props.get("ÃÂÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ", {}).get("select") or {}).get("name", "Ã¢ÂÂ")
        budget = props.get("ÃÂÃÂÃÂ´ÃÂ¶ÃÂµÃÂ Ã¢ÂÂ½", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        leads.append({"name": name, "qual": qual, "interest": interest,
                      "budget": budget, "tg_id": tg_id, "source": "Notion"})
    return leads


async def handle_owner_director(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Director Mode Ã¢ÂÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂµÃÂ ÃÂ·ÃÂ°ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ ÃÂ¾ ÃÂ±ÃÂ¸ÃÂ·ÃÂ½ÃÂµÃÂÃÂµ."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    messages = [{"role": "user", "content": text}]
    bot_ref = context.bot

    # ÃÂ¦ÃÂ¸ÃÂºÃÂ» tool_use
    for _ in range(5):  # ÃÂ¼ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ¼ÃÂÃÂ¼ 5 ÃÂ²ÃÂÃÂ·ÃÂ¾ÃÂ²ÃÂ¾ÃÂ² ÃÂ¸ÃÂ½ÃÂÃÂÃÂÃÂÃÂ¼ÃÂµÃÂ½ÃÂÃÂ¾ÃÂ²
        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=DIRECTOR_SYSTEM,
            tools=DIRECTOR_TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # ÃÂ¤ÃÂ¸ÃÂ½ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂ
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
                            inp.get("qualification", "ÃÂ²ÃÂÃÂµ"),
                            inp.get("limit", 10)
                        )
                    elif tool == "send_to_client":
                        tg_id = inp["tg_id"]
                        text = inp["text"]

                        # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂ»ÃÂ¸ÃÂ´ÃÂ°ÃÂÃÂ¸ÃÂ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° ÃÂ¿ÃÂµÃÂÃÂµÃÂ´ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂºÃÂ¾ÃÂ¹ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
                        photo_urls_check = inp.get("photo_urls", [])
                        buttons_check = inp.get("buttons", [])
                        all_urls = photo_urls_check + [b.get("url","") for b in buttons_check]
                        altacasa_urls = [u for u in all_urls if "kokahouse.ru" in u]

                        if altacasa_urls:
                            # ÃÂÃÂ·ÃÂ²ÃÂ»ÃÂµÃÂºÃÂ°ÃÂµÃÂ¼ product key ÃÂ¸ÃÂ· URL ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂµÃÂºÃÂÃÂÃÂ°
                            import re as _re
                            product_key = None
                            for url in altacasa_urls:
                                m = _re.search(r'product(\d*)', url)
                                if m:
                                    product_key = url.split("/")[-1].replace(".html","")

                            # ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ¸ÃÂ· ÃÂºÃÂµÃÂÃÂ° ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ¾ÃÂ²
                            client_history = dialogs.get(tg_id, [])
                            client_interests = []
                            for msg in client_history[-10:]:
                                content = msg.get("content","") if isinstance(msg.get("content"), str) else ""
                                for cat in ["ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½","ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾","ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ","ÃÂÃÂÃÂ¾ÃÂ»","ÃÂÃÂÃÂÃÂ»","ÃÂÃÂºÃÂ°ÃÂ","ÃÂÃÂÃÂ¼ÃÂ±ÃÂ°","ÃÂ³ÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±"]:
                                    if cat in content.lower():
                                        client_interests.append(cat)

                            # ÃÂÃÂ°ÃÂÃÂµÃÂ³ÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ÃÂ¾ÃÂ³ÃÂ¾ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° ÃÂ¸ÃÂ· ÃÂÃÂµÃÂºÃÂÃÂÃÂ°
                            sending_cats = []
                            for cat in ["ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½","ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾","ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ","ÃÂÃÂÃÂ¾ÃÂ»","ÃÂÃÂÃÂÃÂ»","ÃÂÃÂºÃÂ°ÃÂ","ÃÂÃÂÃÂ¼ÃÂ±ÃÂ°","ÃÂ³ÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±"]:
                                if cat in text.lower() or any(cat in u.lower() for u in all_urls):
                                    sending_cats.append(cat)

                            # ÃÂÃÂÃÂ»ÃÂ¸ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂµÃÂÃÂ ÃÂ¸ÃÂ·ÃÂ²ÃÂµÃÂÃÂÃÂ½ÃÂ ÃÂ¸ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ ÃÂ½ÃÂµ ÃÂÃÂ¾ÃÂ²ÃÂ¿ÃÂ°ÃÂ´ÃÂ°ÃÂµÃÂ Ã¢ÂÂ WARNING
                            if client_interests and sending_cats:
                                mismatch = not any(c in client_interests for c in sending_cats)
                                if mismatch:
                                    warning_msg = (
                                        f"Ã¢ÂÂ Ã¯Â¸Â ÃÂÃÂÃÂÃÂÃÂÃÂÃÂÃÂ!\n"
                                        f"ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂµÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ»ÃÂÃÂ: {', '.join(set(client_interests))}\n"
                                        f"ÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂÃÂµ: {', '.join(set(sending_cats))}\n\n"
                                        f"ÃÂ­ÃÂÃÂ¾ ÃÂ½ÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ½ÃÂ¾? ÃÂ¡ÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ²ÃÂÃÂ ÃÂÃÂ°ÃÂ²ÃÂ½ÃÂ¾ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾."
                                    )
                                    await bot_ref.send_message(
                                        chat_id=int(MANAGER_CHAT_ID),
                                        text=warning_msg
                                    )
                        # Ã¢ÂÂÃ¢ÂÂ ÃÂºÃÂ¾ÃÂ½ÃÂµÃÂ ÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂ´ÃÂ°ÃÂÃÂ¸ÃÂ¸ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
                        photo_urls = inp.get("photo_urls", [])
                        buttons = inp.get("buttons", [])

                        # ÃÂ¡ÃÂÃÂÃÂ¾ÃÂ¸ÃÂ¼ inline-ÃÂºÃÂ»ÃÂ°ÃÂ²ÃÂ¸ÃÂ°ÃÂÃÂÃÂÃÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂµÃÂÃÂÃÂ ÃÂºÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ¸
                        reply_markup = None
                        if buttons:
                            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                            keyboard = [[InlineKeyboardButton(b["text"], url=b["url"])] for b in buttons if b.get("url")]
                            if keyboard:
                                reply_markup = InlineKeyboardMarkup(keyboard)

                        if photo_urls:
                            if len(photo_urls) == 1:
                                # ÃÂÃÂ´ÃÂ½ÃÂ¾ ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¿ÃÂ¸ÃÂÃÂÃÂ
                                await bot_ref.send_photo(
                                    chat_id=tg_id,
                                    photo=photo_urls[0],
                                    caption=text[:1024],
                                    reply_markup=reply_markup
                                )
                            else:
                                # ÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂ¾ÃÂÃÂ¾ Ã¢ÂÂ media group
                                from telegram import InputMediaPhoto
                                media = [InputMediaPhoto(media=url, caption=text[:1024] if i == 0 else None)
                                         for i, url in enumerate(photo_urls[:10])]
                                await bot_ref.send_media_group(chat_id=tg_id, media=media)
                                if reply_markup:
                                    await bot_ref.send_message(chat_id=tg_id, text="Ã°ÂÂÂ ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ¾ÃÂÃÂÃÂ¸ÃÂÃÂµ ÃÂ²ÃÂ°ÃÂÃÂ¸ÃÂ°ÃÂ½ÃÂÃÂ ÃÂ²ÃÂÃÂÃÂµ", reply_markup=reply_markup)
                        else:
                            # ÃÂ¢ÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ ÃÂºÃÂ½ÃÂ¾ÃÂ¿ÃÂºÃÂ°ÃÂ¼ÃÂ¸
                            await bot_ref.send_message(
                                chat_id=tg_id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode="Markdown"
                            )
                        result = {"status": "sent", "tg_id": tg_id, "photos": len(photo_urls), "buttons": len(buttons)}
                    elif tool == "get_channel_info":
                        result = {"channel": CHANNEL_ID, "note": "ÃÂÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ° ÃÂ´ÃÂ¾ÃÂÃÂÃÂÃÂ¿ÃÂ½ÃÂ ÃÂÃÂµÃÂÃÂµÃÂ· Telegram API"}
                    elif tool == "reply_to_lead":
                        # ÃÂÃÂÃÂµÃÂ¼ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ² Notion ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸
                        clients = director_find_client(inp["client_name"])
                        if not clients:
                            result = {"error": f"ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ '{inp['client_name']}' ÃÂ½ÃÂµ ÃÂ½ÃÂ°ÃÂ¹ÃÂ´ÃÂµÃÂ½ ÃÂ² ÃÂ±ÃÂ°ÃÂ·ÃÂµ"}
                        else:
                            client = clients[0]
                            tg_id = client.get("tg_id")
                            if not tg_id:
                                result = {"error": f"ÃÂ£ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° {client['name']} ÃÂ½ÃÂµÃÂ Telegram ID"}
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
                                # ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂ² amoCRM ÃÂºÃÂ°ÃÂº ÃÂ¸ÃÂÃÂÃÂ¾ÃÂ´ÃÂÃÂÃÂµÃÂµ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ
                                if tg_id in _amo_client_cache:
                                    lead_id = _amo_client_cache[tg_id].get("lead_id", 0)
                                    amo_add_note(lead_id, f"Ã°ÂÂÂ¤ ÃÂÃÂÃÂÃÂ¾ÃÂ´ÃÂÃÂÃÂµÃÂµ ÃÂ¾ÃÂ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ° Ã¢ÂÂ {client['name']}:\n{msg}")
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
                            inp.get("group_by", "ÃÂ¸ÃÂÃÂ¾ÃÂ³ÃÂ¾")
                        )
                except Exception as e:
                    result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str)
                })

            messages.append({"role": "user", "content": tool_results})

    await update.message.reply_text("ÃÂÃÂµ ÃÂÃÂ´ÃÂ°ÃÂ»ÃÂ¾ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ. ÃÂÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ±ÃÂÃÂ¹ ÃÂ¿ÃÂµÃÂÃÂµÃÂÃÂ¾ÃÂÃÂ¼ÃÂÃÂ»ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ.")


# Ã¢ÂÂÃ¢ÂÂ ÃÂ¥ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂÃÂµ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ¾ÃÂ² Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
dialogs: dict[int, list[dict]] = {}
MAX_HISTORY = 12


# Ã¢ÂÂÃ¢ÂÂ Notion helpers Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

def get_or_create_client(tg_id: int, name: str, username: str) -> str:
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "Telegram ID", "number": {"equals": tg_id}}
    )
    if results["results"]:
        page = results["results"][0]
        page_id = page["id"]
        # ÃÂÃÂ°ÃÂ³ÃÂÃÂÃÂ¶ÃÂ°ÃÂµÃÂ¼ ÃÂ¸ÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ° ÃÂ¸ÃÂ· Notion ÃÂ² ÃÂ¿ÃÂ°ÃÂ¼ÃÂÃÂÃÂ
        try:
            history_raw = page["properties"].get("ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ JSON", {}).get("rich_text", [])
            if history_raw:
                history_json = history_raw[0]["plain_text"]
                loaded = json.loads(history_json)
                if loaded and tg_id not in dialogs:
                    dialogs[tg_id] = loaded
                    logger.info(f"ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ·ÃÂ°ÃÂ³ÃÂÃÂÃÂ¶ÃÂµÃÂ½ÃÂ° ÃÂ´ÃÂ»ÃÂ {tg_id}: {len(loaded)} ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ¹")
        except Exception as e:
            logger.error(f"History load error: {e}")
        return page_id

    tg_url = f"https://t.me/{username}" if username else None
    props = {
        "Name":        {"title": [{"text": {"content": name}}]},
        "Telegram ID": {"number": tg_id},
        "ÃÂÃÂ°ÃÂ½ÃÂ°ÃÂ»":       {"select": {"name": "Telegram"}},
        "ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ":{"select": {"name": "ÃÂ¥ÃÂ¾ÃÂ»ÃÂ¾ÃÂ´ÃÂ½ÃÂÃÂ¹"}},
        "ÃÂ¯ÃÂ·ÃÂÃÂº":        {"select": {"name": "RU"}},
        "ÃÂÃÂ°ÃÂÃÂ°":        {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    if tg_url:
        props["Telegram"] = {"url": tg_url}
    page = notion.pages.create(parent={"database_id": NOTION_DB_ID}, properties=props)
    logger.info(f"ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ: {name} ({tg_id})")
    return page["id"]


def update_client(page_id: str, dialog_text: str, history: list = None,
                  qualification: str = None, interest: str = None,
                  budget: float = None, escalate: bool = False):
    # ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ 20 ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ¹ ÃÂºÃÂ°ÃÂº JSON (ÃÂÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂµÃÂºÃÂÃÂÃÂ¾ÃÂ²ÃÂÃÂµ)
    history_json = ""
    if history:
        text_only = [m for m in history if isinstance(m.get("content"), str)][-20:]
        history_json = json.dumps(text_only, ensure_ascii=False)

    props = {
        "ÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ ÃÂ ÃÂ±ÃÂ¾ÃÂÃÂ¾ÃÂ¼": {"rich_text": [{"text": {"content": dialog_text[-2000:]}}]},
    }
    if history_json:
        props["ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ JSON"] = {"rich_text": [{"text": {"content": history_json[:2000]}}]}
    if qualification:
        props["ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ"] = {"select": {"name": qualification}}
    if interest:
        props["ÃÂÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ"] = {"select": {"name": interest}}
    if budget:
        props["ÃÂÃÂÃÂ´ÃÂ¶ÃÂµÃÂ Ã¢ÂÂ½"] = {"number": budget}
    if escalate:
        props["ÃÂ­ÃÂÃÂºÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ"] = {"checkbox": True}
        props["ÃÂÃÂ²ÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ"] = {"select": {"name": "ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ½ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ"}}
    notion.pages.update(page_id=page_id, properties=props)


# Ã¢ÂÂÃ¢ÂÂ AI ÃÂ»ÃÂ¾ÃÂ³ÃÂ¸ÃÂºÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

def ask_claude(chat_id: int, user_message: str, image_data: dict = None, extra_system: str = "") -> dict:
    history = dialogs.get(chat_id, [])

    if image_data:
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": image_data["media_type"], "data": image_data["data"]}},
            {"type": "text", "text": user_message or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ°ÃÂ» ÃÂ¸ÃÂ·ÃÂ¾ÃÂ±ÃÂÃÂ°ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ. ÃÂÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂÃÂÃÂ¾ ÃÂ½ÃÂ° ÃÂ½ÃÂÃÂ¼ ÃÂ¸ ÃÂºÃÂ°ÃÂº ÃÂÃÂÃÂ¾ ÃÂÃÂ²ÃÂÃÂ·ÃÂ°ÃÂ½ÃÂ¾ ÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂÃÂ."}
        ]
        history.append({"role": "user", "content": content})
    else:
        history.append({"role": "user", "content": user_message})

    # ÃÂ£ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¸ÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ»ÃÂ API (ÃÂÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂµÃÂºÃÂÃÂ)
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
    """ÃÂ¡ÃÂºÃÂ°ÃÂÃÂ°ÃÂÃÂ ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ¸ÃÂ· Telegram ÃÂ¸ ÃÂ²ÃÂµÃÂÃÂ½ÃÂÃÂÃÂ base64."""
    file = await bot.get_file(file_id)
    url  = file.file_path
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    data = base64.standard_b64encode(resp.content).decode()
    return {"data": data, "media_type": "image/jpeg"}


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂÃÂ°ÃÂ»ÃÂ¾ÃÂ³ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ¾ÃÂ² (ÃÂ´ÃÂ»ÃÂ deep links ÃÂ ÃÂÃÂ°ÃÂ¹ÃÂÃÂ°) Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
PRODUCTS = {
    # ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ
    "mc_a68": {
        "name": "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MC-A68",
        "desc": "ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ°ÃÂ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ° oil-wax, ÃÂ³ÃÂÃÂÃÂ¸ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ, ÃÂ»ÃÂ¸ÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂ¸ÃÂÃÂ°. 3-ÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹ 230ÃÂ97ÃÂ92 ÃÂÃÂ¼.",
        "price": "ÃÂ¾ÃÂ 235 224 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "fort": {
        "name": "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ FORT",
        "desc": "ÃÂÃÂÃÂµÃÂ/ÃÂÃÂÃÂµÃÂ½ÃÂ + ÃÂ²ÃÂµÃÂ»ÃÂÃÂ, ÃÂ²ÃÂÃÂÃÂ¾ÃÂºÃÂ¾ÃÂ¿ÃÂ»ÃÂ¾ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ½. 2Ã¢ÂÂ4 ÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹.",
        "price": "ÃÂ¾ÃÂ 99 634 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "pr701": {
        "name": "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ PR701 ÃÂ«ÃÂÃÂ±ÃÂ»ÃÂ°ÃÂºÃÂ¾ÃÂ»",
        "desc": "ÃÂÃÂ¾ÃÂ´ÃÂÃÂ»ÃÂÃÂ½ÃÂÃÂ¹. ÃÂ¥ÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, ÃÂ³ÃÂÃÂÃÂ¸ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ, ÃÂ»ÃÂ¸ÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂ¸ÃÂÃÂ°. 3Ã¢ÂÂ4 ÃÂ¼ÃÂµÃÂÃÂÃÂ° + ÃÂ¿ÃÂÃÂ.",
        "price": "ÃÂ¾ÃÂ 219 109 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "mk_sofa01": {
        "name": "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MK-SOFA01",
        "desc": "ÃÂÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ/ÃÂ·ÃÂ°ÃÂ¼ÃÂÃÂµÃÂ²ÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ°, ÃÂ¾ÃÂÃÂµÃÂ, ÃÂ»ÃÂ¸ÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂ¸ÃÂÃÂ°. 2Ã¢ÂÂ3 ÃÂ¼ÃÂµÃÂÃÂÃÂ°.",
        "price": "ÃÂ¾ÃÂ 272 833 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "qmw2023": {
        "name": "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ QMW-2023",
        "desc": "ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ°ÃÂ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ°, ÃÂ½ÃÂµÃÂÃÂ¶ÃÂ°ÃÂ²ÃÂµÃÂÃÂÃÂ°ÃÂ ÃÂÃÂÃÂ°ÃÂ»ÃÂ. 1Ã¢ÂÂ4 ÃÂ¼ÃÂµÃÂÃÂÃÂ°.",
        "price": "ÃÂ¾ÃÂ 59 895 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    # ÃÂÃÂÃÂµÃÂÃÂ»ÃÂ°
    "lanyue": {
        "name": "ÃÂÃÂÃÂµÃÂÃÂ»ÃÂ¾ ÃÂ«ÃÂÃÂ°ÃÂ½ÃÂÃÂÃÂÃÂ» ZX-LY3",
        "desc": "ÃÂ¡ÃÂµÃÂ².-ÃÂ°ÃÂ¼ÃÂµÃÂÃÂ¸ÃÂºÃÂ°ÃÂ½ÃÂÃÂºÃÂ¸ÃÂ¹ ÃÂ¾ÃÂÃÂµÃÂ, ÃÂÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, ÃÂ¿ÃÂ¾ÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ½ + ÃÂÃÂ¾ÃÂ»ÃÂ»ÃÂ¾ÃÂÃÂ°ÃÂ¹ÃÂ±ÃÂµÃÂ. 64ÃÂ102ÃÂ74 ÃÂÃÂ¼.",
        "price": "118 921 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "mercer": {
        "name": "ÃÂÃÂÃÂµÃÂÃÂ»ÃÂ¾ MERCER",
        "desc": "ÃÂÃÂÃÂµÃÂ/ÃÂÃÂÃÂµÃÂ½ÃÂ, ÃÂ¿ÃÂÃÂµÃÂ¼ÃÂ¸ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, ÃÂ²ÃÂÃÂÃÂ¾ÃÂºÃÂ¾ÃÂ¿ÃÂ»ÃÂ¾ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ½. 70ÃÂ96ÃÂ95 ÃÂÃÂ¼.",
        "price": "ÃÂ¾ÃÂ 127 490 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "florence": {
        "name": "ÃÂÃÂÃÂµÃÂÃÂ»ÃÂ¾ Lounge Florence",
        "desc": "ÃÂÃÂ¾ÃÂ¶ÃÂ° full-grain, ÃÂºÃÂ°ÃÂÃÂºÃÂ°ÃÂ ÃÂ¸ÃÂ· ÃÂ¾ÃÂÃÂµÃÂÃÂ¾ÃÂ²ÃÂ¾ÃÂ³ÃÂ¾ ÃÂ´ÃÂµÃÂÃÂµÃÂ²ÃÂ°. ÃÂ¡ÃÂÃÂ¸ÃÂ»ÃÂ mid-century modern.",
        "price": "ÃÂ¾ÃÂ 47 500 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "2 ÃÂÃÂ",
    },
    # ÃÂÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ¸
    "roma": {
        "name": "ÃÂÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ Roma Platform",
        "desc": "ÃÂÃÂ°ÃÂÃÂÃÂ¸ÃÂ² ÃÂ´ÃÂÃÂ±ÃÂ°, ÃÂ¼ÃÂÃÂ³ÃÂºÃÂ¾ÃÂµ ÃÂ¸ÃÂ·ÃÂ³ÃÂ¾ÃÂ»ÃÂ¾ÃÂ²ÃÂÃÂµ, ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂÃÂ¼ÃÂ½ÃÂÃÂ¹ ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ·ÃÂ¼. ÃÂ ÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂÃÂ 160/180/200.",
        "price": "ÃÂ¾ÃÂ 62 000 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "5Ã¢ÂÂ7 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    # ÃÂ¡ÃÂÃÂ¾ÃÂ»ÃÂ¸ÃÂºÃÂ¸
    "cj106": {
        "name": "ÃÂÃÂÃÂÃÂ½ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¾ÃÂ»ÃÂ¸ÃÂº MK-CJ106",
        "desc": "ÃÂÃÂ°ÃÂÃÂÃÂ¸ÃÂ² ÃÂÃÂµÃÂ².-ÃÂ°ÃÂ¼ÃÂµÃÂÃÂ¸ÃÂºÃÂ°ÃÂ½ÃÂÃÂºÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¾ÃÂÃÂµÃÂÃÂ°. 135ÃÂ75ÃÂ36 ÃÂÃÂ¼.",
        "price": "98 593 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "palazzo": {
        "name": "ÃÂÃÂ±ÃÂµÃÂ´ÃÂµÃÂ½ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¾ÃÂ» Palazzo",
        "desc": "ÃÂ¡ÃÂÃÂ¾ÃÂ»ÃÂµÃÂÃÂ½ÃÂ¸ÃÂÃÂ° ÃÂ¸ÃÂ· ÃÂ¸ÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¼ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂÃÂ° Calacatta, ÃÂ½ÃÂµÃÂÃÂ¶ÃÂ°ÃÂ²ÃÂµÃÂÃÂÃÂ°ÃÂ ÃÂÃÂÃÂ°ÃÂ»ÃÂ. ÃÂ120/140/160 ÃÂÃÂ¼.",
        "price": "ÃÂ¾ÃÂ 118 000 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "7Ã¢ÂÂ10 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "2 ÃÂÃÂ",
    },
    # ÃÂÃÂÃÂ¸ÃÂ
    "executive": {
        "name": "ÃÂ¡ÃÂÃÂ¾ÃÂ» ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ½ÃÂÃÂ¹ Executive",
        "desc": "ÃÂ¨ÃÂ¿ÃÂ¾ÃÂ½ ÃÂ°ÃÂ¼ÃÂµÃÂÃÂ¸ÃÂºÃÂ°ÃÂ½ÃÂÃÂºÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¾ÃÂÃÂµÃÂÃÂ°, ÃÂÃÂÃÂ¾ÃÂ¼. 3.6Ã¢ÂÂ6.0 ÃÂ¼. ÃÂÃÂÃÂÃÂÃÂ¾ÃÂµÃÂ½ÃÂ½ÃÂÃÂµ ÃÂºÃÂ°ÃÂ±ÃÂµÃÂ»ÃÂ-ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ.",
        "price": "ÃÂ¾ÃÂ 210 000 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "1 ÃÂÃÂ",
    },
    "cabinet_pro": {
        "name": "ÃÂÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂ°ÃÂ ÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ¼ÃÂ° Cabinet Pro",
        "desc": "ÃÂÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ»ÃÂ°ÃÂº + ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂ¿ÃÂ¾ÃÂ½, ÃÂ°ÃÂ»ÃÂÃÂ¼ÃÂ¸ÃÂ½ÃÂ¸ÃÂµÃÂ²ÃÂÃÂµ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ÃÂ»ÃÂ¸. ÃÂÃÂ¾ÃÂ´ ÃÂÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂ.",
        "price": "ÃÂ¾ÃÂ 94 000 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂ¼",
    },
    # ÃÂÃÂÃÂµÃÂ»ÃÂ
    "grand_hotel": {
        "name": "ÃÂ ÃÂµÃÂÃÂµÃÂ¿ÃÂÃÂ½-ÃÂÃÂÃÂ¾ÃÂ¹ÃÂºÃÂ° Grand Hotel",
        "desc": "ÃÂÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ°ÃÂ²ÃÂµÃÂÃÂÃÂ¸ÃÂ½/ÃÂ¼ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ + ÃÂºÃÂ²ÃÂ°ÃÂÃÂ. ÃÂÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂºÃÂ° ÃÂ² ÃÂ±ÃÂ°ÃÂ·ÃÂµ. ÃÂÃÂ¾ÃÂ»ÃÂ½ÃÂ¾ÃÂÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ´ ÃÂÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂ ÃÂ»ÃÂ¾ÃÂ±ÃÂ±ÃÂ¸.",
        "price": "ÃÂ¾ÃÂ 157 200 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "8Ã¢ÂÂ12 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂ¼",
    },
    "chateau": {
        "name": "ÃÂÃÂ°ÃÂ½ÃÂºÃÂµÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂÃÂ» Chateau",
        "desc": "ÃÂÃÂÃÂº + ÃÂÃÂºÃÂ°ÃÂ½ÃÂ/ÃÂºÃÂ¾ÃÂ¶ÃÂ°. ÃÂ¨ÃÂÃÂ°ÃÂ±ÃÂµÃÂ»ÃÂ¸ÃÂÃÂÃÂµÃÂ¼ÃÂÃÂ¹. 50+ ÃÂÃÂ°ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ¾ÃÂº. ÃÂ¡ÃÂµÃÂÃÂÃÂ¸ÃÂÃÂ¸ÃÂºÃÂ°ÃÂ EN 16139.",
        "price": "ÃÂ¾ÃÂ 4 200 Ã¢ÂÂ½/ÃÂÃÂ",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "50 ÃÂÃÂ",
    },
    "milano": {
        "name": "ÃÂÃÂÃÂ¸ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ½ÃÂ°ÃÂ ÃÂÃÂÃÂ¼ÃÂ±ÃÂ° Milano",
        "desc": "ÃÂÃÂ°ÃÂºÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¤ 18 ÃÂÃÂ²ÃÂµÃÂÃÂ¾ÃÂ², ÃÂ»ÃÂ°ÃÂÃÂÃÂ½ÃÂ ÃÂ¼ÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ/ÃÂ³ÃÂ»ÃÂÃÂ½ÃÂµÃÂ. ÃÂÃÂÃÂ´ÃÂ²ÃÂ¸ÃÂ¶ÃÂ½ÃÂ¾ÃÂ¹ ÃÂÃÂÃÂ¸ÃÂº ÃÂ½ÃÂ° ÃÂ´ÃÂ¾ÃÂ²ÃÂ¾ÃÂ´ÃÂÃÂ¸ÃÂºÃÂµ.",
        "price": "ÃÂ¾ÃÂ 18 400 Ã¢ÂÂ½",
        "ÃÂÃÂÃÂ¾ÃÂº": "4Ã¢ÂÂ6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ",
        "moq": "4 ÃÂÃÂ",
    },
}

def get_product_context(product_key: str) -> str:
    """ÃÂÃÂµÃÂÃÂ½ÃÂÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ ÃÂ¾ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµÃÂ¼ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° ÃÂ´ÃÂ»ÃÂ ÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ¼ÃÂ½ÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¿ÃÂÃÂ¾ÃÂ¼ÃÂ¿ÃÂÃÂ°."""
    p = PRODUCTS.get(product_key.lower().replace("-", "_").replace(" ", "_"))
    if not p:
        return ""
    return (
        f"\n\nÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n"
        f"ÃÂÃÂÃÂÃÂÃÂÃÂ¢ ÃÂÃÂ ÃÂÃÂ¨ÃÂÃÂ ÃÂ¡ ÃÂÃÂÃÂ ÃÂ¢ÃÂÃÂ§ÃÂÃÂ ÃÂ¢ÃÂÃÂÃÂÃÂ ÃÂ\n"
        f"Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n"
        f"ÃÂ¢ÃÂ¾ÃÂ²ÃÂ°ÃÂ: {p['name']}\n"
        f"ÃÂÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂµ: {p['desc']}\n"
        f"ÃÂ¦ÃÂµÃÂ½ÃÂ°: {p['price']}\n"
        f"ÃÂ¡ÃÂÃÂ¾ÃÂº ÃÂ¿ÃÂÃÂ¾ÃÂ¸ÃÂ·ÃÂ²ÃÂ¾ÃÂ´ÃÂÃÂÃÂ²ÃÂ°: {p['ÃÂÃÂÃÂ¾ÃÂº']}\n"
        f"ÃÂÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ·ÃÂ°ÃÂºÃÂ°ÃÂ·: {p['moq']}\n\n"
        f"ÃÂÃÂ°ÃÂÃÂ½ÃÂ¸ ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂ²ÃÂµÃÂÃÂÃÂÃÂ²ÃÂ¸ÃÂ ÃÂ¸ ÃÂÃÂÃÂ°ÃÂ·ÃÂ ÃÂÃÂ¿ÃÂ¾ÃÂ¼ÃÂÃÂ½ÃÂ¸ ÃÂÃÂÃÂ¾ÃÂ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ ÃÂ¿ÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¸. "
        f"ÃÂ¡ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ ÃÂÃÂÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ½ÃÂ¾ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂÃÂ¾ÃÂÃÂµÃÂ ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ¸ÃÂÃÂ."
    )


# Ã¢ÂÂÃ¢ÂÂ Telegram handlers Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dialogs[user.id] = []

    # ÃÂ§ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¿ÃÂ°ÃÂÃÂ°ÃÂ¼ÃÂµÃÂÃÂ deep link (product key)
    product_key = context.args[0] if context.args else None
    product_ctx = get_product_context(product_key) if product_key else ""

    # amoCRM ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂ ÃÂ¿ÃÂÃÂ¸ ÃÂ¿ÃÂµÃÂÃÂ²ÃÂ¾ÃÂ¼ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ¸

    if product_ctx:
        # ÃÂÃÂÃÂÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµÃÂºÃÂÃÂ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ÃÂ¼ Claude ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ¿ÃÂµÃÂÃÂÃÂ¾ÃÂ½ÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ½ÃÂ¾ÃÂµ ÃÂ¿ÃÂÃÂ¸ÃÂ²ÃÂµÃÂÃÂÃÂÃÂ²ÃÂ¸ÃÂµ
        result = ask_claude(
            user.id,
            f"[ÃÂ¡ÃÂÃÂ¡ÃÂ¢ÃÂÃÂÃÂ: ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¿ÃÂµÃÂÃÂµÃÂÃÂÃÂ» ÃÂ ÃÂºÃÂ°ÃÂÃÂÃÂ¾ÃÂÃÂºÃÂ¸ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ°. ÃÂÃÂ¾ÃÂ¿ÃÂÃÂ¸ÃÂ²ÃÂµÃÂÃÂÃÂÃÂ²ÃÂÃÂ¹ ÃÂ¸ ÃÂ·ÃÂ°ÃÂ´ÃÂ°ÃÂ¹ ÃÂ¿ÃÂµÃÂÃÂ²ÃÂÃÂ¹ ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ.]{product_ctx}",
            extra_system=product_ctx
        )
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(
            "ÃÂÃÂ´ÃÂÃÂ°ÃÂ²ÃÂÃÂÃÂ²ÃÂÃÂ¹ÃÂÃÂµ! ÃÂÃÂµÃÂ½ÃÂ ÃÂ·ÃÂ¾ÃÂ²ÃÂÃÂ ÃÂ®ÃÂ»ÃÂ.\n\n"
            "ÃÂ¯ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ¾ÃÂ³ÃÂ ÃÂ²ÃÂ°ÃÂ¼ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¾ÃÂ±ÃÂÃÂ°ÃÂÃÂ ÃÂºÃÂ°ÃÂÃÂµÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ, "
            "ÃÂÃÂ°ÃÂÃÂÃÂÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂÃÂÃÂ¾ÃÂ¸ÃÂ¼ÃÂ¾ÃÂÃÂÃÂ ÃÂ¸ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¾ÃÂ±ÃÂÃÂ°ÃÂÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ¸ÃÂ¼ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ²ÃÂ°ÃÂÃÂ¸ÃÂ°ÃÂ½ÃÂ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸.\n\n"
            "ÃÂÃÂ¾ÃÂ´ÃÂÃÂºÃÂ°ÃÂ¶ÃÂ¸ÃÂÃÂµ, ÃÂ¿ÃÂ¾ÃÂ¶ÃÂ°ÃÂ»ÃÂÃÂ¹ÃÂÃÂÃÂ°, ÃÂºÃÂ°ÃÂºÃÂÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ²ÃÂ ÃÂÃÂ°ÃÂÃÂÃÂ¼ÃÂ°ÃÂÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂµÃÂÃÂµ: "
            "ÃÂ´ÃÂ»ÃÂ ÃÂ´ÃÂ¾ÃÂ¼ÃÂ°, ÃÂ¾ÃÂÃÂ¸ÃÂÃÂ°, ÃÂÃÂµÃÂÃÂÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ°, ÃÂ¾ÃÂÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂ´ÃÂÃÂÃÂ³ÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¿ÃÂÃÂ¾ÃÂµÃÂºÃÂÃÂ°?"
        )


async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ ÃÂ² ÃÂ±ÃÂ°ÃÂ·ÃÂ. ÃÂ¢ÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ´ÃÂ»ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ°."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    text = update.message.text.replace("/teach", "").strip()
    if not text:
        await update.message.reply_text(
            "Ã°ÂÂÂ *ÃÂÃÂ°ÃÂº ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂµ:*\n\n"
            "`/teach ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ: ÃÂÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂÃÂ¾ÃÂ¸ÃÂ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°?\nÃÂ¾ÃÂÃÂ²ÃÂµÃÂ: ÃÂ¾ÃÂ 3000 Ã¢ÂÂ½ ÃÂ´ÃÂ¾ ÃÂÃÂ¾ÃÂÃÂºÃÂ²ÃÂ`\n\n"
            "ÃÂÃÂ»ÃÂ¸ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂÃÂ¾:\n"
            "`/teach ÃÂÃÂÃÂ»ÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂÃÂ¿ÃÂÃÂ°ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂµÃÂ ÃÂ¿ÃÂÃÂ¾ ÃÂÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂÃÂºÃÂ Ã¢ÂÂ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ°ÃÂ¹ ÃÂÃÂÃÂ¾ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ ÃÂ±ÃÂ°ÃÂ½ÃÂºÃÂ¾ÃÂ¼ ÃÂ¢ÃÂ¸ÃÂ½ÃÂÃÂºÃÂ¾ÃÂÃÂ, ÃÂÃÂ°ÃÂÃÂÃÂÃÂ¾ÃÂÃÂºÃÂ° 0% ÃÂ½ÃÂ° 12 ÃÂ¼ÃÂµÃÂÃÂÃÂÃÂµÃÂ²`",
            parse_mode="Markdown"
        )
        return

    entry = f"[{datetime.now():%d.%m.%Y}] {text}"
    save_knowledge(entry)
    logger.info(f"Knowledge added: {text[:80]}")
    await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾ ÃÂ² ÃÂ±ÃÂ°ÃÂ·ÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹ ÃÂ®ÃÂ»ÃÂ¸:\n\n_{text[:200]}_", parse_mode="Markdown")


async def cmd_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÃÂÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂÃÂÃÂ ÃÂ±ÃÂ°ÃÂ·ÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹. ÃÂ¢ÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ´ÃÂ»ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ°."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    knowledge = load_knowledge()
    if not knowledge:
        await update.message.reply_text("ÃÂÃÂ°ÃÂ·ÃÂ° ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹ ÃÂ¿ÃÂÃÂÃÂÃÂ°. ÃÂÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂ¹ /teach ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ.")
    else:
        await update.message.reply_text(f"Ã°ÂÂÂ *ÃÂÃÂ°ÃÂ·ÃÂ° ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹:*\n\n{knowledge[:3000]}", parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialogs[update.effective_user.id] = []
    await update.message.reply_text("ÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ ÃÂÃÂ±ÃÂÃÂ¾ÃÂÃÂµÃÂ½.")


def detect_owner_intent(text: str) -> str | None:
    """ÃÂÃÂ¿ÃÂÃÂµÃÂ´ÃÂµÃÂ»ÃÂ¸ÃÂÃÂ ÃÂ½ÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° ÃÂ¸ÃÂ· ÃÂÃÂ²ÃÂ¾ÃÂ±ÃÂ¾ÃÂ´ÃÂ½ÃÂ¾ÃÂ³ÃÂ¾ ÃÂÃÂµÃÂºÃÂÃÂÃÂ°. ÃÂÃÂµÃÂÃÂ½ÃÂÃÂÃÂ ÃÂÃÂ¸ÃÂ¿ ÃÂ¸ÃÂ»ÃÂ¸ None."""
    t = text.lower().strip()

    # ÃÂÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ: ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ¸ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ
    post_triggers = [
        "ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¿ÃÂ¾ÃÂÃÂ", "ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ", "ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ", "ÃÂ·ÃÂ°ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ¸", "ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¿ÃÂÃÂ¾",
        "ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¾ ", "ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¾ ", "ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¿ÃÂÃÂ¾ ", "ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂ¹ ÃÂ°ÃÂ½ÃÂ¾ÃÂ½ÃÂ", "ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ°ÃÂ½ÃÂ¾ÃÂ½ÃÂ",
        "ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂ¹ ÃÂ¾ÃÂ±ÃÂÃÂÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¸ÃÂµ", "ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹:", "ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹ ÃÂÃÂµÃÂºÃÂÃÂ", "ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ",
        "ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ", "ÃÂ½ÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ"
    ]
    if any(t.startswith(tr) or tr in t for tr in post_triggers):
        return "post"

    # ÃÂÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ: ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ³ÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ½ÃÂ°ÃÂ¿ÃÂÃÂÃÂ¼ÃÂÃÂ
    direct_triggers = ["ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹: ", "ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»: ", "ÃÂ¿ÃÂ¾ÃÂÃÂ: "]
    if any(t.startswith(tr) for tr in direct_triggers):
        return "direct_post"

    # ÃÂÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ: ÃÂ¾ÃÂ±ÃÂÃÂÃÂ¸ÃÂÃÂ ÃÂ±ÃÂ¾ÃÂÃÂ°
    teach_triggers = [
        "ÃÂ·ÃÂ°ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ½ÃÂ¸:", "ÃÂ·ÃÂ°ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ½ÃÂ¸,", "ÃÂ·ÃÂ°ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ½ÃÂ¸ ÃÂÃÂÃÂ¾", "ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ ÃÂ² ÃÂ±ÃÂ°ÃÂ·ÃÂ", "ÃÂ¾ÃÂ±ÃÂÃÂÃÂ¸",
        "ÃÂÃÂ»ÃÂ ÃÂ´ÃÂ¾ÃÂ»ÃÂ¶ÃÂ½ÃÂ° ÃÂ·ÃÂ½ÃÂ°ÃÂÃÂ", "ÃÂÃÂ»ÃÂ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ°ÃÂµÃÂ", "ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂÃÂ¿ÃÂÃÂ¾ÃÂÃÂÃÂ ÃÂ¿ÃÂÃÂ¾",
        "ÃÂ¾ÃÂÃÂ²ÃÂµÃÂ ÃÂ½ÃÂ° ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ", "ÃÂaq:", "ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂ:", "ÃÂÃÂºÃÂ°ÃÂ¶ÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°ÃÂ¼"
    ]
    if any(t.startswith(tr) or tr in t for tr in teach_triggers):
        return "teach"

    return None




def load_history_from_amo(tg_id: int, name: str = "") -> bool:
    """ÃÂÃÂ°ÃÂ³ÃÂÃÂÃÂ·ÃÂ¸ÃÂÃÂ ÃÂ¸ÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ° ÃÂ¸ÃÂ· amoCRM ÃÂ¿ÃÂÃÂ¸ ÃÂÃÂµÃÂÃÂÃÂ°ÃÂÃÂÃÂµ ÃÂ±ÃÂ¾ÃÂÃÂ°."""
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
                if "Ã°ÂÂÂ¤" in line[:5] and ": " in line:
                    c = line.split(": ", 1)[1].strip()
                    if c:
                        history.append({"role": "user", "content": c})
                elif "Ã°ÂÂ¤Â ÃÂ®ÃÂ»ÃÂ: " in line[:12]:
                    c = line.split("ÃÂ®ÃÂ»ÃÂ: ", 1)[-1].strip()
                    if c:
                        history.append({"role": "assistant", "content": c})
        if history:
            dialogs[tg_id] = history[-MAX_HISTORY:]
            logger.info(f"ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ¸ÃÂ· amoCRM ÃÂ´ÃÂ»ÃÂ {tg_id}: {len(history)} ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂ¹")
            return True
    except Exception as e:
        logger.error(f"load_history_from_amo error: {e}")
    return False

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    name = user.full_name or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ"

    logger.info(f"[{user.id}] {name}: {text}")

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂµÃÂ: ÃÂÃÂ°ÃÂÃÂ¿ÃÂ¾ÃÂ·ÃÂ½ÃÂ°ÃÂÃÂ¼ ÃÂ½ÃÂ°ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ±ÃÂµÃÂ· ÃÂºÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if is_owner(user):
        # ── Ожидаем подпись к отложенному фото ──────────────────────────
        if context.user_data.get("pending_photo"):
            photo_id = context.user_data.pop("pending_photo")
            import re as _re
            btn_pattern = _re.compile(r'\[([^\[\]]+)\|(https?://[^\]]+)\]')
            buttons_found = btn_pattern.findall(text)
            text_clean = btn_pattern.sub("", text).strip()
            reply_markup = None
            if buttons_found:
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup as IKM
                kb = [[InlineKeyboardButton(b[0], url=b[1])] for b in buttons_found]
                reply_markup = IKM(kb)
            try:
                msg = await context.bot.send_photo(
                    chat_id=CHANNEL_ID,
                    photo=photo_id,
                    caption=text_clean if text_clean else None,
                    reply_markup=reply_markup
                )
                post_link = f"https://t.me/{str(CHANNEL_ID).lstrip('@')}/{msg.message_id}"
                await update.message.reply_text(f"✅ Пост опубликован!\n🔗 {post_link}")
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка: {e}")
            return
        # ────────────────────────────────────────────────────────────────
        intent = detect_owner_intent(text)

        if intent == "post":
            # ÃÂÃÂµÃÂ½ÃÂµÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂÃÂµÃÂÃÂµÃÂ· AI ÃÂ¸ ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂµÃÂ¼
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            prompt = f"""ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¿ÃÂÃÂ¾ÃÂ´ÃÂ°ÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ´ÃÂ»ÃÂ Telegram-ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ° KOKAHOUSE.
ÃÂ¢ÃÂµÃÂ¼ÃÂ°: {text}
ÃÂ¢ÃÂÃÂµÃÂ±ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ: 3-4 ÃÂ°ÃÂ±ÃÂ·ÃÂ°ÃÂÃÂ°, ÃÂ¶ÃÂ¸ÃÂ²ÃÂ¾ÃÂ¹ ÃÂÃÂÃÂ¸ÃÂ»ÃÂ, ÃÂÃÂµÃÂ½ÃÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ·ÃÂ½ÃÂ°ÃÂµÃÂÃÂ, ÃÂ² ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµ ÃÂ¿ÃÂÃÂ¸ÃÂ·ÃÂÃÂ² ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ @kokahouse_Yulia.
2-3 emoji ÃÂÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂ¾. ÃÂ¤ÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ Markdown. ÃÂÃÂµÃÂ· ÃÂÃÂÃÂÃÂÃÂµÃÂ³ÃÂ¾ÃÂ².
ÃÂÃÂµÃÂÃÂ½ÃÂ¸ ÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°."""
            response = ai.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            post_text = response.content[0].text.strip()
            context.user_data["pending_post"] = post_text
            await update.message.reply_text(
                f"Ã°ÂÂÂ ÃÂÃÂÃÂµÃÂ²ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°:\n\n{post_text}\n\n"
                f"ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ 'ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹' ÃÂ¸ÃÂ»ÃÂ¸ /confirm ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»."
            )
            return

        if intent == "direct_post":
            # ÃÂÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂµÃÂ¼ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ½ÃÂ°ÃÂ¿ÃÂÃÂÃÂ¼ÃÂÃÂ
            for prefix in ["ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹: ", "ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»: ", "ÃÂ¿ÃÂ¾ÃÂÃÂ: "]:
                if text.lower().startswith(prefix):
                    post_text = text[len(prefix):]
                    break
            else:
                post_text = text
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                await update.message.reply_text("Ã¢ÂÂ ÃÂÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂµ!")
            except Exception as e:
                await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂÃÂ¸ÃÂ±ÃÂºÃÂ°: {e}")
            return

        if intent == "teach":
            entry = f"[{datetime.now():%d.%m.%Y}] {text}"
            save_knowledge(entry)
            await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂ°ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ½ÃÂ¸ÃÂ»ÃÂ°:\n\n{text[:200]}")
            return

        # ÃÂÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂµÃÂ ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ» "ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹" Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ¶ÃÂ´ÃÂµÃÂ½ÃÂ¸ÃÂµ pending ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°
        if text.lower().strip() in ["ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹", "ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ´ÃÂ¸", "ÃÂ¾ÃÂº ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹", "ÃÂ´ÃÂ° ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹", "ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂ¹!"]:
            post_text = context.user_data.get("pending_post")
            if post_text:
                try:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("Ã¢ÂÂ ÃÂÃÂ¾ÃÂÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂµ!")
                except Exception:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("Ã¢ÂÂ ÃÂÃÂ¾ÃÂÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½!")
            else:
                await update.message.reply_text("ÃÂÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ° ÃÂ´ÃÂ»ÃÂ ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸. ÃÂ¡ÃÂ½ÃÂ°ÃÂÃÂ°ÃÂ»ÃÂ° ÃÂ¿ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ.")
            return

        # Ã¢ÂÂÃ¢ÂÂ Director Mode Ã¢ÂÂ ÃÂ²ÃÂÃÂ ÃÂ¾ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾ÃÂµ ÃÂ¾ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° ÃÂ¸ÃÂ´ÃÂÃÂ ÃÂº AI-ÃÂ´ÃÂ¸ÃÂÃÂµÃÂºÃÂÃÂ¾ÃÂÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
        await handle_owner_director(update, context, text)
        return

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂºÃÂ° ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ¶ÃÂ´ÃÂµÃÂ½ÃÂ¸ÃÂ ÃÂÃÂ ÃÂ¾ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    if user.id in pending_kp and text.strip().lower() in [
        "ÃÂ´ÃÂ°", "ÃÂ´ÃÂ°!", "yes", "ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ¾ÃÂ´ÃÂ¸ÃÂ", "ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂµÃÂ½", "ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂ½ÃÂ°",
        "ÃÂ¾ÃÂÃÂ»ÃÂ¸ÃÂÃÂ½ÃÂ¾", "ÃÂÃÂ¾ÃÂÃÂ¾ÃÂÃÂ¾", "ÃÂ±ÃÂµÃÂÃÂÃÂ¼", "ÃÂ±ÃÂµÃÂÃÂµÃÂ¼", "ÃÂ¾ÃÂº", "ok", "Ã°ÂÂÂ"
    ]:
        kp_data = pending_kp[user.id]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")
        try:
            client_name = user.full_name or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ"
            pdf_bytes = await generate_kp_pdf(kp_data, client_name)
            filename = f"ÃÂÃÂ_ALTA_CASA_{datetime.now().strftime('%d%m%Y')}.pdf"

            # ÃÂÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ PDF ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ
            from telegram import InputFile
            import io
            await context.bot.send_document(
                chat_id=user.id,
                document=InputFile(io.BytesIO(pdf_bytes), filename=filename),
                caption=f"ÃÂÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂµ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ KOKAHOUSE\n{kp_data['product']}\nÃÂÃÂÃÂ¾ÃÂ³ÃÂ¾: {kp_data['total']:,} Ã¢ÂÂ½".replace(',', ' ')
            )

            # ÃÂ£ÃÂ²ÃÂµÃÂ´ÃÂ¾ÃÂ¼ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ°
            if kp_data.get("manager_id"):
                await context.bot.send_message(
                    chat_id=kp_data["manager_id"],
                    text=f"Ã¢ÂÂ ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ {client_name} (ID: {user.id}) ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ´ÃÂ¸ÃÂ» ÃÂÃÂ!\nÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾."
                )

            del pending_kp[user.id]
            logger.info(f"ÃÂÃÂ PDF ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ {user.id}")
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            await update.message.reply_text(
                "ÃÂÃÂÃÂ»ÃÂ¸ÃÂÃÂ½ÃÂ¾! ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ°ÃÂ ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ·ÃÂ°ÃÂÃÂ²ÃÂºÃÂ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ Ã¢ÂÂ ÃÂ¾ÃÂ½ ÃÂÃÂ²ÃÂÃÂ¶ÃÂµÃÂÃÂÃÂ ÃÂ ÃÂ²ÃÂ°ÃÂ¼ÃÂ¸ ÃÂ² ÃÂ±ÃÂ»ÃÂ¸ÃÂ¶ÃÂ°ÃÂ¹ÃÂÃÂµÃÂµ ÃÂ²ÃÂÃÂµÃÂ¼ÃÂ."
            )
        return
    import re
    urls_in_text = re.findall(r'https?://[^\s]+', text)
    has_external_link = any(
        "kokahouse.ru" not in url and "t.me" not in url and "max.ru" not in url
        for url in urls_in_text
    )
    # ÃÂÃÂÃÂ»ÃÂ¸ ÃÂµÃÂÃÂÃÂ ÃÂ²ÃÂ½ÃÂµÃÂÃÂ½ÃÂÃÂ ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ° Ã¢ÂÂ ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂ¼ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂºÃÂ°ÃÂ·ÃÂºÃÂ ÃÂ² ÃÂ¿ÃÂÃÂ¾ÃÂ¼ÃÂ ÃÂ´ÃÂ»ÃÂ Claude
    extra_context = ""
    if has_external_link:
        extra_context = "\n[ÃÂ¡ÃÂÃÂ¡ÃÂ¢ÃÂÃÂÃÂ: ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ°ÃÂ» ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ ÃÂÃÂ ÃÂ ÃÂ½ÃÂ°ÃÂÃÂµÃÂ³ÃÂ¾ ÃÂÃÂ°ÃÂ¹ÃÂÃÂ°. ÃÂÃÂÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂ»ÃÂ¾ ÃÂÃÂÃÂºÃÂ°ÃÂ»ÃÂ°ÃÂÃÂ¸ÃÂ¸ ÃÂ´ÃÂ»ÃÂ ÃÂ²ÃÂ½ÃÂµÃÂÃÂ½ÃÂ¸ÃÂ ÃÂÃÂÃÂÃÂ»ÃÂ¾ÃÂº.]"

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ±ÃÂÃÂÃÂ½ÃÂÃÂ¹ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ


    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    load_history_from_amo(user.id, user.full_name or "")
    result = ask_claude(user.id, text + extra_context)

    # ÃÂÃÂÃÂ»ÃÂ¸ ÃÂ²ÃÂ½ÃÂµÃÂÃÂ½ÃÂÃÂ ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ° Ã¢ÂÂ ÃÂÃÂ¸ÃÂÃÂ¾ ÃÂÃÂ¾ÃÂÃÂ²ÃÂ°ÃÂÃÂ´ÃÂ¸ÃÂ¼ ÃÂÃÂµÃÂ±ÃÂµ (ÃÂ±ÃÂµÃÂ· ÃÂÃÂÃÂºÃÂ°ÃÂ»ÃÂ°ÃÂÃÂ¸ÃÂ¸ ÃÂ² ÃÂÃÂ°ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°)
    if has_external_link and MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=(
                    f"Ã°ÂÂÂ ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ {user.full_name} ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ°ÃÂ» ÃÂ²ÃÂ½ÃÂµÃÂÃÂ½ÃÂÃÂ ÃÂÃÂÃÂÃÂ»ÃÂºÃÂ:\n\n"
                    f"{text[:500]}\n\n"
                    f"ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ ÃÂÃÂµÃÂÃÂµÃÂ·: `ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ {user.full_name} [ÃÂÃÂ²ÃÂ¾ÃÂ¹ ÃÂÃÂµÃÂºÃÂÃÂ]`"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
        # ÃÂÃÂ ÃÂÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂ¼ escalate=True Ã¢ÂÂ ÃÂ®ÃÂ»ÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂ´ÃÂ¾ÃÂ»ÃÂ¶ÃÂ°ÃÂµÃÂ ÃÂ²ÃÂµÃÂÃÂÃÂ¸ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³

    await _send_and_update(update, context, user, result, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÃÂÃÂ±ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂºÃÂ° ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ¾ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°."""
    user = update.effective_user
    name = user.full_name or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ"
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [ÃÂ¤ÃÂÃÂ¢ÃÂ] {caption}")

    # —— Владелец: публикация поста ———————————————————————————
    if is_owner(user):
        await handle_owner_photo(update, context)
        return
    # ———————————————————————————————————————————————
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # ÃÂÃÂµÃÂÃÂÃÂ¼ ÃÂ½ÃÂ°ÃÂ¸ÃÂ±ÃÂ¾ÃÂ»ÃÂÃÂÃÂµÃÂµ ÃÂÃÂ°ÃÂ·ÃÂÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂÃÂ¾ÃÂÃÂ¾
        photo = update.message.photo[-1]
        image_data = await download_photo(context.bot, photo.file_id)
        prompt = caption if caption else "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ°ÃÂ» ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ° ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂ¹ ÃÂÃÂ¾ÃÂÃÂµÃÂ ÃÂ½ÃÂ°ÃÂ¹ÃÂÃÂ¸ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂºÃÂÃÂ¿ÃÂ¸ÃÂÃÂ. ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ ÃÂÃÂ¾ÃÂ³ÃÂ»ÃÂ°ÃÂÃÂ½ÃÂ¾ ÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂ»ÃÂ°ÃÂ¼ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ ÃÂ ÃÂÃÂ¾ÃÂÃÂ¾."
        load_history_from_amo(user.id, user.full_name or "")
        result = ask_claude(user.id, prompt, image_data=image_data)
        # ÃÂ¤ÃÂ¾ÃÂÃÂ¾ ÃÂ¾ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ²ÃÂÃÂµÃÂ³ÃÂ´ÃÂ° ÃÂÃÂÃÂºÃÂ°ÃÂ»ÃÂ¸ÃÂÃÂÃÂµÃÂ¼ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ
        result["escalate"] = True
    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        result = {"reply": "ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ¸ÃÂ»ÃÂ° ÃÂ²ÃÂ°ÃÂÃÂµ ÃÂÃÂ¾ÃÂÃÂ¾! ÃÂ£ÃÂÃÂ¾ÃÂÃÂ½ÃÂ¸ÃÂÃÂµ, ÃÂÃÂÃÂ¾ ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ½ÃÂ¾ ÃÂ²ÃÂ°ÃÂ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂµÃÂÃÂÃÂµÃÂ?",
                  "qualification": None, "interest": None, "budget": None, "escalate": False}

    await _send_and_update(update, context, user, result, f"[ÃÂ¤ÃÂÃÂ¢ÃÂ] {caption}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÃÂÃÂ±ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂºÃÂ° ÃÂ´ÃÂ¾ÃÂºÃÂÃÂ¼ÃÂµÃÂ½ÃÂÃÂ¾ÃÂ²/ÃÂÃÂ°ÃÂ¹ÃÂ»ÃÂ¾ÃÂ²."""
    user = update.effective_user
    name = user.full_name or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ"
    doc  = update.message.document
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [ÃÂ¤ÃÂÃÂÃÂ] {doc.file_name}")



    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ°ÃÂ» ÃÂÃÂ°ÃÂ¹ÃÂ» '{doc.file_name}'"
    if caption:
        prompt += f" ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¿ÃÂ¸ÃÂÃÂÃÂ: {caption}"
    prompt += ". ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂ Ã¢ÂÂ ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ¸ ÃÂÃÂÃÂ¾ ÃÂÃÂÃÂ¾ ÃÂ¸ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ¾ÃÂ¶ÃÂµÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂ¾ÃÂÃÂ."

    load_history_from_amo(user.id, user.full_name or "")
    result = ask_claude(user.id, prompt)
    await _send_and_update(update, context, user, result, f"[ÃÂ¤ÃÂÃÂÃÂ] {doc.file_name}")


async def _send_and_update(update, context, user, result, original_text):
    """ÃÂÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ ÃÂ¸ ÃÂ¾ÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ¸ÃÂÃÂ Notion."""
    # ÃÂ£ÃÂ²ÃÂµÃÂ´ÃÂ¾ÃÂ¼ÃÂ¸ÃÂÃÂ ÃÂ¼ÃÂµÃÂ½ÃÂµÃÂ´ÃÂ¶ÃÂµÃÂÃÂ° ÃÂ¿ÃÂÃÂ¸ ÃÂÃÂÃÂºÃÂ°ÃÂ»ÃÂ°ÃÂÃÂ¸ÃÂ¸ Ã¢ÂÂ ÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ ÃÂÃÂÃÂÃÂ ÃÂ ÃÂÃÂ ÃÂ½ÃÂ° ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°
    if result["escalate"] and MANAGER_CHAT_ID and user.id not in _escalated_clients:
        try:
            # ÃÂ¡ÃÂ¾ÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¸ÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ° ÃÂ´ÃÂ»ÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµÃÂºÃÂÃÂÃÂ°
            history = dialogs.get(user.id, [])
            def clean_msg(text: str) -> str:
                """ÃÂ£ÃÂ±ÃÂÃÂ°ÃÂÃÂ JSON ÃÂ±ÃÂ»ÃÂ¾ÃÂºÃÂ¸ ÃÂ¸ÃÂ· ÃÂÃÂµÃÂºÃÂÃÂÃÂ°."""
                import re as _re
                text = _re.sub(r'```json.*?```', '', text, flags=_re.DOTALL)
                return text.strip()[:150]

            dialog_summary = "\n".join(
                f"{'Ã°ÂÂÂ¤' if m['role'] == 'user' else 'Ã°ÂÂ¤Â'} {clean_msg(m['content']) if isinstance(m['content'], str) else '[ÃÂ¼ÃÂµÃÂ´ÃÂ¸ÃÂ°]'}"
                for m in history[-6:]
                if isinstance(m.get('content'), str) and m['content'].strip()
            )
            interest = result.get("interest") or "ÃÂ½ÃÂµ ÃÂÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂ½"
            budget = f"{int(result['budget']):,} Ã¢ÂÂ½".replace(",", " ") if result.get("budget") else "ÃÂ½ÃÂµ ÃÂÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂ½"
            qualification = result.get("qualification") or "ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹"

            msg = (
                f"Ã°ÂÂÂ¥ ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ»ÃÂ¸ÃÂ´!\n\n"
                f"Ã°ÂÂÂ¤ ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ: {user.full_name}\n"
                f"Ã°ÂÂÂ± TG: @{user.username or 'ÃÂ½ÃÂµÃÂ'} | ID: {user.id}\n"
                f"Ã°ÂÂÂ ÃÂÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ: {interest}\n"
                f"Ã°ÂÂÂ° ÃÂÃÂÃÂ´ÃÂ¶ÃÂµÃÂ: {budget}\n"
                f"Ã°ÂÂÂ ÃÂ¡ÃÂÃÂ°ÃÂÃÂÃÂ: {qualification}\nÃ°ÂÂÂ amoCRM: https://yaninve7.amocrm.ru/leads/detail/{_amo_client_cache.get(user.id, {}).get('lead_id', '?')}\n\n"
                f"Ã°ÂÂÂ ÃÂÃÂÃÂ¸ÃÂÃÂ¸ÃÂ½ÃÂ°:\n{result.get('reply','')[:200]}\n\nÃ°ÂÂÂ¬ ÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³:\n{dialog_summary}"
            )
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=msg
            )
            # Если клиент прислал фото — форвардим боссу
            if update.message.photo:
                photo = update.message.photo[-1]
                caption_text = update.message.caption or ""
                await context.bot.send_photo(
                    chat_id=int(MANAGER_CHAT_ID),
                    photo=photo.file_id,
                    caption=f"📸 Фото от клиента {user.full_name}" + (f"\nПодпись: {caption_text}" if caption_text else "")
                )
            # ÃÂÃÂ¾ÃÂ¼ÃÂµÃÂÃÂ°ÃÂµÃÂ¼ ÃÂÃÂÃÂ¾ ÃÂÃÂ¶ÃÂµ ÃÂÃÂ²ÃÂµÃÂ´ÃÂ¾ÃÂ¼ÃÂ¸ÃÂ»ÃÂ¸ Ã¢ÂÂ ÃÂ½ÃÂµ ÃÂ±ÃÂÃÂ´ÃÂµÃÂ¼ ÃÂÃÂ¿ÃÂ°ÃÂ¼ÃÂ¸ÃÂÃÂ
            _escalated_clients.add(user.id)
        except Exception as e:
            logger.error(f"Escalation notify error: {e}")



    # ÃÂ¡ÃÂ¸ÃÂ½ÃÂÃÂÃÂ¾ÃÂ½ÃÂ¸ÃÂ·ÃÂ°ÃÂÃÂ¸ÃÂ ÃÂ amoCRM
    if not is_owner(user):
        try:
            sync_to_amo(
                tg_id=user.id,
                name=user.full_name or "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ",
                username=user.username or "",
                message_text=original_text[:500],
                bot_reply=result["reply"][:500],
                qualification=result.get("qualification"),
                interest=result.get("interest"),
                budget=int(result["budget"]) if result.get("budget") else None
            )
        except Exception as e:
            logger.error(f"amoCRM sync exception: {e}")

    # ÃÂÃÂÃÂ²ÃÂµÃÂÃÂ¸ÃÂÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ
    await update.message.reply_text(result["reply"])


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂ½ÃÂ°ÃÂ»: ÃÂºÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

OWNER_ID = "8828678082"

def is_owner(user) -> bool:
    return str(user.id) == OWNER_ID


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/post <ÃÂÃÂµÃÂºÃÂÃÂ> Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»."""
    if not is_owner(update.effective_user):
        return

    text = update.message.text.replace("/post", "").strip()
    if not text:
        await update.message.reply_text(
            "Ã°ÂÂÂ¢ *ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ°:*\n\n"
            "`/post ÃÂ¢ÃÂµÃÂºÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°` Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ\n"
            "`/post_photo` + ÃÂ¿ÃÂÃÂ¸ÃÂºÃÂÃÂµÃÂ¿ÃÂ¸ ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¿ÃÂ¸ÃÂÃÂÃÂ Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂÃÂ¾ÃÂÃÂ¾\n"
            "`/ai_post ÃÂ¢ÃÂµÃÂ¼ÃÂ°` Ã¢ÂÂ Claude ÃÂÃÂ°ÃÂ¼ ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂÃÂµÃÂ¼ÃÂµ\n"
            "`/forward` Ã¢ÂÂ ÃÂ¿ÃÂµÃÂÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ»ÃÂÃÂ±ÃÂ¾ÃÂµ ÃÂÃÂ¾ÃÂ¾ÃÂ±ÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ±ÃÂ¾ÃÂÃÂ ÃÂ¸ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ /forward\n"
            "`/channel` Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂÃÂ ID ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ°",
            parse_mode="Markdown"
        )
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
        await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ ÃÂ² {CHANNEL_ID}\n[ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ¾ÃÂÃÂÃÂµÃÂÃÂ](https://t.me/{CHANNEL_ID.lstrip('@')}/{msg.message_id})", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂÃÂ¸ÃÂ±ÃÂºÃÂ°: {e}")


async def cmd_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ai_post <ÃÂÃÂµÃÂ¼ÃÂ°> Ã¢ÂÂ Claude ÃÂ¿ÃÂ¸ÃÂÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¸ ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂµÃÂ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»."""
    if not is_owner(update.effective_user):
        return

    topic = update.message.text.replace("/ai_post", "").strip()
    if not topic:
        await update.message.reply_text("ÃÂ£ÃÂºÃÂ°ÃÂ¶ÃÂ¸ ÃÂÃÂµÃÂ¼ÃÂ: `/ai_post ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MC-A68 ÃÂ¸ÃÂ· ÃÂ¸ÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ¾ÃÂ¹ ÃÂºÃÂ¾ÃÂ¶ÃÂ¸`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"""ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¿ÃÂÃÂ¾ÃÂ´ÃÂ°ÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ´ÃÂ»ÃÂ Telegram-ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ° ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂÃÂ½ÃÂ¾ÃÂ¹ ÃÂºÃÂ¾ÃÂ¼ÃÂ¿ÃÂ°ÃÂ½ÃÂ¸ÃÂ¸ KOKAHOUSE.

ÃÂ¢ÃÂµÃÂ¼ÃÂ°/ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ: {topic}

ÃÂ¢ÃÂÃÂµÃÂ±ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ:
Ã¢ÂÂ 3-5 ÃÂ°ÃÂ±ÃÂ·ÃÂ°ÃÂÃÂµÃÂ², ÃÂ¶ÃÂ¸ÃÂ²ÃÂ¾ÃÂ¹ ÃÂÃÂÃÂ¸ÃÂ»ÃÂ
Ã¢ÂÂ ÃÂ£ÃÂ¿ÃÂ¾ÃÂ¼ÃÂÃÂ½ÃÂ¸ ÃÂ¼ÃÂ°ÃÂÃÂµÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ, ÃÂ¿ÃÂÃÂ¾ÃÂ¸ÃÂ·ÃÂ²ÃÂ¾ÃÂ´ÃÂÃÂÃÂ²ÃÂ¾ ÃÂ² ÃÂÃÂ¸ÃÂÃÂ°ÃÂµ, ÃÂÃÂµÃÂ½ÃÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂ·ÃÂ½ÃÂ°ÃÂµÃÂÃÂ
Ã¢ÂÂ ÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµ: ÃÂ¿ÃÂÃÂ¸ÃÂ·ÃÂÃÂ² ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ² ÃÂ»ÃÂ¸ÃÂÃÂºÃÂ ÃÂ±ÃÂ¾ÃÂÃÂ @kokahouse_Yulia
Ã¢ÂÂ Emoji ÃÂÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂ¾ (1-3 ÃÂÃÂÃÂÃÂºÃÂ¸)
Ã¢ÂÂ ÃÂÃÂµÃÂ· ÃÂÃÂÃÂÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²
Ã¢ÂÂ ÃÂ¤ÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ Markdown (ÃÂ¶ÃÂ¸ÃÂÃÂ½ÃÂÃÂ¹, ÃÂºÃÂÃÂÃÂÃÂ¸ÃÂ²)

ÃÂÃÂµÃÂÃÂ½ÃÂ¸ ÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°, ÃÂ±ÃÂµÃÂ· ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ½ÃÂµÃÂ½ÃÂ¸ÃÂ¹."""

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    post_text = response.content[0].text.strip()

    # ÃÂ¡ÃÂ½ÃÂ°ÃÂÃÂ°ÃÂ»ÃÂ° ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂÃÂ²ÃÂ°ÃÂµÃÂ¼ ÃÂ¿ÃÂÃÂµÃÂ²ÃÂÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ (ÃÂ±ÃÂµÃÂ· parse_mode ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ½ÃÂµ ÃÂÃÂ»ÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ)
    await update.message.reply_text(
        f"Ã°ÂÂÂ ÃÂÃÂÃÂµÃÂ²ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°:\n\n{post_text}\n\n"
        f"ÃÂÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ /confirm ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ, ÃÂ¸ÃÂ»ÃÂ¸ /post <ÃÂÃÂµÃÂºÃÂÃÂ> ÃÂÃÂÃÂ¾ÃÂ±ÃÂ ÃÂ¸ÃÂ·ÃÂ¼ÃÂµÃÂ½ÃÂ¸ÃÂÃÂ"
    )
    # ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂÃÂµÃÂ¼ ÃÂ² ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ¶ÃÂ´ÃÂµÃÂ½ÃÂ¸ÃÂ
    context.user_data["pending_post"] = post_text


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/confirm Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂ¹ ai_post."""
    if not is_owner(update.effective_user):
        return

    post_text = context.user_data.get("pending_post")
    if not post_text:
        await update.message.reply_text("ÃÂÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ° ÃÂ´ÃÂ»ÃÂ ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ°ÃÂÃÂ¸ÃÂ¸. ÃÂ¡ÃÂ½ÃÂ°ÃÂÃÂ°ÃÂ»ÃÂ° ÃÂ¸ÃÂÃÂ¿ÃÂ¾ÃÂ»ÃÂÃÂ·ÃÂÃÂ¹ /ai_post.")
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        context.user_data.pop("pending_post", None)
        await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾!", parse_mode="Markdown")
    except Exception as e:
        # ÃÂÃÂÃÂ»ÃÂ¸ Markdown ÃÂÃÂ»ÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ Ã¢ÂÂ ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂµÃÂ¼ ÃÂ±ÃÂµÃÂ· ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ
        try:
            msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            context.user_data.pop("pending_post", None)
            await update.message.reply_text("Ã¢ÂÂ ÃÂÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ (ÃÂ±ÃÂµÃÂ· Markdown).")
        except Exception as e2:
            await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂÃÂ¸ÃÂ±ÃÂºÃÂ°: {e2}")


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/channel Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂÃÂ¸ÃÂ¹ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(f"Ã°ÂÂÂ¢ ÃÂ¢ÃÂµÃÂºÃÂÃÂÃÂ¸ÃÂ¹ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»: `{CHANNEL_ID}`", parse_mode="Markdown")


async def handle_owner_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Владелец отправил фото — публикуем пост в канал."""
    user = update.effective_user

    # Если не владелец — передаём в handle_photo как клиент
    if not is_owner(user):
        await handle_photo(update, context)
        return

    caption = update.message.caption or ""
    clean_caption = caption.replace("/post_photo", "").strip()

    # Парсим кнопки формата [Текст|URL]
    import re as _re
    btn_pattern = _re.compile(r'\[([^\[\]]+)\|(https?://[^\]]+)\]')
    buttons_found = btn_pattern.findall(clean_caption)
    text_clean = btn_pattern.sub("", clean_caption).strip()
    reply_markup = None
    if buttons_found:
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup as IKM
        kb = [[InlineKeyboardButton(b[0], url=b[1])] for b in buttons_found]
        reply_markup = IKM(kb)

    photo = update.message.photo[-1]

    if text_clean:
        # Есть подпись — публикуем сразу
        try:
            msg = await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=photo.file_id,
                caption=text_clean,
                reply_markup=reply_markup
            )
            post_link = f"https://t.me/{str(CHANNEL_ID).lstrip('@')}/{msg.message_id}"
            await update.message.reply_text(f"✅ Пост опубликован!\n🔗 {post_link}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
    else:
        # Нет подписи — сохраняем фото, просим текст
        context.user_data["pending_photo"] = photo.file_id
        await update.message.reply_text(
            "📸 Фото получено!\n\n"
            "Напиши текст поста или /skip для публикации без текста.\n"
            "Можно добавить кнопку: [Текст кнопки|https://url.com]"
        )


async def cmd_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/skip — опубликовать отложенное фото без подписи."""
    if not is_owner(update.effective_user):
        return
    photo_id = context.user_data.pop("pending_photo", None)
    if not photo_id:
        await update.message.reply_text("Нет отложенного фото.")
        return
    try:
        msg = await context.bot.send_photo(chat_id=CHANNEL_ID, photo=photo_id)
        post_link = f"https://t.me/{str(CHANNEL_ID).lstrip('@')}/{msg.message_id}"
        await update.message.reply_text(f"✅ Пост опубликован без подписи!\n🔗 {post_link}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ÃÂÃÂµÃÂ½ÃÂ ÃÂºÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ ÃÂ´ÃÂ»ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ°."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(
        "Ã°ÂÂÂ *ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ KOKAHOUSE Bot*\n\n"
        "*Ã°ÂÂÂ¥ ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ:*\n"
        "`/start` Ã¢ÂÂ ÃÂ½ÃÂ°ÃÂÃÂ°ÃÂÃÂ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³\n"
        "`/reset` Ã¢ÂÂ ÃÂÃÂ±ÃÂÃÂ¾ÃÂÃÂ¸ÃÂÃÂ ÃÂ¸ÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ¸ÃÂ°ÃÂ»ÃÂ¾ÃÂ³ÃÂ°\n\n"
        "*Ã°ÂÂÂ ÃÂÃÂ±ÃÂÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂ®ÃÂ»ÃÂ¸:*\n"
        "`/teach <ÃÂÃÂµÃÂºÃÂÃÂ>` Ã¢ÂÂ ÃÂ´ÃÂ¾ÃÂ±ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂµ\n"
        "`/knowledge` Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂÃÂ ÃÂ±ÃÂ°ÃÂ·ÃÂ ÃÂ·ÃÂ½ÃÂ°ÃÂ½ÃÂ¸ÃÂ¹\n\n"
        "*Ã°ÂÂÂ¢ ÃÂÃÂ°ÃÂ½ÃÂ°ÃÂ»:*\n"
        "`/post <ÃÂÃÂµÃÂºÃÂÃÂ>` Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ\n"
        "`/post_photo` Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¸ÃÂºÃÂÃÂµÃÂ¿ÃÂ¸ ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ ÃÂÃÂÃÂ¾ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ¿ÃÂ¸ÃÂÃÂÃÂ\n"
        "`/ai_post <ÃÂÃÂµÃÂ¼ÃÂ°>` Ã¢ÂÂ Claude ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ\n"
        "`/confirm` Ã¢ÂÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ai_post\n"
        "`/channel` Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂºÃÂ°ÃÂ·ÃÂ°ÃÂÃÂ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»\n\n"
        "*Ã¢ÂÂ¹Ã¯Â¸Â ÃÂ¡ÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂºÃÂ°:*\n"
        "`/menu` Ã¢ÂÂ ÃÂÃÂÃÂ¾ ÃÂ¼ÃÂµÃÂ½ÃÂ",
        parse_mode="Markdown"
    )


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ (ÃÂÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂµ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ) Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

# ÃÂ¥ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂÃÂµ ÃÂ¾ÃÂ¶ÃÂ¸ÃÂ´ÃÂ°ÃÂÃÂÃÂ¸ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ¶ÃÂ´ÃÂµÃÂ½ÃÂ¸ÃÂ ÃÂÃÂ: {client_tg_id: {ÃÂ´ÃÂ°ÃÂ½ÃÂ½ÃÂÃÂµ ÃÂÃÂ}}
pending_kp: dict[int, dict] = {}


async def cmd_kp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /kp <tg_id ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°> <ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ> <ÃÂÃÂµÃÂ½ÃÂ°Ã¢ÂÂ½> [ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°Ã¢ÂÂ½]
    ÃÂÃÂÃÂ¸ÃÂ¼ÃÂµÃÂ: /kp 283951945 "ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MC-A68 3-ÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹ ÃÂºÃÂ¾ÃÂ¶ÃÂ°" 235000 8000
    """
    if not is_owner(update.effective_user):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Ã°ÂÂÂ *ÃÂÃÂ°ÃÂº ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ ÃÂÃÂ:*\n\n"
            "`/kp <ID_ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°> <ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ> <ÃÂÃÂµÃÂ½ÃÂ°> [ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°]`\n\n"
            "ÃÂÃÂÃÂ¸ÃÂ¼ÃÂµÃÂ:\n"
            "`/kp 283951945 ÃÂÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MC-A68 3-ÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹ 235000 8000`\n\n"
            "ID ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂÃÂ·ÃÂ½ÃÂ°ÃÂÃÂ: ÃÂ¿ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ½ÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ±ÃÂ¾ÃÂÃÂ, "
            "ÃÂ¸ÃÂ»ÃÂ¸ ÃÂ¿ÃÂ¾ÃÂÃÂ¼ÃÂ¾ÃÂÃÂÃÂ¸ ÃÂ² Notion Ã¢ÂÂ Telegram ID",
            parse_mode="Markdown"
        )
        return

    client_id = int(args[0])
    price = int(args[-2]) if len(args) >= 4 else int(args[-1])
    delivery = int(args[-1]) if len(args) >= 4 else 0
    product = " ".join(args[1:-2]) if len(args) >= 4 else " ".join(args[1:-1])
    total = price + delivery

    # ÃÂ¡ÃÂ¾ÃÂÃÂÃÂ°ÃÂ½ÃÂÃÂµÃÂ¼ ÃÂ² ÃÂ¾ÃÂ¶ÃÂ¸ÃÂ´ÃÂ°ÃÂ½ÃÂ¸ÃÂµ
    pending_kp[client_id] = {
        "product": product,
        "price": price,
        "delivery": delivery,
        "total": total,
        "manager_id": update.effective_user.id,
        "created_at": datetime.now().isoformat(),
    }

    # ÃÂÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂÃÂµÃÂ¼ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ
    try:
        msg = (
            f"ÃÂÃÂ´ÃÂÃÂ°ÃÂ²ÃÂÃÂÃÂ²ÃÂÃÂ¹ÃÂÃÂµ!\n\n"
            f"ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ³ÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂ°ÃÂÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂ²ÃÂ°ÃÂÃÂµÃÂ¼ÃÂ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ:\n\n"
            f"Ã°ÂÂÂ¦ *{product}*\n"
            f"Ã°ÂÂÂ° ÃÂ¡ÃÂÃÂ¾ÃÂ¸ÃÂ¼ÃÂ¾ÃÂÃÂÃÂ: {price:,} Ã¢ÂÂ½\n"
        )
        if delivery:
            msg += f"Ã°ÂÂÂ ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°: {delivery:,} Ã¢ÂÂ½\n"
        msg += (
            f"Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ\n"
            f"Ã°ÂÂÂµ *ÃÂÃÂÃÂ¾ÃÂ³ÃÂ¾: {total:,} Ã¢ÂÂ½*\n\n"
            f"ÃÂÃÂ°ÃÂ ÃÂÃÂÃÂÃÂÃÂ°ÃÂ¸ÃÂ²ÃÂ°ÃÂÃÂ ÃÂÃÂÃÂ»ÃÂ¾ÃÂ²ÃÂ¸ÃÂ? ÃÂÃÂÃÂ²ÃÂµÃÂÃÂÃÂÃÂµ *ÃÂ«ÃÂÃÂ°ÃÂ»* Ã¢ÂÂ ÃÂ¸ ÃÂ ÃÂ¿ÃÂÃÂ¸ÃÂÃÂ»ÃÂ ÃÂ¿ÃÂ¾ÃÂ»ÃÂ½ÃÂ¾ÃÂµ ÃÂºÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂµ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ."
        )
        msg = msg.replace(",", " ")

        await context.bot.send_message(
            chat_id=client_id,
            text=msg,
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            f"Ã¢ÂÂ ÃÂ ÃÂ°ÃÂÃÂÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ (ID: {client_id})\n"
            f"ÃÂ¢ÃÂ¾ÃÂ²ÃÂ°ÃÂ: {product}\n"
            f"ÃÂÃÂÃÂ¾ÃÂ³ÃÂ¾: {total:,} Ã¢ÂÂ½\n\n"
            f"ÃÂÃÂ´ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂ¶ÃÂ´ÃÂµÃÂ½ÃÂ¸ÃÂ ÃÂ¾ÃÂ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ°...".replace(",", " ")
        )
        logger.info(f"ÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½ÃÂ¾ ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ {client_id}: {product} {total}Ã¢ÂÂ½")
    except Exception as e:
        await update.message.reply_text(f"Ã¢ÂÂ ÃÂÃÂÃÂ¸ÃÂ±ÃÂºÃÂ° ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸: {e}")


async def generate_kp_pdf(data: dict, client_name: str) -> bytes:
    """ÃÂÃÂµÃÂ½ÃÂµÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ PDF ÃÂºÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂ³ÃÂ¾ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂ."""
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

    # ÃÂÃÂ°ÃÂ³ÃÂ¾ÃÂ»ÃÂ¾ÃÂ²ÃÂ¾ÃÂº
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
                                  fontSize=20, textColor=colors.HexColor('#1a1a2e'),
                                  spaceAfter=6, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=11, textColor=colors.grey, spaceAfter=20)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=11, spaceAfter=8, leading=16)

    story.append(Paragraph("KOKAHOUSE", title_style))
    story.append(Paragraph("ÃÂÃÂ¾ÃÂ¼ÃÂ¼ÃÂµÃÂÃÂÃÂµÃÂÃÂºÃÂ¾ÃÂµ ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ»ÃÂ¾ÃÂ¶ÃÂµÃÂ½ÃÂ¸ÃÂµ", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.5*cm))

    # ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ ÃÂ¸ ÃÂ´ÃÂ°ÃÂÃÂ°
    story.append(Paragraph(f"<b>ÃÂÃÂ»ÃÂ:</b> {client_name}", body_style))
    story.append(Paragraph(f"<b>ÃÂÃÂ°ÃÂÃÂ°:</b> {datetime.now().strftime('%d.%m.%Y')}", body_style))
    story.append(Spacer(1, 0.5*cm))

    # ÃÂ¢ÃÂ°ÃÂ±ÃÂ»ÃÂ¸ÃÂÃÂ° ÃÂ ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ¾ÃÂ¼
    table_data = [
        ['ÃÂÃÂ°ÃÂ¸ÃÂ¼ÃÂµÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ', 'ÃÂ¡ÃÂÃÂ¾ÃÂ¸ÃÂ¼ÃÂ¾ÃÂÃÂÃÂ'],
        [data['product'], f"{data['price']:,} Ã¢ÂÂ½".replace(',', ' ')],
    ]
    if data['delivery']:
        table_data.append(['ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ°', f"{data['delivery']:,} Ã¢ÂÂ½".replace(',', ' ')])
    table_data.append(['ÃÂÃÂ¢ÃÂÃÂÃÂ', f"{data['total']:,} Ã¢ÂÂ½".replace(',', ' ')])

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

    # ÃÂ£ÃÂÃÂ»ÃÂ¾ÃÂ²ÃÂ¸ÃÂ
    story.append(Paragraph("<b>ÃÂ£ÃÂÃÂ»ÃÂ¾ÃÂ²ÃÂ¸ÃÂ:</b>", body_style))
    story.append(Paragraph("Ã¢ÂÂ¢ ÃÂÃÂÃÂ¾ÃÂ¸ÃÂ·ÃÂ²ÃÂ¾ÃÂ´ÃÂÃÂÃÂ²ÃÂ¾: 6Ã¢ÂÂ8 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ", body_style))
    story.append(Paragraph("Ã¢ÂÂ¢ ÃÂÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ°: 30% ÃÂ¿ÃÂÃÂµÃÂ´ÃÂ¾ÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ°, 70% ÃÂ¿ÃÂµÃÂÃÂµÃÂ´ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂºÃÂ¾ÃÂ¹", body_style))
    story.append(Paragraph("Ã¢ÂÂ¢ ÃÂÃÂ°ÃÂÃÂ°ÃÂ½ÃÂÃÂ¸ÃÂ: 12 ÃÂ¼ÃÂµÃÂÃÂÃÂÃÂµÃÂ²", body_style))
    story.append(Paragraph("Ã¢ÂÂ¢ ÃÂÃÂµÃÂ»ÃÂ°ÃÂ ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ¶ÃÂ½ÃÂ, ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ° ÃÂ¿ÃÂ¾ÃÂ´ ÃÂºÃÂ»ÃÂÃÂ", body_style))
    story.append(Spacer(1, 1*cm))

    # ÃÂÃÂ¾ÃÂ½ÃÂÃÂ°ÃÂºÃÂÃÂ
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("KOKAHOUSE | kokahouse.ru | @kokahouse_Yulia", sub_style))

    doc.build(story)
    return buffer.getvalue()


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ¶ÃÂµÃÂ´ÃÂ½ÃÂµÃÂ²ÃÂ½ÃÂÃÂ¹ ÃÂ¾ÃÂÃÂÃÂÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

async def daily_report(bot):
    """ÃÂÃÂ¶ÃÂµÃÂ´ÃÂ½ÃÂµÃÂ²ÃÂ½ÃÂÃÂ¹ ÃÂ¾ÃÂÃÂÃÂÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ ÃÂ² 9:00 ÃÂÃÂ¡ÃÂ."""
    if not MANAGER_CHAT_ID:
        return
    try:
        # ÃÂÃÂ¾ÃÂ»ÃÂÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ»ÃÂ¸ÃÂ´ÃÂ ÃÂ¸ÃÂ· amoCRM ÃÂ·ÃÂ° ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ 24 ÃÂÃÂ°ÃÂÃÂ°
        import time as _time
        since = int(_time.time()) - 86400
        r_new = amo_request("GET", f"leads?filter[created_at][from]={since}&limit=50")
        new_leads = r_new.get("_embedded", {}).get("leads", [])

        # ÃÂÃÂÃÂµ ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ²ÃÂ½ÃÂÃÂµ ÃÂ»ÃÂ¸ÃÂ´ÃÂ
        r_all = amo_request("GET", "leads?limit=50&order[created_at]=desc")
        all_leads = r_all.get("_embedded", {}).get("leads", [])

        # ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂµ (ÃÂ ÃÂÃÂµÃÂ½ÃÂ¾ÃÂ¹ > 0 ÃÂ¸ ÃÂ½ÃÂµ ÃÂ·ÃÂ°ÃÂºÃÂÃÂÃÂÃÂÃÂµ)
        hot = [l for l in all_leads if (l.get("price") or 0) > 0 and l.get("status_id") not in [142, 143]]
        # ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂÃÂ¸ÃÂµ (ÃÂ½ÃÂµ ÃÂ¾ÃÂ±ÃÂ½ÃÂ¾ÃÂ²ÃÂ»ÃÂÃÂ»ÃÂ¸ÃÂÃÂ 3+ ÃÂ´ÃÂ½ÃÂ)
        stale_ts = int(_time.time()) - 259200
        stale = [l for l in all_leads if (l.get("updated_at") or 0) < stale_ts and l.get("status_id") not in [142, 143]]

        total_sum = sum(l.get("price", 0) or 0 for l in all_leads if l.get("status_id") not in [142, 143])

        msg = (
            f"Ã¢ÂÂÃ¯Â¸Â *ÃÂÃÂ¾ÃÂ±ÃÂÃÂ¾ÃÂµ ÃÂÃÂÃÂÃÂ¾! ÃÂÃÂÃÂÃÂÃÂ KOKAHOUSE*\n\n"
            f"Ã°ÂÂÂ ÃÂÃÂ° ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂµ 24 ÃÂÃÂ°ÃÂÃÂ°:\n"
            f"Ã¢ÂÂ¢ ÃÂÃÂ¾ÃÂ²ÃÂÃÂ ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ²: {len(new_leads)}\n"
            f"Ã¢ÂÂ¢ ÃÂÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ ÃÂ² ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂµ: {len(hot)}\n"
            f"Ã¢ÂÂ¢ ÃÂ¡ÃÂÃÂ¼ÃÂ¼ÃÂ° ÃÂ² ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂµ: {total_sum:,} Ã¢ÂÂ½\n\n".replace(",", " ")
        )

        if stale:
            msg += f"Ã¢ÂÂ Ã¯Â¸Â ÃÂÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂ»ÃÂ¸ (3+ ÃÂ´ÃÂ½ÃÂ ÃÂ±ÃÂµÃÂ· ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ²ÃÂ½ÃÂ¾ÃÂÃÂÃÂ¸):\n"
            for l in stale[:5]:
                contacts = l.get("_embedded", {}).get("contacts", [])
                client = contacts[0].get("name", "Ã¢ÂÂ") if contacts else "Ã¢ÂÂ"
                msg += f"Ã¢ÂÂ¢ {client} Ã¢ÂÂ {l.get('name', '?')}\n"
            msg += "\n"

        msg += "ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¼ÃÂ½ÃÂµ ÃÂÃÂÃÂ¾ ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ¾ ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂÃÂ ÃÂÃÂµÃÂ³ÃÂ¾ÃÂ´ÃÂ½ÃÂ ÃÂ¸ÃÂ»ÃÂ¸ ÃÂÃÂ¿ÃÂÃÂ¾ÃÂÃÂ¸ ÃÂÃÂÃÂ°ÃÂÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ."

        await bot.send_message(chat_id=int(MANAGER_CHAT_ID), text=msg, parse_mode="Markdown")
        logger.info("Ã°ÂÂÂ ÃÂÃÂ¶ÃÂµÃÂ´ÃÂ½ÃÂµÃÂ²ÃÂ½ÃÂÃÂ¹ ÃÂ¾ÃÂÃÂÃÂÃÂ ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½")
    except Exception as e:
        logger.error(f"daily_report error: {e}")


# Ã¢ÂÂÃ¢ÂÂ Follow-up ÃÂ°ÃÂ²ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂºÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

# ÃÂ¥ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ¼ ÃÂºÃÂ¾ÃÂ³ÃÂ´ÃÂ° ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂÃÂ»ÃÂ¸ follow-up: {lead_id: [timestamp1, timestamp2]}
_followup_sent: dict[int, list] = {}

FOLLOWUP_MESSAGES = [
    "ÃÂÃÂ¾ÃÂ±ÃÂÃÂÃÂ¹ ÃÂ´ÃÂµÃÂ½ÃÂ! ÃÂÃÂ¾ÃÂ·ÃÂ²ÃÂÃÂ°ÃÂÃÂ°ÃÂÃÂÃÂ ÃÂº ÃÂ²ÃÂ°ÃÂÃÂµÃÂ¼ÃÂ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ. ÃÂ¥ÃÂ¾ÃÂÃÂ¸ÃÂÃÂµ, ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂ±ÃÂµÃÂÃÂ ÃÂ½ÃÂµÃÂÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ²ÃÂ°ÃÂÃÂ¸ÃÂ°ÃÂ½ÃÂÃÂ¾ÃÂ² ÃÂ¿ÃÂ¾ÃÂ´ ÃÂ²ÃÂ°ÃÂ ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂ ÃÂ¸ ÃÂÃÂÃÂ¸ÃÂ»ÃÂ?",
    "ÃÂÃÂ´ÃÂÃÂ°ÃÂ²ÃÂÃÂÃÂ²ÃÂÃÂ¹ÃÂÃÂµ! ÃÂ¥ÃÂ¾ÃÂÃÂµÃÂ»(ÃÂ°) ÃÂÃÂÃÂ¾ÃÂÃÂ½ÃÂ¸ÃÂÃÂ Ã¢ÂÂ ÃÂ¾ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ ÃÂ»ÃÂ¸ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂµÃÂ ÃÂº ÃÂ½ÃÂ°ÃÂÃÂµÃÂ¹ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ¸? ÃÂÃÂ¾ÃÂÃÂ¾ÃÂ²ÃÂ° ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ¸ÃÂÃÂ ÃÂ½ÃÂ° ÃÂ»ÃÂÃÂ±ÃÂÃÂµ ÃÂ²ÃÂ¾ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ.",
]

async def followup_check(bot):
    """ÃÂÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂÃÂµÃÂ¼ ÃÂÃÂÃÂ¿ÃÂ»ÃÂÃÂ/ÃÂ³ÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂ ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ² ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂµ ÃÂ¼ÃÂ¾ÃÂ»ÃÂÃÂ°ÃÂ 2+ ÃÂ´ÃÂ½ÃÂ."""
    import time as _time
    now = int(_time.time())
    cutoff_2d = now - 172800  # 2 ÃÂ´ÃÂ½ÃÂ
    cutoff_5d = now - 432000  # 5 ÃÂ´ÃÂ½ÃÂµÃÂ¹
    cutoff_7d = now - 604800  # 7 ÃÂ´ÃÂ½ÃÂµÃÂ¹

    # ÃÂ¢ÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ´ÃÂ½ÃÂÃÂ¼ (9-20 ÃÂÃÂ¡ÃÂ = 6-17 UTC)
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

            # ÃÂ¢ÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ°ÃÂºÃÂÃÂ¸ÃÂ²ÃÂ½ÃÂÃÂµ ÃÂÃÂÃÂ¿ÃÂ»ÃÂÃÂµ/ÃÂ³ÃÂ¾ÃÂÃÂÃÂÃÂ¸ÃÂµ
            if status_id in [142, 143]:  # Won/Lost
                continue
            if price == 0:  # ÃÂ¥ÃÂ¾ÃÂ»ÃÂ¾ÃÂ´ÃÂ½ÃÂÃÂ¹ Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¾ÃÂ¿ÃÂÃÂÃÂºÃÂ°ÃÂµÃÂ¼
                continue

            sent = _followup_sent.get(lead_id, [])
            contacts = lead.get("_embedded", {}).get("contacts", []) if isinstance(lead.get("_embedded"), dict) else []
            client_name = contacts[0].get("name", "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ") if contacts else "ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂ"

            # ÃÂÃÂÃÂµÃÂ¼ tg_id ÃÂºÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂ° ÃÂ² ÃÂºÃÂµÃÂÃÂµ
            tg_id = None
            for tid, data in _amo_client_cache.items():
                if data.get("lead_id") == lead_id:
                    tg_id = tid
                    break

            if not tg_id:
                continue

            # 2 ÃÂ´ÃÂ½ÃÂ Ã¢ÂÂ ÃÂ¿ÃÂµÃÂÃÂ²ÃÂÃÂ¹ follow-up
            if updated < cutoff_2d and len(sent) == 0:
                msg = FOLLOWUP_MESSAGES[0]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id] = [now]
                amo_add_note(lead_id, f"Ã°ÂÂÂ¤ Follow-up #1 ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½: {msg[:100]}")
                logger.info(f"Follow-up #1 Ã¢ÂÂ lead {lead_id} ({client_name})")

            # 5 ÃÂ´ÃÂ½ÃÂµÃÂ¹ Ã¢ÂÂ ÃÂ²ÃÂÃÂ¾ÃÂÃÂ¾ÃÂ¹ follow-up
            elif updated < cutoff_5d and len(sent) == 1:
                msg = FOLLOWUP_MESSAGES[1]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id].append(now)
                amo_add_note(lead_id, f"Ã°ÂÂÂ¤ Follow-up #2 ÃÂ¾ÃÂÃÂ¿ÃÂÃÂ°ÃÂ²ÃÂ»ÃÂµÃÂ½")
                logger.info(f"Follow-up #2 Ã¢ÂÂ lead {lead_id} ({client_name})")

            # 7 ÃÂ´ÃÂ½ÃÂµÃÂ¹ Ã¢ÂÂ ÃÂ·ÃÂ°ÃÂ´ÃÂ°ÃÂÃÂ° ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ
            elif updated < cutoff_7d and len(sent) == 2:
                if MANAGER_CHAT_ID:
                    await bot.send_message(
                        chat_id=int(MANAGER_CHAT_ID),
                        text=f"Ã¢ÂÂ Ã¯Â¸Â *{client_name}* ÃÂ½ÃÂµ ÃÂ¾ÃÂÃÂ²ÃÂµÃÂÃÂ°ÃÂµÃÂ 7 ÃÂ´ÃÂ½ÃÂµÃÂ¹.\nÃÂ¡ÃÂ´ÃÂµÃÂ»ÃÂºÃÂ°: {lead.get('name', '?')}\nÃÂÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂÃÂÃÂµ ÃÂ²ÃÂÃÂÃÂÃÂ½ÃÂÃÂ."
                    )
                _followup_sent[lead_id].append(now)
                logger.info(f"Follow-up #3 ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ Ã¢ÂÂ lead {lead_id}")

    except Exception as e:
        logger.error(f"followup_check error: {e}")


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ» Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

# ÃÂ¢ÃÂµÃÂ¼ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂ°ÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ¾ÃÂ² Ã¢ÂÂ ÃÂÃÂ¾ÃÂÃÂ°ÃÂÃÂ¸ÃÂ
AUTO_POST_TOPICS = [
    # Ã¢ÂÂÃ¢ÂÂ ÃÂ¢ÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MC-A68 Ã¢ÂÂ ÃÂ¸ÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ° oil-wax, 3-ÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹, ÃÂ¾ÃÂ 235 000 Ã¢ÂÂ½. ÃÂÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ° oil-wax ÃÂ»ÃÂÃÂÃÂÃÂµ ÃÂ¾ÃÂ±ÃÂÃÂÃÂ½ÃÂ¾ÃÂ¹ ÃÂºÃÂ¾ÃÂ¶ÃÂ¸",
    "ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ FORT Ã¢ÂÂ ÃÂ¾ÃÂÃÂµÃÂ ÃÂ¸ ÃÂ²ÃÂµÃÂ»ÃÂÃÂ, ÃÂºÃÂ»ÃÂ°ÃÂÃÂÃÂ¸ÃÂºÃÂ° ÃÂ´ÃÂ»ÃÂ ÃÂ³ÃÂ¾ÃÂÃÂÃÂ¸ÃÂ½ÃÂ¾ÃÂ¹, ÃÂ¾ÃÂ 99 634 Ã¢ÂÂ½. ÃÂÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾ÃÂµ ÃÂ´ÃÂµÃÂÃÂµÃÂ²ÃÂ¾ ÃÂ² ÃÂºÃÂ°ÃÂÃÂºÃÂ°ÃÂÃÂµ ÃÂ²ÃÂ°ÃÂ¶ÃÂ½ÃÂ¾",
    "ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾ ÃÂÃÂ°ÃÂ½ÃÂÃÂÃÂ Ã¢ÂÂ ÃÂÃÂµÃÂ²ÃÂµÃÂÃÂ¾-ÃÂ°ÃÂ¼ÃÂµÃÂÃÂ¸ÃÂºÃÂ°ÃÂ½ÃÂÃÂºÃÂ¸ÃÂ¹ ÃÂ¾ÃÂÃÂµÃÂ, ÃÂÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, 118 921 Ã¢ÂÂ½. ÃÂÃÂ´ÃÂµÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ¾ÃÂµ ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾ ÃÂ´ÃÂ»ÃÂ ÃÂ´ÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ½ÃÂµÃÂ³ÃÂ¾ ÃÂ¾ÃÂÃÂ¸ÃÂÃÂ°",
    "ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ Roma Platform Ã¢ÂÂ ÃÂ¼ÃÂ°ÃÂÃÂÃÂ¸ÃÂ² ÃÂ´ÃÂÃÂ±ÃÂ°, ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂÃÂ¼ÃÂ½ÃÂÃÂ¹ ÃÂ¼ÃÂµÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ·ÃÂ¼, ÃÂ¾ÃÂ 62 000 Ã¢ÂÂ½. ÃÂÃÂ°ÃÂº ÃÂ²ÃÂÃÂ±ÃÂÃÂ°ÃÂÃÂ ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",
    "ÃÂ¾ÃÂ±ÃÂµÃÂ´ÃÂµÃÂ½ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¾ÃÂ» Palazzo Ã¢ÂÂ ÃÂ¼ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ Calacatta ÃÂ¸ ÃÂ½ÃÂµÃÂÃÂ¶ÃÂ°ÃÂ²ÃÂµÃÂÃÂÃÂ°ÃÂ ÃÂÃÂÃÂ°ÃÂ»ÃÂ, ÃÂ¾ÃÂ 118 000 Ã¢ÂÂ½. ÃÂÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ ÃÂ² ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂÃÂµÃÂÃÂµ ÃÂÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ²ÃÂ¾ÃÂ¹",
    "ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ PR701 ÃÂÃÂ±ÃÂ»ÃÂ°ÃÂºÃÂ¾ Ã¢ÂÂ ÃÂ¼ÃÂ¾ÃÂ´ÃÂÃÂ»ÃÂÃÂ½ÃÂÃÂ¹, ÃÂ³ÃÂÃÂÃÂ¸ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ, ÃÂÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, ÃÂ¾ÃÂ 219 000 Ã¢ÂÂ½. ÃÂÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂ³ÃÂÃÂÃÂ¸ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ ÃÂ»ÃÂÃÂÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ½ÃÂ°",
    "ÃÂ³ÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂ°ÃÂ Cabinet Pro Ã¢ÂÂ ÃÂ¼ÃÂ°ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ»ÃÂ°ÃÂº ÃÂ¸ ÃÂÃÂ¿ÃÂ¾ÃÂ½, ÃÂ¿ÃÂ¾ÃÂ´ ÃÂÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂ ÃÂ¿ÃÂ¾ÃÂ¼ÃÂµÃÂÃÂµÃÂ½ÃÂ¸ÃÂ, ÃÂ¾ÃÂ 94 000 Ã¢ÂÂ½. ÃÂÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂ°ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ ÃÂºÃÂ»ÃÂÃÂ",
    "ÃÂÃÂµÃÂÃÂµÃÂ¿ÃÂÃÂ½-ÃÂÃÂÃÂ¾ÃÂ¹ÃÂºÃÂ° Grand Hotel Ã¢ÂÂ ÃÂÃÂÃÂ°ÃÂ²ÃÂµÃÂÃÂÃÂ¸ÃÂ½/ÃÂ¼ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ, ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂ²ÃÂµÃÂÃÂºÃÂ°, ÃÂ¾ÃÂ 157 000 Ã¢ÂÂ½. ÃÂÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ´ÃÂ»ÃÂ ÃÂ¾ÃÂÃÂµÃÂ»ÃÂµÃÂ¹ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",
    "ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾ MERCER Ã¢ÂÂ ÃÂ¾ÃÂÃÂµÃÂ/ÃÂÃÂÃÂµÃÂ½ÃÂ, ÃÂÃÂ»ÃÂ¾ÃÂ¿ÃÂ¾ÃÂº-ÃÂ»ÃÂÃÂ½, ÃÂ¾ÃÂ 127 000 Ã¢ÂÂ½. ÃÂÃÂ°ÃÂº ÃÂÃÂ¾ÃÂÃÂµÃÂÃÂ°ÃÂÃÂ ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ° ÃÂ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ¾ÃÂ¼",
    "ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ MK-SOFA01 Ã¢ÂÂ ÃÂ°ÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ°, ÃÂ¾ÃÂÃÂµÃÂ, ÃÂ¾ÃÂ 273 000 Ã¢ÂÂ½. ÃÂ§ÃÂÃÂ¾ ÃÂÃÂ°ÃÂºÃÂ¾ÃÂµ ÃÂ°ÃÂ½ÃÂ¸ÃÂ»ÃÂ¸ÃÂ½ÃÂ¾ÃÂ²ÃÂ°ÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ° ÃÂ¸ ÃÂ·ÃÂ°ÃÂÃÂµÃÂ¼ ÃÂ¾ÃÂ½ÃÂ° ÃÂ½ÃÂÃÂ¶ÃÂ½ÃÂ°",
    "ÃÂ±ÃÂ°ÃÂ½ÃÂºÃÂµÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂÃÂ» Chateau Ã¢ÂÂ ÃÂ±ÃÂÃÂº, ÃÂÃÂºÃÂ°ÃÂ½ÃÂ/ÃÂºÃÂ¾ÃÂ¶ÃÂ°, ÃÂ¾ÃÂ 4 200 Ã¢ÂÂ½/ÃÂÃÂ. ÃÂÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂÃÂµÃÂÃÂÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ ÃÂ²ÃÂÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ±ÃÂÃÂ°ÃÂ·ÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂµÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµÃÂ½ÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂ°ÃÂº ÃÂ¾ÃÂÃÂ»ÃÂ¸ÃÂÃÂ¸ÃÂÃÂ ÃÂºÃÂ°ÃÂÃÂµÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂÃÂ ÃÂºÃÂ¾ÃÂ¶ÃÂ ÃÂ¾ÃÂ ÃÂ´ÃÂµÃÂÃÂÃÂ²ÃÂ¾ÃÂ¹ Ã¢ÂÂ 5 ÃÂ¿ÃÂÃÂ¸ÃÂ·ÃÂ½ÃÂ°ÃÂºÃÂ¾ÃÂ² ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂµ ÃÂ¼ÃÂ¾ÃÂ¶ÃÂ½ÃÂ¾ ÃÂ¿ÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂ¸ÃÂÃÂ ÃÂ¿ÃÂÃÂÃÂ¼ÃÂ¾ ÃÂ² ÃÂ¼ÃÂ°ÃÂ³ÃÂ°ÃÂ·ÃÂ¸ÃÂ½ÃÂµ",
    "ÃÂÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂ¼ÃÂ°ÃÂÃÂÃÂ¸ÃÂ² ÃÂ´ÃÂµÃÂÃÂµÃÂ²ÃÂ° ÃÂ»ÃÂÃÂÃÂÃÂµ ÃÂÃÂÃÂ¤ Ã¢ÂÂ ÃÂÃÂ°ÃÂ·ÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ² ÃÂºÃÂ°ÃÂÃÂºÃÂ°ÃÂÃÂ° ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ° ÃÂ¸ ÃÂ¿ÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂÃÂÃÂ¾ ÃÂ²ÃÂ°ÃÂ¶ÃÂ½ÃÂ¾",
    "ÃÂÃÂ° ÃÂÃÂÃÂ¾ ÃÂÃÂ¼ÃÂ¾ÃÂÃÂÃÂµÃÂÃÂ ÃÂ¿ÃÂÃÂ¸ ÃÂ²ÃÂÃÂ±ÃÂ¾ÃÂÃÂµ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ° Ã¢ÂÂ ÃÂ¼ÃÂ°ÃÂÃÂµÃÂÃÂ¸ÃÂ°ÃÂ», ÃÂºÃÂ°ÃÂÃÂºÃÂ°ÃÂ, ÃÂ½ÃÂ°ÃÂ¿ÃÂ¾ÃÂ»ÃÂ½ÃÂ¸ÃÂÃÂµÃÂ»ÃÂ, ÃÂÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂ. ÃÂÃÂ¾ÃÂ»ÃÂ½ÃÂÃÂ¹ ÃÂ³ÃÂ°ÃÂ¹ÃÂ´",
    "ÃÂÃÂÃÂÃÂ¸ÃÂ½ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ vs ÃÂ¿ÃÂ¾ÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ½ vs ÃÂÃÂ¾ÃÂ»ÃÂ»ÃÂ¾ÃÂÃÂ°ÃÂ¹ÃÂ±ÃÂµÃÂ Ã¢ÂÂ ÃÂ¸ÃÂ· ÃÂÃÂµÃÂ³ÃÂ¾ ÃÂ»ÃÂÃÂÃÂÃÂµ ÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂÃÂÃÂºÃÂ¸ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ°",
    "ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ¸ÃÂµ ÃÂÃÂºÃÂ°ÃÂ½ÃÂ¸ ÃÂ² ÃÂºÃÂ¸ÃÂÃÂ°ÃÂ¹ÃÂÃÂºÃÂ¾ÃÂ¹ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ¸ Ã¢ÂÂ ÃÂºÃÂ°ÃÂº ÃÂÃÂÃÂ¾ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ ÃÂ¸ ÃÂ¿ÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂÃÂÃÂ¾ ÃÂ½ÃÂµ ÃÂ¼ÃÂ°ÃÂÃÂºÃÂµÃÂÃÂ¸ÃÂ½ÃÂ³",
    "ÃÂÃÂ°ÃÂº ÃÂ²ÃÂÃÂ±ÃÂÃÂ°ÃÂÃÂ ÃÂ¾ÃÂ±ÃÂµÃÂ´ÃÂµÃÂ½ÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¾ÃÂ» ÃÂ´ÃÂ»ÃÂ ÃÂÃÂµÃÂ¼ÃÂÃÂ¸ Ã¢ÂÂ ÃÂÃÂ°ÃÂ·ÃÂ¼ÃÂµÃÂ, ÃÂ¼ÃÂ°ÃÂÃÂµÃÂÃÂ¸ÃÂ°ÃÂ», ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ°. ÃÂ ÃÂ°ÃÂ·ÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¾ÃÂÃÂ¸ÃÂ±ÃÂºÃÂ¸",
    "ÃÂÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ ÃÂ² ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂÃÂµÃÂÃÂµ Ã¢ÂÂ ÃÂ½ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ vs ÃÂ¸ÃÂÃÂºÃÂÃÂÃÂÃÂÃÂ²ÃÂµÃÂ½ÃÂ½ÃÂÃÂ¹. ÃÂÃÂ°ÃÂº ÃÂ½ÃÂµ ÃÂ¿ÃÂµÃÂÃÂµÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ¸ÃÂÃÂ ÃÂ¸ ÃÂ½ÃÂµ ÃÂ¾ÃÂÃÂ¸ÃÂ±ÃÂ¸ÃÂÃÂÃÂÃÂ",
    "ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂÃÂ»ÃÂÃÂ¶ÃÂ¸ÃÂ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ Ã¢ÂÂ ÃÂÃÂµÃÂÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂ°ÃÂ·ÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂ ÃÂ¾ ÃÂÃÂÃÂ¾ÃÂºÃÂ°ÃÂ ÃÂ¸ ÃÂºÃÂ°ÃÂÃÂµÃÂÃÂÃÂ²ÃÂµ",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ° ÃÂºÃÂÃÂ»ÃÂ¸ÃÂÃÂ°ÃÂ¼ÃÂ¸ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂÃÂµÃÂ¼ ÃÂÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂºÃÂ¸ ÃÂ¿ÃÂµÃÂÃÂµÃÂ´ ÃÂ·ÃÂ°ÃÂºÃÂ»ÃÂÃÂÃÂµÃÂ½ÃÂ¸ÃÂµÃÂ¼ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂÃÂ°ÃÂºÃÂÃÂ° Ã¢ÂÂ ÃÂ½ÃÂ°ÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂµÃÂÃÂ ÃÂ¾ÃÂÃÂ±ÃÂ¾ÃÂÃÂ° ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂÃÂ¸ÃÂºÃÂ¾ÃÂ²",
    "ÃÂ§ÃÂÃÂ¾ ÃÂ¿ÃÂÃÂ¾ÃÂ¸ÃÂÃÂÃÂ¾ÃÂ´ÃÂ¸ÃÂ ÃÂ½ÃÂ° ÃÂÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂºÃÂµ ÃÂ·ÃÂ° 6 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ ÃÂ´ÃÂ¾ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸ Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¾ÃÂ¸ÃÂ·ÃÂ²ÃÂ¾ÃÂ´ÃÂÃÂÃÂ²ÃÂ¾ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ¸ ÃÂ¸ÃÂ·ÃÂ½ÃÂÃÂÃÂÃÂ¸",
    "ÃÂÃÂ°ÃÂº ÃÂ²ÃÂÃÂ³ÃÂ»ÃÂÃÂ´ÃÂ¸ÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂÃÂ¾ÃÂ»ÃÂ ÃÂºÃÂ°ÃÂÃÂµÃÂÃÂÃÂ²ÃÂ° ÃÂ½ÃÂ° ÃÂºÃÂ¸ÃÂÃÂ°ÃÂ¹ÃÂÃÂºÃÂ¾ÃÂ¹ ÃÂÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂºÃÂµ Ã¢ÂÂ ÃÂ²ÃÂ¸ÃÂ´ÃÂµÃÂ¾-ÃÂºÃÂ¾ÃÂ½ÃÂÃÂÃÂ¾ÃÂ»ÃÂ, ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂ¿ÃÂµÃÂÃÂµÃÂ´ ÃÂÃÂ¿ÃÂ°ÃÂºÃÂ¾ÃÂ²ÃÂºÃÂ¾ÃÂ¹",
    "ÃÂ¤ÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ vs ÃÂÃÂÃÂ°ÃÂ½ÃÂÃÂ¶ÃÂ¾ÃÂ Ã¢ÂÂ ÃÂ² ÃÂÃÂÃÂ¼ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂ¸ÃÂÃÂ° ÃÂ¸ ÃÂ¾ÃÂÃÂºÃÂÃÂ´ÃÂ° ÃÂ¼ÃÂ ÃÂ·ÃÂ°ÃÂºÃÂ°ÃÂ·ÃÂÃÂ²ÃÂ°ÃÂµÃÂ¼ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂÃÂµ ÃÂºÃÂ°ÃÂÃÂµÃÂ³ÃÂ¾ÃÂÃÂ¸ÃÂ¸ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ¸",
    "ÃÂÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ 340 ÃÂÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂºÃÂ°ÃÂ¼ÃÂ¸ Ã¢ÂÂ ÃÂÃÂ¸ÃÂÃÂÃÂµÃÂ¼ÃÂ° ÃÂ¾ÃÂÃÂ±ÃÂ¾ÃÂÃÂ°, ÃÂÃÂµÃÂ¹ÃÂÃÂ¸ÃÂ½ÃÂ³ÃÂ¸, ÃÂÃÂºÃÂÃÂºÃÂ»ÃÂÃÂ·ÃÂ¸ÃÂ²ÃÂ½ÃÂÃÂµ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂÃÂ°ÃÂºÃÂÃÂ",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂµÃÂ¹ÃÂÃÂ ÃÂ¸ ÃÂ¿ÃÂÃÂ¾ÃÂµÃÂºÃÂÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂ¾ÃÂ¼ÃÂ¿ÃÂ»ÃÂµÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ»ÃÂ¸ ÃÂÃÂµÃÂÃÂÃÂ¾ÃÂÃÂ°ÃÂ½ Ã¢ÂÂ 40 ÃÂ±ÃÂ°ÃÂ½ÃÂºÃÂµÃÂÃÂ½ÃÂÃÂ ÃÂÃÂÃÂÃÂ»ÃÂÃÂµÃÂ² ÃÂ¸ 10 ÃÂÃÂÃÂ¾ÃÂ»ÃÂ¾ÃÂ² ÃÂ¸ÃÂ· ÃÂ¤ÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ ÃÂ·ÃÂ° 5 ÃÂ½ÃÂµÃÂ´ÃÂµÃÂ»ÃÂ. ÃÂÃÂÃÂÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ¿ÃÂÃÂ¾ÃÂµÃÂºÃÂÃÂ°",
    "ÃÂÃÂ¾ÃÂÃÂÃÂ¸ÃÂ½ÃÂ°ÃÂ ÃÂ¿ÃÂ¾ÃÂ´ ÃÂºÃÂ»ÃÂÃÂ ÃÂ ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂÃÂ¾ÃÂ¼ 300 000 Ã¢ÂÂ½ Ã¢ÂÂ ÃÂÃÂÃÂ¾ ÃÂ²ÃÂÃÂ¾ÃÂ´ÃÂ¸ÃÂ ÃÂ¸ ÃÂºÃÂ°ÃÂº ÃÂÃÂÃÂ¾ ÃÂ²ÃÂÃÂ³ÃÂ»ÃÂÃÂ´ÃÂ¸ÃÂ",
    "ÃÂÃÂÃÂµÃÂ»ÃÂ ÃÂ½ÃÂ° 30 ÃÂ½ÃÂ¾ÃÂ¼ÃÂµÃÂÃÂ¾ÃÂ² Ã¢ÂÂ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂºÃÂ¾ÃÂ¼ÃÂ¿ÃÂ»ÃÂµÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ»ÃÂ¸ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¾ÃÂ ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂµÃÂ¹ ÃÂ´ÃÂ¾ ÃÂÃÂµÃÂÃÂµÃÂ¿ÃÂÃÂ½ÃÂ°",
    "ÃÂÃÂÃÂ¸ÃÂ ÃÂ´ÃÂ»ÃÂ IT-ÃÂºÃÂ¾ÃÂ¼ÃÂ¿ÃÂ°ÃÂ½ÃÂ¸ÃÂ¸ Ã¢ÂÂ ÃÂ¿ÃÂµÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²ÃÂ¾ÃÂÃÂ½ÃÂÃÂ¹ ÃÂÃÂÃÂ¾ÃÂ» Executive 5 ÃÂ¼ÃÂµÃÂÃÂÃÂ¾ÃÂ² ÃÂ¸ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ¸ÃÂµ ÃÂ·ÃÂ¾ÃÂ½ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂ¹ÃÂÃÂÃÂÃÂ°ÃÂ¹ÃÂ» ÃÂ¸ ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂÃÂµÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂ°ÃÂº ÃÂ¾ÃÂ±ÃÂÃÂÃÂÃÂÃÂ¾ÃÂ¸ÃÂÃÂ ÃÂ´ÃÂ¾ÃÂ¼ÃÂ°ÃÂÃÂ½ÃÂ¸ÃÂ¹ ÃÂ¾ÃÂÃÂ¸ÃÂ ÃÂ ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂÃÂ¾ÃÂ¼ 150 000 Ã¢ÂÂ½ Ã¢ÂÂ ÃÂÃÂÃÂ¾ÃÂ», ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ¾, ÃÂÃÂÃÂµÃÂ»ÃÂ»ÃÂ°ÃÂ¶ÃÂ¸ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",
    "Japandi ÃÂÃÂÃÂ¸ÃÂ»ÃÂ ÃÂ² ÃÂ¸ÃÂ½ÃÂÃÂµÃÂÃÂÃÂµÃÂÃÂµ Ã¢ÂÂ ÃÂ¾ÃÂÃÂµÃÂ, ÃÂ»ÃÂÃÂ½, ÃÂ¼ÃÂ¸ÃÂ½ÃÂ¸ÃÂ¼ÃÂ°ÃÂ»ÃÂ¸ÃÂ·ÃÂ¼. ÃÂÃÂ°ÃÂºÃÂÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ²ÃÂÃÂ±ÃÂÃÂ°ÃÂÃÂ",
    "ÃÂÃÂ¾ÃÂÃÂÃÂ¸ÃÂ½ÃÂ°ÃÂ ÃÂ² ÃÂÃÂÃÂ¸ÃÂ»ÃÂµ mid-century modern Ã¢ÂÂ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ÃÂ ÃÂ¸ ÃÂºÃÂÃÂµÃÂÃÂ»ÃÂ° ÃÂºÃÂ¾ÃÂÃÂ¾ÃÂÃÂÃÂµ ÃÂÃÂ¾ÃÂ·ÃÂ´ÃÂ°ÃÂÃÂ ÃÂ°ÃÂÃÂ¼ÃÂ¾ÃÂÃÂÃÂµÃÂÃÂ",
    "ÃÂÃÂ¾ÃÂ´ÃÂÃÂ»ÃÂÃÂ½ÃÂÃÂ¹ ÃÂ´ÃÂ¸ÃÂ²ÃÂ°ÃÂ½ vs ÃÂ¾ÃÂ±ÃÂÃÂÃÂ½ÃÂÃÂ¹ Ã¢ÂÂ ÃÂÃÂÃÂ¾ ÃÂ»ÃÂÃÂÃÂÃÂµ ÃÂ´ÃÂ»ÃÂ ÃÂ±ÃÂ¾ÃÂ»ÃÂÃÂÃÂ¾ÃÂ¹ ÃÂ³ÃÂ¾ÃÂÃÂÃÂ¸ÃÂ½ÃÂ¾ÃÂ¹",
    "ÃÂ¡ÃÂ¿ÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ ÃÂ¼ÃÂµÃÂÃÂÃÂ ÃÂ ÃÂ±ÃÂÃÂ´ÃÂ¶ÃÂµÃÂÃÂ¾ÃÂ¼ 200 000 Ã¢ÂÂ½ Ã¢ÂÂ ÃÂºÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂÃÂ, ÃÂÃÂÃÂ¼ÃÂ±ÃÂ¾ÃÂÃÂºÃÂ¸, ÃÂ³ÃÂ°ÃÂÃÂ´ÃÂµÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂ°ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ° ÃÂ¸ ÃÂ»ÃÂ¾ÃÂ³ÃÂ¸ÃÂÃÂÃÂ¸ÃÂºÃÂ° Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂ°ÃÂº ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ ÃÂ±ÃÂµÃÂ»ÃÂ°ÃÂ ÃÂÃÂ°ÃÂ¼ÃÂ¾ÃÂ¶ÃÂ½ÃÂ Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂÃÂÃÂ¾ ÃÂ²ÃÂ°ÃÂ¶ÃÂ½ÃÂ¾ ÃÂ¸ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂÃÂÃÂ¾ ÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂµÃÂ¼",
    "ÃÂ¡ÃÂºÃÂ¾ÃÂ»ÃÂÃÂºÃÂ¾ ÃÂ¸ÃÂ´ÃÂÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ Ã¢ÂÂ ÃÂÃÂµÃÂ°ÃÂ»ÃÂÃÂ½ÃÂÃÂµ ÃÂÃÂÃÂ¾ÃÂºÃÂ¸ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸ ÃÂ¿ÃÂ¾ ÃÂÃÂÃÂÃÂ°ÃÂ½ÃÂ°ÃÂ¼",
    "ÃÂÃÂ°ÃÂº ÃÂÃÂ¿ÃÂ°ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ° ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ Ã¢ÂÂ ÃÂÃÂÃÂ¾ ÃÂ·ÃÂ°ÃÂÃÂ¸ÃÂÃÂ°ÃÂµÃÂ ÃÂµÃÂ ÃÂ² ÃÂ¿ÃÂÃÂÃÂ¸ ÃÂ½ÃÂ° 8 000 ÃÂºÃÂ¼",
    "ÃÂÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ° ÃÂ² ÃÂÃÂ°ÃÂ·ÃÂ°ÃÂÃÂÃÂÃÂ°ÃÂ½, ÃÂÃÂ¸ÃÂÃÂ³ÃÂ¸ÃÂ·ÃÂ¸ÃÂ, ÃÂÃÂÃÂ­ Ã¢ÂÂ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂÃÂ¼ÃÂ¸ ÃÂÃÂÃÂÃÂ°ÃÂ½ÃÂ°ÃÂ¼ÃÂ¸",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂ¡ÃÂÃÂ°ÃÂ²ÃÂ½ÃÂµÃÂ½ÃÂ¸ÃÂ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "ÃÂÃÂÃÂ°ÃÂ»ÃÂÃÂÃÂ½ÃÂÃÂºÃÂ°ÃÂ ÃÂ¼ÃÂµÃÂ±ÃÂµÃÂ»ÃÂ vs ÃÂÃÂ¸ÃÂÃÂ°ÃÂ¹ Ã¢ÂÂ ÃÂ² ÃÂÃÂÃÂ¼ ÃÂÃÂµÃÂ°ÃÂ»ÃÂÃÂ½ÃÂ°ÃÂ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂ¸ÃÂÃÂ° ÃÂ¿ÃÂÃÂ¸ ÃÂ¾ÃÂ´ÃÂ¸ÃÂ½ÃÂ°ÃÂºÃÂ¾ÃÂ²ÃÂ¾ÃÂ¹ ÃÂÃÂµÃÂ½ÃÂµ",
    "ÃÂÃÂµÃÂ±ÃÂµÃÂ»ÃÂ ÃÂ¸ÃÂ· ÃÂÃÂ¸ÃÂÃÂ°ÃÂ vs ÃÂÃÂ¾ÃÂÃÂÃÂ¸ÃÂ¹ÃÂÃÂºÃÂ¸ÃÂµ ÃÂ¼ÃÂ°ÃÂ³ÃÂ°ÃÂ·ÃÂ¸ÃÂ½ÃÂ Ã¢ÂÂ ÃÂÃÂÃÂ°ÃÂ²ÃÂ½ÃÂ¸ÃÂ²ÃÂ°ÃÂµÃÂ¼ ÃÂÃÂµÃÂ½ÃÂ ÃÂ½ÃÂ° ÃÂ¾ÃÂ´ÃÂ¸ÃÂ½ÃÂ°ÃÂºÃÂ¾ÃÂ²ÃÂÃÂµ ÃÂ¿ÃÂ¾ÃÂ·ÃÂ¸ÃÂÃÂ¸ÃÂ¸",
    "ÃÂ¤ÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂÃÂ½ÃÂ°ÃÂ ÃÂÃÂµÃÂ½ÃÂ° EXW vs ÃÂÃÂ¾ÃÂ·ÃÂ½ÃÂ¸ÃÂÃÂ° ÃÂ² ÃÂ ÃÂ¾ÃÂÃÂÃÂ¸ÃÂ¸ Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂÃÂµÃÂ¼ÃÂ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂ¸ÃÂÃÂ° ÃÂ² 2-3 ÃÂÃÂ°ÃÂ·ÃÂ° ÃÂÃÂÃÂ¾ ÃÂ½ÃÂ¾ÃÂÃÂ¼ÃÂ°",

    # Ã¢ÂÂÃ¢ÂÂ ÃÂ ÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ° ÃÂ ÃÂ½ÃÂ°ÃÂ¼ÃÂ¸ Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ
    "340+ ÃÂÃÂ°ÃÂ±ÃÂÃÂ¸ÃÂº ÃÂ¤ÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ ÃÂ¸ ÃÂÃÂÃÂ°ÃÂ½ÃÂÃÂ¶ÃÂ¾ÃÂ Ã¢ÂÂ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂ²ÃÂÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂÃÂ¸ÃÂºÃÂ¾ÃÂ² ÃÂ¸ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂÃÂ¾ÃÂ»ÃÂ¸ÃÂÃÂÃÂµÃÂ¼ ÃÂºÃÂ°ÃÂÃÂµÃÂÃÂÃÂ²ÃÂ¾",
    "ÃÂÃÂ°ÃÂº ÃÂÃÂ´ÃÂµÃÂ»ÃÂ°ÃÂÃÂ ÃÂ·ÃÂ°ÃÂºÃÂ°ÃÂ· ÃÂ² KOKAHOUSE Ã¢ÂÂ ÃÂ¾ÃÂ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂ¾ÃÂÃÂ° ÃÂ´ÃÂ¾ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸. ÃÂÃÂ¾ÃÂÃÂ°ÃÂ³ÃÂ¾ÃÂ²ÃÂÃÂ¹ ÃÂ¿ÃÂÃÂ¾ÃÂÃÂµÃÂÃÂ",
    "ÃÂÃÂ¾ÃÂ¼ÃÂ¿ÃÂ»ÃÂµÃÂºÃÂÃÂ°ÃÂÃÂ¸ÃÂ ÃÂ¾ÃÂ±ÃÂÃÂµÃÂºÃÂÃÂ¾ÃÂ² Ã¢ÂÂ ÃÂ¾ÃÂÃÂµÃÂ»ÃÂ¸, ÃÂÃÂµÃÂÃÂÃÂ¾ÃÂÃÂ°ÃÂ½ÃÂ, ÃÂ¾ÃÂÃÂ¸ÃÂÃÂ, ÃÂ°ÃÂ¿ÃÂ°ÃÂÃÂÃÂ°ÃÂ¼ÃÂµÃÂ½ÃÂÃÂ. ÃÂÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼",
    "ÃÂÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ° ÃÂ² ÃÂÃÂÃÂ±ÃÂ»ÃÂÃÂ, ÃÂ´ÃÂ¾ÃÂ»ÃÂ»ÃÂ°ÃÂÃÂ°ÃÂ, ÃÂºÃÂÃÂ¸ÃÂ¿ÃÂÃÂµ Ã¢ÂÂ ÃÂºÃÂ°ÃÂº ÃÂ¼ÃÂ ÃÂÃÂ°ÃÂ±ÃÂ¾ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂ ÃÂÃÂ°ÃÂ·ÃÂ½ÃÂÃÂ¼ÃÂ¸ ÃÂÃÂÃÂµÃÂ¼ÃÂ°ÃÂ¼ÃÂ¸ ÃÂ¾ÃÂ¿ÃÂ»ÃÂ°ÃÂÃÂ",
]

_last_topic_index = -1


async def auto_post_to_channel(bot):
    """ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ» Ã¢ÂÂ ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂÃÂºÃÂ°ÃÂµÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ ÃÂÃÂ°ÃÂÃÂ¿ÃÂ¸ÃÂÃÂ°ÃÂ½ÃÂ¸ÃÂ."""
    global _last_topic_index
    try:
        # ÃÂÃÂÃÂ±ÃÂ¸ÃÂÃÂ°ÃÂµÃÂ¼ ÃÂÃÂµÃÂ¼ÃÂ Ã¢ÂÂ ÃÂ¿ÃÂ¾ ÃÂ¾ÃÂÃÂµÃÂÃÂµÃÂ´ÃÂ¸, ÃÂ½ÃÂµ ÃÂ¿ÃÂ¾ÃÂ²ÃÂÃÂ¾ÃÂÃÂÃÂµÃÂ¼
        _last_topic_index = (_last_topic_index + 1) % len(AUTO_POST_TOPICS)
        topic = AUTO_POST_TOPICS[_last_topic_index]

        logger.info(f"ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂ: {topic[:50]}...")

        prompt = f"""ÃÂÃÂ°ÃÂ¿ÃÂ¸ÃÂÃÂ¸ ÃÂ¿ÃÂÃÂ¾ÃÂ´ÃÂ°ÃÂÃÂÃÂ¸ÃÂ¹ ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ´ÃÂ»ÃÂ Telegram-ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»ÃÂ° KOKAHOUSE.

ÃÂ¢ÃÂµÃÂ¼ÃÂ°: {topic}

ÃÂ¢ÃÂÃÂµÃÂ±ÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ:
Ã¢ÂÂ 3-4 ÃÂ°ÃÂ±ÃÂ·ÃÂ°ÃÂÃÂ°, ÃÂ¶ÃÂ¸ÃÂ²ÃÂ¾ÃÂ¹ ÃÂÃÂÃÂ¸ÃÂ»ÃÂ ÃÂ±ÃÂµÃÂ· ÃÂºÃÂ°ÃÂ½ÃÂÃÂµÃÂ»ÃÂÃÂÃÂÃÂ¸ÃÂ½ÃÂ
Ã¢ÂÂ ÃÂ£ÃÂ¿ÃÂ¾ÃÂ¼ÃÂÃÂ½ÃÂ¸ ÃÂºÃÂ¾ÃÂ½ÃÂºÃÂÃÂµÃÂÃÂ½ÃÂÃÂµ ÃÂ¼ÃÂ°ÃÂÃÂµÃÂÃÂ¸ÃÂ°ÃÂ»ÃÂ ÃÂ¸ ÃÂ¿ÃÂÃÂµÃÂ¸ÃÂ¼ÃÂÃÂÃÂµÃÂÃÂÃÂ²ÃÂ°
Ã¢ÂÂ ÃÂ¦ÃÂµÃÂ½ÃÂ¾ÃÂ²ÃÂ¾ÃÂ¹ ÃÂ¾ÃÂÃÂ¸ÃÂµÃÂ½ÃÂÃÂ¸ÃÂ ÃÂµÃÂÃÂ»ÃÂ¸ ÃÂµÃÂÃÂÃÂ
Ã¢ÂÂ ÃÂ ÃÂºÃÂ¾ÃÂ½ÃÂÃÂµ: "ÃÂÃÂ¾ÃÂ´ÃÂÃÂ¾ÃÂ±ÃÂ½ÃÂµÃÂµ ÃÂ¸ ÃÂÃÂ°ÃÂÃÂÃÂÃÂ ÃÂ´ÃÂ¾ÃÂÃÂÃÂ°ÃÂ²ÃÂºÃÂ¸ Ã¢ÂÂ @kokahouse_Yulia"
Ã¢ÂÂ 2-3 emoji ÃÂÃÂ¼ÃÂµÃÂÃÂÃÂ½ÃÂ¾
Ã¢ÂÂ ÃÂ¤ÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂµ Markdown (ÃÂ¶ÃÂ¸ÃÂÃÂ½ÃÂÃÂ¹, ÃÂºÃÂÃÂÃÂÃÂ¸ÃÂ²)
Ã¢ÂÂ ÃÂÃÂµÃÂ· ÃÂÃÂÃÂÃÂÃÂµÃÂ³ÃÂ¾ÃÂ²

ÃÂÃÂµÃÂÃÂ½ÃÂ¸ ÃÂ¢ÃÂÃÂÃÂ¬ÃÂÃÂ ÃÂÃÂµÃÂºÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ°."""

        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        post_text = response.content[0].text.strip()

        # ÃÂÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂÃÂµÃÂ¼ ÃÂ² ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»
        await bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        logger.info("Ã¢ÂÂ ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½")

    except Exception as e:
        # ÃÂÃÂÃÂ»ÃÂ¸ Markdown ÃÂÃÂ»ÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¾ÃÂ±ÃÂÃÂµÃÂ¼ ÃÂ±ÃÂµÃÂ· ÃÂÃÂ¾ÃÂÃÂ¼ÃÂ°ÃÂÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂ°ÃÂ½ÃÂ¸ÃÂ
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            logger.info("Ã¢ÂÂ ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¾ÃÂ¿ÃÂÃÂ±ÃÂ»ÃÂ¸ÃÂºÃÂ¾ÃÂ²ÃÂ°ÃÂ½ (ÃÂ±ÃÂµÃÂ· Markdown)")
        except Exception as e2:
            logger.error(f"ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂ ÃÂ¾ÃÂÃÂ¸ÃÂ±ÃÂºÃÂ°: {e2}")


# Ã¢ÂÂÃ¢ÂÂ ÃÂÃÂ°ÃÂ¿ÃÂÃÂÃÂº Ã¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂÃ¢ÂÂ

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()

    # ÃÂÃÂ»ÃÂ¸ÃÂµÃÂ½ÃÂÃÂÃÂºÃÂ¸ÃÂµ ÃÂºÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("reset",     cmd_reset))

    # ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° Ã¢ÂÂ ÃÂ¾ÃÂ±ÃÂÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ
    app.add_handler(CommandHandler("teach",     cmd_teach))
    app.add_handler(CommandHandler("knowledge", cmd_knowledge))

    # ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ° ÃÂÃÂ
    app.add_handler(CommandHandler("kp", cmd_kp))

    # ÃÂ¢ÃÂµÃÂÃÂ amoCRM
    async def cmd_test_amo(update, context):
        if not is_owner(update.effective_user):
            return
        await update.message.reply_text("Ã°ÂÂÂ ÃÂ¢ÃÂµÃÂÃÂÃÂ¸ÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂ´ÃÂºÃÂ»ÃÂÃÂÃÂµÃÂ½ÃÂ¸ÃÂµ ÃÂº amoCRM...")
        r = amo_request("GET", "account")
        if "error" in r:
            await update.message.reply_text(f"Ã¢ÂÂ amoCRM ÃÂ¾ÃÂÃÂ¸ÃÂ±ÃÂºÃÂ°: {r['error']}")
        else:
            name = r.get("name", "?")
            await update.message.reply_text(
                f"Ã¢ÂÂ amoCRM ÃÂ¿ÃÂ¾ÃÂ´ÃÂºÃÂ»ÃÂÃÂÃÂÃÂ½!\n"
                f"ÃÂÃÂºÃÂºÃÂ°ÃÂÃÂ½ÃÂ: {name}\n"
                f"ÃÂÃÂ¾ÃÂ¼ÃÂµÃÂ½: {AMO_DOMAIN}\n"
                f"API: {AMO_API}"
            )
    app.add_handler(CommandHandler("test_amo", cmd_test_amo))

    # ÃÂÃÂ¾ÃÂ¼ÃÂ°ÃÂ½ÃÂ´ÃÂ ÃÂ²ÃÂ»ÃÂ°ÃÂ´ÃÂµÃÂ»ÃÂÃÂÃÂ° Ã¢ÂÂ ÃÂºÃÂ°ÃÂ½ÃÂ°ÃÂ»
    app.add_handler(CommandHandler("post",      cmd_post))
    app.add_handler(CommandHandler("ai_post",   cmd_ai_post))
    app.add_handler(CommandHandler("confirm",   cmd_confirm))
    app.add_handler(CommandHandler("channel",   cmd_channel))
    app.add_handler(CommandHandler("menu",      cmd_menu))
    app.add_handler(CommandHandler("skip",      cmd_skip))

    # ÃÂÃÂµÃÂ´ÃÂ¸ÃÂ° (ÃÂÃÂ¾ÃÂÃÂ¾ ÃÂÃÂ½ÃÂ°ÃÂÃÂ°ÃÂ»ÃÂ° Ã¢ÂÂ ÃÂÃÂÃÂ¾ÃÂ±ÃÂ /post_photo ÃÂ¿ÃÂµÃÂÃÂµÃÂÃÂ²ÃÂ°ÃÂÃÂ¸ÃÂÃÂ)
    app.add_handler(MessageHandler(filters.PHOTO, handle_owner_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # ÃÂ¢ÃÂµÃÂºÃÂÃÂ Ã¢ÂÂ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµÃÂ´ÃÂ½ÃÂ¸ÃÂ¼
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # ÃÂÃÂ»ÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¸ÃÂº ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂÃÂºÃÂ°ÃÂµÃÂÃÂÃÂ ÃÂ¿ÃÂ¾ÃÂÃÂ»ÃÂµ ÃÂÃÂÃÂ°ÃÂÃÂÃÂ° asyncio loop
    async def post_init(application):
        scheduler = AsyncIOScheduler(timezone="UTC")

        # ÃÂÃÂ²ÃÂÃÂ¾-ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ ÃÂ¿ÃÂ½/ÃÂÃÂ/ÃÂ¿ÃÂ ÃÂ² 10:00 ÃÂÃÂ¡ÃÂ (UTC+3 = 07:00 UTC)
        scheduler.add_job(
            auto_post_to_channel,
            CronTrigger(day_of_week="mon,wed,fri", hour=7, minute=0),
            args=[application.bot], id="auto_post"
        )

        # ÃÂÃÂ¶ÃÂµÃÂ´ÃÂ½ÃÂµÃÂ²ÃÂ½ÃÂÃÂ¹ ÃÂ¾ÃÂÃÂÃÂÃÂ ÃÂ² 9:00 ÃÂÃÂ¡ÃÂ (06:00 UTC)
        scheduler.add_job(
            daily_report, CronTrigger(hour=6, minute=0),
            args=[application.bot], id="daily_report"
        )

        # Follow-up ÃÂºÃÂ°ÃÂ¶ÃÂ´ÃÂÃÂµ 6 ÃÂÃÂ°ÃÂÃÂ¾ÃÂ² Ã¢ÂÂ ÃÂ¿ÃÂÃÂ¾ÃÂ²ÃÂµÃÂÃÂÃÂµÃÂ¼ ÃÂ·ÃÂ°ÃÂ²ÃÂ¸ÃÂÃÂÃÂ¸ÃÂ ÃÂ»ÃÂ¸ÃÂ´ÃÂ¾ÃÂ²
        scheduler.add_job(
            followup_check, CronTrigger(hour="6,12,18", minute=0),
            args=[application.bot], id="followup"
        )

        scheduler.start()
        logger.info("Ã°ÂÂÂ ÃÂÃÂ»ÃÂ°ÃÂ½ÃÂ¸ÃÂÃÂ¾ÃÂ²ÃÂÃÂ¸ÃÂº ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂÃÂµÃÂ½: ÃÂ¿ÃÂ¾ÃÂÃÂÃÂ + ÃÂ¾ÃÂÃÂÃÂÃÂ + follow-up")

    app.post_init = post_init

    logger.info("Ã°ÂÂ¤Â KOKAHOUSE Bot ÃÂ·ÃÂ°ÃÂ¿ÃÂÃÂÃÂµÃÂ½")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
