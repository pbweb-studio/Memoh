---
name: studio-people-source
description: Идентичность людей из /data/studio/people.md; memory только как поддержка; Go resolver не нужен.
---

# Studio — people source

## Source of truth

- **`/data/studio/people.md`** — главный файл по людям, ролям и `@handle` для Studio Jarvis.
- **Memory** — дополнительный контекст (встречи, договорённости), но **не** замена `people.md` для канонических полей, если пользователь ожидает ответ «по реестру».

## Как отвечать

- По **`@handle`** или display name: сначала **`Read /data/studio/people.md`**, затем при необходимости retrieval из memory.
- Если в файле нет человека — сообщите, что в SoT записи нет; не «достраивайте» ФИО из предположений.

## Техническое

- Отдельный **Go people resolver** и патчи **sqlc/store** для этого сценария **не требуются** (native baseline).
