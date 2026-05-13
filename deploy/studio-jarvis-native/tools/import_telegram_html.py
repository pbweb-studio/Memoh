#!/usr/bin/env python3
"""
Deterministic Telegram Desktop HTML chat export → Studio JSONL importer.

Writes:
  <studio-dir>/imports/telegram/<slug>/messages.normalized.jsonl
  <studio-dir>/imports/telegram/<slug>/import-summary.json
  <studio-dir>/events/leads-YYYY-MM-DD.jsonl (upsert by event_id + semantic lead key)

Does not modify events/state/events_active.json or people.md.

target_lead rows for the same calendar day are collapsed by semantic key
(source_id + date + normalized phone, or name+city if no phone, else hash of raw text)
so manual evt_* / lead-* rows do not duplicate telegram-message-* for the same person.

Host note (Docker): Jarvis Files/read maps container /data/studio to the bot workspace
.../memoh_memoh_data/_data/workspace-data/<bot_id>/studio. The separate volume
memoh_memoh_studio is not bot-visible SoT unless mounts are explicitly unified — see runbook.
"""

from __future__ import annotations

import argparse
import hashlib
import html as html_lib
import json
import re
import shutil
import sys
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")


def _host_path_normalized(studio: Path) -> str:
    return str(studio.resolve()).replace("\\", "/")


def validate_workspace_studio_dir(
    studio: Path,
    *,
    allow_noncanonical: bool,
) -> int | None:
    """
    Guard against writing to a Docker tree that is not the same as bot-visible /data/studio.

    Returns an exit code (non-zero) to abort, or None to continue.
    """
    sp = _host_path_normalized(studio)
    looks_memoh_studio = "/memoh_memoh_studio/" in sp or sp.rstrip("/").endswith("memoh_memoh_studio/_data")
    if looks_memoh_studio:
        print(
            "WARNING: --studio-dir is under Docker volume memoh_memoh_studio. "
            "Jarvis Files/read for /data/studio is usually workspace-data/<bot_id>/studio "
            "on memoh_memoh_data, not this volume. See deploy/studio-jarvis-native/RUNBOOK.md.",
            file=sys.stderr,
        )
        if not allow_noncanonical:
            print(
                "ERROR: refusing non-canonical studio dir. Use the workspace-data/<bot_id>/studio path, "
                "or pass --allow-noncanonical-studio-dir only if mounts are verified.",
                file=sys.stderr,
            )
            return 3

    events_dir = studio / "events"
    active = studio / "events" / "state" / "events_active.json"
    if active.is_file():
        return None
    if not events_dir.is_dir():
        print(
            f"WARNING: {events_dir} is not a directory yet; it will be created when writing JSONL. "
            "Confirm this path matches what the bot reads as /data/studio (Files tool / workspace bridge).",
            file=sys.stderr,
        )
    else:
        print(
            f"WARNING: missing {active} — weak confirmation this is the bot-visible Studio tree. "
            "Prefer a directory that already contains events/state/events_active.json; "
            "verify stat_sources.json via Files/read before relying on import output.",
            file=sys.stderr,
        )
    return None


def slugify(title: str, max_len: int = 80) -> str:
    t = title.strip().lower()
    t = re.sub(r"\s+", "-", t)
    t = re.sub(r"[^a-z0-9а-яё\-]+", "", t, flags=re.I)
    t = t.strip("-")[:max_len]
    return t or "chat"


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    bak = path.with_suffix(path.suffix + f".bak-{_now_stamp()}-before-telegram-import")
    shutil.copy2(path, bak)
    return bak


def html_fragment_to_plain(html_inner: str) -> str:
    """Convert inner HTML of div.text to plain text (br, a, basic tags)."""
    s = html_inner or ""
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>\s*<p>", "\n\n", s)

    def a_repl(m: re.Match[str]) -> str:
        body = m.group(0)
        href_m = re.search(r'href="([^"]+)"', body, re.I)
        inner = re.sub(r"(?is)<[^>]+>", "", body)
        inner = html_lib.unescape(inner.strip())
        if not href_m:
            return inner
        href = href_m.group(1).strip()
        if href.startswith("tel:"):
            return href[4:]
        if href.startswith("mailto:"):
            return href[7:]
        if inner and inner not in href:
            return f"{inner} {href}".strip()
        return href

    s = re.sub(r"(?is)<a\s+[^>]*>.*?</a>", a_repl, s)
    s = re.sub(r"(?is)<[^>]+>", "", s)
    s = html_lib.unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


