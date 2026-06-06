"""
KOKAHOUSE — MAX Messenger Bot
Юля AI-менеджер в мессенджере MAX.
"""

import asyncio
import logging
import json
import os
import urllib.request
import urllib.parse
import base64
from dotenv import load_dotenv

from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

import anthropic

load_dotenv()

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_TOKEN      = os.getenv("MAX_TOKEN")
ANTHROPIC_KEY  = os.getenv("ANTHROPIC_API_KEY")
MANAGER_MAX_ID = os.getenv("MANAGER_CHAT_ID")
AMO_TOKEN      = os.getenv("AMO_LONG_TOKEN", "")
AMO_DOMAIN     = "yaninve7.amocrm.ru"
OWNER_ID       = "8828678082"

ai  = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
bot = Bot(MAX_TOKEN)
dp  = Dispatcher()

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    _full = f.read()
    if "ФОРМАТ ОТВЕТА" in _full:
        BASE_PROMPT = _full.split("═══════════════════════════════\nФОРМАТ ОТВЕТА")[0].strip()
    else:
        BASE_PROMPT = _full
BASE_PROMPT += "\n\nВАЖНО: Отвечай ТОЛЬКО обычным текстом. Никаких JSON-блоков. Пиши как живой менеджер."

def load_knowledge() -> str:
    if os.path.exists("custom_knowledge.txt"):
        with open("custom_knowledge.txt", "r", encoding="utf-8") as f:
            c = f.read().strip()
        if c:
            return f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ\n═══════════════════════════════\n{c}"
    return ""

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()

dialogs: dict[int, list[dict]] = {}
MAX_HISTORY = 20
_amo_cache: dict[int, int] = {}

