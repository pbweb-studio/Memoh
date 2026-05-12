# Studio Jarvis layer vs Memoh core — план разделения

Документ зафиксирован на **native baseline** (`studio/native-baseline-20260512`). Архив тяжёлого fork (`studio/archive-heavy-fork-20260512-1245`) используется **только как reference** (`git show`), без merge и без возврата кода в baseline.

Ссылки на upstream-документацию в репозитории относительно этого файла: каталог `docs/docs/` (VitePress).

---

## 1. Цель архитектуры

- **Memoh core** остаётся синхронизируемым с `upstream/main` без постоянных конфликтов.
- **Studio Jarvis** — тонкий, явно ограниченный слой: deploy, документация, данные в workspace, skills, MCP/sidecar — всё, что можно выразить **без** правок ядра БД, inbound-пайплайна, memory packer и conversation flow.
- Приоритет решений: **UI → documented config → skills → memory → workspace files → MCP/tools → documented upstream behavior → только потом custom code** (см. также `NATIVE_CAPABILITY_AUDIT_PLAN.md`).

---

## 2. Что считается Memoh core и не должно правиться

Под «не править» имеется в виду: нет локальных изменений без upstream-merge и отдельного решения; нет «быстрых» патчей в зонах ниже.

- **Хранилище и SQL**: `db/**`, `internal/db/**`, sqlc-генерация, миграции, интерфейсы store.
- **Каналы и inbound**: `internal/channel/inbound/**`, адаптеры каналов (кроме политики «не трогать без причины»), маршрутизация сообщений, очереди.
- **Память**: адаптеры memory, упаковка контекста (`context_packer` и смежное), провайдеры — только в русле upstream.
- **Conversation / flow**: резолверы сессий, типы сессий, merge с upstream API.
- **Общие handlers / server / swagger / web app**: всё, что общее с продуктом Memoh; изменения только если это официальные extension points или после согласования с sync.
- **Migrations и схема БД**: только через upstream и штатные инструменты.

---

## 3. Что считается Studio Jarvis layer

- Каталоги и пакеты вида **`internal/studio*`**, **`internal/channel/studiochat/`** (если возвращаются) — изолированная логика Studio.
- **`deploy/studio-jarvis/**`** — compose, образы, скрипты выкладки Studio (не замена core compose Memoh без документации).
- **`docs/studio/**`** — политики, runbook, планы аудита, этот документ.
- **Данные и контракты на диске** в рантайме: например выделенное дерево под Studio в workspace бота (конвенция вида `/data/studio/**` или переменная окружения вроде `MEMOH_STUDIO_DATA_DIR` — как было в архиве; путь не коммитится как секрет).
- **Skills** — поведение и политики Studio как markdown под управляемыми skills (`/data/skills/...` по доке Memoh).
- **MCP и sidecar** — внешние процессы для JSON-реестров, дашбордов, интеграций, если UI Memoh недостаточно.

---

## 4. Штатные extension points Memoh по документации

Ниже — не «плагины к React», а **поддерживаемые поверхности продукта**, на которые опираться в первую очередь.

| Поверхность | Документация | Назначение |
|-------------|--------------|------------|
| Bot Detail tabs (General, Platforms, Memory, Files, MCP, Skills, Schedule, Heartbeat, Access, …) | [Bot Management](../docs/getting-started/bot.md) | Конфигурация моделей, memory/search, каналов, ACL, расписаний без кода. |
| Skills (managed + Supermarket) | [Skills](../docs/getting-started/skills.md) | `SKILL.md`, корни `/data/skills/`, UI включения/отключения. |
| Memory provider + Memory tab | [Memory](../docs/getting-started/memory.md), [Memory providers](../docs/memory-providers/index.md) | Долговременная память, поиск, compaction, rebuild. |
| Search providers | [Search provider](../docs/getting-started/search-provider.md) | Привязка поиска к боту. |
| MCP (stdio / remote / OAuth) | [MCP](../docs/getting-started/mcp.md) | Инструменты и контекст из внешних серверов. |
| Workspace files | [Files](../docs/getting-started/files.md) | Файлы в контейнере бота; совместно с MCP filesystem. |
| Sessions + `/new`, discuss | [Sessions](../docs/getting-started/sessions.md) | Группы vs DM, `discuss` для «наблюдения» в группе. |
| ACL + `/access` | [Access](../docs/getting-started/access.md), [Slash commands](../docs/getting-started/slash-commands.md) | Идентичности каналов, правила доступа. |
| Schedule (cron + API) | [Schedule](../docs/getting-started/schedule.md) | Периодические задачи, в т.ч. «дайджест» как текст команды агенту. |
| Heartbeat | [Heartbeat](../docs/getting-started/heartbeat.md) | Периодический автономный прогон с skills/MCP. |
| Workspace backends | [Workspace backends](../docs/installation/workspace-backends.md) | `config.toml` `[container]` — где живут воркспейсы (не смешивать с секретами в доке). |
| Telegram channel | [Telegram](../docs/channels/telegram.md) | Токен, включение канала, описание возможностей (streaming, вложения). |