MESSAGE_BLOCK_RE = re.compile(
    r'<div class="message (?P<classes>[^"]*)" id="(?P<mid>message[^"]+)"',
    re.I,
)
TITLE_ATTR_RE = re.compile(
    r'title="(?P<d>\d{2})\.(?P<m>\d{2})\.(?P<y>\d{4})\s+(?P<h>\d{2}):(?P<mi>\d{2}):(?P<s>\d{2})\s+[^"]+"',
)
FROM_NAME_RE = re.compile(r'<div class="from_name">\s*([^<]+?)\s*</div>', re.S | re.I)
TEXT_BLOCK_RE = re.compile(
    r'<div class="text[^"]*">\s*(.*?)\s*</div>',
    re.S | re.I,
)


def extract_chat_title(full_html: str) -> str:
    m = re.search(
        r'page_header[\s\S]{0,800}?<div class="text[^"]*">\s*([^<]+?)\s*</div>',
        full_html,
        re.I | re.S,
    )
    if m:
        return html_lib.unescape(m.group(1).strip())
    return "Unknown chat"


def iter_message_blocks(full_html: str) -> Iterator[tuple[str, str, str]]:
    """Yields (message_id_attr, class_attr, block_html) for each message div."""
    for m in MESSAGE_BLOCK_RE.finditer(full_html):
        start = m.start()
        mid = m.group("mid").strip()
        classes = m.group("classes").strip()
        next_m = MESSAGE_BLOCK_RE.search(full_html, m.end())
        end = next_m.start() if next_m else len(full_html)
        yield mid, classes, full_html[start:end]


def parse_dt_from_block(block: str) -> tuple[str, str] | None:
    """Return (YYYY-MM-DD, HH:MM) from date details title."""
    tm = TITLE_ATTR_RE.search(block)
    if not tm:
        return None
    d, mo, y = tm.group("d"), tm.group("m"), tm.group("y")
    h, mi = tm.group("h"), tm.group("mi")
    return f"{y}-{mo}-{d}", f"{h}:{mi}"


def extract_from_name(block: str) -> str | None:
    fm = FROM_NAME_RE.search(block)
    if not fm:
        return None
    return html_lib.unescape(fm.group(1).strip())


def extract_text_raw(block: str) -> str:
    tm = TEXT_BLOCK_RE.search(block)
    if not tm:
        return ""
    return html_fragment_to_plain(tm.group(1))


def numeric_id_from_attr(mid: str) -> str:
    mid = mid.strip()
    if mid.lower().startswith("message"):
        tail = mid[7:]
        digits = re.sub(r"\D", "", tail)
        return digits or tail
    return re.sub(r"\D", "", mid) or mid


def first_ru_phone(text: str) -> str | None:
    """First plausible RU mobile / city digit sequence (10–11 digits), normalized to 7XXXXXXXXXX."""
    if not text:
        return None
    candidates: list[tuple[int, str]] = []
    for m in re.finditer(r"(?:\+?7|8)\s*\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}", text):
        digits = re.sub(r"\D", "", m.group(0))
        if len(digits) == 11 and digits.startswith("7"):
            candidates.append((m.start(), digits))
        elif len(digits) == 11 and digits.startswith("8"):
            candidates.append((m.start(), "7" + digits[1:]))
    for m in re.finditer(r"(?<!\d)(\d{11})(?!\d)", text):
        digits = m.group(1)
        if digits.startswith("7") and digits[1] == "9":
            candidates.append((m.start(), digits))
    for m in re.finditer(r"(?<!\d)(\d{10})(?!\d)", text):
        digits = m.group(1)
        if digits.startswith("9"):
            candidates.append((m.start(), "7" + digits))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def is_summary_report(text: str) -> bool:
    tl = text.lower()
    if re.search(r"отч[её]т\s+за", tl):
        return True
    if re.search(r"целевые\s+лиды", tl) and re.search(r"\d", tl):
        return True
    if "кол-во" in tl and "целевых" in tl:
        return True
    if re.search(r"целевых\s*[-–—:]\s*\d+", tl):
        return True
    return False


