# Native-first Studio — целевая архитектура (рекомендация)

**Ветка baseline:** `studio/native-baseline-20260512`  
**Archive-heavy fork:** `studio/archive-heavy-fork-20260512-1245` — использовать **только как reference** (идеи, данные, формулировки). **Не** merge source для восстановления кода и **не** источник истины для Studio custom в core.  
**Связанные документы:** [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md), [`STUDIO_RESTORE_DECISION_MATRIX.md`](./STUDIO_RESTORE_DECISION_MATRIX.md), [`STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md`](./STUDIO_NATIVE_MVP_IMPLEMENTATION_PLAN.md).

**Готовый native bundle (шаблоны данных, skills, runbook, acceptance):** [`deploy/studio-jarvis-native/README.md`](../deploy/studio-jarvis-native/README.md) — **first implementation batch** подготовлен в репозитории **без** правок Memoh core; перенос в workspace бота — вручную по [`RUNBOOK.md`](../deploy/studio-jarvis-native/RUNBOOK.md).

---

## Краткий статус native audit

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
| Burst / порядок ответов | Три подряд mention-сообщения — все ответы, порядок A→B→C; **custom ModeQueue** не нужен |
| **Schedule / digest** | UI Schedule + cron; агент **read** `projects.json` + `tasks.json`; **harvester/custom cron** из archive для MVP **не** нужен |
| Политика restore | Матрица: старые Go/db/inbound/ModeQueue/**harvester** для этого MVP — **не** возвращать |

---

## Что осталось проверить

1. **Heartbeat** — 1–2 реальных цикла + вкладка **Heartbeat** / `/heartbeat logs` ([heartbeat.md](../docs/docs/getting-started/heartbeat.md)).  
2. **Schedule:** явно выставить **`max_calls`** (UI Run limit или `/schedule` owner), owner-only сценарии slash ([slash-commands.md](../docs/docs/getting-started/slash-commands.md)).  
3. **Telegram-клиент:** отдельно убедиться, что **`send`** с `platform: "telegram"` из schedule-turn реально доходит в личку/группу (в Block **G** подтверждён только tool-result `delivered: current_conversation`).  
4. **Studio Control Mini App** — UX-аудит при необходимости (`not tested` в матрице).  
5. **Raw history / SLA** — только **RFC**, при необходимости MCP/sidecar.

---

## Что точно не возвращать из `archive-heavy-fork`

- **Studio custom** в Go/Vue/inbound как **merge** из archive — **нет** (native-first baseline).  
- **Старый Go people resolver** — **нет**.  
- **Старые db/sqlc/store patches** под people/registry в core — **нет** без RFC.  
- **Старые inbound/channel patches** для **DM + group MVP** — **нет** (runtime E.6–E.8).  
- **Старый ModeQueue custom** — **нет** по результату burst (E.8).  
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
