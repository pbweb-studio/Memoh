# Feature decision template (Studio Jarvis / Memoh Native)

Copy this file for each non-trivial feature. Fill before implementation. Link from PRs or internal notes.

---

## 1. Feature goal

<!-- One paragraph: what we are building. -->

## 2. User value

<!-- Who benefits and how (operator, end user, developer). -->

## 3. Documented Memoh mechanism

<!-- Exact citations: `docs/docs/...` paths and/or https://docs.memoh.ai/... URLs. -->

- Mechanism:
- Doc quotes / section names (optional):

## 4. Native implementation path

<!-- UI step-by-step, skill names, `/data/studio` files, MCP tools, schedule entries, etc. -->

## 5. Data source of truth

<!-- e.g. `/data/studio/projects.json` vs Memory vs external CRM — single SoT. -->

## 6. Does it touch protected core?

**Yes / No**

<!-- If Yes: link to approved RFC and user sign-off; list paths under internal/db, channel, conversation/flow, memory, skills, cmd/agent. -->

## 7. Overlay / sidecar / plugin design

<!-- How this stays disableable; what happens when Studio is off. -->

## 8. Risks

<!-- Security, upgrade fragility, data loss, UX confusion. -->

## 9. Rollback plan

<!-- Disable skill, revert data file, stop sidecar, toggle config — concrete steps. -->

## 10. Acceptance checklist

- [ ] Documented mechanism cited and verified on current Memoh revision
- [ ] No secrets in repo, logs, or skill bodies
- [ ] `/data/studio` (or documented alternative) holds registries; Memory not misused as SoT
- [ ] Studio can be disabled without breaking baseline Memoh
- [ ] Protected core untouched **or** explicit RFC approval attached
- [ ] Upstream update impact assessed (low / medium / high)
