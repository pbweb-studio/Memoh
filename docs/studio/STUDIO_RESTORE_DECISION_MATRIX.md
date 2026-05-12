# Studio restore — decision matrix (native baseline)

**Ветка:** `studio/native-baseline-20260512`  
**Контекст:** чистый native baseline; people identity и **Telegram DM + group MVP** и **Schedule cron digest** закрыты через **Skills + Files + Memory** + Platforms + ACL; core-touch и возврат Studio custom из archive **не** предполагаются без отдельного решения.  
**Доказательства runtime (Web + Telegram DM + Telegram group + **Schedule cron**, `memohwebaudit`):** см. [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md).

**Уточнение по экземпляру Studio Jarvis Native (локальный compose, 2026-05-12):** для бота **`994b7558-…`** зафиксирована **финальная Telegram-приёмка** (DM + group + `/access@jarvispbweb_bot` + strict `/data/studio/*` + burst с caveat — см. [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md) **E.8b**, [`ACCEPTANCE_CHECKLIST.md`](../deploy/studio-jarvis-native/ACCEPTANCE_CHECKLIST.md)). Классификация строк таблицы по-прежнему относится к **возможностям Memoh native**; токены задаются только в UI и **не** дублируются в доках.

Легенда колонки **Native result:** `native` | `native with config` | `files/skills/memory` | `MCP` | `sidecar` | `thin overlay` | `not tested` | `do not restore`

