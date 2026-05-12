# Native runtime audit — Web + Telegram DM + Telegram group (`memohwebaudit`)

**Дата:** 2026-05-12 (обновлено: blocks A–F; Telegram bind + **Telegram DM human E2E** + **Telegram group human E2E** + docs-only Schedule/Heartbeat)  
**Ветка:** `studio/native-baseline-20260512`  
**Окружение:** Docker compose project `memohwebaudit`, Web UI `http://127.0.0.1:8082`, изолированный `.local-web-audit/`. Go/Vue не менялись, deploy не выполнялся под этот аудит. **Telegram DM/group:** автоматизация агента без Telegram-клиента не прогоняет чаты; **DM и группа** ниже — **ручной** runtime пользователя на том же baseline.

**Бот:** Web Audit People (provider + chat model заданы пользователем в UI).

---

## Сводная таблица

| Feature | Scenario | Result | Evidence | Classification | Restore old custom? | Notes |
|---------|----------|--------|----------|----------------|---------------------|-------|
| people identity by handle | Запросы вида «кто такой @grvtkv / @ibambets» | Pass | Корректные ФИО и роли; в новой сессии без повторной загрузки файла — тот же ответ | Native + config / files + skills + memory | **Нет** | Без Go-resolver |
| people identity by display name | «Егор» / «Глеб» | Pass (ранее в том же аудите) | Соответствие `people.md` / памяти | Native + config / files + skills + memory | **Нет** | |
| people.md source of truth | Вопрос о правиле источника данных о людях | Pass | Ответ: `people.md` = SoT; память — доп. контекст | Native + skills (+ memory aux) | **Нет** | Skill `web-audit-people` влияет на формулировки |
| files tool read | Явный запрос прочитать `/data/people.md` | Pass | UI tool trace: **Read** → `/data/people.md`; цитата строки с `@grvtkv` | Native files / workspace | **Нет** | |
| list `/data` | List только инструментами файлов | Pass | UI: **List** → `/data`; перечислены `people.md`, `memory`, `skills`, … | Native files | **Нет** | |
| manual memory entry retrieval | «Не используй people.md / файлы; только memory: кто @grvtkv?» | Pass | Ответ верный; **без** видимых List/Read между вопросом и ответом в a11y snapshot | Native memory (retrieval); file tools не обязательны на turn | **Нет** | Явная строка retrieval в UI не показана — только корректный ответ |
| skill influence | «Какое правило по источнику данных о людях?» | Pass | Текст ответа: `people.md` как SoT | Native skills | **Нет** | Отдельная строка «Use skill» на этом turn в снимке не требовалась — семантика skill видна в ответе |
| cross-session people lookup | New Session → «Кто такой @grvtkv?» без перезагрузки файла | Pass | Ответ: Егор Вотяков; file tool rows в снимке отсутствуют | Native memory / shared bot context | **Нет** | Skills/files бота остаются доступны боту между сессиями |
| cross-session new fact recall | Сессия A: «Запомни: AuditNative ↔ @grvtkv»; сессия B: вопрос о человеке проекта | Pass | Сессия A: UI trace обновления `memory/2026-05-12.md` (+ новая запись); сессия B: ответ `@grvtkv` | Native memory write + cross-session read | **Нет** | |
| raw cross-chat search gap | Поиск по сырой истории vs memory | Partially characterized | См. **Block A** ниже: UI search + agent `Search history`; ограничение по точному токену | Native UI + native agent tool; семантика vs memory — см. memory.md | **Нет** | Полный «продуктовый FTS по всем чатам» не формализован отдельной строкой в этом документе |
| Telegram group runtime (E2E) | Группа: без mention / mention / access / strict JSON / burst | **Pass (human)** | См. **Block E.8** (выполнение по плану **E.7**) | **native with config** + files/skills/memory | **Нет** | Без mention до ответа — **acceptable / default** для группы (`discuss`), если нет отдельного product requirement «слушать всё» |
| Telegram UI bind (adapter) | Platforms → Telegram → Save and enable | Pass | UI **Telegram Active**; в БД строка `telegram`, `disabled=false` | native with config | **Нет** | См. **Block E**; секрет не логировать |
| Telegram DM/Q&A (E2E) | Личка: people/projects/tasks + строгие чтения JSON | **Pass (human)** | См. **Block E.6** — ответы совпали с Web-аудитом (skills/files/memory) | native with config + files/skills/memory | **Нет** | Старые inbound/channel patches для DM/basic lookup **не** восстанавливать |
| studio JSON registries | projects/chats/tasks в `/data/studio/*.json` + skill | Pass | См. **Block B** | files/skills/memory | **Нет** | |
| workspace Files write (UI) | Upload / New Folder / Monaco Save | Pass (UI) | Три JSON загружены через **Upload**; папки `studio/`, `skills/web-audit-studio-data/` через **New Folder**; `SKILL.md` загружен | Native Files (док files.md) | **Нет** | Агентский **Write** файлов в этом прогоне не вызывали (нужен отдельный тест без порчи JSON) |
| MCP / sidecar necessity | Внешний registry vs workspace | Doc + gap | См. **Block C** | MCP опционально; sidecar — при внешнем API | **Нет** | |

