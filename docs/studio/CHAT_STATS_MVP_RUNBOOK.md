# Chat stats MVP — runbook (Studio Jarvis)

Overlay для учёта лидов и отчётов без правок Memoh core. Полная архитектура: [CHAT_STATS_NATIVE_PLAN.md](./CHAT_STATS_NATIVE_PLAN.md).

## 1. Где лежат файлы (SoT)

| Путь | Назначение |
|------|------------|
| `/data/studio/stat_sources.json` | Реестр stat-чатов: `id`, `type`, `title`, **`aliases`** (опционально), `session_id`, `report_visibility`, `local_commands`. |
| `/data/studio/events/leads-YYYY-MM-DD.jsonl` | События за календарный день (одна строка = один JSON). **Не** Memory. |

В контейнере агента **`/data/studio`** — это **workspace bridge** к каталогу бота на хосте. **Canonical SoT на хосте (типичный Docker Compose Memoh):**

`/var/lib/docker/volumes/memoh_memoh_data/_data/workspace-data/<bot_id>/studio`

Отдельный volume **`memoh_memoh_studio`**, смонтированный в **`memoh-server`** как `/data/studio`, **часто не совпадает** с деревом, которое видит Jarvis через Files/read для того же бота. **Не используйте `memoh_memoh_studio/_data` как SoT для импорта/отчётов**, пока не проверите через **Files/read**, что это действительно тот же путь.

Импорт Telegram HTML и любые правки `stat_sources.json` / `events/leads-*.jsonl` должны выполняться с **`--studio-dir`**, указывающим на **canonical workspace-data** (или с эквивалентным `/data/studio` внутри контейнера агента через `exec` — см. skill **`studio-telegram-import`**).

## 2. Зарегистрировать новый stat-чат

1. Добавьте бота в Telegram-группу, убедитесь что passive-сообщения сохраняются (см. логи `passive_saved=true`).
2. Узнайте `session_id` / `route_id` (Web UI → сессии, или лог ingest, или `list_sessions` в чате).
3. Скопируйте шаблон из репозитория: `deploy/studio-jarvis-native/data/stat_sources.example.json` → через **Files** вставьте новый объект в массив `sources` (или отредактируйте существующий).
4. В группе отправьте **`/studio_init leads`** или фразу «инициализируй этот чат как чат лидов» — обрабатывает managed skill **`studio-chat-stats`** (не ядро Memoh).
5. Проверьте ответ бота и содержимое `stat_sources.json`.

## 3. Установить / обновить skill `studio-chat-stats`

1. **Settings → Bot → Skills → New Skill** (или редактирование существующего).
2. Вставьте полный текст `deploy/studio-jarvis-native/skills/studio-chat-stats/SKILL.md` (frontmatter + тело). Сохраните.
3. Убедитесь, что skill **Effective** и не shadowed.

Альтернатива: `POST /api/bots/{bot_id}/container/skills` с массивом строк markdown — см. `deploy/studio-jarvis-native/RUNBOOK.md` §8.

## 4. Проверить passive ingest

- В логах `memoh-server`: `ingested=true`, `passive_saved=true` для группы.
- В UI или через `search_messages` по `session_id` видны пользовательские сообщения с маркером «Целевой».

## 5. Заполнить events (JSONL)

- **Импорт Telegram HTML export:** см. раздел **«Telegram HTML export import»** ниже и managed skill **`studio-telegram-import`** (`deploy/studio-jarvis-native/skills/studio-telegram-import/SKILL.md`).
- **Авто (из переписки Memoh):** попросите бота в Web UI или в чате выполнить извлечение: skill **`studio-chat-stats`** использует `search_messages` и **`write`** в `/data/studio/events/leads-YYYY-MM-DD.jsonl`.
- **Ручная загрузка:** через Files создайте/вставьте строки по образцу `deploy/studio-jarvis-native/data/events/leads-2026-05-13.example.jsonl`.

## 6. Запросить отчёт

### 6.1 Режимы

- **Local:** запрос из **того же** Telegram-чата, что и зарегистрированный source с `report_visibility.local_chat=true` — отчёт только по **`source_id`** этого чата на выбранную дату.
- **Control:** запрос из чата, чей id входит в **`control_chats`** хотя бы одного source — можно спросить отчёт **по одному** source (совпадение по `title`, **`aliases[]`**, `source_id`, `session_id`) или **по всем** `type=leads` с `enabled=true`, разрешённым для этого control.

### 6.2 Примеры фраз (generic)

| Смысл | Пример формулировки |
|--------|---------------------|
| Сегодня в рабочем чате | «Подбей статистику за сегодня», «сколько целевых сегодня», «отчёт по лидам за сегодня» |
| Конкретная дата | «Статистика целевых за 13.05.2026», «сколько лидов было 13.05.2026» |
| Из control по названию / алиасу | «Сводка по лидорубу за 13.05.2026» (если в `stat_sources` заданы `aliases` или уникальный `title`) |
| Агрегат | «По всем чатам лидов за сегодня» |

Условия: `report_visibility.local_chat` / `control_chats` должны совпадать с фактическими `conversation_id`.

### 6.3 Регрессия (один известный чат на стенде)

Проверка, что overlay не сломан:  
**«Подбей статистику целевых за 13.05.2026 по чату Лидоруб PB х Бионика»** — результат должен совпадать с содержимым **`leads-2026-05-13.jsonl`** после импорта/dedupe для `source_id` этого чата.

## 7. Отключить чат

