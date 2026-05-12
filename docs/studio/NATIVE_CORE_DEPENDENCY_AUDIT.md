# Native core dependency audit

## 1. Current state

| Field | Value |
|--------|--------|
| **Current branch** | `studio/native-baseline-20260512` |
| **Current commit** | `1c584c29b4af9ef52c9e0ba48fac3db3f57cef0d` |
| **Upstream remote** | `upstream` → `https://github.com/memohai/Memoh.git` |
| **Upstream branch used** | `main` |
| **Upstream commit** | `15e68dfb990ad947e444bac6a00ea8d3ce2d0499` |
| **Merge-base (HEAD, upstream/main)** | `7b090f0cc65cce2c1230f296caf5113575735b45` |
| **Date** | 2026-05-12 |

Comparison commands (committed trees only; working tree noise excluded):

- **Full tree diff:** `git diff --name-status upstream/main HEAD` — все пути, где снимок `HEAD` отличается от `upstream/main`.
- **Симметрично от merge-base:** `git diff --name-status upstream/main...HEAD` — только изменения, внесённые коммитами, достижимыми из `HEAD` после `merge-base(upstream/main, HEAD)`; не показывает файлы, которые **менял только upstream** после расхождения (например, если `HEAD` не трогал `apps/desktop`, а upstream — да).

## 2. Summary

| Metric | Count |
|--------|------:|
| **Total changed paths vs upstream/main** | 37 |
| **Protected core paths changed** | 0 |
| **Overlay / docs / rules / AGENTS / deploy pack paths** | 27 |
| **Suspicious (outside overlay, touches app/tooling)** | 10 |

**Note:** In this diff there are **no** changes under `internal/db/`, `internal/channel/inbound/`, `internal/channel/adapters/`, `internal/conversation/flow/`, `internal/memory/`, `internal/skills/`, `cmd/agent/`, database migrations, or `internal/db/**/sqlc/` generated packages. Studio Jarvis drift in the committed baseline is **not** anchored in the listed protected core areas — it lives in **desktop/web app layers**, **mise**, and **Studio overlay docs/deploy**.

## 3. Protected core differences

*No paths in this comparison.*

| file/path | type of difference | likely reason | risk level | recommendation |
|-----------|-------------------|---------------|------------|----------------|
| — | — | — | — | Keep enforcing `.cursor/rules/10-core-protection.mdc`; re-run this audit after future commits. |

## 4. Overlay differences

| file/path | purpose | safe for upstream update |
|-----------|---------|----------------------------|
| `.cursor/rules/00-upstream-docs-first.mdc` | Docs-first + RFC при отходе от Memoh | yes |
| `.cursor/rules/10-core-protection.mdc` | Список защищённого ядра | yes |
| `.cursor/rules/20-studio-overlay-model.mdc` | `/data/studio`, skills, overlay | yes |
| `AGENTS.md` | Правила Studio / upstream overlay | yes (merge при обновлении AGENTS upstream вручную) |
| `deploy/studio-jarvis-native/**` | Пакет деплоя, данные-примеры, managed skills | yes |
| `docs/studio/*.md` (кроме этого audit) | Планы и аудиты Studio | yes |
| `docs/studio/FEATURE_DECISION_TEMPLATE.md` | Шаблон решений по фичам | yes |
| `docs/upstream/memoh/**` | Локальный индекс upstream для агентов | yes |

## 5. Suspicious differences