def amo_request(method, path, data=None):
    if not AMO_TOKEN:
        return {}
    headers = {"Authorization": f"Bearer {AMO_TOKEN}", "Content-Type": "application/json"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(f"https://{AMO_DOMAIN}/api/v4/{path}", data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else {"status": "ok"}
    except Exception as e:
        logger.error(f"amoCRM {method} {path}: {e}")
        return {}

def amo_get_or_create_contact(user_id, name):
    if user_id in _amo_cache:
        return _amo_cache[user_id]
    params = urllib.parse.urlencode({"query": name, "limit": 5})
    r = amo_request("GET", f"contacts?{params}")
    for c in r.get("_embedded", {}).get("contacts", []):
        if c.get("name") == name:
            _amo_cache[user_id] = c["id"]
            return c["id"]
    r = amo_request("POST", "contacts", [{"name": name}])
    contacts = r.get("_embedded", {}).get("contacts", [])
    if not contacts:
        return 0
    cid = contacts[0]["id"]
    amo_request("POST", "contacts/notes", [{"entity_id": cid, "note_type": "common", "params": {"text": f"MAX ID: {user_id}"}}])
    _amo_cache[user_id] = cid
    logger.info(f"amoCRM MAX: контакт {name} id={cid}")
    return cid

def sync_to_amo(user_id, name, message_text, bot_reply, qualification=None, interest=None, budget=None):
    if not AMO_TOKEN:
        return
    try:
        cid = amo_get_or_create_contact(user_id, name)
        if not cid:
            return
        note = f"👤 {name}: {message_text}\n🤖 Юля: {bot_reply[:300]}"
        if interest:
            note += f"\n🛋 Интерес: {interest}"
        if budget:
            note += f"\n💰 Бюджет: {budget:,} р.".replace(",", " ")
        if qualification:
            note += f"\n🏷 Статус: {qualification}"
        amo_request("POST", "contacts/notes", [{"entity_id": cid, "note_type": "common", "params": {"text": note}}])
        logger.info(f"amoCRM MAX sync: user={user_id} contact={cid}")
    except Exception as e:
        logger.error(f"amoCRM MAX sync error: {e}")

def is_owner(user_id):
    return str(user_id) == OWNER_ID

async def download_image(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.read()
    except Exception as e:
        logger.error(f"Image download error: {e}")
        return None

def detect_media_type(b: bytes) -> str:
    """Определить реальный MIME-тип картинки по сигнатуре байтов."""
    if not b:
        return "image/jpeg"
    if b[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "image/webp"
    if b[:4] in (b"GIF8",):
        return "image/gif"
    return "image/jpeg"

def ask_claude(chat_id, user_message, image_data=None):
    history = dialogs.get(chat_id, [])
    if image_data:
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": detect_media_type(image_data),
             "data": base64.standard_b64encode(image_data).decode()}},
            {"type": "text", "text": user_message or "Клиент прислал фото товара. Ответь согласно правилам работы с фото."}
        ]
        history.append({"role": "user", "content": content})
    else:
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

    result = {"reply": raw, "qualification": None, "interest": None, "budget": None, "escalate": False}
    if "```json" in raw:
        try:
            text_before = raw.split("```json")[0].strip()
            meta = json.loads(raw.split("```json")[1].split("```")[0].strip())
            json_reply = meta.get("reply", "")
            result["reply"] = json_reply if len(json_reply) > 30 else (text_before if len(text_before) > 10 else raw)
            result["qualification"] = meta.get("qualification")
            result["interest"]      = meta.get("interest")
            result["budget"]        = meta.get("budget")
            result["escalate"]      = meta.get("escalate", False)
        except Exception:
            pass
    return result

def analyze_product_photo(image_bytes, caption=""):
    """Vision-анализ фото товара ДЛЯ ВНУТРЕННЕЙ КОМАНДЫ — что искать у поставщиков."""
    if not image_bytes:
        return ""
    try:
        sys = (
            "Ты эксперт по мебели и предметам интерьера из Китая. "
            "На фото — товар, который клиент хочет найти или купить. "
            "Опиши его КРАТКО для внутренней команды закупки KOKAHOUSE, чтобы они нашли "
            "аналог у китайских поставщиков (1688, Taobao, Alibaba). Формат:\n"
            "• Тип: (диван / стул / стол / кровать / светильник / декор / ...)\n"
            "• Стиль: (модерн / лофт / классика / минимализм / ...)\n"
            "• Материал и цвет:\n"
            "• Особенности: (форма, ножки, обивка, фурнитура, заметные детали)\n"
            "• Ключевые слова для поиска (рус + англ или кит): 3–5 шт\n"
            "Только то, что реально видно на фото. Не выдумывай размеры и бренд. Без вступлений и воды."
        )
        content = [
            {"type": "image", "source": {"type": "base64", "media_type": detect_media_type(image_bytes),
             "data": base64.standard_b64encode(image_bytes).decode()}},
            {"type": "text", "text": (f"Подпись клиента: {caption}\n" if caption else "") + "Опиши товар для поиска."},
        ]
        resp = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=sys,
            messages=[{"role": "user", "content": content}],
        )
        return resp.content[0].text.strip()
    except Exception as e:
        logger.error(f"Photo analysis error: {e}")
        return ""

@dp.bot_started()
async def on_start(event: BotStarted):
    dialogs[event.chat_id] = []
    await event.bot.send_message(
        chat_id=event.chat_id,
        text="Здравствуйте! 👋 Я Юля, персональный менеджер KOKAHOUSE.\n\nПомогу подобрать мебель и товары для интерьера из Китая.\n\nЧто вас интересует?"
    )

@dp.message_created(Command("start"))
async def on_cmd_start(event: MessageCreated):
    dialogs[event.message.recipient.chat_id] = []
    await event.message.answer("Добро пожаловать в KOKAHOUSE! 🏠\n\nЧто вас интересует?")