- `/studio_disable` в чате **или** правка JSON: `"enabled": false` для нужного `source`.

## 8. «Бот не видит историю»

Возможные причины:

1. **Нет JSONL** — отчёт должен честно сказать «нет событий»; выполните извлечение (п. 5).
2. **`search_messages` не находит токен** — см. `docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md`; тогда временно доберите события вручную в JSONL или запланируйте sidecar по HTTP API `GET /api/bots/{bot_id}/messages?session_id=...` (без правок core).
3. **Чат не в реестре** — Jarvis не знает, что это stat-чат; выполните `/studio_init`.
4. **Запрос из запрещённого чата** — ожидаемый отказ без цифр.

## 9. Telegram HTML export import

Используйте, когда нужна **полная прошлая история** чата. **Telegram Bot API не отдаёт старую историю** участникам как «скачать весь чат» — для прошлого нужен **экспорт из Telegram Desktop**.

### 1) Как экспортировать (Telegram Desktop)

1. Откройте нужный чат в **Telegram Desktop**.
2. **⋯** (меню) → **Export chat history**.
3. Формат: **HTML** (не JSON для этого overlay).
4. Сохраните папку; нужен файл **`messages.html`**.

**Перед импортом (обязательно):**

1. Через **Files/read** убедитесь, что **`/data/studio/events/state/events_active.json`** и **`/data/studio/stat_sources.json`** читаются там, куда вы пишете.
2. Запускайте importer с **`--studio-dir /data/studio`** в **`exec`** (внутри контейнера агента) **или** на хосте с путём  
   `/var/lib/docker/volumes/memoh_memoh_data/_data/workspace-data/<bot_id>/studio`.  
   **Не** используйте по умолчанию `memoh_memoh_studio/_data` для SoT этого бота без проверки bridge.
3. Скрипт **`import_telegram_html.py`** откажется писать в путь с **`memoh_memoh_studio`**, если не передан **`--allow-noncanonical-studio-dir`** (аварийный режим).

### 2) Как загрузить Jarvis (Memoh Web UI)

1. Откройте чат с ботом в Web UI.
2. Прикрепите **`messages.html`** к сообщению (как файл).
3. Напишите обычным языком, например:  
   **«Импортируй этот экспорт Telegram как лиды»** / **«Импортируй историю чата лидоруба»**.

В контекст агента попадёт путь вида **`<attachment path="/data/media/.../messages.html"/>`** — его использует skill **`studio-telegram-import`**.

**Fallback (если вложение недоступно агенту):** загрузите файл через **Files** в  
`/data/studio/imports/inbox/messages.html`  
и напишите: **«Импортируй `/data/studio/imports/inbox/messages.html` как leads»**.

### 3) Что делает Jarvis

1. Проверяет, что файл похож на Telegram HTML export.
2. Запускает **`python3 /data/studio/tools/import_telegram_html.py`** через инструмент **`exec`** (может потребоваться **approval** в UI).
3. Скрипт:
   - читает заголовок чата из `page_header` и сопоставляет с **`stat_sources.json`** (или создаёт **draft** при `--auto-register-draft`);
   - пишет нормализованные сообщения в  
     **`/data/studio/imports/telegram/<slug>/messages.normalized.jsonl`**;
   - пишет события в **`/data/studio/events/leads-YYYY-MM-DD.jsonl`** (`target_lead`, `summary_report`, `operational_note`), **без дублирования** по `event_id` и **без смысловых дублей** `target_lead` (дополнительно по ключу `source_id` + `date` + телефон или имя+город);
   - создаёт **`import-summary.json`** рядом с нормализованным JSONL.

Одноразовая чистка уже записанного дня на сервере:  
`python3 /data/studio/tools/import_telegram_html.py --dedupe-jsonl /data/studio/events/leads-YYYY-MM-DD.jsonl` (из контейнера агента или с host-путём к canonical `studio/events/...`).

### 4) Как Jarvis «понимает» чат

По **названию** из HTML и записи в **`stat_sources.json`** (`title`, `id`, `type`, `session_id`, …). Если совпадения нет и включён draft-режим — появится запись с **`enabled: false`**, **`needs_review: true`**, полем **`import_slug`**.

### 5) Где лежат результаты

| Путь | Содержимое |
|------|------------|
| `/data/studio/imports/telegram/<slug>/messages.normalized.jsonl` | Нормализованные сообщения (одна строка = JSON). |
| `/data/studio/imports/telegram/<slug>/import-summary.json` | Сводка импорта (числа, даты, warnings). |
| `/data/studio/events/leads-YYYY-MM-DD.jsonl` | События для отчётов (**SoT** для цифр). |

### 6) Как проверить статистику

После импорта — skill **`studio-chat-stats`**, например:  
**«Подбей статистику целевых за 13.05.2026 по чату Лидоруб PB х Бионика»**.

### 7) Draft source и `needs_review`

**Draft** — запись в `stat_sources.json`, которую импортёр добавил, когда не нашёл существующий чат. Она **выключена** (`enabled: false`) и помечена **`needs_review: true`**, чтобы администратор заполнил `telegram_chat_id` / `session_id` / `route_id` и включил чат.

### 8) Ограничения

- **Bot API** не заменяет HTML export для длинной истории.
- Импортёр не трогает **`events/state/events_active.json`** и **`people.md`**.
- Не храните реальные PII-выгрузки в git.

## 10. Рестарт сервера

При изменении только **`/data/studio/*`** и managed skills **рестарт memoh-server не обязателен**.
