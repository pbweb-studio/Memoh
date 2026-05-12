---
name: studio-project-registry
description: Проекты, чаты и задачи из JSON в /data/studio; строгое чтение файлов по запросу пользователя.
---

# Studio — project registry

## Source of truth

Один контур данных (все пути в workspace бота):

- `/data/studio/projects.json`
- `/data/studio/chats.json`
- `/data/studio/tasks.json`

## Типовые вопросы

Перед ответом **прочитайте** нужный файл (или все три для сводки):

- **Какие проекты есть?** → `projects.json` (`projects[]`).
- **Какие чаты у проекта X?** → `chats.json`: фильтр по `project_ids`, содержащим `id` проекта.
- **Какие задачи по проекту X?** → `tasks.json`: фильтр по `project_id`.
- **Кто ответственный?** → поля `owner_handle` (проект), `assignee_handle` (задача), связка с `people.md` по handle.

## Strict lookup

Если пользователь просит ответ **«строго из файла»** / **«только из JSON»**:

1. Выполните `Read` соответствующего файла в этой же сессии.
2. Перечисляйте только поля, реально присутствующие в JSON (id, name, status, notes, `owner_handle`, `chat_ids`, `task_ids` для проектов; для чатов — `id`, `title`, `type`, `telegram_chat_ref`, `project_ids`, `status`; для задач — `id`, `title`, `project_id`, `assignee_handle`, `status`, `priority`, `due_date`, `source`).
3. Не добавляйте сущности «с головы» и не смешивайте с hub-таблицами БД.
