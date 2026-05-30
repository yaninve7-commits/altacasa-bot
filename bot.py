"""
ALTA CASA — AI Telegram Bot
Бот для общения с клиентами. Claude AI + Notion CRM.

Зависимости: pip install python-telegram-bot anthropic notion-client python-dotenv httpx
"""

import os
import logging
import json
import base64
import httpx
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import anthropic
from notion_client import Client as NotionClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Конфиг ───────────────────────────────────────────────────────────────────
TG_TOKEN        = os.getenv("TG_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
NOTION_TOKEN    = os.getenv("NOTION_TOKEN")
NOTION_DB_ID    = os.getenv("NOTION_CLIENTS_DB_ID")
MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")
CHANNEL_ID      = os.getenv("CHANNEL_ID", "@altacasacn")  # канал для постинга

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
notion = NotionClient(auth=NOTION_TOKEN)

# ── Системный промпт ──────────────────────────────────────────────────────────
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# ── База знаний (обучение через /teach) ───────────────────────────────────────
KNOWLEDGE_FILE = "custom_knowledge.txt"

def load_knowledge() -> str:
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ (добавлены владельцем)\n═══════════════════════════════\n{content}"
    return ""

def save_knowledge(entry: str):
    with open(KNOWLEDGE_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{entry}\n")

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()

# ── Хранилище диалогов ────────────────────────────────────────────────────────
dialogs: dict[int, list[dict]] = {}
MAX_HISTORY = 20


# ── Notion helpers ────────────────────────────────────────────────────────────

def get_or_create_client(tg_id: int, name: str, username: str) -> str:
    results = notion.databases.query(
        database_id=NOTION_DB_ID,
        filter={"property": "Telegram ID", "number": {"equals": tg_id}}
    )
    if results["results"]:
        return results["results"][0]["id"]

    tg_url = f"https://t.me/{username}" if username else None
    props = {
        "Name":        {"title": [{"text": {"content": name}}]},
        "Telegram ID": {"number": tg_id},
        "Канал":       {"select": {"name": "Telegram"}},
        "Квалификация":{"select": {"name": "Холодный"}},
        "Язык":        {"select": {"name": "RU"}},
        "Дата":        {"date": {"start": datetime.utcnow().date().isoformat()}},
    }
    if tg_url:
        props["Telegram"] = {"url": tg_url}
    page = notion.pages.create(parent={"database_id": NOTION_DB_ID}, properties=props)
    logger.info(f"Новый клиент: {name} ({tg_id})")
    return page["id"]


def update_client(page_id: str, dialog_text: str, qualification: str = None,
                  interest: str = None, budget: float = None, escalate: bool = False):
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

def ask_claude(chat_id: int, user_message: str, image_data: dict = None) -> dict:
    history = dialogs.get(chat_id, [])

    if image_data:
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": image_data["media_type"], "data": image_data["data"]}},
            {"type": "text", "text": user_message or "Клиент прислал изображение. Опиши что на нём и как это связано с мебелью."}
        ]
        history.append({"role": "user", "content": content})
    else:
        history.append({"role": "user", "content": user_message})

    # Упрощаем историю для API (только текст)
    api_history = []
    for m in history[-MAX_HISTORY:]:
        if isinstance(m["content"], list):
            api_history.append(m)
        else:
            api_history.append({"role": m["role"], "content": m["content"]})

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=get_system_prompt(),
        messages=api_history
    )

    raw = response.content[0].text
    history.append({"role": "assistant", "content": raw})
    dialogs[chat_id] = history[-MAX_HISTORY:]

    result = {"reply": raw, "qualification": None, "interest": None, "budget": None, "escalate": False}

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


async def download_photo(bot, file_id: str) -> dict:
    """Скачать фото из Telegram и вернуть base64."""
    file = await bot.get_file(file_id)
    url  = file.file_path
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    data = base64.standard_b64encode(resp.content).decode()
    return {"data": data, "media_type": "image/jpeg"}


# ── Telegram handlers ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dialogs[user.id] = []

    try:
        page_id = get_or_create_client(user.id, user.full_name or "Клиент", user.username or "")
        update_client(page_id, f"[START] {datetime.now():%Y-%m-%d %H:%M}")
    except Exception as e:
        logger.error(f"Notion /start error: {e}")

    await update.message.reply_text(
        "Добро пожаловать в *ALTA CASA* 🏠\n\n"
        "Мы поставляем премиальную мебель из Китая — прямо с фабрик Фошаня и Гуанчжоу.\n\n"
        "Расскажите, что вас интересует: диваны, кресла, столики, спальня, офис или комплектация объекта?",
        parse_mode="Markdown"
    )


