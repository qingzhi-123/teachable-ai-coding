from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parent / "data"
LOG_FILE = DATA_DIR / "interactions.jsonl"


def append_interaction(record: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        **record,
    }
    with LOG_FILE.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_recent(limit: int = 100) -> list[dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
    recent = lines[-limit:]
    return [json.loads(line) for line in recent if line.strip()]


def read_session(session_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """读取同一会话最近若干轮对话，用作大模型上下文。"""

    if not LOG_FILE.exists():
        return []
    items = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("session_id") == session_id:
            items.append(record)
    return items[-limit:]
