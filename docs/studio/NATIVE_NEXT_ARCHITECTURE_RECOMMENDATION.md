# Native-first Studio — целевая архитектура (рекомендация)

**Ветка baseline:** `studio/native-baseline-20260512`  
**Archive-heavy fork:** `studio/archive-heavy-fork-20260512-1245` — использовать **только как reference** (идеи, данные, формулировки). **Не** merge source для восстановления кода и **не** источник истины для Studio custom в core.  
**Связанные документы:** [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md), [`STUDIO_RESTORE_DECISION_MATRIX.md`](./STUDIO_RESTORE_DECISION_MATRIX.md), [`STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md`](./STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md).

**Готовый native bundle (шаблоны данных, skills, runbook, acceptance):** [`deploy/studio-jarvis-native/README.md`](../deploy/studio-jarvis-native/README.md) — **first implementation batch** подготовлен в репозитории **без** правок Memoh core; перенос в workspace бота — вручную по [`RUNBOOK.md`](../deploy/studio-jarvis-native/RUNBOOK.md).

**Docker workspace hint (rollout 2026-05-12):** на локальном compose volume `workspace-data/<bot_id>/` каталоги **`studio/`** и **`skills/`** в **корне** workspace соответствуют путям агента и UI **`/data/studio/`** и **`/data/skills/`**; не класть копии в лишний префикс `data/studio` на диске — иначе `Read /data/studio/...` не находит файлы (зафиксировано в [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md)). **Managed skills:** чтобы каталог попал в **`GET .../container/skills`** и в UI, файлы нужно создавать через **UI Skills → New Skill** или **`POST /api/bots/{id}/container/skills`** (bridge write); только копирование `skills/` на bind-mount без upsert давало пустой список. **Короткая формулировка:** *workspace folder `studio/*` maps to agent path `/data/studio/*`.*

---

## Краткий статус native audit

- **Studio Jarvis Native bundle (Web + Schedule UI-smoke + **финальная Telegram-приёмка**, 2026-05-12):** Web strict reads + managed skills — **pass**. **Schedule:** тест `StudioNativeFinalScheduleSmoke` создан/сработал (`schedule completed` ok в логах) и **удалён** через UI. **Telegram (SJN, `@jarvispbweb_bot`):** **DM pass**; **group MVP pass** (`/access@jarvispbweb_bot`, mention, strict `/data/studio/*`); **burst — pass with caveat** (см. [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md) **E.8b** и [`ACCEPTANCE_CHECKLIST.md`](../deploy/studio-jarvis-native/ACCEPTANCE_CHECKLIST.md)): A и C — полные ответы; B в пачке — в основном reaction/ack; B отдельно — полный ответ по `projects.json`; **strict queue semantics** для burst **не** обязательны для MVP; **ModeQueue custom из archive не возвращать** автоматически.
- **Web (`memohwebaudit`):** people, files, memory, skills; session UI search + ограничения `Search history`; реестры `/data/studio/*.json` + skill — **зафиксированы** в runtime audit.  
- **Telegram DM** (people/projects/tasks + строгие `projects.json` / `chats.json`) — **runtime passed** (human E2E, Block **E.6**).  
- **Telegram group MVP** (mention, `/access@bot`, strict `projects.json`, burst; без mention = acceptable default) — **runtime passed** (human E2E, Block **E.8**).  
- **Schedule (cron → agent):** **runtime passed** — тест **`ScheduleAuditNative`**, сессии типа **`schedule`**, **`read`** обоих JSON, доставка через штатный **`send`** (см. Block **G**). **Timezone** срабатываний в примере совпала с **UTC** (как в доке по умолчанию).  
- **Heartbeat:** **доки** зафиксированы в **Block F** audit; отдельный **runtime** heartbeat (вкладка логов) в этом шаге **не** гонялся.

---

## Что уже доказано runtime

