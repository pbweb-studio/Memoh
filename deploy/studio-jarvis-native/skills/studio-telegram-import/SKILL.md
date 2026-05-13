---
name: studio-telegram-import
description: "Импорт истории из Telegram Desktop HTML export (messages.html) в /data/studio/events через overlay-скрипт и exec."
---

# Studio — импорт Telegram HTML export

## Роль

Ты помогаешь **одним запросом** перенести выгрузку **Telegram Desktop → Export chat history → HTML** в нативные события Studio:

- **`/data/studio/events/leads-YYYY-MM-DD.jsonl`** — `target_lead`, `summary_report`, `operational_note`;
- **`/data/studio/imports/telegram/<slug>/`** — нормализованные сообщения и `import-summary.json`;
- при необходимости — **черновик** в **`stat_sources.json`** (`enabled: false`, `needs_review: true`).

**Memory не использовать** как SoT для цифр; после импорта отчёты — только из JSONL (skill **`studio-chat-stats`**).

## Важно про Telegram Bot API

Бот **не может** прочитать «старую» историю чата через Bot API. Для прошлого нужен **HTML export** из Telegram Desktop. Не предлагай «подтянуть историю через API».

## Когда срабатывает skill

Запросы вроде:

- «импортируй экспорт Telegram»
- «импортируй эту историю чата как лиды / лидоруб»
- «это история чата лидов, импортируй»
- «импортируй `/data/studio/imports/inbox/messages.html` как leads»

## Шаг 1 — путь к HTML

1. В тексте пользователя найди XML user header: **`<attachment path="..."/>`** — это **контейнерный путь** к загруженному `messages.html` (часто под `/data/media/...`).
2. Если вложений нет, но пользователь дал **абсолютный путь** к файлу в workspace — используй его (типичный fallback: **`/data/studio/imports/inbox/messages.html`**).
3. Если пути нет — коротко попроси: загрузить файл в чат **или** положить в **`/data/studio/imports/inbox/`** через Files и прислать путь.

## Шаг 2 — быстрая проверка, что это Telegram export

Вызови **`read`** с **`n_lines`** (например 80) по пути из шага 1. Должны быть признаки: `history`, `message`, `pull_right date details`, `from_name`. Если не похоже — не запускай импорт, объясни.

## Шаг 3 — запуск importer (основной путь)

Используй инструмент **`exec`** (может потребоваться **approval** в UI — это нормально для `exec`).

Рабочая директория по умолчанию: **`/data`**. Скрипт установлен в runtime по пути:

**`/data/studio/tools/import_telegram_html.py`**

### Команда (шаблон)

Подставь `<INPUT_PATH>` из шага 1 и при необходимости `--source-id` / `--auto-register-draft`.

```bash
python3 /data/studio/tools/import_telegram_html.py \
  --input "<INPUT_PATH>" \
  --studio-dir /data/studio \
  --source-type leads \
  --source-id leads-lidorub-pb-bionika \
  --telegram-chat-id -5126105025 \
  --session-id f745d4af-b869-4b65-968c-7c726c323707 \
  --route-id aa213be8-7d0c-45bf-897f-ed4019312f44
```

Если пользователь **не указал** конкретный `source_id`, а чат новый:

```bash
python3 /data/studio/tools/import_telegram_html.py \
  --input "<INPUT_PATH>" \
  --studio-dir /data/studio \
  --source-type leads \
  --auto-register-draft
```

Если **`python3` в exec недоступен** (ошибка not found):

1. Попроси пользователя **один раз** выполнить на VPS (см. `deploy/studio-jarvis-native/RUNBOOK.md` § «Telegram HTML import — fallback») — **без** перезапуска `memoh-server`;
2. либо используй уже загруженный файл в **`/data/studio/imports/inbox/messages.html`** и тот же runbook.

## Шаг 4 — ответ пользователю

После успешного `exec`:

1. **`read`** файл **`/data/studio/imports/telegram/<slug>/import-summary.json`** (путь к slug возьми из stdout JSON поля `import_slug` и шаблона `imports/telegram/<slug>/import-summary.json`, либо из поля `normalized_path` — каталог рядом).
2. Ответь **обычным языком**:
   - какой **чат** распознан (`source_chat`);
   - сколько **сообщений** нормализовано (`normalized_messages`);
   - сколько **`target_lead`** и **`summary_report`**;
   - **даты**, где появились/обновились `leads-YYYY-MM-DD.jsonl` (ключи `days`);
   - есть ли **`warnings`** (например, не заполнены `session_id` в draft);
   - как проверить отчёт: «Подбей статистику целевых за ДД.ММ.ГГГГ по чату …» (skill **`studio-chat-stats`**).

## Запреты

- Не выдумывай числа до запуска импорта / чтения summary.
- Не правь **`/data/studio/events/state/events_active.json`** и **`people.md`**.
- Не коммить `messages.html` и JSONL в git (это не твоя задача в чате).
