# Studio Jarvis — native MVP implementation plan

**Ветка:** `studio/native-baseline-20260512`  
**Архив (только reference):** `studio/archive-heavy-fork-20260512-1245` — `git show`, **не** merge source.  
**Связанные документы:** [`NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md`](./NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md), [`STUDIO_RESTORE_DECISION_MATRIX.md`](./STUDIO_RESTORE_DECISION_MATRIX.md), [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md), [`STUDIO_LAYER_SEPARATION_PLAN.md`](./STUDIO_LAYER_SEPARATION_PLAN.md), [`NATIVE_CAPABILITY_AUDIT_PLAN.md`](./NATIVE_CAPABILITY_AUDIT_PLAN.md).  
**Аудит runtime (коммиты):** `29830b3a` (Telegram group), `73786070` (Schedule).

---

## A. MVP goal

**Studio Jarvis v1** на **чистом Memoh core** должен уметь **без** возврата heavy fork:

1. **Идентичность людей** — ответы по `@handle` / ролям из явного SoT-файла + память как доп. контекст (Web, **Telegram DM**, **Telegram group через mention**).  
2. **Операционный контур проекта** — проекты, чаты, задачи из **JSON-реестров** в workspace; строгие запросы «только из файла» работают.  
3. **Канал Telegram** — Platforms + ACL; группа: **`discuss`** (молчание без mention — норма, если нет отдельного ТЗ).  
4. **Периодика** — **Schedule** для digest/напоминаний (cron + NL `command`); опционально **Heartbeat** для фона.  
5. **Дисциплина ответов** — skills задают приоритет файлов vs memory, запрет на выдумывание записей реестра.

**Не входит в MVP v1:** Studio Control Mini App внутри monolith, Go-резолвер людей, кастомный inbound/ModeQueue, sqlc/store people, packer hooks, harvester/cron из archive.

---

## B. Architecture

```text
Clean Memoh core (upstream-first; без патчей по умолчанию)
  ├── Providers / Models        → UI Bot Detail (General)
  ├── Telegram Platform         → Platforms → Save and enable
  ├── Access / ACL              → Access tab + /access
  ├── Memory provider           → Memory tab + retrieval между сессиями
  ├── Files workspace           → /data/studio/** + Files tab
  ├── Managed Skills            → /data/skills/<name>/SKILL.md
  ├── Schedule                  → digest / напоминания (cron + command)
  ├── Heartbeat (optional)      → фоновый routine по доке
  └── MCP / sidecar (later)     → только если files+Schedule+Heartbeat не хватают (RFC)

→ No core patches by default
→ archive-heavy-fork: reference only
```

Порядок решений (как в [`STUDIO_LAYER_SEPARATION_PLAN.md`](./STUDIO_LAYER_SEPARATION_PLAN.md)): **UI → documented config → skills → memory → files → MCP → upstream behavior → custom code (только разрешённые зоны).**

---

## C. Data contracts

Все пути — **внутри workspace бота** (см. [files.md](../docs/docs/getting-started/files.md)). Рекомендуемое дерево: **`/data/studio/`** как единый корень Studio Jarvis (согласуется с аудитом `projects.json` / `chats.json` / `tasks.json`).

### C.1 `/data/studio/people.md`

| Поле | Значение |
|------|----------|
| **Назначение** | SoT по людям: ФИО, роли, `@telegram`, заметки для Jarvis. |
| **Минимальная схема** | Markdown: секции по человеку или таблица; обязательны уникальные `@handle` в тексте. |
| **Пример (фрагмент)** | `# People\n\n## @grvtkv\n- Name: …\n- Role: …\n` |
| **SoT** | **Файл** для фактов о людях; **Memory** — кросс-сессионные факты и ссылки, не замена файла без явного правила в skill. |
| **Как читает Jarvis** | Только через **file tools** после skill `studio-people-source` или явного пользовательского запроса; при конфликте — **файл выше** memory. |

**Замечание:** в раннем аудите использовался `/data/people.md`. Для MVP рекомендуется **перенести/дублировать** контент в **`/data/studio/people.md`** и обновить skills на один путь — меньше путаницы с «глобальным» `/data`.

### C.2 `/data/studio/projects.json`

| Поле | Значение |
|------|----------|
| **Назначение** | Реестр проектов Studio. |
| **Минимальная схема** | `{ "projects": [ { "id": "string", "name": "string", "status": "active|archived", "notes": "string" } ] }` |
| **SoT** | **Файл** для списка проектов. |
| **Как читает Jarvis** | `Read` по skill `studio-project-registry`; не отвечать проекты «из головы». |

### C.3 `/data/studio/chats.json`