---

## Block A — Session search / raw history

### A.1 Документация (локально)

| Файл | Вывод для аудита |
|------|-------------------|
| [sessions.md](../docs/docs/getting-started/sessions.md) | В Web UI: **Search sessions by content**; память **shared across all sessions** для бота. |
| [memory.md](../docs/docs/getting-started/memory.md) | Retrieval долговременной памяти в рантайме **отдельно** от контекста одной сессии и от Memory tab search. |
| [search-provider.md](../docs/docs/getting-started/search-provider.md) | **Веб-поиск**, не поиск по истории Memoh. |
| [files.md](../docs/docs/getting-started/files.md) | Файлы бота — изолированный workspace; бот может работать с файлами через **Skills/MCP**; UI — read/edit/save/upload. |
| [skills.md](../docs/docs/getting-started/skills.md) | Managed skills: `/data/skills/<name>/SKILL.md`; обнаружение из нескольких корней. |

### A.2 Web UI — поиск по сессиям

- В сайдбаре сессий есть поле **Search** (`sessions.md`).
- **Runtime:** после сообщения с уникальной подстрокой `Zebra42` в новой сессии, ввод `Zebra42` в **Search** оставил в списке **только** сессию «Project Zebra42 Discussion» (остальные скрыты).  
  **Вывод:** это **фильтрация списка сессий по содержимому** (сырой текст сообщений участвует в индексе/поиске сессий на уровне UI).

### A.3 Агент vs память — сценарий RawHistoryAudit / Zebra42

1. **Session A:** пользовательское сообщение:  
   `RawHistoryAudit marker: project Zebra42 discussed with @grvtkv.`
2. **Session B (новая):** запрос: найти, где упоминались `RawHistoryAudit` / `Zebra42`.

**Наблюдения:**

- В UI отображён инструмент **`Search history`** (два вызова с запросами `"RawHistoryAudit"` и `"Zebra42"`).
- Модель ответила: точных упоминаний **`RawHistoryAudit` в «истории, доступной мне сейчас» не нашёл**; по `Zebra42` сослался на **memory** (перефразированная формулировка «Проект Zebra42 обсуждался с @grvtkv»), а не на цитату сырого пользовательского маркера и **не** назвала явно title сессии «Project Zebra42 Discussion».

**Интерпретация:**

- **UI session search** и **агентский Search history** — разные слои; второй **не** заменяет полностью «сырой лог» для произвольных токенов (возможны ограничения индексации/токенизации или scope tool).
- Для гарантированного межсессионного recall **маркерных фактов** по-прежнему надёжны **Memory** (или явный SoT-файл), в соответствии с `memory.md`.

### A.4 Нужен ли raw-history sidecar / MCP?

- **Отдельный sidecar** не требуется для базового UX: **есть UI-поиск по сессиям** + **агентский Search history**.
- Если продукту нужен **строгий полнотекст / compliance / внешний архив** с гарантиями — это **отдельный RFC** (возможен MCP или внешний сервис), **не** выводится из одного Web-прогона.

---

## Block B — Projects / chats / tasks (files + skills + memory)

### B.1 Тестовые данные (только несекретные)

