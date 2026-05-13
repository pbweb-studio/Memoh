# Chat stats native plan

## 1. Goal

Универсальный **Memoh-native / overlay-first** механизм учёта и отчётности по **нескольким** Telegram-группам (типы: leads, sales, tasks, support, client_updates, custom), без правок **protected core** и без использования **Memory** как source of truth для сырых лидов.

Целевой поток: пассивные сообщения остаются в штатной истории Memoh → чат регистрируется как источник статистики → периодически или по запросу извлекаются структурированные события → пишутся в **`/data/studio/events/*.jsonl`** → из **control**-чата запрашивается агрегированный отчёт по дню / по чату / по типу.

## 2. Current facts

- **Passive ingest** для Telegram-групп работает: сообщения попадают в **`bot_history_messages`** и связанные **`bot_session_events`** (подтверждено диагностикой на проде).
- **Cross-chat** вопрос из управленческого чата **не** подмешивает автоматически полный сырой лог другой группы в контекст LLM; **Qdrant `memory_sparse`** для фрагментов лида **пуст** (извлечение в долговую память не произошло).
- **`/data/studio/events*`** в текущем виде **не** заполняются автоматически из пассивного трафика — для отчётности нужен **явный overlay-пайплайн** (skills / schedule / API-sidecar), описанный ниже.
- Для примера «Лидоруб»: известны безопасные идентификаторы **`telegram_chat_id`**, **`session_id`**, **`route_id`** (использовать как эталон связки «внешний чат → сессия Memoh» в реестре).

## 3. Documented Memoh mechanisms

| mechanism | docs/code reference | what it can do | limits | relevance |
|-----------|---------------------|----------------|--------|------------|
| **Группы + `discuss`** | [sessions.md](../docs/getting-started/sessions.md) | Пассивный трафик сохраняется; ответ бота в группу только при явном `send`. | Нет автоматического «видеть другой чат» в одном turn. | Базовая модель Telegram-групп. |
| **История сообщений бота** | `GET /api/bots/{bot_id}/messages` — см. [swagger.yaml](../../spec/swagger.yaml) (`/bots/{bot_id}/messages`); реализация: [message.go](../../internal/handlers/message.go) `ListMessages` | Пагинация `limit` / `before`; при наличии **`session_id`** — выборка **по сессии** (`ListLatestBySession` / `ListBeforeBySession`). | В коде лимит по умолчанию 30, макс. 100 за запрос; OpenAPI может **не отражать** `session_id` (расхождение со swagger — проверять код/живой API). | **Sidecar / overlay** может читать историю по `session_id` за день постранично. |
| **Поиск по истории в рантайме агента** | [history.go](../../internal/agent/tools/history.go), подсказки: [_contacts.md](../../internal/agent/prompts/_contacts.md) | Инструменты **`list_sessions`**, **`search_messages`** (фильтры `start_time`/`end_time`, `keyword`, `session_id`, …). | В [NATIVE_RUNTIME_AUDIT_RESULTS.md](./NATIVE_RUNTIME_AUDIT_RESULTS.md) зафиксированы ограничения **Search history** vs UI-поиск; не гарантировать 100% recall по произвольным токенам. | **Option B**: отчёт и экстракция из control/schedule через инструменты агента. |
| **Memory provider** | [memory.md](../docs/getting-started/memory.md) | Retrieval релевантных записей между сессиями; «From conversation». | Не индексирует автоматически каждый пассивный текст; **не** догма SoT для лидов. | Только вспомогательный контекст, **не** база лидов. |
| **Файлы контейнера** | [files.md](../docs/getting-started/files.md) | UI + агент через skills/MCP читает/пишет файлы. | Нужна дисциплина конкурентной записи (append, lock-паттерн в skill). | **`/data/studio/*`** как SoT. |
| **Managed skills** | [skills.md](../docs/getting-started/skills.md) | `/data/skills/<name>/SKILL.md`, политики поведения и tool-use. | Имя skill — идентичность; дубликаты `effective/shadowed`. | Политика init/report/ACL в overlay. |
| **Schedule** | [schedule.md](../docs/getting-started/schedule.md), `POST /api/bots/{bot_id}/schedule` | Cron → NL-команда агенту с инструментами; доставка в каналы через `send` и т.д. | Таймзона сервера (UTC по умолчанию); лимиты `max_calls`. | Ночной extraction + утренний digest. |
| **Slash commands** | [slash-commands.md](../docs/getting-started/slash-commands.md) | Встроенные `/help`, `/new`, `/schedule`, … | Неизвестная строка **`/foo`** — обычное сообщение (не перехватывается ядром). | **`/studio_init`** без core — **не** нативная команда; нужен **skill-триггер** или NL. |
| **ACL** | [access.md](../docs/getting-started/access.md) | Правила allow/deny по identity / channel / conversation. | Не заменяет бизнес-логику «кто видит отчёт»; для тонкого RBAC отчётов — политика в skill + реестр. | Ограничить клиентские чаты; owner/admin bypass. |
| **Studio overlay paths** | [STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md](./STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md), [NATIVE_AUDIT_TELEGRAM_MEMORY_PEOPLE.md](./NATIVE_AUDIT_TELEGRAM_MEMORY_PEOPLE.md) | Реестры `/data/studio/*.json`, skills, файлы как SoT. | Sidecar только при gap без RFC. | Архитектурный каркас. |