async def cmd_teach(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить знания в базу. Только для владельца."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    text = update.message.text.replace("/teach", "").strip()
    if not text:
        await update.message.reply_text(
            "📚 *Как добавить знание:*\n\n"
            "`/teach вопрос: сколько стоит доставка?\nответ: от 3000 ₽ до Москвы`\n\n"
            "Или просто:\n"
            "`/teach Если клиент спрашивает про рассрочку — отвечай что работаем с банком Тинькофф, рассрочка 0% на 12 месяцев`",
            parse_mode="Markdown"
        )
        return

    entry = f"[{datetime.now():%d.%m.%Y}] {text}"
    save_knowledge(entry)
    logger.info(f"Knowledge added: {text[:80]}")
    await update.message.reply_text(f"✅ Добавлено в базу знаний Юли:\n\n_{text[:200]}_", parse_mode="Markdown")


async def cmd_knowledge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущую базу знаний. Только для владельца."""
    user = update.effective_user
    if str(user.id) != str(MANAGER_CHAT_ID):
        return

    knowledge = load_knowledge()
    if not knowledge:
        await update.message.reply_text("База знаний пуста. Используй /teach чтобы добавить.")
    else:
        await update.message.reply_text(f"📚 *База знаний:*\n\n{knowledge[:3000]}", parse_mode="Markdown")


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dialogs[update.effective_user.id] = []
    await update.message.reply_text("Диалог сброшен.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    name = user.full_name or "Клиент"

    logger.info(f"[{user.id}] {name}: {text}")

    page_id = None
    try:
        page_id = get_or_create_client(user.id, name, user.username or "")
    except Exception as e:
        logger.error(f"Notion error: {e}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = ask_claude(user.id, text)
    await _send_and_update(update, context, user, page_id, result, text)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото от клиента."""
    user = update.effective_user
    name = user.full_name or "Клиент"
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [ФОТО] {caption}")

    page_id = None
    try:
        page_id = get_or_create_client(user.id, name, user.username or "")
    except Exception as e:
        logger.error(f"Notion error: {e}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Берём наибольшее разрешение фото
        photo = update.message.photo[-1]
        image_data = await download_photo(context.bot, photo.file_id)
        prompt = caption if caption else "Клиент прислал фото. Пойми что это и ответь как менеджер по мебели."
        result = ask_claude(user.id, prompt, image_data=image_data)
    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        result = {"reply": "Получила ваше фото! Уточните, что именно вас интересует?",
                  "qualification": None, "interest": None, "budget": None, "escalate": False}

    await _send_and_update(update, context, user, page_id, result, f"[ФОТО] {caption}")


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка документов/файлов."""
    user = update.effective_user
    name = user.full_name or "Клиент"
    doc  = update.message.document
    caption = update.message.caption or ""

    logger.info(f"[{user.id}] {name}: [ФАЙЛ] {doc.file_name}")

    page_id = None
    try:
        page_id = get_or_create_client(user.id, name, user.username or "")
    except Exception as e:
        logger.error(f"Notion error: {e}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"Клиент прислал файл '{doc.file_name}'"
    if caption:
        prompt += f" с подписью: {caption}"
    prompt += ". Ответь как менеджер — уточни что это и как можешь помочь."

    result = ask_claude(user.id, prompt)
    await _send_and_update(update, context, user, page_id, result, f"[ФАЙЛ] {doc.file_name}")


async def _send_and_update(update, context, user, page_id, result, original_text):
    """Отправить ответ клиенту и обновить Notion."""
    # Уведомить менеджера при эскалации
    if result["escalate"] and MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=(
                    f"🔥 *Горячий лид!*\n"
                    f"Клиент: {user.full_name}\n"
                    f"TG: @{user.username or 'нет'} | ID: {user.id}\n"
                    f"Сообщение: _{original_text[:200]}_\n\n"
                    f"[Открыть Notion](https://www.notion.so/{(page_id or '').replace('-','')})"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Escalation notify error: {e}")

    # Обновить Notion
    if page_id:
        try:
            history = dialogs.get(user.id, [])
            dialog_text = "\n".join(
                f"{'👤' if m['role']=='user' else '🤖'} {m['content'] if isinstance(m['content'], str) else '[медиа]'}"
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
    await update.message.reply_text(result["reply"])


# ── Канал: команды владельца ──────────────────────────────────────────────────

def is_owner(user) -> bool:
    return str(user.id) == str(MANAGER_CHAT_ID)


async def cmd_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/post <текст> — опубликовать текст в канал."""
    if not is_owner(update.effective_user):
        return

    text = update.message.text.replace("/post", "").strip()
    if not text:
        await update.message.reply_text(
            "📢 *Команды для канала:*\n\n"
            "`/post Текст поста` — опубликовать текст\n"
            "`/post_photo` + прикрепи фото с подписью — опубликовать фото\n"
            "`/ai_post Тема` — Claude сам напишет пост по теме\n"
            "`/forward` — перешли любое сообщение боту и ответь /forward\n"
            "`/channel` — показать ID канала",
            parse_mode="Markdown"
        )
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="Markdown")
        await update.message.reply_text(f"✅ Опубликовано в {CHANNEL_ID}\n[Посмотреть](https://t.me/{CHANNEL_ID.lstrip('@')}/{msg.message_id})", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")


async def cmd_ai_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ai_post <тема> — Claude пишет пост и публикует в канал."""
    if not is_owner(update.effective_user):
        return

    topic = update.message.text.replace("/ai_post", "").strip()
    if not topic:
        await update.message.reply_text("Укажи тему: `/ai_post диван MC-A68 из итальянской кожи`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    prompt = f"""Напиши продающий пост для Telegram-канала мебельной компании ALTA CASA.

Тема/товар: {topic}

Требования:
— 3-5 абзацев, живой стиль
— Упомяни материалы, производство в Китае, цену если знаешь
— В конце: призыв написать в личку боту @altacasacn_bot
— Emoji уместно (1-3 штуки)
— Без хэштегов
— Форматирование Markdown (жирный, курсив)

Верни ТОЛЬКО текст поста, без пояснений."""

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    post_text = response.content[0].text.strip()

    # Сначала показываем превью владельцу
    await update.message.reply_text(
        f"📝 *Превью поста:*\n\n{post_text}\n\n"
        f"Отправь `/confirm` чтобы опубликовать, или отредактируй через `/post <текст>`",
        parse_mode="Markdown"
    )
    # Сохраняем в контекст для подтверждения
    context.user_data["pending_post"] = post_text


async def cmd_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/confirm — опубликовать последний ai_post."""
    if not is_owner(update.effective_user):
        return

    post_text = context.user_data.get("pending_post")
    if not post_text:
        await update.message.reply_text("Нет поста для публикации. Сначала используй /ai_post.")
        return

    try:
        msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        context.user_data.pop("pending_post", None)
        await update.message.reply_text(f"✅ Опубликовано!", parse_mode="Markdown")
    except Exception as e:
        # Если Markdown сломан — публикуем без форматирования
        try:
            msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            context.user_data.pop("pending_post", None)
            await update.message.reply_text("✅ Опубликовано (без Markdown).")
        except Exception as e2:
            await update.message.reply_text(f"❌ Ошибка: {e2}")


async def cmd_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/channel — показать текущий канал."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(f"📢 Текущий канал: `{CHANNEL_ID}`", parse_mode="Markdown")


async def handle_owner_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Если владелец присылает фото с подписью /post_photo — публикуем в канал."""
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
            await update.message.reply_text(f"✅ Фото опубликовано в {CHANNEL_ID}!", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {e}")
        return

    # Иначе — обычная обработка фото от клиента
    await handle_photo(update, context)


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Меню команд для владельца."""
    if not is_owner(update.effective_user):
        return
    await update.message.reply_text(
        "🎛 *Команды ALTA CASA Bot*\n\n"
        "*👥 Клиенты:*\n"
        "`/start` — начать диалог\n"
        "`/reset` — сбросить историю диалога\n\n"
        "*📚 Обучение Юли:*\n"
        "`/teach <текст>` — добавить знание\n"
        "`/knowledge` — показать базу знаний\n\n"
        "*📢 Канал:*\n"
        "`/post <текст>` — опубликовать текст\n"
        "`/post_photo` — прикрепи фото с этой подписью\n"
        "`/ai_post <тема>` — Claude напишет пост\n"
        "`/confirm` — опубликовать ai_post\n"
        "`/channel` — показать канал\n\n"
        "*ℹ️ Справка:*\n"
        "`/menu` — это меню",
        parse_mode="Markdown"
    )


# ── Запуск ────────────────────────────────────────────────────────────────────

def main():
    app = ApplicationBuilder().token(TG_TOKEN).build()

    # Клиентские команды
    app.add_handler(CommandHandler("start",     cmd_start))
    app.add_handler(CommandHandler("reset",     cmd_reset))

    # Команды владельца — обучение
    app.add_handler(CommandHandler("teach",     cmd_teach))
    app.add_handler(CommandHandler("knowledge", cmd_knowledge))

    # Команды владельца — канал
    app.add_handler(CommandHandler("post",      cmd_post))
    app.add_handler(CommandHandler("ai_post",   cmd_ai_post))
    app.add_handler(CommandHandler("confirm",   cmd_confirm))
    app.add_handler(CommandHandler("channel",   cmd_channel))
    app.add_handler(CommandHandler("menu",      cmd_menu))

    # Медиа (фото сначала — чтобы /post_photo перехватить)
    app.add_handler(MessageHandler(filters.PHOTO, handle_owner_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Текст — последним
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 ALTA CASA Bot запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