Создано через **Files** UI (Upload / New Folder), без правок Go/Vue:

| Путь | Назначение |
|------|------------|
| `/data/studio/projects.json` | Проект **AuditNative** (`audit-native`) |
| `/data/studio/chats.json` | Чаты **Audit internal**, **Audit client** |
| `/data/studio/tasks.json` | Задача **Prepare native audit summary**, assignee `@grvtkv` |
| `/data/skills/web-audit-studio-data/SKILL.md` | Skill **web-audit-studio-data**: SoT = три JSON; сначала читать файлы; memory — дополнительно; не выдумывать записи |

### B.2 Runtime Q&A (одна сессия)

Запрос: использовать skill `web-audit-studio-data` и ответить по трём JSON после чтения инструментами.

**Tool trace (UI):**

1. **Use skill** `web-audit-studio-data`
2. **Read** `/data/studio/projects.json`
3. **Read** `/data/studio/chats.json`
4. **Read** `/data/studio/tasks.json`

**Ответ:** перечислен проект AuditNative; чаты Audit internal / Audit client; задача по AuditNative; ответственный за summary — **`@grvtkv`**; источник данных — файлы под `/data/studio/` (`projects.json`, `chats.json`, `tasks.json`).  
**Memory** на этом turn явно не требовалась (retrieval не отображался отдельной строкой).

### B.3 Вывод

Реестры **projects/chats/tasks** закрываются **native Files + managed skill** без core-touch, аналогично people.

---

## Block C — Workspace / MCP feasibility

### C.1 Документация

| Файл | Вывод |
|------|-------|
| [mcp.md](../docs/docs/getting-started/mcp.md) | Stdio MCP (в т.ч. filesystem) и remote MCP; OAuth для части серверов. |
| [files.md](../docs/docs/getting-started/files.md) | Workspace бота изолирован; UI = browse/upload/rename/delete/Monaco **Save**; бот — tools через skills/MCP. |
| [workspace-backends.md](../docs/docs/installation/workspace-backends.md) | Где живут контейнеры/PVC; sidecar overlay — инфраструктурный уровень, не «Studio custom» в коде memoh. |

### C.2 Достаточно ли встроенных Files для Studio registries?

- **Да для типового Studio-слоя:** JSON/Markdown реестры в `/data/studio/` + skills достаточно для CRUD-семантики **через UI** (редактор Monaco) и чтения агентом (**Read** подтверждён).
- **MCP filesystem** имеет смысл, если registry должен жить **вне** workspace бота или синхронизироваться с внешним Git/CRM (**док mcp.md** — stdio с корнем на каталоге данных).
- **Отдельный Studio sidecar** — только если нужен **внешний API**, SLA, multi-bot shared DB, интеграции без копирования в `/data`.

### C.3 CRUD без core changes?

- **Чтение + ответы агента:** да (проверено Read).
- **Создание/редактирование человеком:** да через **Files** (Upload, New Folder, Save в UI по доке).
- **Автоматическая запись агентом:** в этом прогоне **не проверяли** (риск порчи JSON); документация заявляет возможность write через skills/MCP — отдельный контролируемый тест.

---

## Block E — Telegram runtime (`memohwebaudit`, 2026-05-12)

### E.1 Документация

Шаги подключения — [telegram.md](../docs/docs/channels/telegram.md): Bot Detail → **Platforms** → **Add Channel** / **Add Platform** → **Telegram** → вставить **API Token** → **Save and Enable** (в UI кнопка **Save and enable**).

### E.2 Что сделано локально (без вывода секрета)

- Стек **memohwebaudit** (Web `127.0.0.1:8082`, server, postgres) — **Up**.
- Бот **Web Audit People** (UUID из БД не секретный; в отчёт **не** включали токен).
- В Web UI на вкладке **Platforms** добавлена платформа **Telegram**, credentials введены **только в форме UI**, сохранено **Save and enable**.
- **Проверка Telegram Bot API (вне Memoh):** `getMe` → `ok=true`, публичное имя бота `@Jarvispbw_bot` (это публичный username из API, не секрет). Локальные файлы с копией токена для автоматизации **удалены** после шага (в репозиторий не коммитились).

