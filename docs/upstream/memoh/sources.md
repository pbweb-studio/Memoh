# Memoh upstream sources (for agents)

Use this list when tracing **documented** behavior. Prefer **https://docs.memoh.ai** and paths under **`docs/docs/`** in this repo for the revision you have checked out.

| Topic | Primary URL | In-repo mirror (EN) | Notes |
|--------|-------------|---------------------|--------|
| **Memoh GitHub repository** | [https://github.com/memohai/Memoh](https://github.com/memohai/Memoh) | — | Source code, issues, PRs |
| **Memoh docs site** | [https://docs.memoh.ai](https://docs.memoh.ai) | `docs/docs/` | VitePress site source |
| **Skills documentation** | [https://docs.memoh.ai/getting-started/skills](https://docs.memoh.ai/getting-started/skills) | `docs/docs/getting-started/skills.md` | Managed skills |
| **Memory documentation** | [https://docs.memoh.ai/memory-providers/](https://docs.memoh.ai/memory-providers/) | `docs/docs/getting-started/memory.md` | **TODO: verify** exact subsection URLs for your Memoh version on docs.memoh.ai |
| **MCP / tools documentation** | [https://docs.memoh.ai/getting-started/mcp](https://docs.memoh.ai/getting-started/mcp) | `docs/docs/getting-started/mcp.md` | MCP connections, tool gateway |
| **Access / ACL documentation** | [https://docs.memoh.ai/getting-started/access](https://docs.memoh.ai/getting-started/access) | `docs/docs/getting-started/access.md` | Source-aware ACL |
| **Telegram / channels documentation** | [https://docs.memoh.ai/getting-started/channels](https://docs.memoh.ai/getting-started/channels) | `docs/docs/getting-started/channels.md` | Channel adapters, bindings |
| **Schedule documentation** | [https://docs.memoh.ai/getting-started/schedule](https://docs.memoh.ai/getting-started/schedule) | `docs/docs/getting-started/schedule.md` | Cron-style tasks |
| **Releases / tags / changelog** | [https://github.com/memohai/Memoh/releases](https://github.com/memohai/Memoh/releases) | `CHANGELOG.md` (if present at repo root) | **TODO: verify** changelog file name/location for your fork |

## Additional in-repo guides (common Studio needs)

| Topic | In-repo path |
|--------|----------------|
| Workspace files | `docs/docs/getting-started/files.md` |
| Browser automation (gateway) | **TODO: verify** URL path on docs.memoh.ai for browser gateway; in-repo: search `docs/docs` for browser / gateway |
| Search providers | `docs/docs/getting-started/search-provider.md` |
| Heartbeat | `docs/docs/getting-started/heartbeat.md` |
| Compaction | `docs/docs/getting-started/compaction.md` |

## TODO: verify from upstream

- Exact **browser gateway** public doc URL if not only under in-repo `apps/browser` README.
- Whether **Telegram** has a dedicated subpage beyond **Channels** for your docs version.
- **CHANGELOG** vs **GitHub Releases** as the canonical release narrative for your deployment process.

When in doubt, open **https://docs.memoh.ai** and the matching file under **`docs/docs/`** on the same commit.