| Feature | Native result | Recommended home | Restore old custom? | Core-touch allowed? | Evidence | Notes |
|---------|---------------|------------------|---------------------|---------------------|----------|-------|
| people identity | files/skills/memory + native with config (providers) | `people.md` + Memory + skills (`web-audit-people`) | **Нет** | **Нет** (без RFC) | [`NATIVE_AUDIT_TELEGRAM_MEMORY_PEOPLE.md`](./NATIVE_AUDIT_TELEGRAM_MEMORY_PEOPLE.md), [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md) | Go resolver не нужен |
| people.md source of truth | files/skills/memory | `/data/people.md` + skill правила | **Нет** | **Нет** | Tool trace `Read /data/people.md` | |
| manual memory retrieval | native with config | Memory tab + provider | **Нет** | **Нет** | memory.md + runtime | |
| cross-session memory | native | Memory provider для бота | **Нет** | **Нет** | sessions.md + runtime AuditNative | |
| raw session/history search | native (UI) + native with config (agent tool); ограничения не исключены | UI sidebar search; опционально доработка UX/индексации без core | **Нет** | Только с RFC, если gap критичен | Runtime 2026-05-12: UI фильтр по `Zebra42`; агент **Search history** не нашёл точный токен `RawHistoryAudit` | Отличается от memory retrieval (док memory.md) |
| project registry | files/skills/memory | `/data/studio/projects.json` + skill | **Нет** | **Нет** | `Read /data/studio/projects.json` + skill `web-audit-studio-data` | |
| chat registry | files/skills/memory | `/data/studio/chats.json` + skill | **Нет** | **Нет** | `Read /data/studio/chats.json` | |
| task registry | files/skills/memory | `/data/studio/tasks.json` + skill | **Нет** | **Нет** | `Read /data/studio/tasks.json` | |
| Studio Control Mini App | not tested | При необходимости отдельный **thin overlay** (вне core), не archive fork | **Нет** (до отдельного UX-аудита) | **Нет** | Нет runtime в этом прогоне | Не тянуть legacy без ТЗ |
| Telegram adapter bind (UI) | native with config | Platforms → Telegram → Save and enable | **Нет** | **Нет** | [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md) Block E | UI **Telegram Active**; строка `telegram` в `bot_channel_configs` |
| Telegram DM — Q&A (people/projects/tasks + strict JSON reads) | native with config + files/skills/memory | Platforms + adapter + workspace skills/memory + `/data/studio/*.json` | **Нет** | **Нет** | Block E.6 (human E2E) | Старый Go people resolver / inbound/channel / sqlc people patches **не** нужны для этого сценария |
| People/projects/tasks **via Telegram DM** | files/skills/memory | SoT JSON + skills; memory — дополнение | **Нет** | **Нет** | Block E.6 | То же, что Web-аудит, другой транспорт |
| Telegram group / mention / access / strict JSON / burst | **native with config** + files/skills/memory | Mention + ACL + штатный adapter + workspace | **Нет** | **Нет** | Block **E.8** (baseline @Jarvispbw_bot); **E.8b** (SJN `@jarvispbweb_bot`, финальная приёмка 2026-05-12) | Без mention — **acceptable** default (`discuss`); SJN burst — см. **E.8b** (caveat по B в пачке) |
| Telegram group routing / legacy **ModeQueue** custom | **do not restore** для MVP | Нативный burst: baseline **E.8** — полный порядок A→B→C; SJN **E.8b** — MVP pass без strict queue | **Нет** | **Нет** | Block **E.8** + **E.8b** | **ModeQueue** из archive — **не** возвращать автоматически; строгая очередь burst — **RFC / product**, не MVP |
| daily digest / **Schedule** cron | **native with config** + files/skills/memory (runtime **Pass**, Block **G**) | UI **Schedule** + NL `command`; сессии типа `schedule` | **Нет** | **Нет** | Block **G** + schedule.md | `max_calls` / slash owner — см. pending в Block F |
| Heartbeat (autonomous interval) | native with config (док) + **runtime не гоняли** | Heartbeat tab; `/heartbeat` ([slash-commands.md](../docs/docs/getting-started/slash-commands.md)) | **Нет** | **Нет** | heartbeat.md, Block F | Для digest предпочтительнее **Schedule** |
| old **task harvester** / **custom cron** (Studio archive) | **do not restore** для MVP | Заменено штатным **Schedule** + при необходимости **Heartbeat** / MCP | **Нет** | Только явное требование вне Schedule+Heartbeat+MCP (**RFC**) | Block **G** | Пересмотр — если требование **нельзя** закрыть штатными средствами |
| files/workspace registry | native | Files tab, Monaco save, upload | **Нет** | **Нет** | files.md + UI upload/folder | |
| MCP filesystem | MCP (опционально) | MCP stdio `server-filesystem` (док mcp.md) | **Нет** (если хватает встроенных Files) | **Нет** | mcp.md | Нужен для внешнего корня / интеграций |
| Studio sidecar | sidecar (опционально) | Отдельный сервис + remote MCP / API | **Нет** | **Нет** | workspace-backends.md + продуктовая необходимость | Если registry должен жить вне workspace |
| managed skills UI | native | `/data/skills/<name>/SKILL.md`, Skills tab | **Нет** | **Нет** | skills.md + runtime skill traces | |
| native Studio Jarvis deploy bundle (templates + runbook + checklist) | files/skills/config | `deploy/studio-jarvis-native/**` → копирование в `/data/studio/` + `/data/skills/` + UI по RUNBOOK | **Нет** | **Нет** | [`STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md`](./STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md), bundle README | **Без** Studio custom в core; не merge archive |
| old Go people resolver | **do not restore** | Заменено files+skills+memory | **Нет** | **Нет** | People audit | |
| old db/sqlc/store patches | **do not restore** (без RFC) | Файлы/Memory вместо sqlc-реестра people | **Нет** | Только отдельный RFC (SLA/raw-history) | Политика baseline | |
| old inbound/channel patches | **do not restore** для **DM / group MVP** (mention, ACL, strict files, burst — Block E.6–E.8) | ACL + `discuss` + mention + skills + files/memory | **Нет** | Только при **явном** продуктовом требовании: **пассивное** прослушивание **всех** сообщений без mention и/или **отдельная жёсткая** семантика очереди, не закрываемая штатным путём (RFC) | Block E.6–E.8 | Не восстанавливать «на всякий случай» |
| old memory context packer hooks | **do not restore** (для people/project lookup) | Memory provider + явные файлы | **Нет** | **Нет** | Runtime people/projects без packer hooks | Другие причины — только RFC |

### Явные запреты (policy)

- **old Go people resolver:** **do not restore.**  
- **old db/sqlc/store patches:** **do not restore** unless a **separate RFC** proves raw-history/SLA/registry needs that cannot be met with files/Memory/MCP.  
- **old inbound/channel patches:** **do not restore** для **DM и group MVP** (подтверждено **E.6–E.8** и **E.8b** для SJN). Возврат — **только** при **явном** продуктовом требовании: пассивное прослушивание **всех** сообщений группы без mention и/или отдельная **жёсткая** семантика очереди вне штатного поведения (**RFC**).  
- **old task harvester / custom cron (archive):** **do not restore** для MVP при работающем **Schedule** (Block **G**). Пересмотр — только при явном требовании, не закрываемом **Schedule + Heartbeat + MCP/sidecar** (**RFC**).  
- **memory context packer hooks:** **do not restore** for people/project lookup — закрывается провайдером памяти и файловыми SoT.

*Автокоммит не выполнялся.*