### E.3 Состояние в Memoh после bind

- В UI отображается **Telegram — Active**.
- В Postgres (`bot_channel_configs`): тип канала `telegram`, `disabled=false`, `verified_at` на момент проверки был **NULL** (флаг verified может заполняться позже в зависимости от логики продукта — не интерпретировали как сбой).

### E.4 Что **не** прогоняет автоматизация агента

**DM** и **группа** из Cursor не дублировались: результаты — **ручной** runtime пользователя (**E.6** — DM, **E.8** — группа).

### E.5 Studio MVP vs старые inbound / channel / ModeQueue custom

На основании **штатного** Telegram через **Platforms**, **DM E2E** (**E.6**) и **group E2E** (**E.8**):

- **Studio MVP (DM + группа)** закрывается **mention + ACL + files/skills/memory** на нативном адаптере; **Go не трогали**.  
- **Старые inbound/channel patches не возвращать** для **DM / group MVP** (включая mention-Q&A, strict file source, burst) — gap не выявлен.  
- **Старый ModeQueue custom не возвращать** по результатам burst (**E.8**): три ответа подряд, порядок нормальный — **нативное** поведение приемлемо.  
- **Переоценка inbound/legacy queue** — только при **явном** продуктовом требовании: например, **пассивное** прослушивание **всех** сообщений группы без mention или **жёсткая** отдельная семантика очереди, которую штатный путь не закрывает (отдельное ТЗ / RFC).

Сообщение в группе **без mention**, на которое бот **не** отвечает до явного mention, классифицируем как **ожидаемое / допустимое** поведение в духе **`discuss`** ([sessions.md](../docs/docs/getting-started/sessions.md)) — безопасный default, если нет отдельного требования «отвечать на всё».

### E.6 — Telegram DM runtime evidence (human E2E, baseline `memohwebaudit`)

Проверено пользователем в **личке** с ботом, подключённым через **Platforms → Telegram** (тот же baseline, без возврата Studio custom из archive). Секреты и токены в документ **не** включаются.

| # | Сообщение пользователя (суть) | Ожидаемое поведение native baseline | Наблюдаемый результат (human) |
|---|------------------------------|--------------------------------------|-------------------------------|
| 1 | «кто такой @grvtkv» | People identity через memory + ссылки | Корректный ответ про Егора Вотякова + **memory links** |
| 2 | «какие проекты есть» | Projects из memory / skill контекста | **AuditNative**, **Zebra42** из memory |
| 3 | «какие задачи по AuditNative» | Tasks/registry через skill + файлы | **Prepare native audit summary**, ответственный **@grvtkv** |
| 4 | Строгий запрос: полный список проектов **строго** из `/data/studio/projects.json` | Tool **Read** файла, ответ только по SoT | Прочитан `projects.json`, в ответе **AuditNative** |
| 5 | Строгий запрос: чаты проекта AuditNative **строго** из `/data/studio/chats.json` | Tool **Read** файла | Прочитан `chats.json`, показаны **Audit internal** / **Audit client** |

**Классификация:** **native with config** (Platforms + adapter + bot providers) **+** **files / skills / memory** — без Go people resolver, без старых db/sqlc/store и inbound/channel патчей.

**Вывод:** **people / projects / tasks lookup в Telegram DM** для Studio baseline закрывается **штатно** тем же слоем, что и Web-аудит: **Telegram Platform + Skills + Files + Memory**.

### E.7 — Ручной план: Telegram **группа** (mention / slash / ACL / burst)

**Подготовка:** создать тестовую группу, добавить бота участником. Во всех шаблонах ниже замените `YOUR_BOT_USERNAME` на **публичный** `@username` вашего бота (как в Telegram, начинается с `@`).

**Ожидание по доке [sessions.md](../docs/docs/getting-started/sessions.md):** в группах на адаптерах по умолчанию часто **`discuss`** — ответ не обязан быть на каждое сообщение без явного участия бота.

Скопируйте по очереди (сначала без mention, затем mention/slash):

```text
[TEST-GROUP-01] Обычное сообщение в группе без упоминания бота. Ожидаю либо молчание (discuss), либо политику вашего бота — зафиксируйте фактическое поведение.
```