def is_operational_note(text: str) -> bool:
    tl = text.lower()
    if "docs.google.com/spreadsheets" in tl and "целевой" in tl:
        return True
    if "вы точно" in tl and "целевой" in tl:
        return True
    if "подскажите" in tl and "лид" in tl and "?" in text:
        return True
    return False


def is_target_lead_text(text: str) -> bool:
    if not text.strip():
        return False
    tl = text.lower()
    if is_summary_report(text):
        return False
    if is_operational_note(text):
        return False
    if re.search(r"(?<![а-яё])целевой\s*\.", tl):
        return True
    if re.search(r"(?<![а-яё])целевой\s+лид", tl):
        return True
    if "есть целевой лид" in tl:
        return True
    return False


def strip_target_prefix(text: str) -> str:
    t = text.strip()
    # "7900...Целевой." (no space) — strip leading RU phone before marker
    t = re.sub(r"(?is)^(?:\+?7|8)?\d{10,11}(?=[Цц]елевой)", "", t)
    t = re.sub(r"(?is)^\s*целевой\s+лид\.?\s*", "", t)
    t = re.sub(r"(?is)^\s*целевой\.\s*", "", t)
    t = re.sub(r"(?is)^\s*есть\s+целевой\s+лид\.?\s*", "", t)
    return t.strip()


def parse_lead_fields(raw_text: str) -> dict[str, Any]:
    phone = first_ru_phone(raw_text)
    body = strip_target_prefix(raw_text)
    body = body.strip()
    status = "Актуально" if re.search(r"(?i)\bактуально\b", raw_text) else None
    call_when: str | None = None
    if re.search(r"(?i)\bсегодня\b", raw_text):
        call_when = "сегодня"
    if re.search(r"(?i)\bзавтра\b", raw_text):
        call_when = (call_when + ", завтра") if call_when else "завтра"
    if re.search(r"(?i)2\s*я\s+пол", raw_text) or re.search(r"(?i)во\s+2", raw_text):
        call_when = (call_when + ", 2я пол. дня") if call_when else "2я пол. дня"

    work = body
    if phone:
        work = work.replace(phone, " ", 1)
    work = re.sub(r"\s+", " ", work).strip()
    parts = [p.strip() for p in re.split(r"\s*\.\s*", work) if p.strip()]

    name: str | None = None
    city: str | None = None
    comment_parts: list[str] = []

    idx = 0
    while idx < len(parts) and re.match(r"^[\d\s\-\(\)]+$", parts[idx]):
        idx += 1
    if idx < len(parts) and re.search(r"\d", parts[idx]):
        only_digits = re.sub(r"\D", "", parts[idx])
        if len(only_digits) >= 10:
            idx += 1
    if idx < len(parts):
        name = parts[idx]
        idx += 1
    if idx < len(parts):
        nxt = parts[idx]
        low = nxt.casefold()
        if low in {"актуально", "не актуально"}:
            pass
        elif re.match(r"(?i)^(для|для сына|для дочери)\b", nxt):
            comment_parts.append(nxt)
            idx += 1
            if idx < len(parts):
                city = re.sub(r"(?i)^г\.?\s*", "", parts[idx]).strip()
                idx += 1
        else:
            if re.match(r"(?i)^г\.?\s*", nxt) or len(nxt) <= 56:
                city = re.sub(r"(?i)^г\.?\s*", "", nxt).strip()
            else:
                city = nxt
            idx += 1
    while idx < len(parts):
        seg = parts[idx]
        if seg.casefold() in {"актуально", "не актуально"}:
            idx += 1
            continue
        comment_parts.append(seg)
        idx += 1
    comment = ". ".join(comment_parts).strip() or None

    needs_review = False
    stripped = strip_target_prefix(raw_text).strip()
    if is_target_lead_text(raw_text) and not phone:
        if not re.match(r"(?i)^[а-яёa-z][а-яёa-z\s\-]{0,50}\.", stripped):
            needs_review = True
    if name and len(name) > 60:
        needs_review = True

    return {
        "phone": phone,
        "name": name,
        "city": city,
        "status": status,
        "call_when": call_when,
        "comment": comment,
        "needs_review": needs_review,
    }


