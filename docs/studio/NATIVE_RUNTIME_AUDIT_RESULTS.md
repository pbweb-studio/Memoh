# Native runtime audit — Web-only (`memohwebaudit`)

**Дата:** 2026-05-12 (обновлено тем же прогоном: blocks A–D)  
**Ветка:** `studio/native-baseline-20260512`  
**Окружение:** Docker compose project `memohwebaudit`, Web UI `http://127.0.0.1:8082`, изолированный `.local-web-audit/`. Go/Vue не менялись, deploy не выполнялся, реальный Telegram не подключался.

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
| Telegram group runtime | Реальная группа, токен BotFather, inbound/outbound | Not tested | Намеренно не запускали | Documented native; runtime N/A here | **Нет** | Только по `docs/channels/telegram.md` + план |
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

## Tool trace (копируемая формулировка)

**People через файл (ранее + подтверждено):**  
`Use skill web-audit-people` → `List /data` → `Read /data/people.md`.

**Этот прогон (дополнительно):**  
`List /data`; `Read /data/people.md`; запись факта — обновление `memory/2026-05-12.md` (новая memory-запись).

**Studio registries (этот прогон):**  
`Use skill web-audit-studio-data` → `Read /data/studio/projects.json` → `Read /data/studio/chats.json` → `Read /data/studio/tasks.json`.

**Session / history:**  
UI: фильтр сессий по строке поиска; агент: **`Search history`** (см. Block A).

---

## Выводы для планирования

1. **People identity** — закрывать через **files (`people.md`) + skill + memory**; **не** возвращать Go people resolver и **не** делать core-touch под эту задачу.  
2. **Telegram** — оставить на отдельный разрешённый runtime-прогон с реальным каналом.  
3. **Cross-session** для бота в Web подтверждён и для people lookup, и для явно сохранённого факта (через агентское обновление memory-файла).
4. **Projects/chats/tasks** — держать в **`/data/studio/*.json` + skill**; memory — только дополнение; см. `STUDIO_RESTORE_DECISION_MATRIX.md`.
5. **Поиск по истории** — использовать **UI session search** и/или **Search history**; для критичных маркеров — **Memory или SoT-файл**; sidecar — только по RFC.

---

## Block D — Consolidated pointer

Итоговая матрица «что возвращать / что нет»: **`STUDIO_RESTORE_DECISION_MATRIX.md`**.

---

*Автоматический коммит не выполнялся.*