## 4. Proposed architecture

```text
Telegram group (discuss)
    → passive persist (уже есть: bot_history_messages / bot_session_events)
    → /studio_init (overlay): запись в stat registry (/data/studio/stat_sources.json + chats.json mirror)
    → extraction job:
          preferred: Schedule → NL → agent tools (list_sessions / search_messages) + parse → append JSONL
          alternate: sidecar → Memoh HTTP API GET .../messages?session_id&before (pagination)
    → /data/studio/events/{type}/{date}.jsonl  (SoT для аналитики)
    → report request (control chat): agent читает JSONL + registry → формирует ответ → send только в control
```

**Принцип SoT:** числа и списки лидов — только из **`/data/studio/events`** (+ опционально кэш-агрегаты в отдельном файле). **Memory** — не хранилище лидов.

## 5. Chat registry

Рекомендуется **два** файла (разделение ответственности):

### 5.1 `/data/studio/stat_sources.json`

Машинно-читаемый реестр источников статистики (SoT для пайплайна).

```json
{
  "version": 1,
  "sources": [
    {
      "id": "src_leads_lidorub",
      "type": "leads",
      "enabled": true,
      "telegram_chat_id": "-5126105025",
      "title": "Лидоруб PB х Бионика",
      "memoh_session_id": "f745d4af-b869-4b65-968c-7c726c323707",
      "memoh_route_id": "aa213be8-7d0c-45bf-897f-ed4019312f44",
      "owner_channel_identity_id": "",
      "allowed_control_targets": [
        { "channel": "telegram", "conversation_id": "-1003903704506" }
      ],
      "report_rules": {
        "timezone": "Europe/Moscow",
        "day_boundary": "00:00",
        "keywords_mark_target": ["Целевой", "целевой"]
      },
      "created_at": "2026-05-13T00:00:00Z",
      "updated_at": "2026-05-13T00:00:00Z"
    }
  ]
}
```

### 5.2 `/data/studio/chats.json` (опционально)

Человеко-ориентированный alias-файл («лидоруб» → `source_id`) для NL-запросов из control; может дублировать subset полей. **Не** обязателен, если в skill жёстко маппить nicknames из `stat_sources.title`.

**Типы `type`:** `leads` | `sales` | `tasks` | `support` | `client_updates` | `custom` (строка; для `custom` в `report_rules` хранить произвольные hints).

## 6. Initialization flow

