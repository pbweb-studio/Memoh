# Native capability audit — block 1: Telegram, memory/search, people identity

## 1. Scope

Первый блок **native capability audit** на ветке `studio/native-baseline-20260512`: только **upstream-документация** и штатные поверхности (UI, General/Memory/Platforms/Access, skills, files, MCP). **Без** правок Go/core, **без** deploy, **без** реального Telegram-токена и без выкладки секретов. Архивная ветка Studio **не** использовалась.

---

## 2. Docs reviewed

| Документ | Тема |
|----------|------|
| [channels/telegram.md](../docs/channels/telegram.md) | Подключение Telegram, поддерживаемые фичи в ответах |
| [getting-started/sessions.md](../docs/getting-started/sessions.md) | Типы сессий, группы vs DM, `/new`, память между сессиями |
| [getting-started/slash-commands.md](../docs/getting-started/slash-commands.md) | Slash в группах, `/access`, `/fs`, mention-prefix |
| [getting-started/access.md](../docs/getting-started/access.md) | ACL, Channel Identity, scope (group/thread/conversation id) |
| [getting-started/memory.md](../docs/getting-started/memory.md) | Long-term memory, retrieval, Memory tab, compaction vs context |
| [getting-started/search-provider.md](../docs/getting-started/search-provider.md) | Поиск в web через провайдера |
| [memory-providers/index.md](../docs/memory-providers/index.md) | Обзор провайдеров памяти |
| [memory-providers/builtin.md](../docs/memory-providers/builtin.md) | Режимы off/sparse/dense, Qdrant/sparse инфра |

---

## 3. Native Telegram capabilities

**Что явно в [telegram.md](../docs/channels/telegram.md):**

- Создание бота у BotFather → **API token** (хранить в секрете).
- В Memoh: Bot **Detail** → **Platforms** → Add **Telegram** → вставить credentials → **Save and Enable**.
- Поддерживаемые возможности канала: **streaming**, **Markdown**, **attachments** (вход/выход), **replies** (контекст ответов).

**Группы / multi-user (из других штатных доков, не противоречащих Telegram-странице):**

- В [sessions.md](../docs/getting-started/sessions.md): для **group conversations on channel adapters** по умолчанию тип сессии **`discuss`** (бот «наблюдает», говорит только когда явно шлёт `send`; молчание нормально). DM / private → по умолчанию **`chat`**.
- Команды `/new`, `/new chat`, `/new discuss` в адаптерах (в т.ч. Telegram) — сброс активной сессии на маршруте без удаления истории.
- [slash-commands.md](../docs/getting-started/slash-commands.md): в группах поддерживаются **mention-prefixed** команды (`@BotName /help`) и суффиксы Telegram (`/help@MemohBot`).

**Inbound / outbound (логическая модель по докам):**

- **Inbound:** сообщения из Telegram попадают в Memoh как в другие channel adapters; дальше — сессии + ACL (см. п. 5).
- **Outbound:** ответы бота в канал с учётом streaming/Markdown/вложений, как заявлено для Telegram.

**Ограничения / routing, зафиксированные в docs:**

- Док **не** описывает детали Telegram API (privacy mode, права админа, supergroup vs broadcast channel, только @mentions и т.д.) — это **gap** относительно «полной» Telegram-экспертизы; ориентир — официальный Telegram Bot Tutorial (внешняя ссылка в telegram.md) + фактическое поведение Memoh в runtime после включения канала.

---

## 4. Native memory / search capabilities

**Long-term memory ([memory.md](../docs/getting-started/memory.md), [memory-providers](../docs/memory-providers/index.md)):**

- Память привязана к **Memory Provider** (создание провайдера → назначение в **General** → операции в **Memory**).
- При сообщении пользователя Memoh **находит релевантные memories** и включает их в **runtime context** (retrieval зависит от режима провайдера).
- Ручные операции: создать / из переписки / поиск по Memory tab (ID или текст) / edit / delete; **Compact** (перезапись набора памяти); **Rebuild** (переиндексация).

