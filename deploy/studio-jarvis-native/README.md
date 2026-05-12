# Studio Jarvis — native-first bundle (clean Memoh)

Этот каталог — **готовый шаблон** для **Studio Jarvis Native** на **чистом Memoh core**: данные в workspace, поведение через **managed skills**, каналы через **Platforms**, периодика через **Schedule**. **Исходный код Memoh (Go/Vue/sqlc/db) не меняется.**

## Что внутри

| Путь | Назначение |
|------|------------|
| `data/` | Примеры файлов для копирования в workspace бота под **`/data/studio/`** (через Files tab / upload). |
| `skills/` | Шаблоны `SKILL.md` для копирования в **`/data/skills/<name>/`** после создания skill в UI. |
| `RUNBOOK.md` | Пошаговая настройка через UI (без секретов в тексте). |
| `ACCEPTANCE_CHECKLIST.md` | Ручная проверка после деплоя конфигурации. |

## Принципы

- **Memoh core** — upstream-first; патчи core для этого MVP **не** предполагаются.
- **Данные** — только через **Files workspace**: `/data/studio/people.md`, `projects.json`, `chats.json`, `tasks.json` (и опционально журнал событий по образцу `events.example.jsonl`).
- **Поведение** — **managed skills** в `/data/skills/.../SKILL.md` + Memory provider + ACL.
- **Telegram** — **Platforms** в UI (токен хранится в конфигурации приложения; **не** кладите токены в эти markdown-файлы).
- **Digest** — **Schedule** (cron + instruction), **не** custom harvester/cron из archive.
- **Archive** `studio/archive-heavy-fork-20260512-1245` — **только reference** (`git show`), **не** merge source и **не** источник Studio custom в core.

## Что намеренно не возвращаем (MVP)

- Старый **Go people resolver**.
- Патчи **db/sqlc/store** под people или studio registry в core.
- **inbound/channel** patches для сценариев DM / group MVP, закрытых runtime-аудитом.
- **Legacy ModeQueue** custom.
- **memory context packer hooks** для people/project lookup.
- **Old task harvester / custom cron** из archive (замена — Schedule + при необходимости Heartbeat / MCP по RFC).

## Связанные документы в репозитории

- [`docs/studio/STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md`](../../docs/studio/STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md)
- [`docs/studio/NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md`](../../docs/studio/NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md)
- [`docs/studio/STUDIO_RESTORE_DECISION_MATRIX.md`](../../docs/studio/STUDIO_RESTORE_DECISION_MATRIX.md)
- [`docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md`](../../docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md)

## Как использовать

> **Git:** в корне репозитория правило `.gitignore` игнорирует любой путь с сегментом `data`. Шаблоны в `deploy/studio-jarvis-native/data/` уже учтены в истории; при локальном первом добавлении используйте `git add -f deploy/studio-jarvis-native/data/`.

1. Прочитайте **`RUNBOOK.md`** и выполните шаги в UI.
2. Скопируйте содержимое `data/*` в **`/data/studio/`** бота (переименуйте `events.example.jsonl` при необходимости в рабочий `events.jsonl`).
3. Создайте managed skills и вставьте тексты из `skills/*/SKILL.md`.
4. Пройдите **`ACCEPTANCE_CHECKLIST.md`**.

Аудит runtime: коммиты `29830b3a` (Telegram group), `73786070` (Schedule).