| команда / фраза | native без core? | overlay механизм |
|-----------------|------------------|------------------|
| `/studio_init leads` | **Нет** как встроенный slash | Skill: если сообщение начинается с `/studio_init` **или** NL «инициализируй этот чат как …» — выполнить протокол записи в `stat_sources.json` через **file/workspace tools** (и подтвердить `send` в текущий чат). |
| `/studio_status` | Аналогично | Skill + чтение JSON. |
| `/studio_disable` | Аналогично | Skill: `enabled:false`. |
| `/studio_report today` | Аналогично | Skill: проверить, что текущий target ∈ `allowed_control_targets`, затем прочитать JSONL и ответить. |

**Шаги init (логика skill, не код ядра):**

1. Убедиться, что сообщение из **группы** (`conversation_type=group`) и отправитель **owner/admin** (политика skill; опционально сверка с `/access` в инструкциях для оператора).
2. Взять **текущий** `telegram_chat_id` / title из контекста turn (Memoh уже знает маршрут; в skill описать: после init попросить однократно `list_sessions` и сопоставить route — **или** оператор вручную дописывает `session_id` при первом сбое сопоставления).
3. Записать/обновить запись в **`stat_sources.json`**.
4. Ответ в чат: шаблон подтверждения (как в ТЗ).

**Ручной fallback:** правка `stat_sources.json` через вкладку **Files** ([files.md](../docs/getting-started/files.md)).

## 7. Leads event schema

Файл: `/data/studio/events/leads/YYYY-MM-DD.jsonl` — одна JSON-строка = одно извлечённое событие (не обязательно 1:1 с сырой строкой чата).

Рекомендуемые поля:

| поле | тип | описание |
|------|-----|----------|
| `schema_version` | int | Начать с `1`. |
| `source_id` | string | Ссылка на запись в `stat_sources.json`. |
| `telegram_chat_id` | string | Копия для удобства grep. |
| `memoh_session_id` | string | Для трассировки. |
| `raw_message_id` | string | `external_message_id` / platform id, если доступен из истории. |
| `observed_at` | string (ISO-8601) | Время сообщения в UTC или с `timezone` из rules. |
| `phone` | string? | Нормализованный номер или null. |
| `person_name` | string? | |
| `city` | string? | |
| `is_target` | bool | «Целевой» маркер. |
| `status_text` | string | Короткий статус («актуально», «ждём лайнеры», …). |
| `call_window` | object? | `{ "kind": "today"|"tomorrow"|"datetime", "note": "..." }` |
| `flags` | string[] | Например `["no_phone"]`. |
| `raw_excerpt` | string | Усечённая цитата (без секретов; длина лимит в skill). |

Экстрактор **не** обязан валидировать телефон идеально на MVP — достаточно стабильного JSON для отчёта.

## 8. Daily report behavior

**Вход:** `stat_sources.json` + `events/leads/YYYY-MM-DD.jsonl` (+ при необходимости прошлые сутки для «вчера»).

**Агрегация (логика skill / schedule-команды):**

- Фильтр по `source_id` или по `type=leads` и всем enabled источникам.
- Метрики MVP: число `is_target=true` за календарный день; список лидов с телефоном; список без телефона; разбивка по `call_window.kind`.
- Ответ только в **control**-чат: перед генерацией skill проверяет, что текущий `send` target разрешён в `allowed_control_targets`.

**Ошибки:** если JSONL за день отсутствует — честно сообщить «экстракция не запускалась / нет событий», не подменять сырым `search_messages` без явного режима «emergency audit» (чтобы не смешивать SoT).

## 9. Implementation options

### Option A — manual UI / оператор

- **Pros:** нулевой риск автоматизации; полный контроль.
- **Cons:** не масштабируется на много чатов.
- **Update-safety:** максимальная.
- **Effort:** низкий для MVP отчёта, высокий по времени людей.
- **Risk:** человеческий фактор.

### Option B — managed skill + Files + Schedule (+ `search_messages`)

