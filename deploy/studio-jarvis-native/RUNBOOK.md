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

## 8. Managed skills (обязательно через Memoh, не «тихим» копированием на volume)

**Где живут managed skills в рантайме:** в контейнере workspace бота путь **`/data/skills/<skill-name>/SKILL.md`** (см. upstream `docs/docs/getting-started/skills.md`). Список на вкладке **Settings → Bot → Skills** и в боковой панели чата **Skills** строится из API **`GET /api/bots/{bot_id}/container/skills`** (сканирование `/data/skills` и discovery roots через **workspace bridge**, не произвольный произвольный путь на хосте).

**Что не считается штатным способом:** положить каталоги `skills/.../SKILL.md` только на bind-mount хоста (`workspace-data/<bot_id>/skills/...`) и ожидать, что UI их увидит. Если файлы не попали в тот же слой ФС, который обслуживает bridge агента, или каталог `/data/skills` в контейнере не читается, **`GET .../container/skills` вернёт пустой список** — в UI будет **«No skills yet»** (это **пустой каталог skills**, а не «в этой сессии skills не вызывались»).

### Вариант A (рекомендуется): Web UI

1. **Settings** → выберите бота → **Skills** → **New Skill**.
2. Вставьте **полный** текст `SKILL.md` из `deploy/studio-jarvis-native/skills/<name>/SKILL.md` (YAML frontmatter + тело). **Сохраните**.
3. Повторите для четырёх имён: `studio-jarvis-behavior`, `studio-people-source`, `studio-project-registry`, `studio-daily-digest`.
4. Нажмите **Refresh** в списке skills при необходимости; в карточках должны быть бейджи **Managed** + **Effective**.

**YAML:** в поле `description:` не оставляйте неэкранированный текст с двоеточием вроде `Schedule: ...` без кавычек — иначе `POST .../container/skills` вернёт `400 invalid YAML frontmatter`. Безопасно: `description: "..."`.

### Вариант B: HTTP API (автоматизация / CI)

После логина (`POST /api/auth/login` → `access_token`):

- **`POST /api/bots/{bot_id}/container/skills`** с телом `{"skills":["<полный markdown документ 1>", "..."]}` — каждый элемент массива = один `SKILL.md` с валидным frontmatter; сервер создаёт `/data/skills/<name>/` и пишет файл через тот же bridge, что и UI.

Тело JSON нужно сериализовать как **массив строк**, а не «объектов» (см. `SkillsUpsertRequest` в коде).

### Вариант C: только файлы на volume

Имеет смысл **только если** вы гарантировали, что эти же пути видны процессу, который обслуживает `container/skills` (тот же mount, что и для успешного `Read /data/studio/...`). В противном случае снова получите пустой каталог в UI — предпочитайте A или B.

### Production rollout

На проде повторите **вариант A** (или B из защищённого пайплайна с сервисным аккаунтом): не копируйте bundle на сервер без проверки `GET .../container/skills`; после загрузки зафиксируйте в change log, что четыре skill в состоянии **effective**.

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