**Режимы built-in ([builtin.md](../docs/memory-providers/builtin.md)):**

- `off` — файловый индекс, без векторов; `sparse` / `dense` — с Qdrant и разной инфраструктурой (sparse-сервис, embedding для dense).

**Кросс-сессии / «разные чаты»:**

- В [sessions.md](../docs/getting-started/sessions.md) прямо указано: **Memory is shared across all sessions for a bot** — извлечённые из одной сессии воспоминания доступны в **остальных**. Это штатный ответ на «долгая память между чатами» на уровне **memory store**, не обязательно на уровне полного сырого лога всех сессий в одном поисковом запросе UI.

**Search provider ([search-provider.md](../docs/getting-started/search-provider.md)):**

- Это **веб-поиск** (Brave, Bing, Google, …), инструмент во время разговора при необходимости real-time знаний.
- **Не** позиционируется как «поиск по истории чатов Memoh»; поиск по записям памяти — зона **Memory tab** и retrieval в рантайме.

**Итог по докам:** кросс-чат **фактов и извлечённых memories** — штатно; **полнотекстовый поиск по всей истории всех сессий как в отдельном продукте** — в этих страницах **не задокументирован** (см. Gaps).

---

## 5. Native people identity options

**Как Memoh различает сущности (по докам):**

- **Сессии** — потоки сообщений с типами `chat`, `discuss`, … на бота ([sessions.md](../docs/getting-started/sessions.md)).
- **Участники / отправитель** в ACL-модели — через **Channel Identity** (конкретный пользователь на внешнем канале, напр. Telegram user) и **Channel Type**; правила с **source scope**: channel, conversation type (`private` / `group` / `thread`), **conversation id**, **thread id** ([access.md](../docs/getting-started/access.md)).
- Диагностика текущего контекста: **`/access`** — channel identity, linked user, роль, scope, результат ACL ([slash-commands.md](../docs/getting-started/slash-commands.md)).

**«Кто такой @handle / имя» без Go-resolver и без core — варианты:**

| Механизм | Как использовать |
|----------|------------------|
| **a) Memory** | Вручную или «From Conversation» занести факты вида «@username — Иван, роль X»; дальше retrieval подмешивает в ответы. |
| **b) Skill** | `SKILL.md` с правилами: при неизвестном отправителе уточнять; ссылаться на память и файлы people. |
| **c) Workspace file `people.md`** | Создать/редактировать через **Files** tab; бот читает через инструменты/навыки (см. [files.md](../docs/getting-started/files.md) — бот может работать с файлами через skills/MCP). |
| **d) MCP filesystem** | Stdio MCP с корнем на каталог данных бота ([mcp.md](../docs/getting-started/mcp.md)); structured people registry как файлы JSON/MD, без схемы БД в core. |

**Штатное различение «пользователь с Telegram»** для правил доступа — **Channel Identity** в UI после того, как бот «видел» идентичность (док: search and select identity the bot has seen before).

---

## 6. Proposed no-core implementation for Studio Jarvis

Согласовано с [STUDIO_LAYER_SEPARATION_PLAN.md](./STUDIO_LAYER_SEPARATION_PLAN.md):

1. **Telegram:** один штатный канал на бота, ACL пресеты под private/group; для «control»-дискиплины — преимущественно **`discuss`** + skills (когда говорить / когда только read-only действия), без кастомного inbound.
2. **Memory + search:** built-in или внешний провайдер по политике; **General** — memory + search provider; дайджест фактов о людях — в Memory и/или `people.md`.
3. **People:** SoT в **files** (`people.md` или `people/*.md`) + **Memory** для быстрого retrieval + **Skill** «как интерпретировать people + ACL»; опционально **MCP** для редактирования реестра внешним инструментом.
4. Никаких правок `internal/channel/inbound`, `conversation/flow`, `memory/context_packer` для этого блока.

---

## 7. Test scenarios to run manually (без реального токена в этом документе; проверка — когда разрешён доступ к BotFather / UI)

**A. Web-only / без Telegram**

