# Chat stats MVP — runbook (Studio Jarvis)

Overlay для учёта лидов и отчётов без правок Memoh core. Полная архитектура: [CHAT_STATS_NATIVE_PLAN.md](./CHAT_STATS_NATIVE_PLAN.md).

## 1. Где лежат файлы (SoT)

| Путь | Назначение |
|------|------------|
| `/data/studio/stat_sources.json` | Реестр stat-чатов: `type`, `session_id`, `report_visibility`, команды. |
| `/data/studio/events/leads-YYYY-MM-DD.jsonl` | События за календарный день (одна строка = один JSON). **Не** Memory. |

В Docker на типичном деплое volume **`memoh_memoh_studio`** смонтирован в контейнер как **`/data/studio`**.

## 2. Зарегистрировать новый stat-чат

1. Добавьте бота в Telegram-группу, убедитесь что passive-сообщения сохраняются (см. логи `passive_saved=true`).
2. Узнайте `session_id` / `route_id` (Web UI → сессии, или лог ingest, или `list_sessions` в чате).
3. Скопируйте шаблон из репозитория: `deploy/studio-jarvis-native/data/stat_sources.example.json` → через **Files** вставьте новый объект в массив `sources` (или отредактируйте существующий).
4. В группе отправьте **`/studio_init leads`** или фразу «инициализируй этот чат как чат лидов» — обрабатывает managed skill **`studio-chat-stats`** (не ядро Memoh).
5. Проверьте ответ бота и содержимое `stat_sources.json`.

## 3. Установить / обновить skill `studio-chat-stats`

1. **Settings → Bot → Skills → New Skill** (или редактирование существующего).
2. Вставьте полный текст `deploy/studio-jarvis-native/skills/studio-chat-stats/SKILL.md` (frontmatter + тело). Сохраните.
3. Убедитесь, что skill **Effective** и не shadowed.

Альтернатива: `POST /api/bots/{bot_id}/container/skills` с массивом строк markdown — см. `deploy/studio-jarvis-native/RUNBOOK.md` §8.

## 4. Проверить passive ingest

- В логах `memoh-server`: `ingested=true`, `passive_saved=true` для группы.
- В UI или через `search_messages` по `session_id` видны пользовательские сообщения с маркером «Целевой».

## 5. Заполнить events (JSONL)

- **Авто:** попросите бота в Web UI или в чате выполнить извлечение: skill использует `search_messages` и **`write`** в `/data/studio/events/leads-YYYY-MM-DD.jsonl`.
- **Ручная загрузка:** через Files создайте/вставьте строки по образцу `deploy/studio-jarvis-native/data/events/leads-2026-05-13.example.jsonl`.

## 6. Запросить отчёт

| Где | Пример |
|-----|--------|
| **Local** (сам leads-чат) | `@Bot подбей статистику целевых за сегодня` |
| **Control** | `@Bot подбей статистику целевых за сегодня по чату лидоруба` / `по всем чатам лидов` |

Условия: `report_visibility.local_chat` / `control_chats` в `stat_sources.json` должны совпадать с фактическими `conversation_id`.

## 7. Отключить чат

- `/studio_disable` в чате **или** правка JSON: `"enabled": false` для нужного `source`.

## 8. «Бот не видит историю»

Возможные причины:

1. **Нет JSONL** — отчёт должен честно сказать «нет событий»; выполните извлечение (п. 5).
2. **`search_messages` не находит токен** — см. `docs/studio/NATIVE_RUNTIME_AUDIT_RESULTS.md`; тогда временно доберите события вручную в JSONL или запланируйте sidecar по HTTP API `GET /api/bots/{bot_id}/messages?session_id=...` (без правок core).
3. **Чат не в реестре** — Jarvis не знает, что это stat-чат; выполните `/studio_init`.
4. **Запрос из запрещённого чата** — ожидаемый отказ без цифр.

## 9. Рестарт сервера

При изменении только **`/data/studio/*`** и managed skills **рестарт memoh-server не обязателен**.