**Web/UI «extension points» в смысле сторонних плагинов** в официальных getting-started страницах **не описаны** как произвольная загрузка UI-модулей. Расширение — через **данные бота** (files, skills), **MCP**, **REST там, где он задокументирован** (пример: `POST /api/bots/{bot_id}/schedule` в [Schedule](../docs/getting-started/schedule.md)). Отдельные мини-приложения уровня архивного Studio Control **не** являются штатным extension point Memoh-доков.

---

## 5. Карта прошлых Studio возможностей (reference: archive)

Источник контекста без checkout: `git show studio/archive-heavy-fork-20260512-1245:docs/studio_jarvis_scenarios.md` и `docs/studio/UPSTREAM_SYNC.md` в том же ref.

| Возможность | Кратко что было в Studio fork |
|-------------|-------------------------------|
| Telegram group / control use | Отдельный сценарий control-группы vs обычный чат; хаб JSON на диске; пересечение с cross-chat и классификаторами в flow. |
| Cross-chat memory / search | Комбинация vector memory Memoh + политики «когда не подмешивать историю». |
| People identity | Роли/контекст в Studio поверх channel identity Memoh. |
| Projects / chats registry | `studio_projects_registry.json` как SoT операционных сущностей (проекты, привязки, задачи). |
| Tasks / important / meetings / overdue | Логика вокруг hub + LLM/списки; частично без LLM (списки). |
| Skills UI / managed skills | Можно совместить с штатным Skills Memoh. |
| Daily digest / schedules | В Studio могли быть кастомные триггеры; в Memoh есть Schedule + Heartbeat. |
| Studio Control Mini App | WebApp `/studio/app`, API `/studio/api/*`, auth `X-Telegram-Init-Data` — вне документированных extension points Memoh. |
| Deploy bundle | Скрипты/compose под Studio (`deploy/studio-jarvis` в архивной политике overlay). |

---

## 6. Классификация по возможностям

Легенда классов: **native** | **native with config** | **files/skills/memory** | **MCP/tool** | **sidecar** | **thin overlay** | **should not restore**

| Возможность | Класс | Комментарий |
|-------------|--------|-------------|
| Telegram group / control use | native + **native with config** + опционально **files/skills/memory** | Группы: штатный `discuss` ([Sessions](../docs/getting-started/sessions.md)). Control-«режим» без кода: ACL ([Access](../docs/getting-started/access.md)) + skills, ограничивающие ответы; реестр операций — в файлах/MCP, не в core. |
| Cross-chat memory / search | **native with config** | Memory provider + search provider; политики «что вспоминать» — через skills и память, не патч context_packer. |
| People identity | **native with config** + **files/skills/memory** | Channel Identity в ACL; расширенные «роли людей» — в memory или markdown в workspace. |
| Projects / chats registry | **files/skills/memory** или **MCP/tool** или **sidecar** | JSON SoT логичнее как файл в workspace, skill-инструкции, или MCP-сервер с CRUD; не таблицы core без миграций upstream. |
| Tasks / important / meetings / overdue | **native** (Schedule) + **files/skills/memory** | [Schedule](../docs/getting-started/schedule.md) + tool `schedule`; напоминания — cron-команды агенту. Хранение списков — файлы/memory. |
| Skills UI / managed skills | **native** | [Skills](../docs/getting-started/skills.md), Supermarket. |
| Daily digest | **native** | Schedule «раз в день» + команда на сводку; при необходимости Heartbeat для фона. |
| Studio Control Mini App | **sidecar** или **MCP/tool**; **should not restore** в core | Воспроизвести функции отдельным мини-сервисом + MCP/ссылки; **не** встраивать в `apps/web` и generic handlers без согласования. |
| Deploy bundle | **thin overlay** (разрешённая зона) | Только `deploy/studio-jarvis/**`, не дублировать upstream `deploy/` там, где это ломает обновления. |

---

## 7. Запрещённые core-touch зоны

Согласовано с политикой из архивного `docs/studio/UPSTREAM_SYNC.md` и общим здравым смыслом sync:

| Зона | Почему запрет |
|------|----------------|
| `db/**`, sqlc, `internal/db/**`, store interfaces | Ломает миграции и совместимость с upstream. |
| `internal/channel/inbound/**`, core channel routing | Регрессии всех каналов, сложный merge. |
| Memory core / context packer | Тонкая производительность и контракты retrieval. |
| `internal/conversation/flow/**`, `internal/conversation/types.go` | Сессии, discuss/chat, конфликты при каждом sync. |
| Generic `internal/handlers/**` без изоляции | Риск затронуть весь API/UI. |
| Migrations вне upstream | Расхождение схемы. |
| `apps/web/**`, `spec/swagger*` «под Studio» | Нет документированного UI-plugin API; только координация с upstream или отдельный фронт sidecar. |

---

## 8. Разрешённые зоны для Studio layer