1. Создать тестового бота, назначить memory provider (хотя бы built-in `off` если достаточно без Qdrant) и при необходимости search provider — только через UI, ключи не логировать.
2. **Memory:** создать 2 ручные записи о «вымышленных людях»; во **второй сессии** (New Session в Web) спросить модель о них — ожидание: ответ использует память (док: shared across sessions).
3. **Files:** положить `workspace/people.md` (путь по выбору под файловый менеджер) с таблицей имён; попросить бота процитировать — проверка чтения файлов.
4. **Skill:** добавить короткий skill «При неизвестном пользователе спроси ник и предложи добавить в people.md».
5. **`/access`** в Web UI chat (если применимо к маршруту) — убедиться, что вывод не содержит секретов при сохранении скриншотов/логов.

**B. Когда Telegram разрешён отдельно**

1. Подключить канал по [telegram.md](../docs/channels/telegram.md); ACL: например `group_only` или deny-all + allow identities.
2. В группе: убедиться в default **`discuss`**; проверить `@Bot /help` и `/help@YourBot`.
3. Один и тот же вопрос о «человеке из people.md» из **DM** и из **group** — согласованность с ACL и памятью.
4. `/new chat` vs `/new discuss` в группе — смена типа сессии по доке.

**Пример содержимого (план, не production-секреты):**

- `people.md`: markdown-таблица колонок `handle`, `display_name`, `notes` (выдуманные данные).
- Skill: YAML `name: studio-people-router`, description + тело с отсылкой к файлу и Memory.

---

## 8. Gaps / unknowns

- [telegram.md](../docs/channels/telegram.md) **не** покрывает: групповые права Bot API, privacy mode, channel vs supergroup, rate limits, inline-кнопки — поведение только из runtime или внешней доки Telegram.
- Точная семантика **retrieval** (как ранжируются memories между многими чатами) зависит от режима провайдера — детали в коде, не раскрыты в одном абзаце user-facing docs.
- **Поиск по полной истории сообщений** всех сессий как отдельная фича — в просмотренных страницах **не** заявлен; есть поиск по **Memory** и sidebar **search sessions by content** в Web ([sessions.md](../docs/getting-started/sessions.md)) — глубина и семантика «search sessions» без чтения кода остаются **unknown** для строгого аудита только по docs.

---

## 9. Classification table

| Feature | Native/config/files/skills/MCP? | Needs custom? | Recommended home | Risk | Notes |
|---------|-----------------------------------|---------------|-------------------|------|-------|
| Telegram подключение | native + config (token в UI) | Нет | Platforms | Low | Токен только в UI/секрет-хранилище окружения |
| Streaming / MD / вложения / replies | native | Нет | Channel adapter | Low | Из telegram.md |
| Групповой режим «наблюдатель» | native (`discuss`) | Нет | Sessions default | Med | Культура ответа — skills |
| Slash в группах + mention | native | Нет | Slash system | Low | slash-commands.md |
| ACL по пользователю/группе/треду | native | Нет | Access tab | Med | Тонкая настройка scope |
| Long-term memory | native + config (provider) | Нет | Memory + General | Med | Qdrant/sparse инфра для режимов |
| Память между сессиями | native | Нет | Memory pipeline | Low | Явно в sessions.md |
| Memory tab text search | native | Нет | Web UI | Low | По записям памяти |
| Web search | native + config | Нет | Search provider | Low | Не путать с историей чатов |
| Кто есть кто (бизнес-факт) | memory + files + skills | Нет | Memory + `people.md` + SKILL | Low | |
| Идентичность для правил | native (Channel Identity) | Нет | Access | Low | После того как бот «видел» identity |
| Реестр людей JSON из Studio hub | files или MCP | Опционально MCP | MCP / workspace | Med | Не тянуть в core |
| Полнотекст по всей истории чатов | не ясно из docs | Возможно нет в продукте | Уточнить по UI/runtime | Med | Gap |

---

## 10. Decision

**Можно вернуть без core-touch**