| Поле | Значение |
|------|----------|
| **Назначение** | Привязки чатов к проектам / роли чата (как в аудите: internal / client и т.д.). |
| **Минимальная схема** | `{ "chats": [ { "id": "string", "title": "string", "project_id": "string", "tier": "internal|client|ignored|needs_label" } ] }` |
| **SoT** | **Файл**. |
| **Как читает Jarvis** | Тот же skill, что и реестр проектов, или отдельный блок в нём; всегда `Read` перед ответом по реестру. |

### C.4 `/data/studio/tasks.json`

| Поле | Значение |
|------|----------|
| **Назначение** | Задачи по проектам. |
| **Минимальная схема** | `{ "tasks": [ { "id": "string", "title": "string", "project_id": "string", "status": "open|done", "assignee": "@handle" } ] }` |
| **SoT** | **Файл**. |
| **Как читает Jarvis** | `Read` + skill; статусы только из JSON. |

### C.5 (optional) `/data/studio/events.jsonl`

| Поле | Значение |
|------|----------|
| **Назначение** | Append-only журнал событий (созвон, решение, смена статуса) для человека и для будущего digest. |
| **Формат** | Одна JSON-строка на строку файла (`jsonl`). |
| **SoT** | **Файл**; не смешивать с `bot_history` в БД. |
| **Как читает Jarvis** | По запросу или в digest skill — `Read` с лимитом последних N строк; для больших объёмов позже — MCP/sidecar. |

---

## D. Skills to create

Каталоги: `/data/skills/<skill-name>/SKILL.md` ([skills.md](../docs/docs/getting-started/skills.md)). Имена ниже — **целевые** для продакшн-Jarvis (можно заменить префиксом окружения).

### D.1 `studio-jarvis-behavior`

| | |
|--|--|
| **Цель** | Общая дисциплина: приоритет SoT, тон, когда отвечать в группе (только с mention), не выдумывать реестр. |
| **Файлы** | Указатель на `people.md`, `projects.json`, `chats.json`, `tasks.json` (пути в преамбуле). |
| **Правила** | Сначала проверить, нужен ли **file read**; в группе без mention — не инициировать болтливость; маркеры strict («строго из файла») → обязательный `Read`. |
| **Не делать** | Не подменять файлы вымышленными списками; не требовать Go API. |

### D.2 `studio-people-source`

| | |
|--|--|
| **Цель** | Вопросы «кто такой @…» → `Read /data/studio/people.md` (или согласованный путь), затем memory. |
| **Файлы** | `/data/studio/people.md` (обязательно). |
| **Правила** | SoT = markdown; memory = дополнение с явной пометкой, если факт не в файле. |
| **Не делать** | Не отвечать ФИО без просмотра файла или подтверждённого memory-retrieval. |

### D.3 `studio-project-registry`

| | |
|--|--|
| **Цель** | Проекты / чаты / задачи из JSON одним контрактом. |
| **Файлы** | `/data/studio/projects.json`, `chats.json`, `tasks.json`. |
| **Правила** | Любой ответ по реестру — после `Read` нужного файла (или всех трёх для сводки). |
| **Не делать** | Не смешивать с hub-таблицами БД; не предполагать схему без чтения файла. |

### D.4 `studio-daily-digest`

| | |
|--|--|
| **Цель** | Текст для поля **Schedule → Instruction**: что читать, в каком порядке, какой формат вывода (маркер, краткость). |
| **Файлы** | `projects.json`, `tasks.json`, опционально `events.jsonl`, `people.md` для assignee. |
| **Правила** | Только факты из файлов; дата/маркер в первой строке; при `send` — помнить про **`platform`** (см. [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md) Block G). |
| **Не делать** | Не дублировать harvester; не писать в БД из digest без отдельного инструмента. |

---

## E. Native setup steps (UI / config)

Порядок для нового бота **Studio Jarvis** (чеклист оператора):

1. **Providers / Models** — Bot → General: выбрать chat (и при необходимости heartbeat) model.  
2. **Создать/выбрать бота** — имя, язык по необходимости.  
3. **Memory** — подключить провайдер памяти; убедиться, что retrieval включён для бота ([memory.md](../docs/docs/getting-started/memory.md)).  
4. **Telegram** — Platforms → Telegram → token → **Save and enable** ([telegram.md](../docs/docs/channels/telegram.md)).  
5. **Access** — ACL preset + правила для DM / групп / owner ([access.md](../docs/docs/getting-started/access.md)).  
6. **Files** — создать `/data/studio/`, загрузить `people.md`, `projects.json`, `chats.json`, `tasks.json` (Upload / New folder / Monaco).  
7. **Skills** — создать четыре каталога skill, вставить `SKILL.md` из шаблонов (первый batch, п. G).  
8. **Schedule** — daily digest: pattern `0 9 * * *` (или локальный timezone в [`config.toml`](../docs/docs/getting-started/schedule.md)), Instruction со ссылкой на правила `studio-daily-digest`; при необходимости **Run limit / max_calls**.  
9. **Проверка** — раздел H; `/access` в канале при сомнениях.