- **Pros:** полностью внутри Memoh; Schedule штатный ([schedule.md](../docs/getting-started/schedule.md)); чтение/запись SoT через Files ([files.md](../docs/getting-started/files.md)); история через **`search_messages`** ([_contacts.md](../../internal/agent/prompts/_contacts.md)).
- **Cons:** ограничения **Search history** (см. [NATIVE_RUNTIME_AUDIT_RESULTS.md](./NATIVE_RUNTIME_AUDIT_RESULTS.md)); возможны пропуски редких токенов; длинные дни → много tool-rounds.
- **Update-safety:** высокая (без деплоя core).
- **Effort:** средний (качество skill + тесты сценариев).
- **Risk:** средний (качество извлечения + стоимость LLM).

### Option C — sidecar (small service) + Memoh HTTP API

- **Pros:** детерминированная пагинация `GET /bots/{bot_id}/messages?session_id=…&before=…` ([message.go](../../internal/handlers/message.go)); не зависит от recall `search_messages`.
- **Cons:** отдельный процесс, секреты API (хранить вне репозитория; не в этом шаге); сопровождение.
- **Update-safety:** зависит от стабильности публичного API (сейчас `session_id` поддержан в коде).
- **Effort:** средний/высокий.
- **Risk:** низкий по данным, средний по эксплуатации.

### Option D — изменение core (новый pipeline hook, slash, индексация)

- **Pros:** идеальная интеграция.
- **Cons:** **запрещено** без RFC; ломает upstream-compat.
- **Risk:** высокий.

## 10. Recommended MVP

**Гибрид B → при drift качества C:**

1. **SoT:** `stat_sources.json` + `events/leads/*.jsonl` под `/data/studio/`.
2. **Init:** managed skill «studio-chat-stats» с триггерами `/studio_init …` и NL; запись через file tools; ручной **Files** fallback.
3. **Extraction:** nightly **Schedule** с командой вида: «Для каждого enabled `type=leads` в stat_sources за вчера вызови `search_messages` с `session_id` и окном времени; дополни JSONL только новыми `raw_message_id`».
4. **Report:** в control — NL вопрос; skill читает JSONL, не Memory.
5. Если за неделю видны пропуски событий — спланировать **Option C** как read-only sidecar, пишущий только JSONL (ядро не трогать).

## 11. Acceptance checklist

- [ ] Добавить бота в **новую** тестовую группу, включить пассив (как сейчас).
- [ ] Выполнить **init** (`/studio_init leads` или NL) → подтверждение в чате → запись в `stat_sources.json`.
- [ ] Отправить **3** тестовых сообщения с маркером «Целевой…».
- [ ] Дождаться Schedule или вручную запустить extraction-команду → появился/обновился **`events/leads/{date}.jsonl`**.
- [ ] Из **control**-чата запросить отчёт за сегодня по имени чата / `source_id` → корректные числа.
- [ ] Из **клиентского** чата (не в `allowed_control_targets`) запросить отчёт → **отказ** или нейтральный ответ без цифр (по политике skill).

## 12. Open questions

1. **Точное сопоставление** `telegram_chat_id` → `session_id` без ручного шага: нужен ли операторский «первый sync» через `list_sessions`, или достаточно логов маршрутизатора?
2. **Swagger vs код:** зафиксировать в тикете обновление OpenAPI для `session_id` на `GET /bots/{bot_id}/messages`, чтобы sidecar не полагался только на чтение Go.
3. **Конкурентная запись JSONL:** нужен ли паттерн «один writer» (только schedule) vs допуск append из группы (риск гонок)?
4. **Нормализация телефонов / PII:** политика хранения excerpt в JSONL (ретеншн) — юридический слой, не только технический.
5. **Нагрузка на LLM:** лимиты токенов при большом объёме `search_messages` за день — возможно разбиение по часам в команде Schedule.

---

**Примечание:** этот документ — **проектирование**; реализация skills/Schedule без изменения core и без выкладки на этом шаге.
