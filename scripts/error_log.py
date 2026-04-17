"""
错误日志 — append-only JSONL

用法（from 其它脚本）：
    from scripts.error_log import log_error
    try:
        ...
    except Exception as e:
        log_error(category="fetch_data", exc=e, context={"match": match_name})
        raise  # 或继续降级流程

查看最近错误：
    python scripts/stats.py --errors
"""
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG_PATH = ROOT / "data" / "errors.jsonl"


def _new_id() -> str:
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = "".join(random.choice("0123456789ABCDEF") for _ in range(3))
    return f"ERR-{date}-{suffix}"


def log_error(category: str, exc: BaseException, context: dict | None = None) -> str:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "id": _new_id(),
        "logged": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "category": category,
        "exc_type": type(exc).__name__,
        "summary": str(exc)[:200],
        "context": context or {},
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry["id"]


def load_errors(limit: int = 10) -> list[dict]:
    if not LOG_PATH.exists():
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def summarize_recent(limit: int = 10) -> str:
    errors = load_errors(limit)
    if not errors:
        return "  暂无错误记录。\n"
    lines = [f"  最近 {len(errors)} 条错误（data/errors.jsonl）:\n"]
    for e in errors:
        ts = e.get("logged", "?")[:19]
        cat = e.get("category", "?")
        exc_type = e.get("exc_type", "?")
        summary = e.get("summary", "")[:100]
        ctx_brief = ""
        ctx = e.get("context") or {}
        if ctx:
            ctx_brief = " " + " ".join(f"{k}={v}" for k, v in list(ctx.items())[:3])
        lines.append(f"  · [{e.get('id','?')}] {ts}  {cat}/{exc_type}{ctx_brief}")
        lines.append(f"    {summary}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    # CLI: print a recent summary, or add --demo for a self-test entry
    if "--demo" in sys.argv:
        try:
            raise RuntimeError("demo error — self-test")
        except Exception as e:
            eid = log_error("self_test", e, {"demo": True})
            print(f"logged {eid}")
    print(summarize_recent())
