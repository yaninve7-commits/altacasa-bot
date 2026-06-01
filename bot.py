"""
ALTA CASA — AI Telegram Bot
Бот для общения с клиентами. Claude AI + Notion CRM.

Зависимости: pip install python-telegram-bot anthropic python-dotenv httpx
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
# notion_client удалён — используем только amoCRM

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Конфиг ───────────────────────────────────────────────────────────────────
TG_TOKEN        = os.getenv("TG_TOKEN")
ANTHROPIC_KEY   = os.getenv("ANTHROPIC_API_KEY")
# notion_client удалён — используем только amoCRM

MANAGER_CHAT_ID = os.getenv("MANAGER_CHAT_ID")
CHANNEL_ID      = os.getenv("CHANNEL_ID", "@altacasacn")  # канал для постинга

ai     = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ── Системный промпт ──────────────────────────────────────────────────────────
with open("system_prompt.txt", "r", encoding="utf-8") as f:
    BASE_PROMPT = f.read()

# ── База знаний (хранится в GitHub — постоянно) ───────────────────────────────
GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO   = "yaninve7-commits/altacasa-bot"
KNOWLEDGE_FILE = "custom_knowledge.txt"
_knowledge_cache: str = ""
_knowledge_loaded: bool = False


def github_get_file(path: str):
    """Получить содержимое файла из GitHub. Вернуть (content, sha)."""
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
    """Сохранить файл в GitHub автоматически."""
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
    """Загрузить базу знаний из GitHub (постоянное хранилище)."""
    global _knowledge_cache, _knowledge_loaded
    if _knowledge_loaded:
        return _knowledge_cache
    try:
        content, _ = github_get_file(KNOWLEDGE_FILE)
        if content and content.strip():
            _knowledge_cache = (
                f"\n\n═══════════════════════════════\n"
                f"ДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ (добавлены владельцем)\n"
                f"═══════════════════════════════\n{content.strip()}"
            )
            logger.info(f"База знаний загружена из GitHub ({len(content)} символов)")
        elif os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                local = f.read().strip()
            if local:
                _knowledge_cache = f"\n\n═══════════════════════════════\nДОПОЛНИТЕЛЬНЫЕ ЗНАНИЯ\n═══════════════════════════════\n{local}"
        _knowledge_loaded = True
    except Exception as e:
        logger.error(f"Knowledge load error: {e}")
    return _knowledge_cache


def save_knowledge(entry: str):
    """Сохранить знание — локально + автоматически в GitHub."""
    global _knowledge_loaded
    try:
        current, _ = github_get_file(KNOWLEDGE_FILE)
        new_content = (current.strip() + f"\n{entry}").strip()
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            f.write(new_content)
        ok = github_save_file(KNOWLEDGE_FILE, new_content, f"Knowledge: {entry[:60]}")
        if ok:
            logger.info(f"Знание сохранено в GitHub: {entry[:60]}")
        _knowledge_loaded = False
    except Exception as e:
        logger.error(f"Knowledge save error: {e}")

def get_system_prompt() -> str:
    return BASE_PROMPT + load_knowledge()


# ── Director Mode — AI-директор для владельца ────────────────────────────────

DIRECTOR_SYSTEM = """Ты — персональный AI-директор компании ALTA CASA.
Ты разговариваешь с владельцем бизнеса. Отвечай коротко, по делу, как опытный COO.
Используй данные которые получаешь через инструменты.
Всегда давай конкретные цифры и факты, не общие слова.
Если нужно — предлагай действия: написать клиенту, создать пост, отправить КП.
Отвечай на русском.

ВАЖНО — если ты не можешь выполнить запрос по техническим причинам (нет нужного инструмента, функция не реализована, данные недоступны):
1. Коротко объясни что именно не работает
2. Сразу после этого добавь блок с готовым промтом для разработчика в формате:

---
📋 ЗАДАЧА ДЛЯ РАЗРАБОТЧИКА:
[Чёткое описание что нужно реализовать, какие данные получать, откуда (Notion/amoCRM/Telegram), как отображать результат. Максимально конкретно, как техническое задание.]
---

