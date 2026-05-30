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

KNOWLEDGE_PAGE_ID = os.getenv("NOTION_KNOWLEDGE_PAGE_ID", "")
_knowledge_cache: str = ""
_knowledge_loaded: bool = False

def load_knowledge() -> str:
    global _knowledge_cache, _knowledge_loaded
    if _knowledge_loaded:
        return _knowledge_cache
    try:
        if KNOWLEDGE_PAGE_ID:
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
                _knowledge_cache = f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ\n═══════════════════════════════\n{content}"
        _knowledge_loaded = True
    except Exception as e:
        logger.error(f"Knowledge load error: {e}")
    return _knowledge_cache

# LEGACY FALLBACK - не используется если есть Notion
def load_knowledge_file() -> str:
    if os.path.exists("custom_knowledge.txt"):
        with open("custom_knowledge.txt", "r", encoding="utf-8") as f:
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

PRODUCTS = {
    "mc_a68":     {"name":"Диван MC-A68","desc":"Итальянская кожа oil-wax, гусиный пух, лиственница. 3-местный 230×97×92 см.","price":"от 235 224 ₽","срок":"6–8 недель","moq":"1 шт"},
    "fort":       {"name":"Диван FORT","desc":"Орех/ясень + велюр, высокоплотный поролон. 2–4 местный.","price":"от 99 634 ₽","срок":"6–8 недель","moq":"1 шт"},
    "pr701":      {"name":"Диван PR701 «Облако»","desc":"Модульный. Хлопок-лён, гусиный пух. 3–4 места + пуф.","price":"от 219 109 ₽","срок":"6–8 недель","moq":"1 шт"},
    "mk_sofa01":  {"name":"Диван MK-SOFA01","desc":"Анилиновая/замшевая кожа, орех. 2–3 места.","price":"от 272 833 ₽","срок":"6–8 недель","moq":"1 шт"},
    "qmw2023":    {"name":"Диван QMW-2023","desc":"Итальянская кожа, нерж. сталь. 1–4 места.","price":"от 59 895 ₽","срок":"6–8 недель","moq":"1 шт"},
    "lanyue":     {"name":"Кресло Ланьюэ ZX-LY3","desc":"Орех, хлопок-лён. 64×102×74 см.","price":"118 921 ₽","срок":"4–6 недель","moq":"1 шт"},
    "mercer":     {"name":"Кресло MERCER","desc":"Орех/ясень, хлопок-лён. 70×96×95 см.","price":"от 127 490 ₽","срок":"4–6 недель","moq":"1 шт"},
    "florence":   {"name":"Кресло Lounge Florence","desc":"Кожа full-grain, орех. Mid-century modern.","price":"от 47 500 ₽","срок":"4–6 недель","moq":"2 шт"},
    "roma":       {"name":"Кровать Roma Platform","desc":"Массив дуба, мягкое изголовье, подъёмный механизм. 160/180/200.","price":"от 62 000 ₽","срок":"5–7 недель","moq":"1 шт"},
    "cj106":      {"name":"Столик MK-CJ106","desc":"Массив ореха. 135×75×36 см.","price":"98 593 ₽","срок":"4–6 недель","moq":"1 шт"},
    "palazzo":    {"name":"Стол Palazzo","desc":"Мрамор Calacatta, нерж. сталь. Ø120/140/160 см.","price":"от 118 000 ₽","срок":"7–10 недель","moq":"2 шт"},
    "executive":  {"name":"Стол переговорный Executive","desc":"Шпон ореха, 3.6–6 м, кабель-каналы.","price":"от 210 000 ₽","срок":"6–8 недель","moq":"1 шт"},
    "grand_hotel":{"name":"Ресепшн-стойка Grand Hotel","desc":"Травертин/мрамор + кварц. Под размер лобби.","price":"от 157 200 ₽","срок":"8–12 недель","moq":"кастом"},
    "chateau":    {"name":"Банкетный стул Chateau","desc":"Бук + ткань/кожа. Штабелируемый. MOQ 50 шт.","price":"от 4 200 ₽/шт","срок":"4–6 недель","moq":"50 шт"},
    "milano":     {"name":"Тумба Milano","desc":"МДФ 18 цветов, латунь. MOQ 4 шт.","price":"от 18 400 ₽","срок":"4–6 недель","moq":"4 шт"},
}

def get_product_context(product_key: str) -> str:
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


def ask_claude(chat_id: int, user_message: str, extra_system: str = "") -> dict:
    history = dialogs.get(chat_id, [])
    history.append({"role": "user", "content": user_message})

    response = ai.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=get_system_prompt() + extra_system,
        messages=history[-MAX_HISTORY:]
    )

    raw = response.content[0].text
    history.append({"role": "assistant", "content": raw})
    dialogs[chat_id] = history[-MAX_HISTORY:]

    result = {"reply": raw, "qualification": None, "interest": None,
              "budget": None, "escalate": False}

    if "```json" in raw:
        try:
            # Текст ДО json-блока — это и есть ответ клиенту
            text_before_json = raw.split("```json")[0].strip()
            json_part = raw.split("```json")[1].split("```")[0].strip()
            meta = json.loads(json_part)
            # Берём reply из JSON, но если он короткий (описание) — берём текст до JSON
            json_reply = meta.get("reply", "")
            if json_reply and len(json_reply) > 30:
                result["reply"] = json_reply
            elif text_before_json and len(text_before_json) > 10:
                result["reply"] = text_before_json
            else:
                result["reply"] = raw.split("```json")[0].strip() or raw
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
    """Клиент нажал 'Запустить бота' — возможно с параметром товара."""
    chat_id = event.chat_id
    dialogs[chat_id] = []

    # Читаем payload (product key) из deep link
    product_key = getattr(event, "payload", None) or getattr(event, "start_param", None)
    product_ctx = get_product_context(product_key) if product_key else ""

    try:
        get_or_create_client(chat_id, str(chat_id), "")
    except Exception as e:
        logger.error(f"Notion start error: {e}")

    if product_ctx:
        result = ask_claude(
            chat_id,
            "[СИСТЕМА: клиент перешёл с карточки товара. Поприветствуй и задай первый вопрос.]",
            extra_system=product_ctx
        )
        await event.bot.send_message(chat_id=chat_id, text=result["reply"])
    else:
        await event.bot.send_message(
            chat_id=chat_id,
            text=(
                "Здравствуйте! Меня зовут Юля.\n\n"
                "Я помогу вам подобрать качественную мебель из Китая, "
                "рассчитать стоимость и подобрать оптимальный вариант доставки.\n\n"
                "Подскажите, какую мебель вы рассматриваете: "
                "для дома, офиса, ресторана, отеля или другого проекта?"
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
