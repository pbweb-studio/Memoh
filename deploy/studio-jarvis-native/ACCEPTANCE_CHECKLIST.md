# Studio Jarvis Native — acceptance checklist

Отметьте пункты после ручной проверки на настроенном боте. Секреты и токены в чеклист не вносить.

## Web — managed skills

- [x] **People lookup** — вопрос по известному `@handle` из `people.md`; ответ согласован с файлом и/или memory. *(Studio Jarvis Native Web smoke 2026-05-12: `Read /data/studio/people.md`.)*
- [x] **Skills catalog в UI** — `GET .../container/skills` возвращает 4 managed skill; в **Settings → Skills** и в боковой панели чата видны карточки/описания (не «No skills yet»). *(2026-05-12: создание через `POST /api/bots/{bot_id}/container/skills` эквивалентно UI **New Skill**.)*
- [x] **Skills + Q&A** — в новой сессии ответ на вопрос про правила для людей / проектов / digest ссылается на **`studio-people-source`**, **`studio-project-registry`**, **`studio-daily-digest`**; строгий `Read /data/studio/people.md` для `@grvtkv` без памяти — **pass**.
- [x] **Strict people.md** — запрос вида «строго из people.md» приводит к чтению файла и ответу только по нему. *(Тот же прогон.)*
- [x] **Strict projects/tasks** — список проектов и задач по запросу «строго из файла» совпадает с `projects.json` / `tasks.json` после `Read`. *(Тот же прогон + `chats.json`.)*

## Telegram

- [ ] **DM** — те же сценарии people + projects + tasks, что в Web (см. runtime Block E.6).
- [ ] **Group mention** — ответ после `@BotName`, без mention бот не обязан отвечать (MVP default).
- [ ] **`/access` в группе** — идентичность канала и ACL отображаются ожидаемо (`/access@Bot` при необходимости).

## Нагрузка / порядок

- [ ] **Burst A / B / C** — три подряд mention в группе; три ответа, порядок A → B → C; без legacy **ModeQueue**.

## Schedule

- [ ] **Schedule digest** — срабатывание по cron; сессия типа `schedule`; в истории видны чтения JSON; вывод краткий и помеченный (см. Block G).

## Политика репозитория

- [ ] **No core patches** — в ветке baseline нет возврата Go/Vue/sqlc/inbound custom под этот MVP.
- [ ] **Old custom not restored** — нет Go people resolver, sqlc people patches, packer hooks для lookup, harvester/custom cron из archive, merge archive-heavy-fork как источника кода.

## Документация

- [ ] Команда знает, где SoT: **`/data/studio/people.md`** и **`/data/studio/*.json`**.

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
| Telegram DM / group / `/access` / burst | **не запускалось** | В этом проходе не настраивалось. |
| Schedule digest smoke | **не запускалось** | В этом проходе не настраивалось. |
| No core patches | **да** | Только docs + workspace файлы; Go/Vue/sqlc/db не менялись. |
| Old custom not restored | **да** | Только штатный Memoh + bundle. |
