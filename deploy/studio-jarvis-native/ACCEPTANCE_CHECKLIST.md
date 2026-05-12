# Studio Jarvis Native — acceptance checklist

Отметьте пункты после ручной проверки на настроенном боте. Секреты и токены в чеклист не вносить.

## Web — managed skills

- [x] **People lookup** — вопрос по известному `@handle` из `people.md`; ответ согласован с файлом и/или memory. *(Studio Jarvis Native Web smoke 2026-05-12: `Read /data/studio/people.md`.)*
- [x] **Skills catalog в UI** — `GET .../container/skills` возвращает 4 managed skill; в **Settings → Skills** и в боковой панели чата видны карточки/описания (не «No skills yet»). *(2026-05-12: создание через `POST /api/bots/{bot_id}/container/skills` эквивалентно UI **New Skill**.)*
- [x] **Skills + Q&A** — в новой сессии ответ на вопрос про правила для людей / проектов / digest ссылается на **`studio-people-source`**, **`studio-project-registry`**, **`studio-daily-digest`**; строгий `Read /data/studio/people.md` для `@grvtkv` без памяти — **pass**.
- [x] **Strict people.md** — запрос вида «строго из people.md» приводит к чтению файла и ответу только по нему. *(Тот же прогон.)*
- [x] **Strict projects/tasks** — список проектов и задач по запросу «строго из файла» совпадает с `projects.json` / `tasks.json` после `Read`. *(Тот же прогон + `chats.json`.)*

## Telegram

- [x] **DM** — те же сценарии people + projects + tasks, что в Web (см. runtime Block E.6). *(Studio Jarvis Native, `memohwebaudit`, финальный прогон 2026-05-12: **pass** после `/start` и стабилизации adapter.)*
- [x] **Group mention** — ответ после `@BotName`, без mention бот не обязан отвечать (MVP default). *(SJN: mention — **pass**.)*
- [x] **`/access` в группе** — идентичность канала и ACL отображаются ожидаемо (`/access@Bot` при необходимости). *(SJN: `/access@jarvispbweb_bot` — **pass**; Conversation Type **group**, Chat ACL **allow**.)*

## Нагрузка / порядок

- [x] **Burst A / B / C** — три подряд mention в группе; **MVP:** нативное поведение без legacy **ModeQueue**. *(SJN 2026-05-12: **BURST-A** — полный корректный ответ; **BURST-B** в пачке — в основном **reaction/ack**, без полного текста; **BURST-C** — полный корректный ответ; **BURST-B** отдельным сообщением после пачки — полный ответ по `projects.json`. Строгая семантика очереди «полный ответ на каждое из трёх подряд» **не** гарантируется штатным MVP — только **RFC / product**, если понадобится; **custom ModeQueue из archive не возвращать** автоматически.)*

## Schedule

- [x] **Schedule digest (UI smoke)** — тестовое расписание **`StudioNativeFinalScheduleSmoke`**: режим **Every N minutes (2)**, инструкция с **strict** чтением `projects.json` / `tasks.json` и маркером в ответе; в логах `memoh-server`: **`schedule completed` … `status=ok`** (два срабатывания на одном `schedule_id`); после проверки расписание **удалено** через UI (**`DELETE …/schedule/{id}` → 204**). *(Открытая сессия schedule в UI для полного трейса Read не просматривалась; при необходимости — повторить и открыть сессию из сайдбара Schedule.)*

## Политика репозитория

- [x] **No core patches** — в ветке baseline нет возврата Go/Vue/sqlc/inbound custom под этот MVP.
- [x] **Old custom not restored** — нет Go people resolver, sqlc people patches, packer hooks для lookup, harvester/custom cron из archive, merge archive-heavy-fork как источника кода.

## Документация

- [x] Команда знает, где SoT: **`/data/studio/people.md`** и **`/data/studio/*.json`**.

---

## Rollout log — Studio Jarvis Native (local `memohwebaudit`, 2026-05-12)

Короткая фиксация прогона Cursor + Web UI на `http://127.0.0.1:8082` (ветка `studio/native-baseline-20260512`). Секреты не использовались.

