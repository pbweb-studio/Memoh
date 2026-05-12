---
name: studio-daily-digest
description: Поведение для Schedule: краткий daily digest из файлов /data/studio без custom harvester.
---

# Studio — daily digest (Schedule)

## Когда применяется

Этот skill описывает поведение агента в **turn сессии типа `schedule`** (cron + instruction в UI Schedule), а не отдельный процесс вне Memoh.

## Что читать

В указанном порядке (по необходимости краткости):

1. `/data/studio/projects.json`
2. `/data/studio/tasks.json`
3. `/data/studio/chats.json` (если нужен контекст каналов)
4. `/data/studio/people.md` (для расшифровки `owner_handle` / `assignee_handle`)

Опционально: последние строки `events.jsonl`, если файл есть и пользователь/Instruction просит хронику.

## Что выводить

- Краткий **daily digest**: активные проекты, открытые задачи с дедлайнами, блокеры — **только** из файлов.
- Первая строка — дата/маркер запуска (например `Studio digest YYYY-MM-DD`).
- **Не** реализуйте **custom harvester** и **не** ожидайте legacy cron из archive — источник событий только файлы + штатный Schedule.

## Telegram

Если Instruction требует отправить digest в мессенджер — используйте **только** настроенный в продукте способ доставки (например tool `send` с корректным **`platform`**, как в runtime audit Block G). Не подставляйте токены и chat id в текст skill.
