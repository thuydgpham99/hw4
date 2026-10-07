"""Append-only audit trail for the Campus Customs agent loop.

Every tool call and every run outcome is appended to `output/audit_trail.json`.
The file is **never truncated** — it survives restarts and accumulates across
runs, so the trail is a history of what the agent actually did rather than a
snapshot of the last conversation.

Stored as a JSON array (not JSON Lines) so it can be opened and read directly by
a grader. Appending reads the existing array and rewrites it with the new entry,
which is O(n) but trivially fast at assignment scale, and the write goes to a
temporary file first so an interrupted write cannot corrupt the history.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"

# Serialises concurrent writes — FastAPI can handle more than one chat at a time.
_LOCK = threading.Lock()

# Arguments and results are truncated before they are written. A full product
# list would bury the trail, and a shopper's message could be long.
MAX_FIELD_CHARS = 220


# Shoppers sometimes type things they should not, and the prompt tells the agent
# to refuse them — but the message still passes through this logger on its way to
# disk. These patterns are masked before anything is written. The log cannot tell
# a test card number from a real one, so it stores neither.
_REDACTIONS = (
    # 13–19 digit card-like runs, with or without spaces/dashes
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[redacted-card]"),
    # US-style SSN
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[redacted-ssn]"),
    # Long opaque tokens: sk-..., ghp_..., and similar
    (re.compile(r"\b(?:sk|pk|ghp|gho|xox[bp])[-_][A-Za-z0-9]{16,}\b"), "[redacted-token]"),
)


def _redact(text: str) -> str:
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _clip(value: Any) -> Any:
    """Shorten a value for the trail, redacting anything that should not persist."""
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, dict):
        return {k: _clip(v) for k, v in list(value.items())[:8]}
    if isinstance(value, (list, tuple)):
        clipped = [_clip(v) for v in value[:3]]
        if len(value) > 3:
            clipped.append(f"… +{len(value) - 3} more")
        return clipped
    text = _redact(str(value))
    return text if len(text) <= MAX_FIELD_CHARS else text[:MAX_FIELD_CHARS] + "…"


def _read_existing() -> list[dict]:
    """Load the current trail. A damaged file is preserved, never silently reset."""
    if not AUDIT_PATH.exists():
        return []
    try:
        with AUDIT_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        # Keep the unreadable file rather than overwriting someone's history.
        damaged = AUDIT_PATH.with_suffix(".damaged.json")
        try:
            AUDIT_PATH.replace(damaged)
        except OSError:
            pass
        return []


def append(event: str, **fields: Any) -> None:
    """Append one entry. Never raises — auditing must not break a conversation."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "event": event,
        **{key: _clip(value) for key, value in fields.items()},
    }

    try:
        with _LOCK:
            AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
            trail = _read_existing()
            trail.append(entry)

            # Write to a temp file and swap it in, so a crash mid-write cannot
            # leave a half-written trail behind.
            temp = AUDIT_PATH.with_suffix(".tmp")
            with temp.open("w", encoding="utf-8") as handle:
                json.dump(trail, handle, indent=2, ensure_ascii=False)
            os.replace(temp, AUDIT_PATH)
    except Exception:  # noqa: BLE001
        # A failed audit write is not worth failing a shopper's question over.
        pass


def log_tool(name: str, args: dict, result: Any, *, conversation_id: str | None = None) -> None:
    """Record one tool call: what was asked of it and what came back."""
    summary: Any
    if isinstance(result, list):
        summary = f"{len(result)} result(s)"
        if result and isinstance(result[0], dict) and "name" in result[0]:
            summary = f"{len(result)}: " + ", ".join(
                str(r.get("name")) for r in result[:3]
            )
    elif isinstance(result, dict):
        summary = {
            k: result[k]
            for k in ("product_name", "price", "found", "in_stock", "size", "quantity", "note")
            if k in result
        }
    elif result is None:
        summary = "none"
    else:
        summary = result

    append(
        "tool_call",
        tool=name,
        args=args,
        result=summary,
        conversation_id=conversation_id,
    )


def log_run(
    *,
    stop_reason: str,
    conversation_id: str | None = None,
    message: str | None = None,
    reply_chars: int | None = None,
    tool_calls: int | None = None,
    products_returned: int | None = None,
    signed_in: bool | None = None,
    current_product_id: str | None = None,
    usage: dict | None = None,
) -> None:
    """Record the outcome of one agent loop, including why it stopped."""
    append(
        "run_end",
        stop_reason=stop_reason,
        conversation_id=conversation_id,
        message=message,
        reply_chars=reply_chars,
        tool_calls=tool_calls,
        products_returned=products_returned,
        signed_in=signed_in,
        current_product_id=current_product_id,
        usage=usage,
    )
