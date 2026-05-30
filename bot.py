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

# ── База знаний (хранится в Notion) ──────────────────────────────────────────
KNOWLEDGE_PAGE_ID = os.getenv("NOTION_KNOWLEDGE_PAGE_ID", "")
_knowledge_cache: str = ""
_knowledge_loaded: bool = False

def load_knowledge() -> str:
    """Загрузить базу знаний из Notion (кешируем на сессию)."""
    global _knowledge_cache, _knowledge_loaded
    if _knowledge_loaded:
        return _knowledge_cache
    try:
        if KNOWLEDGE_PAGE_ID:
            page = notion.pages.retrieve(page_id=KNOWLEDGE_PAGE_ID)
            blocks = notion.blocks.children.list(block_id=KNOWLEDGE_PAGE_ID)
            lines = []
            for block in blocks.get("results", []):
                bt = block.get("type")
                if bt == "paragraph":
                    texts = block["paragraph"].get("rich_text", [])
                    line = "".join(t["plain_text"] for t in texts)
                    if line.strip():
                        lines.append(line)
            content = "\n".join(lines).strip()
            if content:
                _knowledge_cache = f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ (добавлены владельцем)\n═══════════════════════════════\n{content}"
            else:
                _knowledge_cache = ""
        _knowledge_loaded = True
    except Exception as e:
        logger.error(f"Knowledge load error: {e}")
    return _knowledge_cache