---

## F. Migration from archive heavy fork

| Категория | Действие |
|-----------|----------|
| **Keep as reference** | Сценарии control vs client, формулировки skills, идеи digest, структура JSON — через `git show studio/archive-heavy-fork-20260512-1245:…`. |
| **Reimplement as files / skills / config** | Реестры → `/data/studio/*.json` + skills; люди → `people.md`; периодика → Schedule; ACL → Access tab. |
| **Maybe sidecar / MCP later** | Богатый CRUD UI, внешний Git CRM, SLA-отчёты, полнотекст по всем чатам — только после RFC. |
| **Do not restore** | Merge ветки archive в baseline; Go people resolver; inbound/channel patches; ModeQueue custom; sqlc/store people; memory packer hooks; harvester/custom cron; Studio Control в core web. |

---

## G. First implementation batch (без изменения core)

После утверждения плана Cursor может сделать **только** артефакты в репозитории вне `internal/**`, `apps/**`, `db/**`:

1. **Создать каталог** `deploy/studio-jarvis-native/` (или `docs/studio-native/`) с **README**: что копировать на сервер, что остаётся в workspace.  
2. **Шаблоны файлов** — `templates/data/studio/people.md.example`, `projects.json.example`, `chats.json.example`, `tasks.json.example`, опционально `events.jsonl.example`.  
3. **Шаблоны skills** — `templates/skills/studio-jarvis-behavior/SKILL.md`, `studio-people-source`, `studio-project-registry`, `studio-daily-digest` (текст из разделов D).  
4. **Runbook** — `docs/studio/STUDIO_NATIVE_MVP_SETUP_RUNBOOK.md` (один файл): пошаговый UI чеклист из раздела E + ссылки на upstream docs.  
5. **Не трогать** Go/Vue/sqlc/migrations/inbound.

*(На baseline сейчас может не быть `deploy/studio-jarvis/` — это норма; новый каталог не заменяет upstream `deploy/`.)*

---

## H. Acceptance tests (ручные)

| # | Сценарий | Ожидание |
|---|----------|----------|
| 1 | Web: «кто такой @handle» | Ответ согласован с `people.md` / memory; при strict — виден `Read`. |
| 2 | Telegram DM: тот же вопрос | Как Web. |
| 3 | Telegram group: `@bot вопрос` | Ответ после mention; без mention — молчание OK для MVP. |
| 4 | Strict: «проекты строго из projects.json» | `Read` + только данные из файла. |
| 5 | Strict: задачи по `project_id` | `Read tasks.json` + корректные поля. |
| 6 | Schedule: срабатывание digest | Сессия типа `schedule`; в истории — `read` JSON; вывод с маркером. |
| 7 | `/access` / `/access@bot` | Корректный channel identity, ACL, group vs DM. |
| 8 | Burst: три mention подряд | Порядок ответов стабильный; без legacy ModeQueue. |

---

## I. Explicitly forbidden for MVP

- **Go people resolver** (любой возврат из archive).  
- **db / sqlc / store** patches под people или studio registry в core.  
- **inbound / channel** patches для MVP-сценариев DM/group/strict files.  
- **memory context packer** hooks для people/project lookup.  
- **Old task harvester / custom cron** из archive.  
- **Merge** ветки `studio/archive-heavy-fork-20260512-1245` в baseline как источник кода.  
- **Studio Control Mini App** внутри monolith без отдельного ТЗ и RFC.

---

## J. Open decisions

| Тема | Вопрос |
|------|--------|
| **Studio Control Mini App** | Нужен ли v2 как **sidecar** + deep link / MCP, или достаточно Files + внешний редактор? |
| **Raw history / SLA** | Достаточно UI session search + Memory + `Search history`, или нужен MCP/sidecar с архивом? |
| **Heartbeat** | Нужен ли фоновый routine в проде или достаточно Schedule? |
| **Путь people** | Только `/data/studio/people.md` или временно поддерживать `/data/people.md` для миграции? |
| **Production deploy** | Pipeline образов / VPS — вне этого документа; не смешивать с MVP-контрактами. |
| **Токены** | После аудитов — ротация BotFather + обновление Platforms ([telegram.md](../docs/docs/channels/telegram.md)). |

---

## Ссылки на коммиты аудита

- `29830b3a` — `docs(studio): record telegram group native audit`  
- `73786070` — `docs(studio): record schedule native audit`

---

*Автокоммит не выполнялся.*
