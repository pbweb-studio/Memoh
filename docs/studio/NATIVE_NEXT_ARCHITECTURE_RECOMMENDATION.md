# Native-first Studio — целевая архитектура (рекомендация)

**Ветка baseline:** `studio/native-baseline-20260512`  
**Archive-heavy fork:** `studio/archive-heavy-fork-20260512-1245` — использовать **только как reference** (идеи, данные, формулировки). **Не** merge source для восстановления кода и **не** источник истины для Studio custom в core.  
**Связанные документы:** [`NATIVE_RUNTIME_AUDIT_RESULTS.md`](./NATIVE_RUNTIME_AUDIT_RESULTS.md), [`STUDIO_RESTORE_DECISION_MATRIX.md`](./STUDIO_RESTORE_DECISION_MATRIX.md)

---

## Краткий статус native audit

- **Web (`memohwebaudit`):** people, files, memory, skills; session UI search + ограничения `Search history`; реестры `/data/studio/*.json` + skill — **зафиксированы** в runtime audit.  
- **Telegram DM** (people/projects/tasks + строгие `projects.json` / `chats.json`) — **runtime passed** (human E2E, Block **E.6**).  
- **Telegram group MVP** (mention, `/access@bot`, strict `projects.json`, burst; без mention = acceptable default) — **runtime passed** (human E2E, Block **E.8**).  
- **Schedule / Heartbeat:** **MVP по документации** для daily digest — **OK** (Block F в audit); **фактический** firing cron + доставка в Telegram — **pending** отдельным коротким runtime-шагом при необходимости.

---

## Что уже доказано runtime

| Область | Доказательство |
|---------|----------------|
| People identity | Web + **Telegram DM** + **Telegram group (mention)** — skills + `people.md` + memory |
| Projects / chats / tasks | Web + DM + **group** — `/data/studio/*.json`, strict reads |
| Канал Telegram | UI **Platforms**, adapter active; **ACL** в группе (`/access@bot` — allow, write off) |
| Burst / порядок ответов | Три подряд mention-сообщения — все ответы, порядок A→B→C; **custom ModeQueue** не нужен |
| Политика restore | Матрица: старые Go/db/inbound/ModeQueue custom для этого MVP — **не** возвращать |

---

## Что осталось проверить

1. **Schedule firing** в реальном timezone + одно подтверждение доставки digest в Telegram (опционально, если продукту нужен автодайджест).  
2. **Heartbeat** — осмысленный «routine» для Studio и просмотр логов (если нужен автономный сбор).  
3. **Studio Control Mini App** — отдельный UX-аудит при необходимости (`not tested` в матрице).  
4. **Raw history / SLA** вне UI + `Search history` + Memory — только **RFC**, при необходимости MCP/sidecar.

---

## Что точно не возвращать из `archive-heavy-fork`

- **Studio custom** в Go/Vue/inbound как **merge** из archive — **нет** (native-first baseline).  
- **Старый Go people resolver** — **нет**.  
- **Старые db/sqlc/store patches** под people/registry в core — **нет** без RFC.  
- **Старые inbound/channel patches** для **DM + group MVP** — **нет** (runtime E.6–E.8).  
- **Старый ModeQueue custom** — **нет** по результату burst (E.8).  
- **Старые memory context packer hooks** для этого lookup — **нет**.

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
  + Schedule + Heartbeat — для digest / периодики (док-MVP ок; отдельно при желании runtime-проверка firing + Telegram)
  + optional sidecar / MCP — только для внешнего CRUD, SLA, raw-history, если native + files не хватают
  → no core patches by default
  → archive-heavy-fork: только reference, не merge source
```

**Инвариант:** Web, **Telegram DM** и **Telegram group (через mention)** используют один агентский слой: **files + skills + memory** и штатный adapter/ACL.

---

## Следующий крупный шаг (рекомендация)

Короткий **runtime**-прогон **Schedule** (одно задание + проверка сессии типа `schedule` и сообщения в Telegram) и при необходимости **Heartbeat**; затем приоритизировать **Studio Control** UX-аудит, если Mini App нужен в продукте.

---

*Автокоммит не выполнялся.*
