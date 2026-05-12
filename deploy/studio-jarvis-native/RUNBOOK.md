# Studio Jarvis Native — runbook (UI setup)

Пошаговая настройка **без** правок Memoh core. **Не** вставляйте токены, пароли и ключи в workspace-файлы этого bundle — только в штатные поля UI (Platforms и т.д.).

## 0. Предпосылки

- Запущенный экземпляр **Memoh** (локально или на сервере — по вашей схеме).
- Аккаунт с правом создавать ботов и редактировать Files / Skills / Schedule.
- Документация upstream: [getting-started](https://github.com/memohq/memoh/tree/main/docs/docs/getting-started) (в монорепо: `docs/docs/getting-started/`).

## 1. Запустить Memoh

- Поднимите приложение согласно вашему окружению.
- Убедитесь, что веб-интерфейс доступен.

## 2. Provider / Model

- Откройте **Bot** (или создание бота) → раздел **General**.
- Выберите **chat model** (и при необходимости модель для heartbeat — по доке проекта).
- Сохраните настройки.

## 3. Создать бота «Studio Jarvis Native»

- Создайте нового бота с понятным именем (например, `Studio Jarvis Native`).
- Зафиксируйте **slug** / идентификатор для ссылок в Schedule и документации команды.

## 4. Memory Provider

- Вкладка **Memory** у бота.
- Подключите провайдер памяти и включите **retrieval** между сессиями (см. `memory.md` в доках Memoh).
- Память — **дополнение** к файлам; SoT по людям и реестрам остаётся в `/data/studio/`.

## 5. Telegram Platform

- **Platforms** → **Telegram**.
- Вставьте токен бота из **BotFather** только в поле UI → **Save and enable**.
- Убедитесь, что адаптер в состоянии **Active** (см. runtime audit Block E).

## 6. Access / ACL

- Вкладка **Access**.
- Настройте preset для **DM** и для **групп** (роли owner / team по политике команды).
- В группе проверьте **`/access`** / **`/access@YourBot`** после добавления бота (см. audit Block E.8).

## 7. Files workspace — `/data/studio/`

Через **Files** (upload / new file / Monaco):

1. Создайте папку **`/data/studio/`** (если её нет).
2. Создайте или загрузите:
   - `people.md` — скопируйте из `deploy/studio-jarvis-native/data/people.md` и **замените** содержимое на production SoT (роли, handles, без секретов).
   - `projects.json`, `chats.json`, `tasks.json` — из `data/` этого bundle, затем правьте под реальность.
3. Опционально: журнал событий по образцу `events.example.jsonl` → рабочий файл, например `events.jsonl` (append-only).

## 8. Managed skills

Для каждого имени из списка:

1. **Skills** → создать skill с именем каталога (как в репозитории: `studio-jarvis-behavior`, `studio-people-source`, `studio-project-registry`, `studio-daily-digest`).
2. Откройте **`SKILL.md`** в редакторе и вставьте текст из соответствующего файла в `deploy/studio-jarvis-native/skills/<name>/SKILL.md`.
3. Сохраните. Убедитесь, что skill **включён** для бота (по правилам UI Memoh).

## 9. Schedule — daily digest

- **Schedule** → новое правило.
- **Cron**: например `0 9 * * *` (утро по серверному timezone — см. доку `schedule.md`; в аудите timezone совпала с UTC).
- **Instruction / command**: кратко укажите, что агент должен прочитать `projects.json`, `tasks.json`, при необходимости `chats.json` и `people.md`, и сформировать краткий digest; отсылайте к правилам skill **`studio-daily-digest`**.
- При необходимости задайте **Run limit** / `max_calls` и владельца slash-команд (см. pending в audit Block F).
- Доставка в Telegram — только если в сценарии Schedule явно настроена отправка на нужный **platform** (см. `NATIVE_RUNTIME_AUDIT_RESULTS.md` Block G).

## 10. Проверки

- **DM**: вопрос по `@handle` и строгий запрос по JSON-файлам.
- **Группа**: ответ только после **mention** бота (без mention — допустимо молчание для MVP).
- Пройдите **`ACCEPTANCE_CHECKLIST.md`**.

## 11. Token rotation (напоминание)

После аудитов и выдачи токенов третьим лицам: перевыпустите токен в **BotFather**, обновите поле в **Platforms**, старый токен отзовите. **Не** храните токены в git и в markdown runbook.