| Зона | Назначение |
|------|------------|
| `deploy/studio-jarvis/**` | Сборка/compose только Studio-окружения; не заменять официальный способ установки Memoh без причины. |
| `docs/studio/**` | Документация, планы, runbooks. |
| Workspace data contracts (`/data/studio/**` или согласованный root через env) | JSON, markdown, артефакты SoT; бэкап как файлы. |
| Skills через штатный механизм | Managed skills в `/data/skills/<name>/SKILL.md`. |
| MCP / sidecar | HTTP/SSE или stdio MCP для реестров, отчётов, интеграций. |
| Новые изолированные пакеты `internal/studio*` | Только после чеклиста п. 10 и если MCP/files не покрывают. |

На **текущем native baseline** часть путей из архива физически отсутствует — это ожидаемо; слой добавляется отдельными коммитами поверх sync-ветки, не смешиваясь с core.

---

## 9. Migration plan from archived heavy fork

| Категория | Действие |
|-----------|----------|
| **Keep (идеи и контракты)** | Семантика control vs group chat; SoT реестра; политики ACL; навыки формулировок — в docs + skills. |
| **Reimplement natively** | Дайджесты и напоминания → Schedule + Heartbeat; идентичности → ACL + `/access`; группы → discuss + sessions doc. |
| **Move to MCP / sidecar** | JSON-реестр с богатой структурой, REST для мини-панели, фоновые джобы вне agent loop — отдельный сервис + MCP tools для чтения/записи при необходимости. |
| **Drop** | Дублирование того, что Memoh уже даёт UI; глубокие хуки в context_packer/flow ради того, что решается skills+memory; мини-app внутри monolith web без долгосрочной поддержки. |

Процедура sync остаётся: ветка от актуального Studio tracking → `merge upstream/main` → конфликты в core **в пользу upstream** → восстановить минимум overlay (см. архивный UPSTREAM_SYNC).

---

## 10. Decision checklist перед любым custom code

1. **Какая страница upstream-doc прочитана?** (ссылка на `docs/docs/...`.)
2. **Почему недостаточно config?** (какие поля UI / `config.toml` пробовали.)
3. **Почему недостаточно skills + files + memory?**
4. **Почему недостаточно MCP или sidecar?**
5. **Минимальная область кода** (конкретные пакеты/файлы только из разрешённых зон).
6. **Rollback:** откат ветки / удаление overlay-пакета / отключение MCP; данные только в `/data/studio` или skills.

---

## Таблица: Feature → путь и риск

| Feature | Desired behavior | Native path | Needs custom? | Recommended home | Risk | Notes |
|---------|------------------|-------------|----------------|------------------|------|-------|
| Telegram DM/group | Бот отвечает в DM и группах по политике | [Telegram](../docs/channels/telegram.md) + [Sessions](../docs/getting-started/sessions.md) (`discuss`) | Нет | Platforms tab + ACL | Low | Control-режим — дисциплина skills, не патч inbound. |
| Control chat discipline | Меньше «болтливости», фокус на командах | `discuss`, skills | Нет | Skills + session type | Low | |
| Cross-chat context | Помнить факты между чатами | Memory provider + retrieval | Нет | Memory tab | Low | Не дублировать второй vector store в core. |
| Web search | Актуальные данные из сети | Search provider | Нет | General tab | Low | |
| People / roles | Кто есть кто для бота | ACL Channel Identity + memory entries | Обычно нет | Access + Memory | Low | |
| Project list SoT | Единый список проектов | Files (JSON) + bot reads via tools | Часто нет | `/data/...` markdown/json в workspace | Med | При конкуренции записей — MCP с блокировками. |
| Chat registry | Привязки чат ↔ проект | Files или MCP | Возможен MCP | MCP filesystem / custom MCP | Med | |
| Tasks / overdue | Напоминания и статусы | Schedule + команда агенту | Нет | Schedule tab + memory | Low | |
| Meetings summary | После встречи сводка | Schedule или по требованию в чат | Нет | Schedule / skills | Low | |
| Managed skills | Редактируемые модули промпта | Skills UI | Нет | Skills tab | Low | |
| Daily digest | Раз в день отчёт | Cron in Schedule | Нет | [Schedule](../docs/getting-started/schedule.md) | Low | |
| Heartbeat maintenance | Фоновые проверки | Heartbeat tab | Нет | [Heartbeat](../docs/getting-started/heartbeat.md) | Low | |
| Structured hub lists | Быстрые списки без LLM | MCP tool returning JSON или статические files | Да (вне core) | Sidecar MCP | Med | Не восстанавливать `control_plane_hub_lists` в core без RFC. |
| Studio Mini App UI | Отдельный web UI под Telegram | Нет в upstream docs | Да | Sidecar web + Telegram deep link | High | Не встраивать в Memoh web как неофициальный fork UI. |
| Deploy tarball pipeline | Сборка артефакта для VPS | Нет в product docs | Да (ops) | `deploy/studio-jarvis/**` | Med | Сборка локально/CI, не на VPS. |

---

## Версионирование документа

- **Baseline ветка:** `studio/native-baseline-20260512`
- **Архив reference:** `studio/archive-heavy-fork-20260512-1245`
- При смене upstream после merge — перечитать соответствующие страницы `docs/docs` и обновить только этот файл (отдельный doc commit).