def load_jsonl_events_by_id(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        eid = str(obj.get("event_id") or "").strip()
        if eid:
            out[eid] = obj
    return out


def write_jsonl_merged(path: Path, events_by_id: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(events_by_id[k], ensure_ascii=False) for k in sorted(events_by_id.keys())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _norm_semantic_token(value: Any) -> str:
    s = unicodedata.normalize("NFKC", str(value or "").strip()).casefold()
    s = re.sub(r"\s+", " ", s)
    return s


def semantic_lead_key(ev: dict[str, Any]) -> str:
    """Stable key: source_id + date + phone, else name+city, else raw hash."""
    if ev.get("event_type") != "target_lead":
        return f"_non_target|{ev.get('event_id')}"
    sid = str(ev.get("source_id") or "").strip() or "_no_source"
    day = str(ev.get("date") or "").strip() or "_no_date"
    phone = ev.get("phone")
    if phone is not None and str(phone).strip():
        digits = re.sub(r"\D", "", str(phone))
        if len(digits) == 11 and digits.startswith("8"):
            digits = "7" + digits[1:]
        return f"tl|{sid}|{day}|p|{digits}"
    name = _norm_semantic_token(ev.get("name"))
    city = _norm_semantic_token(ev.get("city"))
    if name or city:
        return f"tl|{sid}|{day}|nc|{name}|{city}"
    raw = _norm_semantic_token(ev.get("raw_text"))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"tl|{sid}|{day}|h|{digest}"


def _lead_completeness_rank(ev: dict[str, Any]) -> tuple[int, int, int]:
    """Sort key: higher tuple = richer record."""
    keys = (
        "phone",
        "name",
        "city",
        "status",
        "call_when",
        "comment",
        "raw_text",
        "session_id",
        "route_id",
        "telegram_chat_id",
        "import_source",
        "telegram_message_id",
        "source_type",
        "author",
    )
    filled = 0
    for k in keys:
        v = ev.get(k)
        if v is None or v == "" or v is False:
            continue
        filled += 1
    raw_len = len(str(ev.get("raw_text") or ""))
    eid = str(ev.get("event_id") or "")
    kind = 0
    if eid.startswith("telegram-message-"):
        kind = 2
    elif eid.startswith("evt_") or eid.startswith("lead-"):
        kind = 1
    return (filled, kind, raw_len)


def richer_target_lead(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ra, rb = _lead_completeness_rank(a), _lead_completeness_rank(b)
    if rb > ra:
        return b
    if rb < ra:
        return a
    if str(b.get("event_id", "")).startswith("telegram-message-"):
        return b
    return a


def dedupe_semantic_target_leads(events_by_id: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Keep non-target_lead rows; collapse target_lead rows sharing semantic_lead_key (richest wins)."""
    non_target: dict[str, dict[str, Any]] = {}
    targets: list[dict[str, Any]] = []
    for eid, ev in events_by_id.items():
        if ev.get("event_type") == "target_lead":
            targets.append(ev)
        else:
            non_target[eid] = ev
    by_sk: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in targets:
        by_sk[semantic_lead_key(ev)].append(ev)
    merged_targets: dict[str, dict[str, Any]] = {}
    for rows in by_sk.values():
        chosen = rows[0]
        for r in rows[1:]:
            chosen = richer_target_lead(chosen, r)
        merged_targets[str(chosen["event_id"])] = chosen
    out = {**non_target, **merged_targets}
    return out


def dedupe_jsonl_file(path: Path) -> tuple[Path, int, int]:
    """Backup path, before count, after count (target_lead only)."""
    if not path.is_file():
        raise FileNotFoundError(path)
    stamp = _now_stamp()
    bak = path.with_suffix(path.suffix + f".bak-{stamp}-before-dedupe")
    shutil.copy2(path, bak)
    cur = load_jsonl_events_by_id(path)
    before_tl = sum(1 for v in cur.values() if v.get("event_type") == "target_lead")
    new = dedupe_semantic_target_leads(cur)
    after_tl = sum(1 for v in new.values() if v.get("event_type") == "target_lead")
    write_jsonl_merged(path, new)
    return bak, before_tl, after_tl


def match_source(
    registry: dict[str, Any],
    *,
    source_id: str | None,
    title: str,
    source_type: str,
) -> dict[str, Any] | None:
    sources = registry.get("sources")
    if not isinstance(sources, list):
        return None
    if source_id:
        for s in sources:
            if isinstance(s, dict) and str(s.get("id", "")).strip() == source_id:
                return s
        return None
    tl = title.casefold()
    for s in sources:
        if not isinstance(s, dict):
            continue
        if str(s.get("type", "")).strip() != source_type:
            continue
        st = str(s.get("title", "")).casefold()
        if st and (st in tl or tl in st or st[:20] in tl):
            return s
    return None


def append_draft_source(
    registry: dict[str, Any],
    *,
    title: str,
    source_type: str,
    slug: str,
) -> dict[str, Any]:
    sources = registry.setdefault("sources", [])
    assert isinstance(sources, list)
    draft_id = f"draft-{slug}"[:120]
    rec = {
        "id": draft_id,
        "type": source_type,
        "title": title,
        "telegram_chat_id": None,
        "session_id": None,
        "route_id": None,
        "enabled": False,
        "needs_review": True,
        "import_slug": slug,
        "report_visibility": {"local_chat": False, "control_chats": []},
        "local_commands": [],
        "allowed_requesters": [],
        "created_at": datetime.now(timezone.utc).date().isoformat(),
        "updated_at": datetime.now(timezone.utc).date().isoformat(),
    }
    if not any(isinstance(s, dict) and str(s.get("id")) == draft_id for s in sources):
        sources.append(rec)
    return rec


def ensure_source_from_cli(
    registry: dict[str, Any],
    *,
    source_id: str,
    source_type: str,
    title: str,
    telegram_chat_id: str | None,
    session_id: str | None,
    route_id: str | None,
) -> dict[str, Any]:
    sources = registry.setdefault("sources", [])
    assert isinstance(sources, list)
    for s in sources:
        if isinstance(s, dict) and str(s.get("id", "")).strip() == source_id:
            return s
    rec = {
        "id": source_id,
        "type": source_type,
        "title": title,
        "telegram_chat_id": telegram_chat_id,
        "session_id": session_id,
        "route_id": route_id,
        "enabled": True,
        "needs_review": False,
        "report_visibility": {"local_chat": True, "control_chats": []},
        "local_commands": [],
        "allowed_requesters": [],
        "created_at": datetime.now(timezone.utc).date().isoformat(),
        "updated_at": datetime.now(timezone.utc).date().isoformat(),
    }
    sources.append(rec)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Import Telegram Desktop HTML export into Studio JSONL.",
        epilog=(
            "Studio root must be the same tree Jarvis sees as /data/studio (bot workspace "
            "workspace-data/<bot_id>/studio on host). Do not point --studio-dir at memoh_memoh_studio "
            "unless you pass --allow-noncanonical-studio-dir and verified mounts."
        ),
    )
    ap.add_argument(
        "--dedupe-jsonl",
        metavar="FILE",
        help="Rewrite FILE: collapse semantic duplicate target_lead rows (backup .bak-*-before-dedupe); exit.",
    )
    ap.add_argument("--input", help="Path to messages.html (required unless --dedupe-jsonl)")
    ap.add_argument(
        "--studio-dir",
        help="Studio root (must match bot-visible /data/studio: stat_sources.json, events/)",
    )
    ap.add_argument("--source-type", default="leads")
    ap.add_argument("--source-id", default=None)
    ap.add_argument("--telegram-chat-id", default=None)
    ap.add_argument("--session-id", default=None)
    ap.add_argument("--route-id", default=None)
    ap.add_argument("--auto-register-draft", action="store_true")
    ap.add_argument(
        "--allow-noncanonical-studio-dir",
        action="store_true",
        help="Allow studio dir under memoh_memoh_studio Docker volume (discouraged; verify mounts).",
    )
    args = ap.parse_args()

    if args.dedupe_jsonl:
        p = Path(args.dedupe_jsonl).resolve()
        try:
            bak, before_tl, after_tl = dedupe_jsonl_file(p)
        except FileNotFoundError:
            print(f"ERROR: file not found: {p}", file=sys.stderr)
            return 2
        print(json.dumps({"backup": str(bak), "target_lead_before": before_tl, "target_lead_after": after_tl}, indent=2))
        return 0

    if not args.input:
        ap.error("--input is required unless --dedupe-jsonl is set")
    if not args.studio_dir:
        ap.error("--studio-dir is required unless --dedupe-jsonl is set")

    input_path = Path(args.input).resolve()
    studio = Path(args.studio_dir).resolve()
    v = validate_workspace_studio_dir(studio, allow_noncanonical=bool(args.allow_noncanonical_studio_dir))
    if v is not None:
        return v
    if not input_path.is_file():
        print(f"ERROR: input not found: {input_path}", file=sys.stderr)
        return 2

    raw_html = input_path.read_text(encoding="utf-8", errors="replace")
    if "history" not in raw_html or "message" not in raw_html:
        print("ERROR: file does not look like Telegram HTML export", file=sys.stderr)
        return 2

    chat_title = extract_chat_title(raw_html)
    slug = slugify(chat_title)

    stat_path = studio / "stat_sources.json"
    if not stat_path.exists():
        print(f"ERROR: stat_sources.json missing: {stat_path}", file=sys.stderr)
        return 2

    registry = json.loads(stat_path.read_text(encoding="utf-8"))
    source: dict[str, Any] | None = None

    if args.auto_register_draft:
        source = match_source(registry, source_id=None, title=chat_title, source_type=args.source_type)
        if source is None:
            backup_file(stat_path)
            source = append_draft_source(registry, title=chat_title, source_type=args.source_type, slug=slug)
            stat_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        sid = (args.source_id or "").strip() or None
        if sid:
            source = match_source(registry, source_id=sid, title=chat_title, source_type=args.source_type)
            if source is None:
                backup_file(stat_path)
                source = ensure_source_from_cli(
                    registry,
                    source_id=sid,
                    source_type=args.source_type,
                    title=chat_title,
                    telegram_chat_id=args.telegram_chat_id,
                    session_id=args.session_id,
                    route_id=args.route_id,
                )
                stat_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        else:
            source = match_source(registry, source_id=None, title=chat_title, source_type=args.source_type)
            if source is None:
                backup_file(stat_path)
                source = append_draft_source(registry, title=chat_title, source_type=args.source_type, slug=slug)
                stat_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    assert source is not None
    source_id = str(source.get("id", "")).strip()
    telegram_chat_id = str(source.get("telegram_chat_id") or args.telegram_chat_id or "").strip() or None
    session_id = str(source.get("session_id") or args.session_id or "").strip() or None
    route_id = str(source.get("route_id") or args.route_id or "").strip() or None

    import_root = studio / "imports" / "telegram" / slug
    import_root.mkdir(parents=True, exist_ok=True)
    norm_path = import_root / "messages.normalized.jsonl"

    last_author: str | None = None
    normalized_rows: list[dict[str, Any]] = []
    target_events: list[dict[str, Any]] = []
    summary_events: list[dict[str, Any]] = []
    op_events: list[dict[str, Any]] = []

    for mid, classes, block in iter_message_blocks(raw_html):
        is_service = "service" in classes.casefold()
        is_joined = "joined" in classes.casefold()
        dt = parse_dt_from_block(block)
        if not dt:
            continue
        date_iso, time_hm = dt
        author = extract_from_name(block)
        if author:
            last_author = author
        elif is_joined and last_author:
            author = last_author
        else:
            author = author or "unknown"

        text_plain = extract_text_raw(block)
        numeric = numeric_id_from_attr(mid)
        norm = {
            "telegram_message_id": mid,
            "numeric_id": numeric,
            "date": date_iso,
            "time": time_hm,
            "author": author,
            "is_service": is_service,
            "text": text_plain,
        }
        normalized_rows.append(norm)

        if is_service:
            continue

        if is_summary_report(text_plain):
            summary_events.append(
                {
                    "event_id": f"telegram-message-{numeric}",
                    "event_type": "summary_report",
                    "source_id": source_id,
                    "source_type": args.source_type,
                    "telegram_chat_id": telegram_chat_id,
                    "session_id": session_id,
                    "route_id": route_id,
                    "date": date_iso,
                    "time": time_hm,
                    "author": author,
                    "raw_text": text_plain,
                    "import_source": "telegram_html_export",
                    "telegram_message_id": mid,
                    "needs_review": False,
                }
            )
            continue

        if is_operational_note(text_plain):
            op_events.append(
                {
                    "event_id": f"telegram-message-{numeric}",
                    "event_type": "operational_note",
                    "source_id": source_id,
                    "source_type": args.source_type,
                    "telegram_chat_id": telegram_chat_id,
                    "session_id": session_id,
                    "route_id": route_id,
                    "date": date_iso,
                    "time": time_hm,
                    "author": author,
                    "raw_text": text_plain,
                    "import_source": "telegram_html_export",
                    "telegram_message_id": mid,
                    "needs_review": True,
                }
            )
            continue

        if not is_target_lead_text(text_plain):
            continue

        fields = parse_lead_fields(text_plain)
        target_events.append(
            {
                "event_id": f"telegram-message-{numeric}",
                "event_type": "target_lead",
                "source_id": source_id,
                "source_type": args.source_type,
                "telegram_chat_id": telegram_chat_id,
                "session_id": session_id,
                "route_id": route_id,
                "date": date_iso,
                "time": time_hm,
                "author": author,
                "raw_text": text_plain,
                "phone": fields["phone"],
                "name": fields["name"],
                "city": fields["city"],
                "status": fields["status"],
                "call_when": fields["call_when"],
                "comment": fields["comment"],
                "import_source": "telegram_html_export",
                "telegram_message_id": mid,
                "needs_review": bool(fields["needs_review"]),
            }
        )

    norm_path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in normalized_rows) + "\n",
        encoding="utf-8",
    )

    all_out_events = target_events + summary_events + op_events
    by_day: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for ev in all_out_events:
        by_day[str(ev["date"])].append(ev)

    day_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"target_leads": 0, "summary_reports": 0, "operational_notes": 0})
    leads_backups: list[str] = []
    for day, evs in sorted(by_day.items()):
        for ev in evs:
            et = ev.get("event_type")
            if et == "target_lead":
                day_stats[day]["target_leads"] += 1
            elif et == "summary_report":
                day_stats[day]["summary_reports"] += 1
            elif et == "operational_note":
                day_stats[day]["operational_notes"] += 1

        out_path = studio / "events" / f"leads-{day}.jsonl"
        existing = load_jsonl_events_by_id(out_path)
        existing = dedupe_semantic_target_leads(existing)
        for ev in evs:
            existing[str(ev["event_id"])] = ev
        existing = dedupe_semantic_target_leads(existing)
        if out_path.exists():
            b = backup_file(out_path)
            if b:
                leads_backups.append(str(b))
        write_jsonl_merged(out_path, existing)

    summary = {
        "source_chat": chat_title,
        "source_id": source_id,
        "source_type": args.source_type,
        "imported_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "input_file": str(input_path),
        "normalized_messages": len(normalized_rows),
        "target_leads_total": len(target_events),
        "summary_reports_total": len(summary_events),
        "operational_notes_total": len(op_events),
        "days": {d: {"target_leads": day_stats[d]["target_leads"], "summary_reports": day_stats[d]["summary_reports"]} for d in sorted(day_stats)},
        "import_slug": slug,
        "normalized_path": str(norm_path),
        "warnings": [],
    }
    if not telegram_chat_id or not session_id:
        summary["warnings"].append("source missing telegram_chat_id or session_id; fill stat_sources.json for full reporting.")

    (import_root / "import-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
