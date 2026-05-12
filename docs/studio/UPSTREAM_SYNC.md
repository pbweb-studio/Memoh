# Studio Jarvis — синхронизация с upstream Memoh

Документ для безопасных будущих обновлений: upstream core остаётся базой, Studio Jarvis — тонкий overlay поверх него.

## Политика remotes (native baseline / Studio overlay, 2026-05)

| Remote | URL | Назначение |
|--------|-----|------------|
| **`upstream`** | `https://github.com/memohai/Memoh.git` | Официальный Memoh — **источник правды** для `main` и core. |
| **`origin`** | Часто **тот же** URL, что и `upstream` (`memohai/Memoh`), если репозиторий клонирован напрямую с организации. **Push в `memohai/Memoh` без write-доступа даёт 403** — это нормально для внешних контрибьюторов. |
| **`fork`** | `https://github.com/pbweb-studio/Memoh.git` | **Персональный/командный fork** для **всех рабочих веток Studio** (baseline, sync, фичи). Сюда делается **`git push`**; в организацию — через **PR**. |

Перед любой синхронизацией: `git fetch upstream` и `git fetch fork` (при необходимости `git fetch origin`).

### Куда пушить Studio-ветки

- **Рабочие ветки Studio** (в т.ч. **`studio/native-baseline-20260512`**) нужно пушить в **`fork`**, а **не** ожидать успешного push в `memohai/Memoh` с машины без org-write.
- Пример: `git push -u fork studio/native-baseline-20260512`
- Публичная ветка на fork (пример текущего baseline): `https://github.com/pbweb-studio/Memoh/tree/studio/native-baseline-20260512`
- В **`memohai/Memoh`** изменения попадают через **Pull Request** с ветки на `fork` (или по процессу мейнтейнеров). **`git push` в upstream организации без прав — не использовать; force push в `memohai/Memoh` запрещён.**

## Процедура upstream sync (merge, не массовый rebase)

1. Убедиться, что рабочее дерево чистое по отслеживаемым файлам; локальные `.cursor/` (кроме явно версионируемых правил), `memory-bank/` вне Memoh — не коммитить (см. ниже) — при необходимости добавить в `.git/info/exclude`.
2. `git fetch upstream`
3. Создать ветку `studio/upstream-sync-YYYYMMDD` от актуальной baseline/feature-ветки (как принято в репо).
4. `git merge upstream/main` (предпочтительно **merge**, не rebase длинной истории).
5. После merge — **sanity-check diff к `upstream/main`**:
   - **Protected core** (`internal/db/**`, `internal/channel/inbound/**`, `internal/channel/adapters/**`, `internal/conversation/flow/**`, `internal/memory/**`, `internal/skills/**`, `cmd/agent/**`, миграции, generated sqlc): отличий **не должно быть**, кроме случаев с **явным RFC** и согласованием (см. `.cursor/rules/10-core-protection.mdc`, `docs/studio/NATIVE_CORE_DEPENDENCY_AUDIT.md`).
   - **`apps/desktop`**, **`apps/web`**, **`mise.toml`**: держать **parity с `upstream/main`**, если нет **явного** Studio-решения с документированным отступлением; иначе восстановить из upstream (`git checkout upstream/main -- <paths>`) отдельным коммитом, как для baseline.
   - **Studio-слой** должен по-прежнему укладываться в **overlay / docs / rules / native bundle** (например `deploy/studio-jarvis-native/**`, `docs/studio/**`, `docs/upstream/memoh/**`, `.cursor/rules/*.mdc`, расширения `AGENTS.md`).
6. Конфликты: **сначала принять upstream** для core и для app/tooling parity, затем минимально восстановить Studio overlay.
7. При изменении SQL в `db/*/queries/*.sql` — `sqlc generate` (Docker: `sqlc/sqlc:1.29.0`, корень репо смонтирован в `/src`).
8. Проверки (см. раздел ниже), затем коммит вида `chore(studio): sync with upstream memoh`.
9. **Пуш результата:** в **`fork`**, не в org: `git push -u fork <ветка>`. **Без `--force`** (в т.ч. на ветках baseline).

## Force push

- **Не применять** `--force` / `--force-with-lease` к **`memohai/Memoh`**.
- Для веток **native baseline** на **`fork`** также избегать force-push, чтобы не ломать историю ревью и ссылок; обычный `git push` достаточен.

## Каталоги и зоны Studio overlay

Типичный Studio-слой (расширять по мере появления новых `studio*` пакетов):

- `internal/studio*`, `internal/channel/studiochat/`
- **`deploy/studio-jarvis-native/`** (native baseline bundle), при необходимости legacy `deploy/studio-jarvis/` из старых доков — не смешивать без явного решения
- `docs/studio/`, `docs/upstream/memoh/`, `.cursor/rules/*.mdc` (версионируемые guardrails), фрагменты `AGENTS.md` про Studio
- Точечные хуки в core: `internal/handlers/*` (studio-only файлы и регистрация), `internal/memory/*`, `internal/conversation/*`, `internal/channel/inbound/*` (осторожно: пересекается с core)
- `apps/web/*`, `spec/swagger*` — при изменениях API/UI со стороны upstream

## Core-файлы, требующие осторожности

При merge чаще всего конфликтуют или ломают сборку, если не сверить с upstream:

- `internal/memory/adapters/builtin/context_packer.go`
- `internal/conversation/flow/*`, `internal/conversation/types.go`
- `internal/handlers/*`
- `internal/channel/inbound/channel.go` (конструктор, `QueuedTask`, `NewIdentityResolver` — держать в соответствии с upstream API)
- `internal/db/store/queries.go`, `internal/db/*/sqlc/*`, `db/*/queries/*.sql`
- `spec/swagger*`, `apps/web/*`
- `deploy/studio-jarvis/*`

Studio-расширения store-интерфейса (пример): `CountMessagesBySessionSince`, `CountPassiveMessagesBySession`, `DeleteTelegramGroupMessagesOlderThan` — после sync проверить, что методы есть в `internal/db/postgres/sqlc`, `internal/db/sqlite/sqlc` и обёртках `internal/db/sqlite/store`.

## Проверки перед deploy

В Docker (`golang:1.25-alpine`, монтирование `C:\AI\memoh` → `/src`):

```sh
gofmt -w <изменённые .go>
go test ./internal/channel/studiochat/... ./internal/studioapp/... ./internal/studioevents/... \
  ./internal/studiohubdisk/... ./internal/handlers/... ./internal/memory/... ./internal/skills/...
go test ./internal/channel/inbound/...
go build -o /dev/null ./cmd/agent
```

При смене фронта/API upstream: `pnpm` lint/build в `apps/web` — если `pnpm` недоступен в среде, зафиксировать пропуск в отчёте задачи.

## Что не коммитить

- Секреты: `.env`, `config.toml` с токенами, ключи, пароли, приватные URL.
- Локальные артефакты IDE: `.cursor/`, `memory-bank/` — держать вне индекса (`.git/info/exclude` или локальный exclude).

## Deploy (только `memoh-server`)

На VPS (путь `/opt/memoh`), только сервис `server`, без трогания остальных сервисов:

```sh
cd /opt/memoh
docker compose build server
docker compose up -d --no-deps server
```

Health: внешний `https://memo.pb-web.ru/ping`, внутренний ping на хосте — по конфигурации compose (например `curl -fsS http://127.0.0.1:<порт>/ping`).

Сборку образа выполнять на CI или там, где принято в проекте; на VPS не гонять тяжёлый `go build` для разработки.
