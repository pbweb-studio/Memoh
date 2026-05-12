# Upstream Memoh — local documentation index

This directory (`docs/upstream/memoh/`) is a **local index and snapshot pointer** for **Cursor and coding agents** working on **Studio Jarvis / Memoh Native**.

It is **not** a full mirror of upstream documentation. It tells agents **where to look first** and how Studio should relate to Memoh capabilities.

## Source of truth for freshness

- **Official repository:** see `sources.md` (GitHub).
- **Official documentation site:** **https://docs.memoh.ai** — authoritative for up-to-date behavior, new features, and wording.
- **In-repo doc tree:** `docs/docs/` (VitePress sources) tracks the same content as the public site for the checked-out revision.

When `docs/upstream/memoh/` disagrees with **current** upstream, **trust GitHub + docs.memoh.ai** and update this index in a follow-up change.

## Agent workflow

Before **designing or implementing** a Studio Jarvis feature, Cursor must:

1. Read files in **`docs/upstream/memoh/`** (this README, `sources.md`, `native-capabilities.md`).
2. Open the relevant **official** guides under `docs/docs/getting-started/` (or the matching URL on docs.memoh.ai).
3. Record which **documented Memoh mechanism** the feature uses (see `AGENTS.md` and `.cursor/rules/00-upstream-docs-first.mdc`).

## Related project rules

- `.cursor/rules/00-upstream-docs-first.mdc` — docs-first + RFC when departing from documented behavior.
- `.cursor/rules/10-core-protection.mdc` — protected core paths.
- `.cursor/rules/20-studio-overlay-model.mdc` — `/data/studio`, skills, memory, MCP/sidecars.