Пример: если пользователь просит "покажи статистику продаж по менеджерам" а у тебя нет такого инструмента — объясни это и напиши готовый промт для разработчика чтобы он добавил нужную функцию."""

DIRECTOR_TOOLS = [
    {
        "name": "get_stats",
        "description": "Получить статистику лидов за период: количество, квалификация, бюджеты, каналы",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "За сколько дней (например 1, 2, 7, 30, 90)"}
            },
            "required": ["days"]
        }
    },
    {
        "name": "find_client",
        "description": "Найти клиента по имени, username или Telegram ID",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Имя, username или ID клиента"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_leads",
        "description": "Получить список лидов по квалификации",
        "input_schema": {
            "type": "object",
            "properties": {
                "qualification": {
                    "type": "string",
                    "enum": ["Горячий", "Тёплый", "Холодный", "Передан менеджеру", "все"],
                    "description": "Фильтр по квалификации"
                },
                "limit": {"type": "integer", "description": "Сколько записей (макс 20)"}
            },
            "required": ["qualification"]
        }
    },
    {
        "name": "send_to_client",
        "description": "Отправить сообщение клиенту: текст, фото, ссылки, кнопки",
        "input_schema": {
            "type": "object",
            "properties": {
                "tg_id": {"type": "integer", "description": "Telegram ID клиента"},
                "text": {"type": "string", "description": "Текст сообщения"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Список URL фотографий товара (до 10 штук)"
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
                    "description": "Inline-кнопки: [{text: 'Подробнее', url: 'https://...'}, ...]"
                }
            },
            "required": ["tg_id", "text"]
        }
    },
    {
        "name": "get_channel_info",
        "description": "Получить информацию о канале: подписчики, последние посты",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "reply_to_lead",
        "description": "Найти клиента по имени/username и отправить ему сообщение от Юли. Используй когда владелец хочет ответить клиенту или задать уточняющий вопрос.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "Имя или username клиента (из уведомления)"},
                "message": {"type": "string", "description": "Что написать клиенту от Юли"},
                "photo_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Фото товаров для отправки (опционально)"
                },
                "buttons": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"text": {"type": "string"}, "url": {"type": "string"}}},
                    "description": "Кнопки-ссылки (опционально)"
                }
            },
            "required": ["client_name", "message"]
        }
    },
    {
        "name": "update_deal",
        "description": "Обновить сделку в amoCRM: изменить статус, сумму, добавить примечание",
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_id": {"type": "integer", "description": "ID сделки в amoCRM"},
                "status": {
                    "type": "string",
                    "enum": ["новая", "переговоры", "кп_отправлено", "согласование", "успешно", "отказ"],
                    "description": "Новый статус сделки"
                },
                "price": {"type": "integer", "description": "Новая сумма сделки в рублях"},
                "note": {"type": "string", "description": "Примечание к сделке"}
            },
            "required": ["deal_id"]
        }
    },
    {
        "name": "create_deal",
        "description": "Создать новую сделку в amoCRM из Telegram-лида",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Название сделки"},
                "client_name": {"type": "string", "description": "Имя клиента"},
                "price": {"type": "integer", "description": "Сумма сделки в рублях"},
                "note": {"type": "string", "description": "Описание / первое сообщение клиента"}
            },
            "required": ["name", "client_name"]
        }
    },
    {
        "name": "search_deals",
        "description": "Найти сделки в amoCRM по названию или клиенту",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Поисковый запрос (имя клиента или название сделки)"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_revenue_stats",
        "description": "Получить статистику выручки и сделок: суммы, количество, средний чек, по стадиям и менеджерам. Сравнение с предыдущим периодом.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Период в днях (1, 7, 30, 90)"},
                "group_by": {
                    "type": "string",
                    "enum": ["менеджер", "стадия", "итого"],
                    "description": "Группировка результатов"
                }
            },
            "required": ["days"]
        }
    }
]


def director_get_stats(days: int) -> dict:
    """Статистика лидов за период."""
    from datetime import timedelta
    since = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
    try:
        results = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "Дата", "date": {"on_or_after": since}}
        )
    except Exception:
        # Если фильтр по дате не работает — берём всё
        results = notion.databases.query(database_id=NOTION_DB_ID, page_size=100)
    pages = results.get("results", [])
    stats = {"total": len(pages), "by_qual": {}, "by_channel": {}, "total_budget": 0, "hot": []}
    for p in pages:
        props = p.get("properties", {})
        qual = props.get("Квалификация", {}).get("select", {})
        qual_name = qual.get("name", "Не указана") if qual else "Не указана"
        stats["by_qual"][qual_name] = stats["by_qual"].get(qual_name, 0) + 1
        ch = props.get("Канал", {}).get("select", {})
        ch_name = ch.get("name", "Не указан") if ch else "Не указан"
        stats["by_channel"][ch_name] = stats["by_channel"].get(ch_name, 0) + 1
        budget = props.get("Бюджет ₽", {}).get("number") or 0
        stats["total_budget"] += budget
        if qual_name == "Горячий":
            name_arr = props.get("Name", {}).get("title", [])
            name = name_arr[0]["plain_text"] if name_arr else "—"
            tg_id = props.get("Telegram ID", {}).get("number")
            stats["hot"].append({"name": name, "budget": budget, "tg_id": tg_id})
    return stats


def director_find_client(query: str) -> list:
    """Найти клиента."""
    results = []
    # Поиск по имени
    try:
        r = notion.databases.query(
            database_id=NOTION_DB_ID,
            filter={"property": "Name", "title": {"contains": query}}
        )
        results.extend(r.get("results", []))
    except Exception:
        pass
    # Поиск по TG ID если число
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
        name = name_arr[0]["plain_text"] if name_arr else "—"
        qual = (props.get("Квалификация", {}).get("select") or {}).get("name", "—")
        interest = (props.get("Интерес", {}).get("select") or {}).get("name", "—")
        budget = props.get("Бюджет ₽", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        tg_url = props.get("Telegram", {}).get("url", "—")
        dialog = (props.get("Диалог с ботом", {}).get("rich_text") or [{}])
        dialog_text = dialog[0].get("plain_text", "")[-300:] if dialog else ""
        clients.append({
            "name": name, "qual": qual, "interest": interest,
            "budget": budget, "tg_id": tg_id, "tg_url": tg_url,
            "dialog_preview": dialog_text
        })
    return clients


DEALS_DB_ID = "36e698e7193a8092b378eeb45a969b84"  # Воронка сделок (Notion)
AMO_TOKEN   = os.getenv("AMO_LONG_TOKEN", "")
AMO_DOMAIN  = "yaninve7.amocrm.ru"
AMO_API     = "yaninve7.amocrm.ru"   # используем subdomain — он принимает токен


def amo_get_leads(days: int, limit: int = 250) -> list:
    """Получить сделки из amoCRM за последние N дней."""
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


# ── amoCRM CRM Sync ───────────────────────────────────────────────────────────
# Кеш: tg_id → {"contact_id": int, "lead_id": int}
_amo_client_cache: dict[int, dict] = {}
# Клиенты по которым уже было эскалационное уведомление
_escalated_clients: set = set()
# Персистентный маппинг tg_id → amo_contact_id (защита от дублей при рестарте)
AMO_MAP_FILE = "amo_id_map.json"

def _load_amo_map() -> dict:
    """Загрузить маппинг tg_id → {contact_id, lead_id} из файла."""
    if os.path.exists(AMO_MAP_FILE):
        try:
            with open(AMO_MAP_FILE, "r") as f:
                return {int(k): v for k, v in json.load(f).items()}
        except Exception:
            pass
    return {}

def _save_amo_map(tg_id: int, contact_id: int, lead_id: int):
    """Сохранить маппинг персистентно."""
    data = _load_amo_map()
    data[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
    try:
        with open(AMO_MAP_FILE, "w") as f:
            json.dump({str(k): v for k, v in data.items()}, f)
    except Exception as e:
        logger.error(f"amo_map save error: {e}")

# Загружаем маппинг при старте
_amo_client_cache = _load_amo_map()

# Маппинг статусов → ID в воронке amoCRM (стандартные)
AMO_STATUS_MAP = {
        "новый_лид":     86187794,  # Новый лид
            "квалификация":  86187798,  # Квалификация
                "подбор":        86187802,  # Подбор товара
                    "кп_отправлено": 86187806,  # КП отправлено
                        "переговоры":    86187810,  # Переговоры
                            "ожидание":      86187814,  # Ожидание оплаты
                                "оплачено":      86187818,  # Оплачено
                                    "доставка":      86187822,  # Доставка
                                        "успешно":       142,       # Успешно реализовано (system)
                                            "отказ":         143,       # Закрыто и не реализовано (system)
                                            }
AMO_WON_STATUS  = 142  # Won (победа)
AMO_LOST_STATUS = 143  # Lost (отказ)


def amo_request(method: str, path: str, data: dict = None) -> dict:
    """Универсальный запрос к amoCRM API."""
    import urllib.request, urllib.error
    if not AMO_TOKEN:
        logger.error("amoCRM: AMO_LONG_TOKEN не настроен")
        return {"error": "AMO_LONG_TOKEN не настроен"}
    # Используем реальный API домен (не subdomain который делает редирект)
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
            logger.info(f"amoCRM {method} {path} → {r.status}")
            return json.loads(raw) if raw else {"status": "ok"}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()[:300]
        logger.error(f"amoCRM HTTP {e.code} {method} {path}: {err_body}")
        return {"error": f"HTTP {e.code}: {err_body}"}
    except Exception as e:
        logger.error(f"amoCRM error {method} {path}: {e}")
        return {"error": str(e)}


def amo_get_pipeline_statuses() -> dict:
    """Получить ID статусов из первой воронки."""
    r = amo_request("GET", "leads/pipelines")
    pipelines = r.get("_embedded", {}).get("pipelines", [])
    if not pipelines:
        return {}
    statuses = {}
    for s in pipelines[0].get("_embedded", {}).get("statuses", []):
        statuses[s["name"].lower()] = s["id"]
    return {"pipeline_id": pipelines[0]["id"], "statuses": statuses}


def director_update_deal(deal_id: int, status: str = None, price: int = None, note: str = None) -> dict:
    """Обновить сделку в amoCRM."""
    payload = {}

    if status:
        # Получаем реальные ID статусов
        pipe_info = amo_get_pipeline_statuses()
        statuses = pipe_info.get("statuses", {})
        # Ищем нужный статус
        status_id = None
        status_map = {
            "новая": ["первичный", "новая", "new"],
            "переговоры": ["переговор", "discuss"],
            "кп_отправлено": ["кп", "предложение", "принимают"],
            "согласование": ["согласован", "decision"],
            "успешно": ["успешно", "won", "закрыт"],
            "отказ": ["отказ", "lost", "провал"]
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

    # Добавляем примечание
    if note:
        amo_request("POST", "notes", [{"entity_id": deal_id, "note_type": "common", "params": {"text": note}, "entity_type": "leads"}])

    return {"deal_id": deal_id, "updated": payload, "result": result}


def director_create_deal(name: str, client_name: str, price: int = 0, note: str = "") -> dict:
    """Создать новую сделку в amoCRM."""
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

    if note and result.get("_embedded", {}).get("leads"):
        deal_id = result["_embedded"]["leads"][0]["id"]
        amo_request("POST", "notes", [{
            "entity_id": deal_id,
            "note_type": "common",
            "params": {"text": note},
            "entity_type": "leads"
        }])

    return result


def director_search_deals(query: str) -> list:
    """Найти сделки по запросу."""
    r = amo_request("GET", f"leads?query={query}&limit=10&with=contacts")
    leads = r.get("_embedded", {}).get("leads", [])
    result = []
    for l in leads:
        contacts = l.get("_embedded", {}).get("contacts", [])
        client = contacts[0].get("name", "—") if contacts else "—"
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
    """Найти или создать контакт в amoCRM. Вернуть contact_id."""
    import urllib.parse as _urlparse
    if not AMO_TOKEN:
        return 0

    # 1. Ищем по имени — с правильным URL-encode
    params = _urlparse.urlencode({"query": name, "limit": 5})
    r = amo_request("GET", f"contacts?{params}")
    contacts = r.get("_embedded", {}).get("contacts", [])
    for c in contacts:
        if c.get("name") == name:
            return c["id"]

    # 2. Также ищем по tg_id если есть
    if not contacts and tg_username:
        params2 = _urlparse.urlencode({"query": tg_username, "limit": 3})
        r2 = amo_request("GET", f"contacts?{params2}")
        for c in r2.get("_embedded", {}).get("contacts", []):
            if c.get("name") == name:
                return c["id"]

    # 3. Создаём нового — только стандартные поля без кастомных field_code
    note_text = f"Telegram ID: {tg_id}"
    if tg_username:
        note_text += f"\n@{tg_username}"

    data = [{"name": name}]  # минимальный payload без кастомных полей
    r = amo_request("POST", "contacts", data)
    new_contacts = r.get("_embedded", {}).get("contacts", [])
    if not new_contacts:
        logger.error(f"amoCRM: не удалось создать контакт для {name}: {r}")
        return 0
    contact_id = new_contacts[0]["id"]

    # 4. Добавляем Telegram данные как примечание (надёжнее чем кастомные поля)
    amo_request("POST", "contacts/notes", [{
        "entity_id": contact_id,
        "note_type": "common",
        "params": {"text": note_text}
    }])
    logger.info(f"amoCRM: создан контакт {name} (id={contact_id})")
    return contact_id


def amo_get_or_create_lead(tg_id: int, contact_id: int, name: str) -> int:
    """Найти активную сделку контакта или создать новую. Вернуть lead_id."""
    if not AMO_TOKEN or not contact_id:
        return 0
    # Ищем сделки контакта
    r = amo_request("GET", f"leads?filter[contact_id]={contact_id}&limit=5")
    leads = r.get("_embedded", {}).get("leads", [])
    # Берём последнюю незакрытую
    for l in leads:
        if l.get("status_id") not in [142, 143]:  # не Won/Lost
            return l["id"]
    # Создаём новую
    pipe_info = amo_get_pipeline_statuses()
    data = [{
        "name": f"Запрос от {name}",
        "price": 0,
        "_embedded": {"contacts": [{"id": contact_id}]}
    }]
    if pipe_info.get("pipeline_id"):
        data[0]["pipeline_id"] = pipe_info["pipeline_id"]
    r = amo_request("POST", "leads/complex", data)
    leads = r.get("_embedded", {}).get("leads", [])
    return leads[0]["id"] if leads else 0


def amo_add_note(lead_id: int, text: str, note_type: str = "common"):
    """Добавить комментарий к сделке."""
    if not AMO_TOKEN or not lead_id:
        return
    amo_request("POST", "leads/notes", [{
        "entity_id": lead_id,
        "note_type": note_type,
        "params": {"text": text[:1000]}
    }])


def amo_move_pipeline(lead_id: int, qualification: str, interest: str = None, budget: int = None):
    """Двинуть сделку по воронке на основе квалификации."""
    if not AMO_TOKEN or not lead_id:
        return
    pipe_info = amo_get_pipeline_statuses()
    statuses = pipe_info.get("statuses", {})
    pipeline_id = pipe_info.get("pipeline_id")

    # Находим нужный статус по квалификации
    target_status = None
    if qualification == "Горячий":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["переговор", "кп", "принимают", "discuss"]):
                target_status = sid
                break
    elif qualification == "Передан менеджеру":
        for name, sid in statuses.items():
            if any(k in name.lower() for k in ["кп", "отправлено", "ожидан"]):
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
    """Главная функция синхронизации диалога с amoCRM."""
    if not AMO_TOKEN:
        return

    try:
        # Получаем из кеша или создаём
        if tg_id not in _amo_client_cache:
            contact_id = amo_get_or_create_contact(tg_id, name, username)
            if not contact_id:
                return

            # Для горячего лида — создаём именованную сделку
            if qualification == "Горячий" and interest:
                lead_name = f"{name} — {interest}"
            else:
                lead_name = f"Запрос от {name}"

            lead_id = amo_get_or_create_lead(tg_id, contact_id, lead_name)
            _amo_client_cache[tg_id] = {"contact_id": contact_id, "lead_id": lead_id}
            _save_amo_map(tg_id, contact_id, lead_id)  # персистентно
        else:
            lead_id = _amo_client_cache[tg_id].get("lead_id", 0)

            # Обновляем название сделки если стал горячим
            if qualification == "Горячий" and interest and lead_id:
                amo_request("PATCH", "leads", [{"id": lead_id, "name": f"{name} — {interest}"}])

        if not lead_id:
            return

        # Добавляем сообщение клиента как комментарий
        note = f"👤 {name}: {message_text}\n🤖 Юля: {bot_reply[:300]}"
        if interest:
            note += f"\n📦 Интерес: {interest}"
        if budget:
            note += f"\n💰 Бюджет: {budget:,} ₽".replace(",", " ")
        if qualification:
            note += f"\n📊 Статус: {qualification}"
        amo_add_note(lead_id, note)

        # Двигаем по воронке + обновляем сумму если известен бюджет
        if qualification in ("Горячий", "Передан менеджеру"):
            amo_move_pipeline(lead_id, qualification, interest, budget)

        logger.info(f"amoCRM sync: tg={tg_id} lead={lead_id} qual={qualification}")
    except Exception as e:
        logger.error(f"amoCRM sync error: {e}")


def director_get_revenue_stats(days: int, group_by: str = "итого") -> dict:
    """Статистика выручки. Источник: amoCRM (основной) или Notion (fallback)."""

    # ── amoCRM ────────────────────────────────────────────────────────────────
    if AMO_TOKEN:
        leads = amo_get_leads(days)
        prev_leads = amo_get_leads(days * 2)
        # prev_leads включает текущий период — убираем
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
                # Менеджер
                embedded = d.get("_embedded", {})
                users = embedded.get("users", []) if isinstance(embedded, dict) else []
                manager = users[0].get("name", "Не назначен") if users else "Не назначен"
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

    # ── Notion fallback ───────────────────────────────────────────────────────
    from datetime import timedelta
    now = datetime.utcnow()
    since = (now - timedelta(days=days)).date().isoformat()
    try:
        r = notion.databases.query(
            database_id=DEALS_DB_ID,
            filter={"property": "Дедлайн", "date": {"on_or_after": since}}
        )
        deals = r.get("results", [])
    except Exception:
        r = notion.databases.query(database_id=DEALS_DB_ID, page_size=100)
        deals = r.get("results", [])

    total_rub = sum(d.get("properties", {}).get("Сумма ₽", {}).get("number") or 0 for d in deals)
    count = len(deals)

    by_stage = {}
    for d in deals:
        props = d.get("properties", {})
        stage = (props.get("Стадия", {}).get("status") or {}).get("name", "—")
        rub = props.get("Сумма ₽", {}).get("number") or 0
        by_stage[stage] = by_stage.get(stage, {"count": 0, "sum_rub": 0})
        by_stage[stage]["count"] += 1
        by_stage[stage]["sum_rub"] += rub

    return {
        "source": "Notion (amoCRM токен не активен)",
        "period_days": days,
        "current": {"count": count, "total": total_rub, "avg": total_rub // count if count else 0, "by_stage": by_stage},
        "previous": {},
        "delta": None,
        "delta_pct": None,
    }


def director_list_leads(qualification: str, limit: int = 10) -> list:
    """Список лидов — из amoCRM (основной) или Notion (fallback)."""

    # ── amoCRM ────────────────────────────────────────────────────────────────
    if AMO_TOKEN:
        import urllib.parse
        # Маппинг квалификации → статус amoCRM (примерный)
        status_filter = ""
        if qualification == "Горячий":
            # Ищем лиды в стадии переговоров/КП
            pass  # фильтруем по pipeline stage позже

        r = amo_request("GET", f"leads?limit={min(limit,50)}&with=contacts&order[created_at]=desc")
        raw_leads = r.get("_embedded", {}).get("leads", [])

        leads = []
        for l in raw_leads:
            contacts = l.get("_embedded", {}).get("contacts", []) if isinstance(l.get("_embedded"), dict) else []
            client = contacts[0].get("name", "—") if contacts else "—"
            price = l.get("price") or 0
            created = l.get("created_at", 0)
            from datetime import datetime as _dt
            created_str = _dt.fromtimestamp(created).strftime("%d.%m.%Y %H:%M") if created else "—"
            leads.append({
                "id": l.get("id"),
                "name": l.get("name", "—"),
                "client": client,
                "price": price,
                "status_id": l.get("status_id"),
                "created_at": created_str,
                "source": "amoCRM"
            })

        # Фильтрация по qualification если нужно
        if qualification == "Горячий":
            # Горячие — не закрытые и с суммой > 0
            leads = [l for l in leads if l.get("price", 0) > 0][:limit]
        elif qualification != "все":
            leads = leads[:limit]

        return leads if leads else [{"note": "В amoCRM нет лидов за последнее время"}]

    # ── Notion fallback ───────────────────────────────────────────────────────
    try:
        if qualification != "все":
            r = notion.databases.query(
                database_id=NOTION_DB_ID,
                filter={"property": "Квалификация", "select": {"equals": qualification}},
                page_size=min(limit, 20)
            )
        else:
            r = notion.databases.query(database_id=NOTION_DB_ID, page_size=min(limit, 20))
    except Exception as e:
        return [{"error": f"Ошибка Notion: {e}"}]

    leads = []
    for p in r.get("results", []):
        props = p.get("properties", {})
        name_arr = props.get("Name", {}).get("title", [])
        name = name_arr[0]["plain_text"] if name_arr else "—"
        qual = (props.get("Квалификация", {}).get("select") or {}).get("name", "—")
        interest = (props.get("Интерес", {}).get("select") or {}).get("name", "—")
        budget = props.get("Бюджет ₽", {}).get("number")
        tg_id = props.get("Telegram ID", {}).get("number")
        leads.append({"name": name, "qual": qual, "interest": interest,
                      "budget": budget, "tg_id": tg_id, "source": "Notion"})
    return leads


async def handle_owner_director(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Director Mode — владелец задаёт вопросы о бизнесе."""
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    messages = [{"role": "user", "content": text}]
    bot_ref = context.bot

    # Цикл tool_use
    for _ in range(5):  # максимум 5 вызовов инструментов
        response = ai.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=DIRECTOR_SYSTEM,
            tools=DIRECTOR_TOOLS,
            messages=messages
        )

        if response.stop_reason == "end_turn":
            # Финальный ответ
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
                            inp.get("qualification", "все"),
                            inp.get("limit", 10)
                        )
                    elif tool == "send_to_client":
                        tg_id = inp["tg_id"]
                        text = inp["text"]

                        # ── Валидация товара перед отправкой ─────────────────
                        photo_urls_check = inp.get("photo_urls", [])
                        buttons_check = inp.get("buttons", [])
                        all_urls = photo_urls_check + [b.get("url","") for b in buttons_check]
                        altacasa_urls = [u for u in all_urls if "altacasa.ru" in u]

                        if altacasa_urls:
                            # Извлекаем product key из URL или текста
                            import re as _re
                            product_key = None
                            for url in altacasa_urls:
                                m = _re.search(r'product(\d*)', url)
                                if m:
                                    product_key = url.split("/")[-1].replace(".html","")

                            # Получаем интерес клиента из кеша диалогов
                            client_history = dialogs.get(tg_id, [])
                            client_interests = []
                            for msg in client_history[-10:]:
                                content = msg.get("content","") if isinstance(msg.get("content"), str) else ""
                                for cat in ["диван","кресло","кровать","стол","стул","шкаф","тумба","гардероб"]:
                                    if cat in content.lower():
                                        client_interests.append(cat)

                            # Категория отправляемого товара из текста
                            sending_cats = []
                            for cat in ["диван","кресло","кровать","стол","стул","шкаф","тумба","гардероб"]:
                                if cat in text.lower() or any(cat in u.lower() for u in all_urls):
                                    sending_cats.append(cat)

                            # Если интересы известны и товар не совпадает — WARNING
                            if client_interests and sending_cats:
                                mismatch = not any(c in client_interests for c in sending_cats)
                                if mismatch:
                                    warning_msg = (
                                        f"⚠️ ВНИМАНИЕ!\n"
                                        f"Клиент интересовался: {', '.join(set(client_interests))}\n"
                                        f"Вы отправляете: {', '.join(set(sending_cats))}\n\n"
                                        f"Это намеренно? Сообщение всё равно отправлено."
                                    )
                                    await bot_ref.send_message(
                                        chat_id=int(MANAGER_CHAT_ID),
                                        text=warning_msg
                                    )
                        # ── конец валидации ───────────────────────────────────
                        photo_urls = inp.get("photo_urls", [])
                        buttons = inp.get("buttons", [])

                        # Строим inline-клавиатуру если есть кнопки
                        reply_markup = None
                        if buttons:
                            from telegram import InlineKeyboardMarkup, InlineKeyboardButton
                            keyboard = [[InlineKeyboardButton(b["text"], url=b["url"])] for b in buttons if b.get("url")]
                            if keyboard:
                                reply_markup = InlineKeyboardMarkup(keyboard)

                        if photo_urls:
                            if len(photo_urls) == 1:
                                # Одно фото с подписью
                                await bot_ref.send_photo(
                                    chat_id=tg_id,
                                    photo=photo_urls[0],
                                    caption=text[:1024],
                                    reply_markup=reply_markup
                                )
                            else:
                                # Несколько фото — media group
                                from telegram import InputMediaPhoto
                                media = [InputMediaPhoto(media=url, caption=text[:1024] if i == 0 else None)
                                         for i, url in enumerate(photo_urls[:10])]
                                await bot_ref.send_media_group(chat_id=tg_id, media=media)
                                if reply_markup:
                                    await bot_ref.send_message(chat_id=tg_id, text="👆 Посмотрите варианты выше", reply_markup=reply_markup)
                        else:
                            # Только текст с кнопками
                            await bot_ref.send_message(
                                chat_id=tg_id,
                                text=text,
                                reply_markup=reply_markup,
                                parse_mode="Markdown"
                            )
                        result = {"status": "sent", "tg_id": tg_id, "photos": len(photo_urls), "buttons": len(buttons)}
                    elif tool == "get_channel_info":
                        result = {"channel": CHANNEL_ID, "note": "Данные канала доступны через Telegram API"}
                    elif tool == "reply_to_lead":
                        # Ищем клиента в Notion по имени
                        clients = director_find_client(inp["client_name"])
                        if not clients:
                            result = {"error": f"Клиент '{inp['client_name']}' не найден в базе"}
                        else:
                            client = clients[0]
                            tg_id = client.get("tg_id")
                            if not tg_id:
                                result = {"error": f"У клиента {client['name']} нет Telegram ID"}
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
                                # Добавляем в amoCRM как исходящее сообщение
                                if tg_id in _amo_client_cache:
                                    lead_id = _amo_client_cache[tg_id].get("lead_id", 0)
                                    amo_add_note(lead_id, f"📤 Исходящее от менеджера → {client['name']}:\n{msg}")
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
                            inp.get("group_by", "итого")
                        )
                except Exception as e:
                    result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False, default=str)
                })

            messages.append({"role": "user", "content": tool_results})

    await update.message.reply_text("Не удалось получить данные. Попробуй переформулировать.")


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

        # ── Director Mode — всё остальное от владельца идёт к AI-директору ──────
        await handle_owner_director(update, context, text)
        return

    # ── Проверка подтверждения КП от клиента ──────────────────────────────────
    if user.id in pending_kp and text.strip().lower() in [
        "да", "да!", "yes", "подходит", "согласен", "согласна",
        "отлично", "хорошо", "берём", "берем", "ок", "ok", "👍"
    ]:
        kp_data = pending_kp[user.id]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_document")
        try:
            client_name = user.full_name or "Клиент"
            pdf_bytes = await generate_kp_pdf(kp_data, client_name)
            filename = f"КП_ALTA_CASA_{datetime.now().strftime('%d%m%Y')}.pdf"

            # Отправляем PDF клиенту
            from telegram import InputFile
            import io
            await context.bot.send_document(
                chat_id=user.id,
                document=InputFile(io.BytesIO(pdf_bytes), filename=filename),
                caption=f"Коммерческое предложение ALTA CASA\n{kp_data['product']}\nИтого: {kp_data['total']:,} ₽".replace(',', ' ')
            )

            # Уведомляем менеджера
            if kp_data.get("manager_id"):
                await context.bot.send_message(
                    chat_id=kp_data["manager_id"],
                    text=f"✅ Клиент {client_name} (ID: {user.id}) подтвердил КП!\nКП отправлено."
                )

            del pending_kp[user.id]
            logger.info(f"КП PDF отправлен клиенту {user.id}")
        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            await update.message.reply_text(
                "Отлично! Передаю вашу заявку менеджеру — он свяжется с вами в ближайшее время."
            )
        return

    # ── Проверка внешних ссылок ────────────────────────────────────────────────
    import re
    urls_in_text = re.findall(r'https?://[^\s]+', text)
    has_external_link = any(
        "altacasa.ru" not in url and "t.me" not in url and "max.ru" not in url
        for url in urls_in_text
    )
    # Если есть внешняя ссылка — добавим подсказку в промт для Claude
    extra_context = ""
    if has_external_link:
        extra_context = "\n[СИСТЕМА: клиент прислал ссылку НЕ с нашего сайта. Применяй правило эскалации для внешних ссылок.]"

    # ── Обычный клиент ─────────────────────────────────────────────────────────
    page_id = None
    try:
        page_id = get_or_create_client(user.id, name, user.username or "")
    except Exception as e:
        logger.error(f"Notion error: {e}")

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    load_history_from_amo(user.id)
    result = ask_claude(user.id, text + extra_context)

    # Если внешняя ссылка — тихо форвардим тебе (без эскалации в чат клиента)
    if has_external_link and MANAGER_CHAT_ID:
        try:
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=(
                    f"🔗 Клиент {user.full_name} прислал внешнюю ссылку:\n\n"
                    f"{text[:500]}\n\n"
                    f"Ответь через: `ответь {user.full_name} [твой текст]`"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
        # НЕ ставим escalate=True — Юля продолжает вести диалог

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
        prompt = caption if caption else "Клиент прислал фото товара который хочет найти или купить. Ответь согласно правилам работы с фото."
        load_history_from_amo(user.id)
        result = ask_claude(user.id, prompt, image_data=image_data)
        # Фото от клиента всегда эскалируем владельцу
        result["escalate"] = True
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

    load_history_from_amo(user.id)
    result = ask_claude(user.id, prompt)
    await _send_and_update(update, context, user, page_id, result, f"[ФАЙЛ] {doc.file_name}")


async def _send_and_update(update, context, user, page_id, result, original_text):
    """Отправить ответ клиенту и обновить Notion."""
    # Уведомить менеджера при эскалации — ТОЛЬКО ОДИН РАЗ на клиента
    if result["escalate"] and MANAGER_CHAT_ID and user.id not in _escalated_clients:
        try:
            # Собираем историю диалога для контекста
            history = dialogs.get(user.id, [])
            def clean_msg(text: str) -> str:
                """Убрать JSON блоки из текста."""
                import re as _re
                text = _re.sub(r'```json.*?```', '', text, flags=_re.DOTALL)
                return text.strip()[:150]

            dialog_summary = "\n".join(
                f"{'👤' if m['role'] == 'user' else '🤖'} {clean_msg(m['content']) if isinstance(m['content'], str) else '[медиа]'}"
                for m in history[-6:]
                if isinstance(m.get('content'), str) and m['content'].strip()
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
                f"📊 Статус: {qualification}\n🔗 amoCRM: https://yaninve7.amocrm.ru/leads/detail/{_amo_client_cache.get(user.id, {}).get('lead_id', '?')}\n\n"
                f"📝 Причина:\n{result.get('reply','')[:200]}\n\n💬 Диалог:\n{dialog_summary}"
            )
            await context.bot.send_message(
                chat_id=int(MANAGER_CHAT_ID),
                text=msg
            )
            # Помечаем что уже уведомили — не будем спамить
            _escalated_clients.add(user.id)
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

    # Синхронизация с amoCRM
    if not is_owner(user):
        try:
            sync_to_amo(
                tg_id=user.id,
                name=user.full_name or "Клиент",
                username=user.username or "",
                message_text=original_text[:500],
                bot_reply=result["reply"][:500],
                qualification=result.get("qualification"),
                interest=result.get("interest"),
                budget=int(result["budget"]) if result.get("budget") else None
            )
        except Exception as e:
            logger.error(f"amoCRM sync exception: {e}")

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


# ── КП (Коммерческое предложение) ────────────────────────────────────────────

# Хранилище ожидающих подтверждения КП: {client_tg_id: {данные КП}}
pending_kp: dict[int, dict] = {}


async def cmd_kp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /kp <tg_id клиента> <товар> <цена₽> [доставка₽]
    Пример: /kp 283951945 "Диван MC-A68 3-местный кожа" 235000 8000
    """
    if not is_owner(update.effective_user):
        return

    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "📋 *Как отправить КП:*\n\n"
            "`/kp <ID_клиента> <товар> <цена> [доставка]`\n\n"
            "Пример:\n"
            "`/kp 283951945 Диван MC-A68 3-местный 235000 8000`\n\n"
            "ID клиента узнать: попроси клиента написать боту, "
            "или посмотри в Notion → Telegram ID",
            parse_mode="Markdown"
        )
        return

    client_id = int(args[0])
    price = int(args[-2]) if len(args) >= 4 else int(args[-1])
    delivery = int(args[-1]) if len(args) >= 4 else 0
    product = " ".join(args[1:-2]) if len(args) >= 4 else " ".join(args[1:-1])
    total = price + delivery

    # Сохраняем в ожидание
    pending_kp[client_id] = {
        "product": product,
        "price": price,
        "delivery": delivery,
        "total": total,
        "manager_id": update.effective_user.id,
        "created_at": datetime.now().isoformat(),
    }

    # Отправляем клиенту
    try:
        msg = (
            f"Здравствуйте!\n\n"
            f"Мы подготовили расчёт по вашему запросу:\n\n"
            f"📦 *{product}*\n"
            f"💰 Стоимость: {price:,} ₽\n"
        )
        if delivery:
            msg += f"🚚 Доставка: {delivery:,} ₽\n"
        msg += (
            f"━━━━━━━━━━━━━━\n"
            f"💵 *Итого: {total:,} ₽*\n\n"
            f"Вас устраивают условия? Ответьте *«Да»* — и я пришлю полное коммерческое предложение."
        )
        msg = msg.replace(",", " ")

        await context.bot.send_message(
            chat_id=client_id,
            text=msg,
            parse_mode="Markdown"
        )
        await update.message.reply_text(
            f"✅ Расчёт отправлен клиенту (ID: {client_id})\n"
            f"Товар: {product}\n"
            f"Итого: {total:,} ₽\n\n"
            f"Жду подтверждения от клиента...".replace(",", " ")
        )
        logger.info(f"КП отправлено клиенту {client_id}: {product} {total}₽")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки: {e}")


async def generate_kp_pdf(data: dict, client_name: str) -> bytes:
    """Генерировать PDF коммерческого предложения."""
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

    # Заголовок
    title_style = ParagraphStyle('Title', parent=styles['Normal'],
                                  fontSize=20, textColor=colors.HexColor('#1a1a2e'),
                                  spaceAfter=6, fontName='Helvetica-Bold')
    sub_style = ParagraphStyle('Sub', parent=styles['Normal'],
                                fontSize=11, textColor=colors.grey, spaceAfter=20)
    body_style = ParagraphStyle('Body', parent=styles['Normal'],
                                 fontSize=11, spaceAfter=8, leading=16)

    story.append(Paragraph("ALTA CASA", title_style))
    story.append(Paragraph("Коммерческое предложение", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.5*cm))

    # Клиент и дата
    story.append(Paragraph(f"<b>Для:</b> {client_name}", body_style))
    story.append(Paragraph(f"<b>Дата:</b> {datetime.now().strftime('%d.%m.%Y')}", body_style))
    story.append(Spacer(1, 0.5*cm))

    # Таблица с товаром
    table_data = [
        ['Наименование', 'Стоимость'],
        [data['product'], f"{data['price']:,} ₽".replace(',', ' ')],
    ]
    if data['delivery']:
        table_data.append(['Доставка', f"{data['delivery']:,} ₽".replace(',', ' ')])
    table_data.append(['ИТОГО', f"{data['total']:,} ₽".replace(',', ' ')])

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

    # Условия
    story.append(Paragraph("<b>Условия:</b>", body_style))
    story.append(Paragraph("• Производство: 6–8 недель", body_style))
    story.append(Paragraph("• Оплата: 30% предоплата, 70% перед отправкой", body_style))
    story.append(Paragraph("• Гарантия: 12 месяцев", body_style))
    story.append(Paragraph("• Белая таможня, доставка под ключ", body_style))
    story.append(Spacer(1, 1*cm))

    # Контакты
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e0e0e0')))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("ALTA CASA | altacasa.ru | @altacasacn_bot", sub_style))

    doc.build(story)
    return buffer.getvalue()


# ── Ежедневный отчёт ────────────────────────────────────────────────────────

async def daily_report(bot):
    """Ежедневный отчёт владельцу в 9:00 МСК."""
    if not MANAGER_CHAT_ID:
        return
    try:
        # Получаем лиды из amoCRM за последние 24 часа
        import time as _time
        since = int(_time.time()) - 86400
        r_new = amo_request("GET", f"leads?filter[created_at][from]={since}&limit=50")
        new_leads = r_new.get("_embedded", {}).get("leads", [])

        # Все активные лиды
        r_all = amo_request("GET", "leads?limit=50&order[created_at]=desc")
        all_leads = r_all.get("_embedded", {}).get("leads", [])

        # Горячие (с ценой > 0 и не закрытые)
        hot = [l for l in all_leads if (l.get("price") or 0) > 0 and l.get("status_id") not in [142, 143]]
        # Зависшие (не обновлялись 3+ дня)
        stale_ts = int(_time.time()) - 259200
        stale = [l for l in all_leads if (l.get("updated_at") or 0) < stale_ts and l.get("status_id") not in [142, 143]]

        total_sum = sum(l.get("price", 0) or 0 for l in all_leads if l.get("status_id") not in [142, 143])

        msg = (
            f"☀️ *Доброе утро! Отчёт ALTA CASA*\n\n"
            f"📊 За последние 24 часа:\n"
            f"• Новых лидов: {len(new_leads)}\n"
            f"• Горячих в работе: {len(hot)}\n"
            f"• Сумма в работе: {total_sum:,} ₽\n\n".replace(",", " ")
        )

        if stale:
            msg += f"⚠️ Зависли (3+ дня без активности):\n"
            for l in stale[:5]:
                contacts = l.get("_embedded", {}).get("contacts", [])
                client = contacts[0].get("name", "—") if contacts else "—"
                msg += f"• {client} — {l.get('name', '?')}\n"
            msg += "\n"

        msg += "Напиши мне что нужно сделать сегодня или спроси статистику."

        await bot.send_message(chat_id=int(MANAGER_CHAT_ID), text=msg, parse_mode="Markdown")
        logger.info("📊 Ежедневный отчёт отправлен")
    except Exception as e:
        logger.error(f"daily_report error: {e}")


# ── Follow-up автоматика ──────────────────────────────────────────────────────

# Храним когда отправляли follow-up: {lead_id: [timestamp1, timestamp2]}
_followup_sent: dict[int, list] = {}

FOLLOWUP_MESSAGES = [
    "Добрый день! Возвращаюсь к вашему запросу. Хотите, я подберу несколько вариантов под ваш бюджет и стиль?",
    "Здравствуйте! Хотел(а) уточнить — остался ли интерес к нашей мебели? Готова ответить на любые вопросы.",
]

async def followup_check(bot):
    """Проверяем тёплых/горячих лидов которые молчат 2+ дня."""
    import time as _time
    now = int(_time.time())
    cutoff_2d = now - 172800  # 2 дня
    cutoff_5d = now - 432000  # 5 дней
    cutoff_7d = now - 604800  # 7 дней

    # Только днём (9-20 МСК = 6-17 UTC)
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

            # Только активные тёплые/горячие
            if status_id in [142, 143]:  # Won/Lost
                continue
            if price == 0:  # Холодный — пропускаем
                continue

            sent = _followup_sent.get(lead_id, [])
            contacts = lead.get("_embedded", {}).get("contacts", []) if isinstance(lead.get("_embedded"), dict) else []
            client_name = contacts[0].get("name", "Клиент") if contacts else "Клиент"

            # Ищем tg_id клиента в кеше
            tg_id = None
            for tid, data in _amo_client_cache.items():
                if data.get("lead_id") == lead_id:
                    tg_id = tid
                    break

            if not tg_id:
                continue

            # 2 дня — первый follow-up
            if updated < cutoff_2d and len(sent) == 0:
                msg = FOLLOWUP_MESSAGES[0]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id] = [now]
                amo_add_note(lead_id, f"📤 Follow-up #1 отправлен: {msg[:100]}")
                logger.info(f"Follow-up #1 → lead {lead_id} ({client_name})")

            # 5 дней — второй follow-up
            elif updated < cutoff_5d and len(sent) == 1:
                msg = FOLLOWUP_MESSAGES[1]
                await bot.send_message(chat_id=tg_id, text=msg)
                _followup_sent[lead_id].append(now)
                amo_add_note(lead_id, f"📤 Follow-up #2 отправлен")
                logger.info(f"Follow-up #2 → lead {lead_id} ({client_name})")

            # 7 дней — задача владельцу
            elif updated < cutoff_7d and len(sent) == 2:
                if MANAGER_CHAT_ID:
                    await bot.send_message(
                        chat_id=int(MANAGER_CHAT_ID),
                        text=f"⚠️ *{client_name}* не отвечает 7 дней.\nСделка: {lead.get('name', '?')}\nПроверьте вручную."
                    )
                _followup_sent[lead_id].append(now)
                logger.info(f"Follow-up #3 владельцу → lead {lead_id}")

    except Exception as e:
        logger.error(f"followup_check error: {e}")


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

    # Команда КП
    app.add_handler(CommandHandler("kp", cmd_kp))

    # Тест amoCRM
    async def cmd_test_amo(update, context):
        if not is_owner(update.effective_user):
            return
        await update.message.reply_text("🔄 Тестирую подключение к amoCRM...")
        r = amo_request("GET", "account")
        if "error" in r:
            await update.message.reply_text(f"❌ amoCRM ошибка: {r['error']}")
        else:
            name = r.get("name", "?")
            await update.message.reply_text(
                f"✅ amoCRM подключён!\n"
                f"Аккаунт: {name}\n"
                f"Домен: {AMO_DOMAIN}\n"
                f"API: {AMO_API}"
            )
    app.add_handler(CommandHandler("test_amo", cmd_test_amo))

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

    # Планировщик запускается после старта asyncio loop
    async def post_init(application):
        scheduler = AsyncIOScheduler(timezone="UTC")

        # Авто-посты пн/ср/пт в 10:00 МСК (UTC+3 = 07:00 UTC)
        scheduler.add_job(
            auto_post_to_channel,
            CronTrigger(day_of_week="mon,wed,fri", hour=7, minute=0),
            args=[application.bot], id="auto_post"
        )

        # Ежедневный отчёт в 9:00 МСК (06:00 UTC)
        scheduler.add_job(
            daily_report, CronTrigger(hour=6, minute=0),
            args=[application.bot], id="daily_report"
        )

        # Follow-up каждые 6 часов — проверяем зависших лидов
        scheduler.add_job(
            followup_check, CronTrigger(hour="6,12,18", minute=0),
            args=[application.bot], id="followup"
        )

        scheduler.start()
        logger.info("📅 Планировщик запущен: посты + отчёт + follow-up")

    app.post_init = post_init

    logger.info("🤖 ALTA CASA Bot запущен")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
