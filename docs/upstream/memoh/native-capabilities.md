# Memoh native capabilities — map for Studio Jarvis

Concise guide: **what to use**, **what to avoid**, and **Studio examples**. Always confirm details in official docs (`docs/docs/` + https://docs.memoh.ai).

---

## 1. Files / workspace data

| Use for | Do not use for |
|--------|----------------|
| Durable structured Studio registries (people, projects, chats, tasks), bot-local reference files, templates shipped with deploy packs | Secrets, tokens, credentials; duplicating what already belongs in DB-backed Memoh settings without a documented reason |

**Studio Jarvis examples:** `/data/studio/people.md`, `/data/studio/projects.json`, optional `events*.jsonl` for append-only logs — skills read/write these per overlay rules (`.cursor/rules/20-studio-overlay-model.mdc`).

---

## 2. Managed skills

| Use for | Do not use for |
|--------|----------------|
| Behavior, tone, workflows, checklists, how the agent should interpret Studio data | Large canonical registries (full org charts, megabyte JSON blobs); secret storage |

**Studio Jarvis examples:** `studio-jarvis-behavior`, `studio-people-source`, `studio-project-registry` style skills that **point at** `/data/studio` files.

---

## 3. Memory

| Use for | Do not use for |
|--------|----------------|
| Conversation facts, retrieval, long-horizon context per upstream memory providers | Source of truth for employees/projects/chats/tasks (use `/data/studio` + documented APIs/UI) |

**Studio Jarvis examples:** “User prefers weekly digest on Monday”, “decision from last call” — not “canonical employee ID table”.

---

## 4. MCP / tools

| Use for | Do not use for |
|--------|----------------|
| Integrations (issue trackers, calendars, internal APIs), extra automation, federation per docs | Replacing Memoh’s own tool approval / security model without documentation |

**Studio Jarvis examples:** Sidecar HTTP service + MCP server for CRM lookup; filesystem MCP for guarded exports.

---

## 5. Access / ACL

| Use for | Do not use for |
|--------|----------------|
| Who may trigger which bot/session/channel per documented ACL rules | Ad-hoc security bypasses in custom inbound code |

**Studio Jarvis examples:** Restrict inbound triggers for a “production” vs “sandbox” bot using documented ACL UI and rules.

---

## 6. Telegram Platform / channels

| Use for | Do not use for |
|--------|----------------|
| Inbound/outbound messaging, bindings, documented channel behavior | Custom Telegram pipeline in Go without RFC + approval (protected core) |

**Studio Jarvis examples:** Route Studio notifications through a dedicated channel binding; use documented channel configs.

---

## 7. Schedule

| Use for | Do not use for |
|--------|----------------|
| Cron-style jobs, documented heartbeat/schedule features per Memoh docs | Custom harvesters replacing Memoh schedule without approval |

**Studio Jarvis examples:** Nightly digest at fixed local time using documented schedule + skills.

---

## 8. UI / config

| Use for | Do not use for |
|--------|----------------|
| Bot settings, models, providers, channels, schedules, skills attachment in UI | Anything requiring forked web app for a feature that docs support via config |

**Studio Jarvis examples:** Enable MCP, attach skills, set memory providers — cite the relevant getting-started page.

---

## 9. Browser / tool execution (if documented)

| Use for | Do not use for |
|--------|----------------|
| Headless browsing via **Browser Gateway** where Memoh documents it (Playwright stack) | Long-running scraping farms unrelated to bot scope |

**Studio Jarvis examples:** “Open internal dashboard and summarize” via documented browser tools — confirm in `docs/docs` and gateway docs.

---

## Cross-cutting rule

If a capability is **not** listed in official docs for your version, treat it as **undocumented** → follow **RFC / «ОТХОЖУ ОТ ЗАДОКУМЕНТИРОВАННОГО СПОСОБА»** in `.cursor/rules/00-upstream-docs-first.mdc` before implementation.
