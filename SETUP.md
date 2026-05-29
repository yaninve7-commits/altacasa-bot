# ALTA CASA Bot — Инструкция по запуску

## Что делает бот
- Общается с клиентами в Telegram от имени менеджера "Юля"
- Квалифицирует лидов (холодный / тёплый / горячий)
- Автоматически создаёт и обновляет записи в Notion CRM
- При горячем лиде — присылает уведомление менеджеру

---

## Шаг 1 — Настройка Notion Integration

1. Зайди на https://www.notion.so/my-integrations
2. Нажми **+ New integration**
3. Название: `altacasa-bot`, тип: Internal
4. Скопируй **Internal Integration Token** → вставь в `.env` как `NOTION_TOKEN`
5. В Notion открой базу **Клиенты** → `...` → **Connections** → добавь `altacasa-bot`

---

## Шаг 2 — Получить Anthropic API Key

1. Зайди на https://console.anthropic.com
2. API Keys → Create Key
3. Вставь в `.env` как `ANTHROPIC_API_KEY`

---

## Шаг 3 — Настроить .env

```bash
cp .env.example .env
# Открой .env и заполни все значения
```

Токен бота (`TG_TOKEN`) уже заполнен — это `@altacasacn_bot`.

---

## Шаг 4 — Установить и запустить

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python bot.py
```

---

## Шаг 5 — Запуск на сервере (опционально, для 24/7)

Рекомендуем VPS Hetzner CX11 (~4€/мес):

```bash
# Установить screen
sudo apt install screen

# Запустить в фоне
screen -S altacasa_bot
python bot.py
# Ctrl+A, D — отсоединиться (бот продолжает работать)

# Вернуться к логам
screen -r altacasa_bot
```

Или через systemd:
```bash
sudo nano /etc/systemd/system/altacasa.service
```
```ini
[Unit]
Description=AltaCasa Telegram Bot
After=network.target

[Service]
WorkingDirectory=/opt/altacasa_bot
ExecStart=/usr/bin/python3 bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl enable altacasa && sudo systemctl start altacasa
```

---

## Структура Notion — база "Клиенты"

Бот автоматически заполняет:
| Поле | Что пишет |
|------|-----------|
| Name | Имя из Telegram |
| Telegram ID | числовой ID |
| Telegram | ссылка @username |
| Канал | Telegram |
| Квалификация | Холодный/Тёплый/Горячий/Передан менеджеру |
| Интерес | Диваны/Кресла/Столики/Комплект/Другое |
| Бюджет ₽ | если клиент назвал |
| Диалог с ботом | последние 10 сообщений |
| Эскалировать | ✅ если горячий лид |

---

## Команды бота

- `/start` — начать диалог (создаёт запись в Notion)
- `/reset` — сбросить историю диалога

---

## Стоимость работы

| Компонент | Стоимость |
|-----------|-----------|
| Claude Haiku (AI) | ~$0.001 за диалог |
| Notion API | Бесплатно |
| Telegram Bot API | Бесплатно |
| VPS сервер | ~4€/мес |

При 100 диалогах в месяц — расходы на AI < $1.