```text
YOUR_BOT_USERNAME ответь одним коротким предложением: слышишь ли ты это сообщение через mention?
```

```text
YOUR_BOT_USERNAME /access
```

```text
YOUR_BOT_USERNAME /help
```

```text
/access
```

```text
YOUR_BOT_USERNAME кратко перечисли проекты строго из /data/studio/projects.json (только факты из файла).
```

**Burst / очередь (native, без custom ModeQueue):** отправьте **быстро подряд** три строки (можно в одном сообщении или тремя подряд — зафиксируйте способ):

```text
YOUR_BOT_USERNAME [BURST-A] первое быстрое сообщение
YOUR_BOT_USERNAME [BURST-B] второе быстрое сообщение
YOUR_BOT_USERNAME [BURST-C] третье быстрое сообщение
```

**Что записать в отчёт:** для каждого шага — «ответил / не ответил», задержка, дубли, порядок ответов, ошибки ACL; скрин или пересланные ответы **без** токенов.

**Статус плана:** прогон выполнен пользователем — см. **E.8**.

### E.8 — Telegram group runtime evidence (human E2E, baseline `memohwebaudit`)

Тестовая **группа**, бот с публичным username `@Jarvispbw_bot` (username не секрет). Токены и прочие credentials **не** фиксируем.

| # | Сценарий | Ввод (суть) | Наблюдаемый результат | Интерпретация |
|---|----------|-------------|----------------------|---------------|
| G1 | Сообщение **без** mention бота | Текст: `кто такой @grvtkv` (в группе, бот не @упомянут) | Бот **не ответил**, пока не было mention | **Expected / acceptable:** для групп по умолчанию часто **`discuss`** — молчание без явного обращения к боту нормально и **безопасно**, если нет product requirement слушать все сообщения |
| G2 | Mention + people | `@Jarvispbw_bot кто такой @grvtkv` | Ответ: `@grvtkv` — Егор Вотяков, роль (ассистент маркетолога / аккаунт-менеджер) | **Pass:** people через тот же слой, что DM/Web |
| G3 | ACL / slash (Telegram suffix) | `/access@Jarvispbw_bot` | Диагностика: Channel Identity present; Linked User none; Bot Role none; Write Commands **no**; Channel telegram; Conversation Type **group**; Conversation ID present; Thread none; **Chat ACL: allow** | **Pass:** slash + identity; write отключён для не-owner — ожидаемо для обычного участника |
| G4 | Strict file source | `@Jarvispbw_bot покажи полный список проектов строго из /data/studio/projects.json` | В ответе **AuditNative** из файла | **Pass:** strict SoT через files/tools |
| G5 | Burst (три подряд) | `@Jarvispbw_bot BURST-A кто такой @grvtkv` / `… BURST-B какие проекты есть` / `… BURST-C какие задачи по AuditNative` | Все **три** ответа получены, **порядок** A → B → C сохранён: A — человек @grvtkv; B — проекты из `projects.json` (AuditNative); C — задача **Prepare native audit summary**, assignee **@grvtkv**, status **open** | **Pass:** нативная обработка серии без необходимости **custom ModeQueue** из archive |

**Классификация group MVP:** **native with config** (Platforms + adapter + ACL) **+** **files / skills / memory** — без старых inbound/channel patches и без возврата **ModeQueue custom** по этому аудиту.

---

## Block F — Schedule / Heartbeat (только по документации, без runtime)

Источники: [schedule.md](../docs/docs/getting-started/schedule.md), [heartbeat.md](../docs/docs/getting-started/heartbeat.md), [sessions.md](../docs/docs/getting-started/sessions.md), [slash-commands.md](../docs/docs/getting-started/slash-commands.md).