def save_knowledge(entry: str):
    """Сохранить знание в Notion и обновить кеш."""
    global _knowledge_cache, _knowledge_loaded
    try:
        if KNOWLEDGE_PAGE_ID:
            notion.blocks.children.append(
                block_id=KNOWLEDGE_PAGE_ID,
                children=[{
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": entry}}]
                    }
                }]
            )
            # Сбрасываем кеш чтобы перечитать
            _knowledge_loaded = False
        else:
            # Fallback — файл (если нет Notion страницы)
            with open("custom_knowledge.txt", "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
            _knowledge_loaded = False
    except Exception as e:
        logger.error(f"Knowledge save error: {e}")

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
        page = results["results"][0]
        page_id = page["id"]
        # Загружаем историю диалога из Notion в память
        try:
            history_raw = page["properties"].get("История JSON", {}).get("rich_text", [])
            if history_raw:
                history_json = history_raw[0]["plain_text"]
                loaded = json.loads(history_json)
                if loaded and tg_id not in dialogs:
                    dialogs[tg_id] = loaded
                    logger.info(f"История загружена для {tg_id}: {len(loaded)} сообщений")
        except Exception as e:
            logger.error(f"History load error: {e}")
        return page_id

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


def update_client(page_id: str, dialog_text: str, history: list = None,
                  qualification: str = None, interest: str = None,
                  budget: float = None, escalate: bool = False):
    # Сохраняем последние 20 сообщений как JSON (только текстовые)
    history_json = ""
    if history:
        text_only = [m for m in history if isinstance(m.get("content"), str)][-20:]
        history_json = json.dumps(text_only, ensure_ascii=False)

    props = {
        "Диалог с ботом": {"rich_text": [{"text": {"content": dialog_text[-2000:]}}]},
    }
    if history_json:
        props["История JSON"] = {"rich_text": [{"text": {"content": history_json[:2000]}}]}
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

def ask_claude(chat_id: int, user_message: str, image_data: dict = None, extra_system: str = "") -> dict:
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
        system=get_system_prompt() + extra_system,
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


# ── Каталог товаров (для deep links с сайта) ─────────────────────────────────
PRODUCTS = {
    # Диваны
    "mc_a68": {
        "name": "Диван MC-A68",
        "desc": "Итальянская натуральная кожа oil-wax, гусиный пух, лиственница. 3-местный 230×97×92 см.",
        "price": "от 235 224 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    "fort": {
        "name": "Диван FORT",
        "desc": "Орех/ясень + велюр, высокоплотный поролон. 2–4 местный.",
        "price": "от 99 634 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    "pr701": {
        "name": "Диван PR701 «Облако»",
        "desc": "Модульный. Хлопок-лён, гусиный пух, лиственница. 3–4 места + пуф.",
        "price": "от 219 109 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    "mk_sofa01": {
        "name": "Диван MK-SOFA01",
        "desc": "Анилиновая/замшевая кожа, орех, лиственница. 2–3 места.",
        "price": "от 272 833 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    "qmw2023": {
        "name": "Диван QMW-2023",
        "desc": "Итальянская натуральная кожа, нержавеющая сталь. 1–4 места.",
        "price": "от 59 895 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    # Кресла
    "lanyue": {
        "name": "Кресло «Ланьюэ» ZX-LY3",
        "desc": "Сев.-американский орех, хлопок-лён, поролон + холлофайбер. 64×102×74 см.",
        "price": "118 921 ₽",
        "срок": "4–6 недель",
        "moq": "1 шт",
    },
    "mercer": {
        "name": "Кресло MERCER",
        "desc": "Орех/ясень, премиальный хлопок-лён, высокоплотный поролон. 70×96×95 см.",
        "price": "от 127 490 ₽",
        "срок": "4–6 недель",
        "moq": "1 шт",
    },
    "florence": {
        "name": "Кресло Lounge Florence",
        "desc": "Кожа full-grain, каркас из орехового дерева. Стиль mid-century modern.",
        "price": "от 47 500 ₽",
        "срок": "4–6 недель",
        "moq": "2 шт",
    },
    # Кровати
    "roma": {
        "name": "Кровать Roma Platform",
        "desc": "Массив дуба, мягкое изголовье, подъёмный механизм. Размеры 160/180/200.",
        "price": "от 62 000 ₽",
        "срок": "5–7 недель",
        "moq": "1 шт",
    },
    # Столики
    "cj106": {
        "name": "Журнальный столик MK-CJ106",
        "desc": "Массив сев.-американского ореха. 135×75×36 см.",
        "price": "98 593 ₽",
        "срок": "4–6 недель",
        "moq": "1 шт",
    },
    "palazzo": {
        "name": "Обеденный стол Palazzo",
        "desc": "Столешница из итальянского мрамора Calacatta, нержавеющая сталь. Ø120/140/160 см.",
        "price": "от 118 000 ₽",
        "срок": "7–10 недель",
        "moq": "2 шт",
    },
    # Офис
    "executive": {
        "name": "Стол переговорный Executive",
        "desc": "Шпон американского ореха, хром. 3.6–6.0 м. Встроенные кабель-каналы.",
        "price": "от 210 000 ₽",
        "срок": "6–8 недель",
        "moq": "1 шт",
    },
    "cabinet_pro": {
        "name": "Гардеробная система Cabinet Pro",
        "desc": "Матовый лак + натуральный шпон, алюминиевые профили. Под размер помещения.",
        "price": "от 94 000 ₽",
        "срок": "6–8 недель",
        "moq": "кастом",
    },
    # Отель
    "grand_hotel": {
        "name": "Ресепшн-стойка Grand Hotel",
        "desc": "Натуральный травертин/мрамор + кварц. Подсветка в базе. Полностью под размер лобби.",
        "price": "от 157 200 ₽",
        "срок": "8–12 недель",
        "moq": "кастом",
    },
    "chateau": {
        "name": "Банкетный стул Chateau",
        "desc": "Бук + ткань/кожа. Штабелируемый. 50+ расцветок. Сертификат EN 16139.",
        "price": "от 4 200 ₽/шт",
        "срок": "4–6 недель",
        "moq": "50 шт",
    },
    "milano": {
        "name": "Прикроватная тумба Milano",
        "desc": "Лакированный МДФ 18 цветов, латунь матовая/глянец. Выдвижной ящик на доводчике.",
        "price": "от 18 400 ₽",
        "срок": "4–6 недель",
        "moq": "4 шт",
    },
}

def get_product_context(product_key: str) -> str:
    """Вернуть текст с описанием товара для системного промпта."""
    p = PRODUCTS.get(product_key.lower().replace("-", "_").replace(" ", "_"))
    if not p:
        return ""
    return (
        f"\n\n═══════════════════════════════\n"
        f"КЛИЕНТ ПРИШЁЛ С КАРТОЧКИ ТОВАРА\n"
        f"═══════════════════════════════\n"
        f"Товар: {p['name']}\n"
        f"Описание: {p['desc']}\n"
        f"Цена: {p['price']}\n"
        f"Срок производства: {p['срок']}\n"
        f"Минимальный заказ: {p['moq']}\n\n"
        f"Начни с приветствия и сразу упомяни этот товар по имени. "
        f"Спроси что именно клиент хочет уточнить."
    )


# ── Telegram handlers ─────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    dialogs[user.id] = []

    # Читаем параметр deep link (product key)
    product_key = context.args[0] if context.args else None
    product_ctx = get_product_context(product_key) if product_key else ""

    try:
        page_id = get_or_create_client(user.id, user.full_name or "Клиент", user.username or "")
        label = f"[START:{product_key}]" if product_key else "[START]"
        update_client(page_id, f"{label} {datetime.now():%Y-%m-%d %H:%M}")
    except Exception as e:
        logger.error(f"Notion /start error: {e}")

    if product_ctx:
        # Есть контекст товара — просим Claude написать персонализированное приветствие
        result = ask_claude(
            user.id,
            f"[СИСТЕМА: клиент перешёл с карточки товара. Поприветствуй и задай первый вопрос.]{product_ctx}",
            extra_system=product_ctx
        )
        await update.message.reply_text(result["reply"])
    else:
        await update.message.reply_text(
            "Здравствуйте! Меня зовут Юля.\n\n"
            "Я помогу вам подобрать качественную мебель из Китая, "
            "рассчитать стоимость и подобрать оптимальный вариант доставки.\n\n"
            "Подскажите, пожалуйста, какую мебель вы рассматриваете: "
            "для дома, офиса, ресторана, отеля или другого проекта?"
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


def detect_owner_intent(text: str) -> str | None:
    """Определить намерение владельца из свободного текста. Вернуть тип или None."""
    t = text.lower().strip()

    # Намерение: написать и опубликовать пост
    post_triggers = [
        "напиши пост", "сделай пост", "опубликуй пост", "запости", "пост про",
        "пост о ", "напиши о ", "напиши про ", "сделай анонс", "напиши анонс",
        "сделай объявление", "опубликуй:", "опубликуй текст", "написать пост",
        "создай пост", "новый пост"
    ]
    if any(t.startswith(tr) or tr in t for tr in post_triggers):
        return "post"

    # Намерение: опубликовать готовый текст напрямую
    direct_triggers = ["опубликуй: ", "в канал: ", "пост: "]
    if any(t.startswith(tr) for tr in direct_triggers):
        return "direct_post"

    # Намерение: обучить бота
    teach_triggers = [
        "запомни:", "запомни,", "запомни что", "добавь в базу", "обучи",
        "юля должна знать", "юля отвечает", "если спросят про",
        "ответ на вопрос", "фaq:", "вопрос:", "скажи клиентам"
    ]
    if any(t.startswith(tr) or tr in t for tr in teach_triggers):
        return "teach"

    return None


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    name = user.full_name or "Клиент"

    logger.info(f"[{user.id}] {name}: {text}")

    # ── Владелец: распознаём намерение без команд ──────────────────────────────
    if is_owner(user):
        intent = detect_owner_intent(text)

        if intent == "post":
            # Генерируем пост через AI и публикуем
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            prompt = f"""Напиши продающий пост для Telegram-канала ALTA CASA.
Тема: {text}
Требования: 3-4 абзаца, живой стиль, цены если знаешь, в конце призыв писать @altacasacn_bot.
2-3 emoji уместно. Форматирование Markdown. Без хэштегов.
Верни ТОЛЬКО текст поста."""
            response = ai.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )
            post_text = response.content[0].text.strip()
            context.user_data["pending_post"] = post_text
            await update.message.reply_text(
                f"📝 Превью поста:\n\n{post_text}\n\n"
                f"Напиши 'публикуй' или /confirm чтобы опубликовать в канал."
            )
            return

        if intent == "direct_post":
            # Публикуем текст напрямую
            for prefix in ["опубликуй: ", "в канал: ", "пост: "]:
                if text.lower().startswith(prefix):
                    post_text = text[len(prefix):]
                    break
            else:
                post_text = text
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                await update.message.reply_text("✅ Опубликовано в канале!")
            except Exception as e:
                await update.message.reply_text(f"❌ Ошибка: {e}")
            return

        if intent == "teach":
            entry = f"[{datetime.now():%d.%m.%Y}] {text}"
            save_knowledge(entry)
            await update.message.reply_text(f"✅ Запомнила:\n\n{text[:200]}")
            return

        # Владелец написал "публикуй" — подтверждение pending поста
        if text.lower().strip() in ["публикуй", "подтверди", "ок публикуй", "да публикуй", "публикуй!"]:
            post_text = context.user_data.get("pending_post")
            if post_text:
                try:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("✅ Пост опубликован в канале!")
                except Exception:
                    await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
                    context.user_data.pop("pending_post", None)
                    await update.message.reply_text("✅ Пост опубликован!")
            else:
                await update.message.reply_text("Нет поста для публикации. Сначала попроси написать пост.")
            return

    # ── Обычный клиент ─────────────────────────────────────────────────────────
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
            # Собираем историю диалога для контекста
            history = dialogs.get(user.id, [])
            dialog_summary = "\n".join(
                f"{'👤' if m['role'] == 'user' else '🤖'} {m['content'][:150] if isinstance(m['content'], str) else '[медиа]'}"
                for m in history[-6:]
            )
            interest = result.get("interest") or "не указан"
            budget = f"{int(result['budget']):,} ₽".replace(",", " ") if result.get("budget") else "не указан"
            qualification = result.get("qualification") or "Горячий"

            msg = (
                f"🔥 Горячий лид!\n\n"
                f"👤 Клиент: {user.full_name}\n"
                f"📱 TG: @{user.username or 'нет'} | ID: {user.id}\n"
                f"🛋 Интерес: {interest}\n"
                f"💰 Бюджет: {budget}\n"
                f"📊 Статус: {qualification}\n\n"
                f"💬 Диалог:\n{dialog_summary}"
            )
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=msg
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
                          history=history,
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

    # Сначала показываем превью владельцу (без parse_mode чтобы не сломать)
    await update.message.reply_text(
        f"📝 Превью поста:\n\n{post_text}\n\n"
        f"Отправь /confirm чтобы опубликовать, или /post <текст> чтобы изменить"
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


# ── Авто-посты в канал ────────────────────────────────────────────────────────

# Темы для авто-постов — ротация
AUTO_POST_TOPICS = [
    # ── Товары ──────────────────────────────────────────────────────────────────
    "диван MC-A68 — итальянская кожа oil-wax, 3-местный, от 235 000 ₽. Почему кожа oil-wax лучше обычной кожи",
    "диван FORT — орех и велюр, классика для гостиной, от 99 634 ₽. Почему натуральное дерево в каркасе важно",
    "кресло Ланьюэ — северо-американский орех, хлопок-лён, 118 921 ₽. Идеальное кресло для домашнего офиса",
    "кровать Roma Platform — массив дуба, подъёмный механизм, от 62 000 ₽. Как выбрать кровать из Китая",
    "обеденный стол Palazzo — мрамор Calacatta и нержавеющая сталь, от 118 000 ₽. Мрамор в интерьере столовой",
    "диван PR701 Облако — модульный, гусиный пух, хлопок-лён, от 219 000 ₽. Почему гусиный пух лучше поролона",
    "гардеробная Cabinet Pro — матовый лак и шпон, под размер помещения, от 94 000 ₽. Гардеробная из Китая под ключ",
    "ресепшн-стойка Grand Hotel — травертин/мрамор, подсветка, от 157 000 ₽. Мебель для отелей из Китая",
    "кресло MERCER — орех/ясень, хлопок-лён, от 127 000 ₽. Как сочетать кресла с диваном",
    "диван MK-SOFA01 — анилиновая кожа, орех, от 273 000 ₽. Что такое анилиновая кожа и зачем она нужна",
    "банкетный стул Chateau — бук, ткань/кожа, от 4 200 ₽/шт. Почему рестораны выбирают мебель из Китая",

    # ── Образовательный контент ──────────────────────────────────────────────────
    "Как отличить качественную кожу от дешёвой — 5 признаков которые можно проверить прямо в магазине",
    "Почему массив дерева лучше МДФ — разбираем состав каркаса дивана и почему это важно",
    "На что смотреть при выборе дивана — материал, каркас, наполнитель, размер. Полный гайд",
    "Гусиный пух vs поролон vs холлофайбер — из чего лучше делать подушки дивана",
    "Итальянские ткани в китайской мебели — как это работает и почему это не маркетинг",
    "Как выбрать обеденный стол для семьи — размер, материал, форма. Разбираем ошибки",
    "Мрамор в интерьере — натуральный vs искусственный. Как не переплатить и не ошибиться",
    "Сколько служит диван из Китая — честный разговор о сроках и качестве",

    # ── За кулисами ──────────────────────────────────────────────────────────────
    "Как мы проверяем фабрики перед заключением контракта — наш процесс отбора поставщиков",
    "Что происходит на фабрике за 6 недель до доставки — производство мебели изнутри",
    "Как выглядит контроль качества на китайской фабрике — видео-контроль, фото перед упаковкой",
    "Фошань vs Гуанчжоу — в чём разница и откуда мы заказываем разные категории мебели",
    "Как мы работаем с 340 фабриками — система отбора, рейтинги, эксклюзивные контракты",

    # ── Кейсы и проекты ──────────────────────────────────────────────────────────
    "Комплектовали ресторан — 40 банкетных стульев и 10 столов из Фошаня за 5 недель. История проекта",
    "Гостиная под ключ с бюджетом 300 000 ₽ — что входит и как это выглядит",
    "Отель на 30 номеров — как мы комплектовали мебель от кроватей до ресепшна",
    "Офис для IT-компании — переговорный стол Executive 5 метров и рабочие зоны из Китая",

    # ── Лайфстайл и интерьер ─────────────────────────────────────────────────────
    "Как обустроить домашний офис с бюджетом 150 000 ₽ — стол, кресло, стеллажи из Китая",
    "Japandi стиль в интерьере — орех, лён, минимализм. Какую мебель выбрать",
    "Гостиная в стиле mid-century modern — диваны и кресла которые создают атмосферу",
    "Модульный диван vs обычный — что лучше для большой гостиной",
    "Спальня мечты с бюджетом 200 000 ₽ — кровать, тумбочки, гардеробная из Китая",

    # ── Доставка и логистика ─────────────────────────────────────────────────────
    "Как работает белая таможня — почему это важно и как мы это делаем",
    "Сколько идёт мебель из Китая — реальные сроки доставки по странам",
    "Как упакована мебель из Китая — что защищает её в пути на 8 000 км",
    "Доставка в Казахстан, Киргизию, ОАЭ — как мы работаем с разными странами",

    # ── Сравнения ────────────────────────────────────────────────────────────────
    "Итальянская мебель vs Китай — в чём реальная разница при одинаковой цене",
    "Мебель из Китая vs российские магазины — сравниваем цены на одинаковые позиции",
    "Фабричная цена EXW vs розница в России — почему разница в 2-3 раза это норма",

    # ── Работа с нами ────────────────────────────────────────────────────────────
    "340+ фабрик Фошаня и Гуанчжоу — как мы выбираем поставщиков и контролируем качество",
    "Как сделать заказ в ALTA CASA — от запроса до доставки. Пошаговый процесс",
    "Комплектация объектов — отели, рестораны, офисы, апартаменты. Как мы работаем",
    "Оплата в рублях, долларах, крипте — как мы работаем с разными схемами оплаты",
]

_last_topic_index = -1


async def auto_post_to_channel(bot):
    """Авто-пост в канал — запускается по расписанию."""
    global _last_topic_index
    try:
        # Выбираем тему — по очереди, не повторяем
        _last_topic_index = (_last_topic_index + 1) % len(AUTO_POST_TOPICS)
        topic = AUTO_POST_TOPICS[_last_topic_index]

        logger.info(f"Авто-пост: {topic[:50]}...")

        prompt = f"""Напиши продающий пост для Telegram-канала ALTA CASA.

Тема: {topic}

Требования:
— 3-4 абзаца, живой стиль без канцелярщины
— Упомяни конкретные материалы и преимущества
— Ценовой ориентир если есть
— В конце: "Подробнее и расчёт доставки — @altacasacn_bot"
— 2-3 emoji уместно
— Форматирование Markdown (жирный, курсив)
— Без хэштегов

Верни ТОЛЬКО текст поста."""

        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}]
        )
        post_text = response.content[0].text.strip()

        # Публикуем в канал
        await bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown")
        logger.info("✅ Авто-пост опубликован")

    except Exception as e:
        # Если Markdown сломан — пробуем без форматирования
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            logger.info("✅ Авто-пост опубликован (без Markdown)")
        except Exception as e2:
            logger.error(f"Авто-пост ошибка: {e2}")


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

    # Планировщик авто-постов: пн/ср/пт в 10:00 по Москве (UTC+3 = 07:00 UTC)
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        auto_post_to_channel,
        CronTrigger(day_of_week="mon,wed,fri", hour=7, minute=0),
        args=[app.bot],
        id="auto_post"
    )
    scheduler.start()
    logger.info("📅 Авто-посты запланированы: пн/ср/пт в 10:00 МСК")

    logger.info("🤖 ALTA CASA Bot запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