@dp.message_created()
async def on_message(event: MessageCreated):
    msg     = event.message
    chat_id = msg.recipient.chat_id
    text    = (msg.body.text if msg.body else "") or ""
    user    = msg.sender
    user_id = user.user_id
    name    = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Клиент"

    # DEBUG: дамп структуры сообщения
    try:
        body_attrs = {k: str(getattr(msg.body, k, None))[:100] for k in dir(msg.body) if not k.startswith('_')} if msg.body else {}
        msg_attrs = {k: str(getattr(msg, k, None))[:100] for k in ['attachments', 'link', 'body'] if hasattr(msg, k)}
        logger.info(f"[MAX DEBUG] msg attrs: {msg_attrs}")
        logger.info(f"[MAX DEBUG] body attrs: {body_attrs}")
    except Exception as de:
        logger.info(f"[MAX DEBUG] error: {de}")

    # Фото
    image_data = None
    photo_url = None
    attachments = getattr(msg, "attachments", []) or []
    # Также проверяем body.attachments
    if not attachments and msg.body:
        attachments = getattr(msg.body, "attachments", []) or []
    if attachments:
        logger.info(f"[MAX] attachments count={len(attachments)}")
    for att in attachments:
        att_type = str(getattr(att, "type", "") or "")
        logger.info(f"[MAX] att={att!r} type={att_type}")
        # Image(type='i') — тип может быть 'image', 'i', или объект enum
        is_image = (
            "image" in att_type.lower() or
            att_type == "i" or
            type(att).__name__ == "Image" or
            hasattr(att, "url") or
            hasattr(att, "payload")
        )
        if is_image:
            # Пробуем разные места для URL
            photo_url = (
                getattr(att, "url", None) or
                getattr(att, "photo_url", None) or
                getattr(getattr(att, "payload", None), "url", None) or
                getattr(getattr(att, "payload", None), "photo_url", None) or
                getattr(getattr(att, "payload", None), "thumbnail_url", None)
            )
            logger.info(f"[MAX] photo_url={photo_url}")
            if photo_url:
                image_data = await download_image(photo_url)
                if not text:
                    text = "[ФОТО]"
                break

    if not text and not image_data:
        return

    logger.info(f"[MAX][{user_id}] {name}: {text[:100]}")

    if is_owner(user_id):
        await event.message.answer("✅ Получено")
        return

    # Всё, что ниже — в защите: ошибка с одним сообщением (например фото)
    # НЕ должна ронять polling и заставлять Юлю замолчать.
    try:
        result = ask_claude(chat_id, text, image_data=image_data)
    except Exception as e:
        logger.error(f"[MAX] ask_claude error: {e}", exc_info=True)
        result = {"reply": "Спасибо, получила! Уточните, пожалуйста, что именно вас интересует — подберём вариант.",
                  "qualification": None, "interest": None, "budget": None, "escalate": bool(image_data)}

    # Vision-анализ товара для внутренней команды + фото всегда эскалируем
    analysis = ""
    if image_data:
        analysis = analyze_product_photo(image_data, text if text != "[ФОТО]" else "")
        result["escalate"] = True

    # amoCRM — добавляем URL фото и анализ в заметку
    note_text = text
    if photo_url:
        note_text += f"\n📸 Фото: {photo_url}"
    if analysis:
        note_text += f"\n\n🔎 Что на фото (для поиска):\n{analysis}"
    try:
        sync_to_amo(user_id, name, note_text, result["reply"],
                    qualification=result.get("qualification"),
                    interest=result.get("interest"),
                    budget=result.get("budget"))
    except Exception as e:
        logger.error(f"[MAX] amoCRM sync error: {e}")

    if result.get("escalate") and MANAGER_MAX_ID:
        try:
            lead_msg = f"🔥 Горячий лид из MAX!\n👤 {name} | ID: {user_id}\n🛋 {result.get('interest') or '—'}\n💬 {text[:200]}"
            if analysis:
                lead_msg += f"\n\n🔎 Что на фото (для поиска):\n{analysis}"
            await bot.send_message(chat_id=int(MANAGER_MAX_ID), text=lead_msg)
            # Форвардим фото менеджеру
            if photo_url:
                await bot.send_message(
                    chat_id=int(MANAGER_MAX_ID),
                    text=f"📸 Фото от клиента {name}:\n{photo_url}"
                )
        except Exception as e:
            logger.error(f"Escalation error: {e}")

    try:
        await msg.answer(result["reply"])
    except Exception as e:
        logger.error(f"[MAX] answer error: {e}")

async def main():
    await bot.delete_webhook()
    logger.info("🤖 KOKAHOUSE MAX Bot запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
