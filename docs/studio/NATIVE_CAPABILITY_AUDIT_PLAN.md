# План аудита штатных возможностей Memoh (native baseline)

## Контекст веток

| Роль | Ветка | Назначение |
|------|-------|------------|
| Архив Studio / тяжёлого fork | `studio/archive-heavy-fork-20260512-1245` | Снимок прежнего состояния (Studio Jarvis sync / кастом поверх upstream). Ничего не удаляется из истории; возврат к этой ветке = возврат к накопленному fork. |
| Чистая baseline для аудита | `studio/native-baseline-20260512` | Создана от `upstream/main` без переноса Studio custom; здесь только upstream + документация по аудиту. |

**Upstream:** `https://github.com/memohai/Memoh.git` (`upstream`). На момент baseline `origin` и `upstream` оба указывают на `memohai/Memoh` — `origin` не менялся.

## Принцип аудита (порядок проверки)

Сначала проверять то, что Memoh даёт **из коробки** или через **документированную** конфигурацию и UI — без доработок core:

1. UI и сценарии настройки (что видит пользователь).
2. Core config (`config.toml` и штатные профили) — без выкладки секретов в отчёты.
3. Skills (регистрация, загрузка, ограничения по документации).
4. Memory / search (встроенные провайдеры, кросс-чат по докам).
5. Workspace files и интеграция с файловой системой / MCP filesystem (как описано upstream).
6. Поведение, зафиксированное в upstream-документации (channels, sessions, tasks — где это относится к файлам или native memory).

Только после этого — решения про **тонкий overlay** или sidecar, если штатных средств недостаточно. **Custom Studio-код в baseline не переносится.**

## Список возможностей для штатной проверки

1. **Telegram** — каналы/группы, inbound/outbound, ограничения по [официальной документации Memoh](../docs/channels/telegram.md) (при необходимости — `../docs/zh/channels/telegram.md`).
2. **Cross-chat memory / search** — встроенный memory provider, compaction, поиск по памяти согласно docs (getting-started/memory, search-provider).
3. **People / identity** — через memory, workspace files и skills (без хардкода в core до отдельного решения).
4. **Skills через UI** — supermarket, загрузка, лимиты, см. getting-started/skills.
5. **Workspace files / MCP filesystem** — workspace-backends, MCP в getting-started/mcp.
6. **Projects / chats / tasks** — что upstream отдаёт через файлы или native memory/sessions (sessions, files, schedule — по докам).
7. **Schedule / heartbeat / daily digest** — **только если** это явно описано в upstream-документации для выбранной версии (не предполагать Studio-поведение).
8. **Web / browser / tools** — только если штатно доступны в Memoh (MCP, documented tools); не смешивать с незадокументированными расширениями.

## Классификация исходов (таблица)

| Класс | Смысл | Действие |
|-------|--------|----------|
| **native** | Работает в vanilla Memoh без кода | Зафиксировать конфиг и сценарий; использовать как основу. |
| **native with config** | Нужны только настройки / ключи / провайдеры | Документировать минимальный config; не трогать core. |
| **needs sidecar** | Нужен отдельный сервис/процесс вне агента | План интеграции (API, сеть, деплой) — отдельное решение. |
| **needs thin overlay** | Недостаточно upstream, но достаточно тонкого слоя | Только `internal/studio*` / документированные точки расширения; без переписывания Memoh core. |
| **do not restore** | Несёт технический долг или дублирует upstream | Не переносить в baseline; при необходимости оставить только идею в архивной ветке. |

## Запреты

- **Не трогать Memoh core** без отдельного явного решения (отдельная задача, review, согласование с upstream sync).
- Не смешивать этот baseline с коммитами Studio fork: baseline остаётся эталоном «чистого Memoh + план».

## Следующий шаг после baseline

Пройти таблицу классификации по каждому пункту списка выше, обновляя этот документ или отдельный отчёт ссылками на конкретные страницы docs и воспроизводимые шаги (без секретов).
