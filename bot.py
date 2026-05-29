"""
ALTA CASA — AI Telegram Bot
Бот для общения с клиентами. Claude AI + Notion CRM.

Зависимости: pip install python-telegram-bot anthropic notion-client python-dotenv
"""

import os
import logging
import json
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import anthropic
from notion_client import Client as NotionClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Клиенты ──────────────────────────────────────────────────────────────────
TG_TOKEN       = os.getenv("TG_TOKEN")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")
NOTION_TOKEN   = os.getenv("NOTION_TOKEN")
NOTION_DB_ID   = os.getenv("NOTION_CLIENTS_DB_ID")   # ID базы "Клиенты"
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")        # куда слать уведомление при эскалации

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
notion = NotionClient(auth=NOTION_TOKEN)

# ── Системный промпт ──────────────────────────────────────────────────────────
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

# ── Хранилище диалогов в памяти (chat_id → список сообщений) ─────────────────
dialogs: dict[int, list[dict]] = {}

MAX_HISTORY = 20  # последних сообщений в контексте


# ── Notion helpers ────────────────────────────────────────────────────────────

def get_or_create_client(tg_id: int, name: str, username: str) -> str:
    """Найти клиента по Telegram ID или создать нового. Вернуть page_id."""
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "Telegram ID", "number": {"equals": tg_id}}
    )
    if results["results"]:
        return results["results"][0]["id"]

    # Создаём нового
    tg_url = f"https://t.me/{username}" if username else ""
    page = notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties={
            "Name":        {"title": [{"text": {"content": name}}]},
            "Telegram ID": {"number": tg_id},
            "Telegram":    {"url": tg_url} if tg_url else {"url": None},
            "Канал":       {"select": {"name": "Telegram"}},
            "Квалификация":{"select": {"name": "Холодный"}},
            "Язык":        {"select": {"name": "RU"}},
            "Дата":        {"date": {"start": datetime.utcnow().date().isoformat()}},
        }
    )
    logger.info(f"Новый клиент создан: {name} ({tg_id})")
    return page["id"]


def update_client(page_id: str, dialog_text: str, qualification: str = None,
                  interest: str = None, budget: float = None, escalate: bool = False):
    """Обновить запись клиента в Notion."""
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
    """
    Отправить сообщение в Claude, получить ответ.
    Возвращает dict: {reply, qualification, interest, budget, escalate}
    """
    history = dialogs.get(chat_id, [])
    history.append({"role": "user", "content": user_message})

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=history[-MAX_HISTORY:]
    )

    raw = response.content[0].text
    history.append({"role": "assistant", "content": raw})
    dialogs[chat_id] = history[-MAX_HISTORY:]

    # Пытаемся распарсить JSON-метаданные если AI вернул их
    result = {
        "reply": raw,
        "qualification": None,
        "interest": None,
        "budget": None,
        "escalate": False,
    }

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


# ── Telegram handlers ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = user.full_name or "Клиент"
    dialogs[user.id] = []  # сбрасываем историю

    page_id = get_or_create_client(user.id, name, user.username or "")

    welcome = (
        f"Добро пожаловать в *ALTA CASA* 🏠\n\n"
        f"Мы поставляем премиальную мебель из Китая — прямо с фабрик Фошаня и Гуанчжоу.\n\n"
        f"Расскажите, что вас интересует: диваны, кресла, столики, спальня, офис или комплектация объекта?"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
    update_client(page_id, f"[START] {datetime.now():%Y-%m-%d %H:%M}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    name = user.full_name or "Клиент"

    logger.info(f"[{user.id}] {name}: {text}")

    # Получаем/создаём клиента в Notion
    page_id = get_or_create_client(user.id, name, user.username or "")

    # Показываем "печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Спрашиваем AI
    result = ask_claude(user.id, text)

    # Формируем текст диалога для Notion
    history = dialogs.get(user.id, [])
    dialog_text = "\n".join(
        f"{'👤' if m['role']=='user' else '🤖'} {m['content']}"
        for m in history[-10:]
    )

    # Обновляем Notion
    update_client(
        page_id=page_id,
        dialog_text=dialog_text,
        qualification=result["qualification"],
        interest=result["interest"],
        budget=result["budget"],
        escalate=result["escalate"],
    )

    # Если нужна эскалация — уведомить менеджера
    if result["escalate"] and MANAGER_CHAT_ID:
        manager_msg = (
            f"🔥 *Горячий лид!*\n"
            f"Клиент: {name}\n"
            f"TG: @{user.username or 'нет'}\n"
            f"Последнее сообщение: _{text}_\n\n"
            f"[Открыть в Notion](https://www.notion.so/{page_id.replace('-','')})"
        )
        try:
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=manager_msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка отправки менеджеру: {e}")

    # Отвечаем клиенту
    await update.message.reply_text(result["reply"])


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сбросить диалог (для тестов)."""
    dialogs[update.effective_user.id] = []
    await update.message.reply_text("Диалог сброшен. Начнём заново!")


# ── Запуск ────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 ALTA CASA Bot запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
