# Native runtime audit — Web-only (`memohwebaudit`)

**Дата:** 2026-05-12  
**Ветка:** `studio/native-baseline-20260512`  
**Окружение:** Docker compose project `memohwebaudit`, Web UI `http://127.0.0.1:8082`, изолированный `.local-web-audit/`. Go/Vue не менялись, deploy не выполнялся, реальный Telegram не подключался.

**Бот:** Web Audit People (provider + chat model заданы пользователем в UI).

---

## Сводная таблица

| Feature | Scenario | Result | Evidence | Classification | Restore old custom? | Notes |
|---------|----------|--------|----------|----------------|---------------------|-------|
| people identity by handle | Запросы вида «кто такой @grvtkv / @ibambets» | Pass | Корректные ФИО и роли; в новой сессии без повторной загрузки файла — тот же ответ | Native + config / files + skills + memory | **Нет** | Без Go-resolver |
| people identity by display name | «Егор» / «Глеб» | Pass (ранее в том же аудите) | Соответствие `people.md` / памяти | Native + config / files + skills + memory | **Нет** | |
| people.md source of truth | Вопрос о правиле источника данных о людях | Pass | Ответ: `people.md` = SoT; память — доп. контекст | Native + skills (+ memory aux) | **Нет** | Skill `web-audit-people` влияет на формулировки |
| files tool read | Явный запрос прочитать `/data/people.md` | Pass | UI tool trace: **Read** → `/data/people.md`; цитата строки с `@grvtkv` | Native files / workspace | **Нет** | |
| list `/data` | List только инструментами файлов | Pass | UI: **List** → `/data`; перечислены `people.md`, `memory`, `skills`, … | Native files | **Нет** | |
| manual memory entry retrieval | «Не используй people.md / файлы; только memory: кто @grvtkv?» | Pass | Ответ верный; **без** видимых List/Read между вопросом и ответом в a11y snapshot | Native memory (retrieval); file tools не обязательны на turn | **Нет** | Явная строка retrieval в UI не показана — только корректный ответ |
| skill influence | «Какое правило по источнику данных о людях?» | Pass | Текст ответа: `people.md` как SoT | Native skills | **Нет** | Отдельная строка «Use skill» на этом turn в снимке не требовалась — семантика skill видна в ответе |
| cross-session people lookup | New Session → «Кто такой @grvtkv?» без перезагрузки файла | Pass | Ответ: Егор Вотяков; file tool rows в снимке отсутствуют | Native memory / shared bot context | **Нет** | Skills/files бота остаются доступны боту между сессиями |
| cross-session new fact recall | Сессия A: «Запомни: AuditNative ↔ @grvtkv»; сессия B: вопрос о человеке проекта | Pass | Сессия A: UI trace обновления `memory/2026-05-12.md` (+ новая запись); сессия B: ответ `@grvtkv` | Native memory write + cross-session read | **Нет** | |
| raw cross-chat search gap | Полнотекстовый поиск по всей сырой истории чатов как отдельный продуктовый сценарий | Not tested | В этом прогоне не проверялось | Unknown / doc gap | **Нет** | См. also §8 исходного audit-дока |
| Telegram group runtime | Реальная группа, токен BotFather, inbound/outbound | Not tested | Намеренно не запускали | Documented native; runtime N/A here | **Нет** | Только по `docs/channels/telegram.md` + план |

---

## Tool trace (копируемая формулировка)

**People через файл (ранее + подтверждено):**  
`Use skill web-audit-people` → `List /data` → `Read /data/people.md`.

**Этот прогон (дополнительно):**  
`List /data`; `Read /data/people.md`; запись факта — обновление `memory/2026-05-12.md` (новая memory-запись).

---

## Выводы для планирования

1. **People identity** — закрывать через **files (`people.md`) + skill + memory**; **не** возвращать Go people resolver и **не** делать core-touch под эту задачу.  
2. **Telegram** — оставить на отдельный разрешённый runtime-прогон с реальным каналом.  
3. **Cross-session** для бота в Web подтверждён и для people lookup, и для явно сохранённого факта (через агентское обновление memory-файла).

---

*Автоматический коммит не выполнялся.*