| Область | Доказательство |
|---------|----------------|
| People identity | Web + **Telegram DM** + **Telegram group (mention)** — skills + `people.md` + memory |
| Projects / chats / tasks | Web + DM + **group** — `/data/studio/*.json`, strict reads |
| Канал Telegram | UI **Platforms**, adapter active; **ACL** в группе (`/access@bot` — allow, write off) |
| Burst / порядок ответов | **MVP:** нативный burst **без** custom **ModeQueue** — **pass** для baseline (**E.8**, все A→B→C полные) и **pass with caveat** для SJN (**E.8b**: B в пачке — reaction/ack; A/C и B отдельно — полные). **Strict queue** (полный ответ на **каждое** сообщение burst **в порядке**) — **не** требование MVP; при необходимости — **RFC / product**. **ModeQueue** из archive **не** возвращать автоматически |
| **Schedule / digest** | UI Schedule + cron; агент **read** `projects.json` + `tasks.json`; **harvester/custom cron** из archive для MVP **не** нужен |
| Политика restore | Матрица: старые Go/db/inbound/ModeQueue/**harvester** для этого MVP — **не** возвращать |

---

## Что осталось проверить

1. **Heartbeat** — 1–2 реальных цикла + вкладка **Heartbeat** / `/heartbeat logs` ([heartbeat.md](../docs/docs/getting-started/heartbeat.md)).  
2. **Schedule:** явно выставить **`max_calls`** (UI Run limit или `/schedule` owner), owner-only сценарии slash ([slash-commands.md](../docs/docs/getting-started/slash-commands.md)).  
3. **Telegram-клиент:** отдельно убедиться, что **`send`** с `platform: "telegram"` из schedule-turn реально доходит в личку/группу (в Block **G** подтверждён только tool-result `delivered: current_conversation`).  
4. **Studio Control Mini App** — UX-аудит при необходимости (`not tested` в матрице).  
5. **Raw history / SLA** — только **RFC**, при необходимости MCP/sidecar.
6. **Telegram + Schedule для Studio Jarvis Native** — на локальном `memohwebaudit` (2026-05-12): **Schedule** UI-smoke и **Telegram** DM + group (в т.ч. `/access`, strict files, burst с caveat по **E.8b**) — **закрыты**; остаток см. п.п. 1–5 (Heartbeat runtime, `max_calls`, доставка `send` в клиент Telegram, Mini App, raw history RFC).

---

## Что точно не возвращать из `archive-heavy-fork`

- **Studio custom** в Go/Vue/inbound как **merge** из archive — **нет** (native-first baseline).  
- **Старый Go people resolver** — **нет**.  
- **Старые db/sqlc/store patches** под people/registry в core — **нет** без RFC.  
- **Старые inbound/channel patches** для **DM + group MVP** — **нет** (runtime E.6–E.8).  
- **Старый ModeQueue custom** — **нет** для MVP: baseline burst (**E.8**) и SJN (**E.8b**, caveat по B в пачке) **не** требуют возврата; строгая очередь — только **RFC / product**.  
- **Старые memory context packer hooks** для этого lookup — **нет**.  
- **Old task harvester / custom cron** — **нет** для MVP, пока **Schedule** закрывает digest (**Block G**).

---

## Что возвращать только как files / skills / memory

- Реестры, playbooks, SLA-тексты, контакты — **`/data/**`**, **`/data/skills/**/SKILL.md`**, **Memory**.  
- Идеи из archive — **контентом** в workspace, не патчем core.

---

## Что потенциально MCP / sidecar

- Внешний registry, **SLA / raw history** с гарантиями, интеграции без `/data` — remote MCP или sidecar **вне** Memoh core.  
- **CRUD UI** или внешние системы — только при продуктовой необходимости и RFC.

---

## Что потенциально thin overlay

- UX над **Studio Control** без изменения upstream core.

---

## Что запрещено трогать в Memoh core (по умолчанию)

- **MEMORY approval flow**, секреты, произвольные правки inbound/dispatcher/store.  
- **Core-touch** без RFC и без доказанного gap после native path.

---

## Рекомендуемая архитектура Studio Jarvis

```text
Clean Memoh core (upstream-first; без studio-custom patches по умолчанию)
  + Providers / Platforms / Access (ACL) — конфиг в UI
  + Managed Skills (/data/skills/.../SKILL.md)
  + Files workspace: /data/studio/*.json, people.md, memory/*.md
  + Memory provider (shared для бота по сессиям/каналам)
  + Schedule — календарные digest и точечные NL-задачи (cron + command; runtime OK — Block G)
  + Heartbeat — периодический «routine» / мониторинг (доки OK; runtime при желании)
  + optional sidecar / MCP — только если явное требование не закрывается Schedule+Heartbeat+files
  → no core patches by default
  → archive-heavy-fork: только reference, не merge source
```

**Инвариант:** Web, **Telegram DM**, **Telegram group (mention)** и **Schedule** используют один агентский слой (**files + skills + memory**) и штатные механизмы Memoh без Studio custom в core.

---

## Следующий крупный шаг (рекомендация)

1. **Ручной rollout Studio Jarvis Native:** настройка бота по [`deploy/studio-jarvis-native/RUNBOOK.md`](../deploy/studio-jarvis-native/RUNBOOK.md) и проверка по [`ACCEPTANCE_CHECKLIST.md`](../deploy/studio-jarvis-native/ACCEPTANCE_CHECKLIST.md).  
2. Затем — короткий **runtime Heartbeat** (включить на тест, посмотреть логи) и при продуктовой необходимости — **подтверждение Telegram-клиентом** доставки digest из schedule.  
3. Параллельно при необходимости — **Studio Control** UX-аудит; отдельно — план **sidecar / MCP / thin overlay** только после явного gap (RFC).

---

*Коммиты bundle см. историю git на ветке `studio/native-baseline-20260512` (сообщение `docs(studio): add native studio jarvis bundle`).*
