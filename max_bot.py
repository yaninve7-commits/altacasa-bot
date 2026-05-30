"""
ALTA CASA — MAX Messenger Bot
Тот же AI (Юля) + Notion CRM, канал MAX.

pip install maxapi anthropic notion-client python-dotenv
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv

from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

import anthropic
from notion_client import Client as NotionClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Конфиг ───────────────────────────────────────────────────────────────────
MAX_TOKEN       = os.getenv("MAX_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
NOTION_TOKEN    = os.getenv("NOTION_TOKEN")
NOTION_DB_ID    = os.getenv("NOTION_CLIENTS_DB_ID")
MANAGER_MAX_ID  = os.getenv("MANAGER_CHAT_ID")   # твой user_id в MAX

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
notion = NotionClient(auth=NOTION_TOKEN)

bot = Bot(MAX_TOKEN)
dp  = Dispatcher()

# ── Системный промпт ──────────────────────────────────────────────────────────
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

KNOWLEDGE_FILE = "custom_knowledge.txt"

def load_knowledge() -> str:
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ\n═══════════════════════════════\n{content}"
    return ""

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()

# ── Хранилище диалогов ────────────────────────────────────────────────────────
dialogs: dict[int, list[dict]] = {}
MAX_HISTORY = 20

# ── Notion helpers ────────────────────────────────────────────────────────────

def get_or_create_client(user_id: int, name: str, username: str = "") -> str:
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "Telegram ID", "number": {"equals": user_id}}
    )
    if results["results"]:
        return results["results"][0]["id"]

    props = {
        "Name":        {"title": [{"text": {"content": name}}]},
        "Telegram ID": {"number": user_id},
        "Канал":       {"select": {"name": "MAX"}},
        "Квалификация":{"select": {"name": "Холодный"}},
        "Дата":        {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    page = notion.pages.create(parent={"database_id": NOTION_DB_ID}, properties=props)
    logger.info(f"Новый клиент MAX: {name} ({user_id})")
    return page["id"]


def update_client(page_id: str, dialog_text: str, qualification=None,
                  interest=None, budget=None, escalate=False):
    props = {
        "Диалог с ботом": {"rich_text": [{"text": {"content": dialog_text[-2000:]}}]},
    }
    if qualification:
        props["Квалификация"] = {"select": {"name": qualification}}
    if interest:
        props["Интерес"] = {"select": {"name": interest}}
    if budget:
        props["Бюджет ₽"] = {"number": budget}
    if escalate:
        props["Эскалировать"] = {"checkbox": True}
        props["Квалификация"] = {"select": {"name": "Передан менеджеру"}}
    notion.pages.update(page_id=page_id, properties=props)


# ── AI логика ─────────────────────────────────────────────────────────────────

def ask_claude(chat_id: int, user_message: str) -> dict:
    history = dialogs.get(chat_id, [])
    history.append({"role": "user", "content": user_message})

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=get_system_prompt(),
        messages=history[-MAX_HISTORY:]
    )

    raw = response.content[0].text
    history.append({"role": "assistant", "content": raw})
    dialogs[chat_id] = history[-MAX_HISTORY:]

    result = {"reply": raw, "qualification": None, "interest": None,
              "budget": None, "escalate": False}

    if "```json" in raw:
        try:
            json_part = raw.split("```json")[1].split("```")[0].strip()
            meta = json.loads(json_part)
            result["reply"]         = meta.get("reply", raw)
            result["qualification"] = meta.get("qualification")
            result["interest"]      = meta.get("interest")
            result["budget"]        = meta.get("budget")
            result["escalate"]      = meta.get("escalate", False)
        except Exception:
            pass

    return result


# ── MAX handlers ──────────────────────────────────────────────────────────────

@dp.bot_started()
async def on_start(event: BotStarted):
    """Клиент нажал 'Запустить бота'."""
    chat_id = event.chat_id
    dialogs[chat_id] = []

    try:
        get_or_create_client(chat_id, str(chat_id), "")
    except Exception as e:
        logger.error(f"Notion start error: {e}")

    await event.bot.send_message(
        chat_id=chat_id,
        text=(
            "Добро пожаловать в ALTA CASA 🏠\n\n"
            "Мы поставляем премиальную мебель из Китая — прямо с фабрик Фошаня и Гуанчжоу.\n\n"
            "Расскажите, что вас интересует: диваны, кресла, столики, спальня, офис или комплектация объекта?"
        )
    )


@dp.message_created(Command("start"))
async def on_cmd_start(event: MessageCreated):
    chat_id = event.message.recipient.chat_id
    dialogs[chat_id] = []

    try:
        user = event.message.sender
        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Клиент"
        get_or_create_client(user.user_id, name)
    except Exception as e:
        logger.error(f"Notion cmd_start error: {e}")

    await event.message.answer(
        "Добро пожаловать в ALTA CASA 🏠\n\n"
        "Мы поставляем премиальную мебель из Китая напрямую с фабрик.\n\n"
        "Что вас интересует?"
    )


@dp.message_created()
async def on_message(event: MessageCreated):
    """Все входящие сообщения."""
    msg     = event.message
    chat_id = msg.recipient.chat_id
    text    = msg.body.text if msg.body else ""

    if not text:
        return

    user = msg.sender
    user_id = user.user_id
    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Клиент"

    logger.info(f"[MAX][{user_id}] {name}: {text}")

    # Получаем/создаём клиента в Notion
    page_id = None
    try:
        page_id = get_or_create_client(user_id, name)
    except Exception as e:
        logger.error(f"Notion error: {e}")

    # AI ответ
    result = ask_claude(chat_id, text)

    # Уведомление менеджеру при эскалации
    if result["escalate"] and MANAGER_MAX_ID:
        try:
            await bot.send_message(
                chat_id=int(MANAGER_MAX_ID),
                text=(
                    f"🔥 Горячий лид из MAX!\n"
                    f"Клиент: {name} (ID: {user_id})\n"
                    f"Сообщение: {text[:200]}"
                )
            )
        except Exception as e:
            logger.error(f"Escalation error: {e}")

    # Обновить Notion
    if page_id:
        try:
            history = dialogs.get(chat_id, [])
            dialog_text = "\n".join(
                f"{'👤' if m['role']=='user' else '🤖'} {m['content']}"
                for m in history[-10:]
            )
            update_client(page_id, dialog_text,
                          qualification=result["qualification"],
                          interest=result["interest"],
                          budget=result["budget"],
                          escalate=result["escalate"])
        except Exception as e:
            logger.error(f"Notion update error: {e}")

    # Ответить клиенту
    await msg.answer(result["reply"])


# ── Запуск ────────────────────────────────────────────────────────────────────

async def main():
    await bot.delete_webhook()   # убираем webhook если был
    logger.info("🤖 ALTA CASA MAX Bot запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
