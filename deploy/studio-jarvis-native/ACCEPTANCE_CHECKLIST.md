# Studio Jarvis Native — acceptance checklist

Отметьте пункты после ручной проверки на настроенном боте. Секреты и токены в чеклист не вносить.

## Web

- [ ] **People lookup** — вопрос по известному `@handle` из `people.md`; ответ согласован с файлом и/или memory.
- [ ] **Strict people.md** — запрос вида «строго из people.md» приводит к чтению файла и ответу только по нему.
- [ ] **Strict projects/tasks** — список проектов и задач по запросу «строго из файла» совпадает с `projects.json` / `tasks.json` после `Read`.

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
