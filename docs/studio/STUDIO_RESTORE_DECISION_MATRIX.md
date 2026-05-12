# Studio restore — decision matrix (native baseline)

**Ветка:** `studio/native-baseline-20260512`  
**Контекст:** чистый native baseline; people identity закрыт через **Skills + Files + Memory**; core-touch и возврат Studio custom из archive **не** предполагаются без отдельного решения.  
**Доказательства runtime (Web, `memohwebaudit`):** см. [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md).

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
| Telegram channel runtime | not tested | Штатный channel + ACL (доки) | **Нет** | **Нет** | [telegram.md](../docs/docs/channels/telegram.md) only | Следующий audit block |
| Telegram group routing / ModeQueue | not tested; **do not restore** legacy routing по умолчанию | `discuss` + skills + ACL | **Нет** | **Нет** без доказательства gap | Нет реального Telegram | Возврат старых патчей — только если native не закрывает сценарий |
| daily digest / schedule | native with config (док) | Schedule + heartbeat сессии (доки) | **Нет** | **Нет** | sessions.md, UI tab «Schedule» | Runtime не тестировали |
| files/workspace registry | native | Files tab, Monaco save, upload | **Нет** | **Нет** | files.md + UI upload/folder | |
| MCP filesystem | MCP (опционально) | MCP stdio `server-filesystem` (док mcp.md) | **Нет** (если хватает встроенных Files) | **Нет** | mcp.md | Нужен для внешнего корня / интеграций |
| Studio sidecar | sidecar (опционально) | Отдельный сервис + remote MCP / API | **Нет** | **Нет** | workspace-backends.md + продуктовая необходимость | Если registry должен жить вне workspace |
| managed skills UI | native | `/data/skills/<name>/SKILL.md`, Skills tab | **Нет** | **Нет** | skills.md + runtime skill traces | |
| old Go people resolver | **do not restore** | Заменено files+skills+memory | **Нет** | **Нет** | People audit | |
| old db/sqlc/store patches | **do not restore** (без RFC) | Файлы/Memory вместо sqlc-реестра people | **Нет** | Только отдельный RFC (SLA/raw-history) | Политика baseline | |
| old inbound/channel patches | **do not restore** (без Telegram runtime gap) | ACL + sessions + skills | **Нет** | Только если native не закрывает | Политика baseline | |
| old memory context packer hooks | **do not restore** (для people/project lookup) | Memory provider + явные файлы | **Нет** | **Нет** | Runtime people/projects без packer hooks | Другие причины — только RFC |

### Явные запреты (policy)

- **old Go people resolver:** **do not restore.**  
- **old db/sqlc/store patches:** **do not restore** unless a **separate RFC** proves raw-history/SLA/registry needs that cannot be met with files/Memory/MCP.  
- **old inbound/channel patches:** **do not restore** unless **Telegram runtime audit** proves native channel + ACL + sessions cannot solve the scenario.  
- **memory context packer hooks:** **do not restore** for people/project lookup — закрывается провайдером памяти и файловыми SoT.

---

*Автокоммит не выполнялся.*