| file/path | why suspicious | recommendation |
|-----------|----------------|------------------|
| `apps/desktop/.gitignore` | Прикладной слой; не overlay | **needs human review** — сверить с upstream desktop; убрать если это локальный мусор |
| `apps/desktop/electron-builder.yml` | Меняет упаковку десктопа | **needs human review** — intentional Studio packaging vs accidental drift |
| `apps/desktop/package.json` | Зависимости/скрипты десктопа | **needs human review** — сравнить с upstream; не держать без причины |
| `apps/desktop/scripts/build.mjs` | Сборка Electron | **needs human review** |
| `apps/desktop/scripts/prepare-gstreamer.mjs` (deleted vs upstream) | Удаление скрипта — расхождение с политикой мультимедиа upstream | **needs human review** — либо вернуть как upstream, либо оформить RFC если GStreamer намеренно выкинут |
| `apps/desktop/src/main/gstreamer.ts` (deleted vs upstream) | Удаление интеграции GStreamer | **high attention** — связано с медиа/дисплеем; не смешивать со Studio без явного решения |
| `apps/desktop/src/main/local-server.ts` | Локальный сервер в desktop shell | **needs human review** — частая точка форка |
| `apps/web/src/pages/bots/components/bot-desktop.vue` | UI бота | **needs human review** — не overlay |
| `apps/web/src/pages/home/components/display-pane.vue` | Отображение медиа/энкодера (в т.ч. ветки `gstreamer unavailable`) | **needs human review** — upstream `main` уже содержит фиксы display runtime (#455); ветка может быть **старше/расходящейся** по смыслу, не только по строкам |
| `mise.toml` | Dev toolchain / tasks | **needs human review** — держать минимальный diff к upstream |

Ни один из этих путей **не** доказывает копирование с `studio/archive-heavy-fork-20260512-1245` по одному только списку файлов; при необходимости сделать точечное сравнение с архивной веткой **отдельно** (вне этого отчёта).

## 6. Initial migration plan

- **Оставить как overlay:** `deploy/studio-jarvis-native/`, `docs/studio/` (включая шаблоны и планы), `docs/upstream/memoh/`, три файла `.cursor/rules/*.mdc`, расширения `AGENTS.md` про Studio.
- **Убрать или выровнять с upstream:** изменения в `apps/desktop/*` и `apps/web/*`, если они не нужны для Studio Native — цель **нулевой** diff в прикладном коде при сохранении только overlay.
- **Вынести в sidecar/plugin:** интеграции, которым «не хватает» UI/skills/`/data/studio` — не восполнять через desktop/web патчи без RFC.
- **Явный RFC:** любое решение **сохранить** отличия в `apps/desktop` / `apps/web` / `mise.toml` как продуктовую особенность Studio (не только документацию).

## 7. Next recommended step

Сделать одно сравнение содержимого: `git diff upstream/main HEAD -- apps/desktop apps/web mise.toml` (локально, без коммита) и для каждого отличия зафиксировать: **нужно для Studio** / **случайный дрейф** / **вернуть как upstream**.

---

## 8. Non-core drift review

**Краткий список `git diff --name-status upstream/main...HEAD`** (изменения только на стороне коммитов `HEAD` после merge-base; **без** `apps/desktop`, `apps/web`, `mise.toml`):

`A` `.cursor/rules/00-upstream-docs-first.mdc`, `10-core-protection.mdc`, `20-studio-overlay-model.mdc` · `M` `AGENTS.md` · `A` весь `deploy/studio-jarvis-native/**` · `A` `docs/studio/FEATURE_DECISION_TEMPLATE.md` и прочие `docs/studio/*.md` из baseline · `A` `docs/upstream/memoh/*`.

**Источник таблицы ниже:** `git diff --name-status upstream/main HEAD` (non-core = `apps/desktop/**`, `apps/web/**`, `mise.toml`). Краткая сводка `git diff --stat upstream/main HEAD -- apps/desktop apps/web mise.toml`: **10 files changed, 24 insertions(+), 505 deletions(-)** — на стороне `HEAD` заметно **меньше** кода, чем в `upstream/main` (в т.ч. отсутствуют крупные файлы GStreamer в desktop).

**Категории:** **A** = нужно Studio Jarvis · **B** = случайный drift · **C** = upstream/vendor drift (нужно подтянуть upstream) · **D** = требует human review.

| path | category | likely reason | recommendation | safe to revert now |
|------|----------|---------------|----------------|-------------------|
| `apps/desktop/scripts/prepare-gstreamer.mjs` | **D** (или **C**) | В `upstream/main` файл есть; в `HEAD` отсутствует (**D** в дереве). Похоже на отставание от upstream по медиа-сборке, а не на Studio-overlay. | Либо восстановить из `upstream/main` для parity, либо зафиксировать в RFC, если отказ от GStreamer осознанный. | **yes** (в смысле `git checkout upstream/main -- <path>` для выравнивания с upstream; проверить сборку desktop) |
| `apps/desktop/src/main/gstreamer.ts` | **D** / **C** | Аналогично: отсутствует в `HEAD`, есть в upstream. | Как выше. | **yes** (при цели parity с upstream) |
| `apps/desktop/scripts/build.mjs` | **D** | −17 строк net; вероятно связано с удалением GStreamer/сопутствующих шагов. | Сверить с upstream; не оставлять «тихий» дрейф. | **unknown** (без просмотра hunk’ов) |
| `apps/desktop/package.json` | **D** | Зависимости/скрипты; малый diff. | Сравнить с upstream; убрать лишнее. | **unknown** |
| `apps/desktop/electron-builder.yml` | **D** | Упаковка Electron. | Подтвердить intent Studio vs parity. | **unknown** |
| `apps/desktop/.gitignore` | **B** / **D** | 1 строка; часто случайный drift. | Выровнять с upstream, если нет явной цели. | **yes** (низкий риск) |
| `apps/desktop/src/main/local-server.ts` | **D** | Порт/жизненный цикл локального сервера — типичная точка форка. | Решить: нужен ли отдельный diff к upstream для Studio. | **unknown** |
| `apps/web/src/pages/home/components/display-pane.vue` | **D** / **C** | Существенный diff (~35 строк в stat); upstream недавно двигает display runtime (см. историю `main`). | Явно сравнить с upstream: не потеряны ли важные фиксы. | **unknown** (риск регрессий UI/медиа) |
| `apps/web/src/pages/bots/components/bot-desktop.vue` | **B** / **D** | 1 строка — часто форматирование или мелкий флаг. | Проверить hunk; при отсутствии цели — как upstream. | **unknown** |
| `mise.toml` | **B** / **D** | −15 строк net относительно upstream. | Минимизировать diff к upstream; отделить Studio-хуки документированно. | **unknown** |

**Итог по non-core:** ни один из путей не выглядит как обязательный **Studio Jarvis overlay** (категория **A**) без отдельного подтверждения; преобладают **D** и риск **C** (отставание от upstream по desktop/GStreamer и web display).

---

## 9. Untracked files review

**Источник:** `git status --short` (2026-05-12). Секретные файлы не открывались; для `.sh`/очевидных markdown просмотрены только начальные строки там, где это уместно.

**Категории untracked:** **A** = нужно сохранить · **B** = можно удалить (после явного решения; автоматически не удалять) · **C** = не трогать без решения.

| path | category | recommendation |
|------|----------|----------------|
| `docs/studio/NATIVE_CORE_DEPENDENCY_AUDIT.md` | **A** | Сохранить; при необходимости добавить в git отдельным коммитом, когда будет решение. |
| `_obey_user_intent_block.md` | **B** | Локальная заготовка правил; можно удалить после подтверждения, не нужна репозиторию. |
| `_soul_tool_synthesis_append.md` | **B** | То же. |
| `_deepseek_cleanup_remote.sh` | **C** | Не анализировать полностью без нужды; не удалять без решения (может трогать окружение). |
| `_patch_soul_obey_remote.sh` | **C** | Содержит пути к Docker volume / workspace (видно по первым строкам); не удалять и не запускать без явного решения. |
| `_patch_soul_remote.sh` | **C** | Как соседние patch-скрипты. |
| `_verify_soul_obey.sh` | **C** | Верификационный скрипт; не трогать без решения. |
| `_verify_soul_remote.sh` | **C** | Аналогично. |
| `cmd/bridge/template/SOUL.md.bak-20260509-pre-web-fresh` | **B** / **C** | Резервная копия; можно удалить после подтверждения, что бэкап не нужен. |
| `internal/workspace/templates/SOUL.md.bak-20260509-pre-web-fresh` | **B** / **C** | То же. |
| `scripts/deepseek_vision_probe.py` | **B** / **C** | Локальный probe API (ключ только через env); не коммитить ключи; удаление — только по решению. |

---

## 10. Desktop / GStreamer drift review

**Read-only проверка (2026-05-12).** Команды: `git diff --name-status upstream/main HEAD -- apps/desktop`, `git diff --stat upstream/main HEAD -- apps/desktop`; сравнение с `merge-base(upstream/main, HEAD)` = `7b090f0cc65cce2c1230f296caf5113575735b45`.

**Факт:** `git diff --stat 7b090f0 HEAD -- apps/desktop` даёт **пустой** diff — коммиты на `HEAD` после merge-base **не меняли** `apps/desktop/`. Все отличия `HEAD` от `upstream/main` в этом каталоге объясняются тем, что **upstream добавил изменения после расхождения** (в истории для путей GStreamer виден коммит `15e68dfb` — *fix: desktop display runtime handling (#455)*). Это **не** выглядит как «мы удалили GStreamer в Studio-коммите» — в дереве `HEAD` файлов просто **нет** тех версий, которые появились на `upstream/main`.

**Поиск намеренного отключения Studio:** по `docs/**`, `deploy/**`, `AGENTS.md` и сообщениям `git log` (без `.env`/секретов) **нет** упоминаний, что GStreamer отключали специально для Studio Jarvis.

**Классификация A/B/C/D** (см. задачу §4): **A** = upstream добавил новое, у нас отсутствует · **B** = у нас намеренно удалено/упрощено · **C** = случайный drift · **D** = требует human review.

| path | upstream difference | likely reason | risk | recommendation | safe to restore from upstream |
|------|---------------------|---------------|------|----------------|------------------------------|
| `apps/desktop/scripts/prepare-gstreamer.mjs` | Файл есть на `upstream/main`, **отсутствует** в `HEAD` (в diff помечен как `D`). | **A** — добавлен на upstream после merge-base (`#455`); на ветке Studio не подтягивали. | **medium** — без скрипта не выполняются шаги `prepare:gstreamer*` из `package.json` upstream. | Взять версию из `upstream/main` вместе с остальными правками `#455` или эквивалентно смержить upstream desktop. | **yes** |
| `apps/desktop/src/main/gstreamer.ts` | Аналогично: **есть** upstream, **нет** в `HEAD`. | **A** | **medium** — функциональность дисплея/энкодера на desktop. | Как выше. | **yes** |
| `apps/desktop/package.json` | Отличается от upstream (скрипты `prepare:gstreamer*`, цепочка `dev`). | **A** / **C** — отражает upstream `#455`, у `HEAD` старая версия от merge-base. | **medium** — рассинхрон с документацией upstream по сборке desktop. | Синхронизировать с upstream или точечно перенести нужные поля после ревью. | **yes** (как часть синка) |
| `apps/desktop/scripts/build.mjs` | Upstream добавил строки (+17 net к merge-base), у `HEAD` меньше. | **A** / **C** — сопутствующие шаги сборки под GStreamer/ресурсы. | **medium** | Синхронизировать с upstream вместе с `prepare-gstreamer` / `package.json`. | **yes** |
| `apps/desktop/electron-builder.yml` | Небольшое расхождение (+4 строки к merge-base на upstream). | **A** / **C** — упаковка под новые нативные ресурсы. | **low**–**medium** | Сверить с upstream перед релизом desktop. | **yes** |
| `apps/desktop/.gitignore` | 1 строка: upstream **добавил** игнор, в `HEAD` нет. | **A** / **C** | **low** | Принять как upstream при общем синке. | **yes** |
| `apps/desktop/src/main/local-server.ts` | Небольшой diff относительно upstream (~19 строк в сумме с merge-base по upstream). | **A** / **D** — изменения в рамках `#455` (локальный сервер / дисплей); на Studio-коммитах не трогался. | **medium** — точка входа desktop ↔ server. | Прочитать diff к merge-base при синке; не смешивать с логикой Studio без причины. | **yes** (при цели parity; иначе **unknown** без просмотра hunk) |

**Вывод по смыслу**

- **Намеренное Studio-изменение «выключить GStreamer»:** признаков **нет** (ни в документации Studio, ни в studio-коммитах на этой ветке, ни в диффе merge-base→HEAD по `apps/desktop`).
- **Upstream drift:** **да** — ветка `HEAD` на merge-base по desktop **не включала** desktop/GStreamer изменения, уже попавшие в `upstream/main` (ключевой коммит для путей: **`15e68dfb`**). Ниже — **фактическое выравнивание** (после read-only аудита).

### Выровнено с `upstream/main` (фиксация)

- **Дата:** 2026-05-12.
- **Действие:** `git checkout upstream/main --` для семи путей:  
  `apps/desktop/.gitignore`, `apps/desktop/electron-builder.yml`, `apps/desktop/package.json`,  
  `apps/desktop/scripts/build.mjs`, `apps/desktop/scripts/prepare-gstreamer.mjs`,  
  `apps/desktop/src/main/gstreamer.ts`, `apps/desktop/src/main/local-server.ts`.
- **Проверка parity (после коммита восстановления):** `git diff --name-status upstream/main HEAD -- apps/desktop` — **без вывода** (дерево `apps/desktop` на `HEAD` совпадает с `upstream/main`).
- **Проверка до коммита (индекс/рабочая копия vs upstream):** `git diff --name-status upstream/main -- apps/desktop` — **без вывода**.
- **Коммит:** отдельный коммит с сообщением **`chore(studio): restore desktop upstream parity`** на этой ветке. Полный SHA не дублируется в тексте (он меняется при `--amend`); найти: `git log -1 --pretty=%H --grep='restore desktop upstream parity'` или `git log -1 --pretty=%H -- apps/desktop/scripts/prepare-gstreamer.mjs` сразу после выравнивания.
- **Ограничения соблюдены:** protected core не менялся; `apps/web/`, `mise.toml` не менялись; секреты и untracked не трогались.
