# Studio Jarvis — native-first bundle (clean Memoh)

Этот каталог — **готовый шаблон** для **Studio Jarvis Native** на **чистом Memoh core**: данные в workspace, поведение через **managed skills**, каналы через **Platforms**, периодика через **Schedule**. **Исходный код Memoh (Go/Vue/sqlc/db) не меняется.**

## Что внутри

| Путь | Назначение |
|------|------------|
| `data/` | Примеры для **`/data/studio/`**: `people.md`, JSON-реестры, **`stat_sources.example.json`**, **`events/leads-*.example.jsonl`**. |
| `skills/` | Шаблоны `SKILL.md` (в т.ч. **`studio-chat-stats`**, **`studio-telegram-import`**) — копировать в managed skills через UI/API. |
| `tools/` | **`import_telegram_html.py`** — детерминированный импорт Telegram Desktop HTML → JSONL (ставится в `/data/studio/tools/` на рантайме). |
| `RUNBOOK.md` | Пошаговая настройка через UI (без секретов в тексте). |
| `ACCEPTANCE_CHECKLIST.md` | Ручная проверка после деплоя конфигурации. |

## Принципы

- **Memoh core** — upstream-first; патчи core для этого MVP **не** предполагаются.
- **Данные** — через **Files workspace**: `/data/studio/people.md`, `projects.json`, `chats.json`, `tasks.json`, **`stat_sources.json`**, **`events/leads-YYYY-MM-DD.jsonl`** (см. `docs/studio/CHAT_STATS_MVP_RUNBOOK.md`).
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

- [`docs/studio/CHAT_STATS_NATIVE_PLAN.md`](../../docs/studio/CHAT_STATS_NATIVE_PLAN.md)
- [`docs/studio/CHAT_STATS_MVP_RUNBOOK.md`](../../docs/studio/CHAT_STATS_MVP_RUNBOOK.md)
- [`docs/studio/STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md`](../../docs/studio/STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md)
- [`docs/studio/NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md`](../../docs/studio/NATIVE_NEXT_ARCHITECTURE_RECOMMENDATION.md)
- [`docs/studio/STUDIO_RESTORE_DECISION_MATRIX.md`](../../docs/studio/STUDIO_RESTORE_DECISION_MATRIX.md)
- [`docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md`](../../docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md)

## Как использовать

> **Git:** в корне репозитория правило `.gitignore` игнорирует любой путь с сегментом `data`. Шаблоны в `deploy/studio-jarvis-native/data/` уже учтены в истории; при локальном первом добавлении используйте `git add -f deploy/studio-jarvis-native/data/`.

1. Прочитайте **`RUNBOOK.md`** и выполните шаги в UI.
2. Скопируйте содержимое `data/*` в **`/data/studio/`** бота (`stat_sources.json` из `stat_sources.example.json`, события лидов из `data/events/leads-*.example.jsonl`; при необходимости переименуйте `events.example.jsonl` в рабочий `events.jsonl`).
3. Создайте managed skills и вставьте тексты из `skills/*/SKILL.md`.
4. Пройдите **`ACCEPTANCE_CHECKLIST.md`**.

Аудит runtime: коммиты `29830b3a` (Telegram group), `73786070` (Schedule).