**Инвариант workspace (bundle):** на volume `workspace-data/<bot_id>/` каталог **`studio/`** в корне workspace соответствует агентским путям **`/data/studio/*`** (не создавать зеркало `data/studio/` на диске — иначе `Read /data/studio/...` не находит файлы). Аналогично **`skills/<name>/SKILL.md`** → **`/data/skills/<name>/SKILL.md`**.

### Web smoke (после layout-fix), бот Studio Jarvis Native

**Bot id:** `994b7558-a192-4a5a-991d-b6dac6ca647e` · **Chat model:** GPT-5.4 mini · **Core:** без изменений (только проверка в UI + volume).

| Чеклист | Статус | Комментарий |
|---------|--------|---------------|
| Web people strict (`people.md`) | **pass** | Вопрос: прочитать `/data/studio/people.md`, кто `@grvtkv` без памяти. Трейс: **Read** `/data/studio/people.md` (+ при необходимости **Read** `/data`). Ответ согласован с шаблоном в файле. |
| Web strict `projects.json` | **pass** | Перечень проектов строго из файла; трейс: **Read** `/data/studio/projects.json`. |
| Web strict `chats.json` / `tasks.json` | **pass** | Чаты и задачи **AuditNative** строго из JSON; трейс: **Read** `/data/studio/chats.json`, **Read** `/data/studio/tasks.json`. |
| Web `events.example.jsonl` | **pass** | Доп. проверка: первые строки файла; трейс: **Read** `/data/studio/events.example.jsonl`. |
| Behavior / источники (вопрос E) | **pass** | Модель перечислила SoT: `people.md`, `projects.json`, `chats.json`, `tasks.json` под `/data/studio/`. |
| Files → Refresh + дерево `/data` | **pass** | Папка **`studio`** видна под `/data`; после smoke в треде отображаются кнопки путей ко всем перечисленным файлам. |
| Skills → Refresh + 4 имени в UI | **pass** | Ранее: только копирование `skills/` на volume → пустой `GET .../container/skills` → «No skills yet». Исправление: **`POST /api/bots/{id}/container/skills`** (или UI **New Skill**) пишет в **`/data/skills/<name>/SKILL.md`** через bridge. В **Settings → Skills** отображаются 4 карточки **Managed / Effective**; в чате в сайдбаре — описания skills. В `studio-daily-digest` исправлен YAML `description` (кавычки из‑за `Schedule:`). |
| Telegram DM (SJN) | **pass** | People/projects/tasks + strict `/data/studio/*.md` / `*.json` — согласовано с Web-слоем (skills/files/memory). |
| Telegram group + `/access` + strict files (SJN) | **pass (MVP)** | Mention — pass; `/access@jarvispbweb_bot` — group, ACL allow; strict lookup people/projects/tasks — pass. |
| Burst A/B/C (SJN, native) | **pass with caveat** | A — полный ответ; B в пачке — reaction/ack; C — полный ответ; B отдельно — полный ответ по `projects.json`. **Не** строгая очередь «3 полных ответа подряд» без RFC; **ModeQueue custom не возвращать** для MVP. |
| Schedule digest smoke | **pass (UI + server log)** | `StudioNativeFinalScheduleSmoke`: создание → `schedule completed` ok → удаление UI. |
| No core patches | **да** | Только docs + workspace файлы; Go/Vue/sqlc/db не менялись. |
| Old custom not restored | **да** | Только штатный Memoh + bundle. |

### Ручные тексты для Telegram (после включения Platforms → Telegram)

Подставьте реальный `@username` бота вместо `@BOT_USERNAME`.

**DM**

1. Кто такой @grvtkv? Сначала Read `/data/studio/people.md`, потом ответь.
2. Перечисли проекты строго из `/data/studio/projects.json`.
3. Задачи для `project_id` `proj-audit-native` строго из `/data/studio/tasks.json`.

**Group**

1. `@BOT_USERNAME` Кто такой @ibambets? Read `/data/studio/people.md`.
2. `/access@BOT_USERNAME`
3. `@BOT_USERNAME` BURST-A кто такой @grvtkv
4. `@BOT_USERNAME` BURST-B какие проекты есть
5. `@BOT_USERNAME` BURST-C какие задачи по AuditNative