| Вопрос | Вывод по докам |
|--------|----------------|
| Можно ли штатно сделать **daily digest**? | **Да:** **Schedule** с cron (`pattern`, например `0 9 * * *`) и полем **`command`** — произвольная NL-инструкция агенту; создание через UI **Schedule**, разговор с ботом (schedule tool) или `POST /api/bots/{bot_id}/schedule`. |
| Какие **inputs** нужны digest'у? | По смыслу задачи: **Memory** (общая для бота), **Files** (`/data/studio/*.json`, `people.md`), **tasks/projects** из JSON, при необходимости web search / MCP — всё доступно агенту в **turn** по той же модели, что и обычный чат. |
| Можно ли отправлять digest **в Telegram** штатно? | В [schedule.md](../docs/docs/getting-started/schedule.md) указано: результаты могут доставляться в **любой подключённый канал**; в примере `command` явно фигурирует формулировка про отправку в Telegram. Значит **MVP закрывается документированно** без custom cron вне Memoh. |
| Что тестировать **отдельно** (runtime)? | Факт срабатывания cron в вашем timezone (`timezone` в конфиге сервера, по умолчанию UTC); что именно бот отправил в Telegram/Web; лимиты `max_calls`; права **owner-only** на `/schedule create` и т.д. ([slash-commands.md](../docs/docs/getting-started/slash-commands.md)). |
| Нужен ли **custom cron / внешний harvester**? | **По умолчанию нет:** Schedule + Heartbeat покрывают периодику; Heartbeat — фиксированный интервал и «routine» промпт ([heartbeat.md](../docs/docs/getting-started/heartbeat.md)), Schedule — точное время и **кастомная** команда. Внешний harvester имеет смысл только при интеграции вне Memoh (отдельный RFC / sidecar). |

**Связь с сессиями:** при срабатывании создаётся тип сессии **`schedule`** / **`heartbeat`** — их видно в списке сессий ([sessions.md](../docs/docs/getting-started/sessions.md)); логи heartbeat — вкладка **Heartbeat** и slash `/heartbeat` ([slash-commands.md](../docs/docs/getting-started/slash-commands.md)).

---

## Tool trace (копируемая формулировка)

**People через файл (ранее + подтверждено):**  
`Use skill web-audit-people` → `List /data` → `Read /data/people.md`.

**Этот прогон (дополнительно):**  
`List /data`; `Read /data/people.md`; запись факта — обновление `memory/2026-05-12.md` (новая memory-запись).

**Studio registries (этот прогон):**  
`Use skill web-audit-studio-data` → `Read /data/studio/projects.json` → `Read /data/studio/chats.json` → `Read /data/studio/tasks.json`.

**Session / history:**  
UI: фильтр сессий по строке поиска; агент: **`Search history`** (см. Block A).

**Telegram DM (human E2E, см. E.6):**  
Ответы по people/projects/tasks и строгим путям `/data/studio/projects.json` / `chats.json` согласованы с Web-аудитом (skills + files + memory); отдельный tool trace в Telegram UI здесь не дублировали.

**Telegram group (human E2E, см. E.8):**  
MVP (mention, `/access@bot`, strict `projects.json`, burst) — **pass**; без mention до ответа — **acceptable default**; legacy inbound / **ModeQueue custom** — **не** восстанавливать по этому результату.

---

## Выводы для планирования

1. **People identity** — закрывать через **files (`people.md`) + skill + memory**; **не** возвращать Go people resolver и **не** делать core-touch под эту задачу.  
2. **Telegram** — **Platforms** + adapter (**Block E**). **DM** (**E.6**) и **группа** (**E.8**) — **подтверждены** human E2E: group MVP = **mention + ACL + files/skills/memory**; burst нативный — **достаточно**. После чувствительных тестов по-прежнему разумно **revoke/regenerate** токена в BotFather и обновить credentials в Memoh.  
3. **Cross-session** для бота в Web подтверждён и для people lookup, и для явно сохранённого факта (через агентское обновление memory-файла).
4. **Projects/chats/tasks** — держать в **`/data/studio/*.json` + skill**; memory — только дополнение; см. `STUDIO_RESTORE_DECISION_MATRIX.md`.
5. **Поиск по истории** — использовать **UI session search** и/или **Search history**; для критичных маркеров — **Memory или SoT-файл**; sidecar — только по RFC.

---

## Block D — Consolidated pointer

Итоговая матрица «что возвращать / что нет»: **`STUDIO_RESTORE_DECISION_MATRIX.md`**.  
Целевая архитектура native-first Studio: **`NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md`**.

---

*Автоматический коммит не выполнялся.*
