---
name: studio-stat-onboarding
description: "NL-инициализация нового stat-чата: stat_sources.json, list_sessions, опционально report_schemas; без обязательного exec."
---

# Studio — onboarding stat-чата (leads)

## Роль

Ты помогаешь **один раз** зарегистрировать Telegram-группу как **stat source** типа **`leads`**: корректные `session_id`, `route_id`, `telegram_chat_id`, `report_visibility`, при необходимости **`report_schema_ref`**.

- **SoT:** **`/data/studio/stat_sources.json`** (+ опционально **`/data/studio/report_schemas/*.json`**).
- **Отчёты и подсчёт лидов** — в managed skill **`studio-chat-stats`**; здесь только **регистрация** и краткое подтверждение в чате.

**`exec` в Phase 1 не обязателен** — все шаги через **`read` / `write` / `list`** (и при необходимости **`edit`**) по workspace.

## Триггеры (смысл)

- «зарегистрируй этот чат для статистики», «сделай этот чат чатом лидов», «инициализируй studio для лидов здесь»;
- пользователь явно просит помочь **первичной настройке** без запроса отчёта за дату.

Если пользователь уже просит **цифры за день** — делегируй формулировкой: «отчёт сформирует **`studio-chat-stats`** после регистрации», и при отсутствии записи сначала выполни onboarding.

## Инструменты

- **`list_sessions`** — сопоставить название чата / платформу с `session_id` и при необходимости `route_id`, если пользователь не вставил UUID.
- **`read`** `deploy/studio-jarvis-native/data/stat_sources.example.json` **недоступен из рантайма** — ориентир по полям возьми из памяти skill: см. репозиторий оператора `stat_sources.example.json` (в чате можно кратко перечислить обязательные поля: `id`, `type`, `title`, `telegram_chat_id`, `session_id`, `route_id`, `enabled`, `report_visibility`, опционально `aliases`, `local_commands`, `allowed_requesters`, **`report_schema_ref`**).

В рантайме **`read`** `/data/studio/stat_sources.json` перед записью; **`write`** / **`edit`** — аккуратно, с валидным JSON (массив `sources[]`, `version`).

## Шаги (обязательный порядок)

1. Убедись, что запрос про **регистрацию** stat-чата (не про отчёт). Если неясно — задай **один** короткий вопрос.
2. **`read`** `/data/studio/stat_sources.json`. Если файла нет — создай минимальный объект `{"version":1,"sources":[]}` (или по политике команды).
3. Собери идентификаторы текущего чата:
   - из метаданных turn (предпочтительно): `telegram_chat_id`, `conversation_id`, `session_id`, `route_id` если доступны;
   - иначе **`list_sessions`** и выбери сессию, совпадающую с названием / платформой **Telegram**.
4. Сформируй **новый** объект `source`:
   - уникальный **`id`**: например `leads-<slug-из-title>` (латиница, дефисы);
   - **`type`**: `leads`;
   - **`title`**: человекочитаемое имя группы (уточни у пользователя при двусмысленности);
   - **`enabled`**: `true` по умолчанию;
   - **`report_visibility`**: `local_chat: true` для рабочей группы; **`control_chats`**: массив строк `conversation_id` управленческих чатов (спроси или используй политику из тикета; не выдумывай id);
   - опционально **`aliases`**, **`local_commands`**, **`allowed_requesters`**, **`report_rules`** — по политике.
5. **Опционально `report_schema_ref`:** если команда использует схемы — подскажи оператору скопировать в Files шаблоны из репозитория:
   - `deploy/studio-jarvis-native/data/report_schemas/leads.v1.example.json` → `/data/studio/report_schemas/leads.v1.json` (или другое имя);
   - при необходимости `daily_metrics.v1.example.json` — отдельный файл для дневных агрегатов.
   Затем пропиши в `source` строку **`report_schema_ref`** с **абсолютным** путём под `/data/studio/...`. Без файла схемы поле **не** задавай.
6. Вставь объект в `sources[]` (без дубликата по **`id`** или по паре `telegram_chat_id`+`type` — если уже есть, **обнови** существующий и объясни пользователю).
7. **`write`** / **`edit`** сохранённый JSON. Кратко подтверди в чате: `id`, `title`, куда писать события (`events/leads-YYYY-MM-DD.jsonl`), что отчёты — skill **`studio-chat-stats`**.

## Запрещено

- Считать **Memory** источником правды по лидам.
- Писать в **`memoh_memoh_studio`** или произвольный mount без подтверждения, что это тот же workspace, что **`/data/studio`** для бота (см. **`studio-telegram-import`** / RUNBOOK: canonical `workspace-data/<bot_id>/studio`).
- Требовать **`exec`** для завершения onboarding в Phase 1.

## Связь с другими skills

- **`studio-chat-stats`** — отчёты и дозапись JSONL.
- **`studio-telegram-import`** — импорт истории Telegram Desktop HTML в JSONL.