- Telegram как штатный канал + ACL + `chat`/`discuss` + slash-команды.
- Общая память между сессиями + Memory tab + compaction/rebuild по политике.
- Search provider для web.
- Люди: ACL identities + Memory + `people.md` + skills; опционально MCP filesystem.

**Требует sidecar / MCP (не core)**

- Внешний редактируемый реестр людей/проектов с API, если нужен не файловый UX — отдельный MCP server или sidecar.

**Не возвращать в core**

- Кастомные Telegram routing/resolver-ы, хуки в inbound/memory packer/flow ради того, что закрывается ACL + sessions + memory + files + skills.

---

## 11. Runtime audit (Web-only, `memohwebaudit`, 2026-05-12)

**Окружение:** локальный compose-проект `memohwebaudit`, Web UI `http://127.0.0.1:8082`, конфиг только из изолированного `.local-web-audit/` (без правок рабочего `config.toml`, без реального Telegram). Бот в UI: **Web Audit People**. Provider и Chat Model заданы пользователем в UI; в репозиторий секреты не выносились.

### 11.1 People identity — результат runtime

Проверено в чате (handles и отображаемые имена согласованы с `people.md` / памятью, без Go-resolver):

| Запрос (смысл) | Ожидание | Итог |
|----------------|----------|------|
| `@grvtkv` | Егор Вотяков | OK |
| «Егор» (display) | Егор Вотяков | OK |
| `@ibambets` | Глеб Крячок | OK |
| «Глеб» (display) | Глеб Крячок | OK |

**Классификация:** **native with config + files + skills + memory** — идентичность людей закрывается штатными поверхностями (workspace `people.md`, skill `web-audit-people`, ручные Memory-записи, retrieval в рантайме), **без** правок Go/core.

### 11.2 Tool trace evidence (people / files)

**Ранее зафиксированный сценарий** (запрос в духе «прочитай `people.md`…»): в UI отображалась цепочка инструментов:

1. **Use skill** `web-audit-people`
2. **List** `/data`
3. **Read** `/data/people.md`  
→ ответ с данными из файла.

**Повтор в этой сессии аудита (2026-05-12):**

- **List** `/data` — перечисление верхнего уровня (в т.ч. `people.md`, каталоги `memory`, `skills`, …).
- **Read** `/data/people.md` — по явному запросу прочитать файл; в trace: `Read` → `/data/people.md`, ответ с цитатой строки вида `@grvtkv | Егор Вотяков | …`.

**Memory-only сценарий** (инструкция не использовать `people.md` и не читать файлы, только long-term memory; вопрос «кто такой @grvtkv?»): ответ совпал с профилем; **между пользовательским сообщением и ответом в accessibility-снимке не отображались строки List/Read** (нет явного файлового tool trace на этом turn; релевантность через Memory не выводится отдельной строкой в UI).

**Запоминание факта** («Запомни: тестовый проект AuditNative связан с @grvtkv»): в UI отображено обновление **`memory/2026-05-12.md`** (новая запись с topic AuditNative и текстом факта). В **новой** Web-сессии вопрос «С каким человеком связан тестовый проект AuditNative?» → краткий ответ **`@grvtkv`** (кросс-сессия для сохранённого факта подтверждена).

**Skill / SoT** (вопрос: какое правило по источнику данных о людях): ответ модели явно указал **`people.md` как source of truth**, память — дополнительный контекст.

### 11.3 Жёсткие запреты (people identity)

- **Go people resolver не возвращать** — отдельный Go-resolver для people не нужен: сценарий закрыт Files + Skills + Memory.
- **Core changes для people identity запрещены** — не вносить правки в core/Go ради реестра людей; использовать конфигурацию, файлы, skills и Memory.

### 11.4 Telegram в этом runtime-прогоне

Реальный Telegram и токены **не** использовались. Статус: **documented / native по docs, runtime в Telegram не тестировался** (см. также `NATIVE_RUNTIME_AUDIT_RESULTS.md`).

---

*Документ создан в рамках native audit block 1; коммит по умолчанию не выполнялся.*
