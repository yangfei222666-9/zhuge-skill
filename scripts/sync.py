"""
共同进化 — 晶体共享同步

工作模式：
1. 上传：把本地结晶的「高命中晶体」匿名上传到共享池（GitHub Release / 本地共享文件）
2. 下载：从共享池拉别人贡献的晶体
3. 合并：本地晶体 + 共享晶体 → 形成集体智能

支持两种共享池：
- 本地文件：~/.zhuge_skill/shared/crystals.jsonl（多 Agent 共享同一台机器）
- GitHub Release：通过 URL 拉远程晶体（默认开启）

用法：
    python scripts/sync.py pull               # 拉远程晶体
    python scripts/sync.py push               # 推本地晶体到本地共享文件
    python scripts/sync.py status             # 查看晶体池状态
"""
import sys
import json
import os
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.crystallizer import (CRYSTALS_LOCAL, CRYSTALS_SHARED, load_crystals,
                                crystallize)
from core.welcome import (NEON_CYAN, NEON_GREEN, NEON_YELLOW, GOLD,
                          DIM, BOLD, RESET, HOT_RED as RED)

# 共享池位置
SHARED_HUB = Path.home() / ".zhuge_skill" / "shared" / "crystals.jsonl"
REMOTE_URL = os.getenv("ZHUGE_REMOTE_CRYSTAL_URL",
    "https://raw.githubusercontent.com/taijios9/zhuge-crystals/main/crystals.jsonl")


def status():
    local = load_crystals()
    shared_hub_count = 0
    if SHARED_HUB.exists():
        with open(SHARED_HUB, encoding="utf-8") as f:
            shared_hub_count = sum(1 for line in f if line.strip())

    print(f"\n  {NEON_CYAN}╔═══ 晶体池状态 {' ' * 30}═══╗{RESET}")
    print(f"  {NEON_CYAN}║{RESET}")
    print(f"  {NEON_CYAN}║{RESET}  本地晶体: {GOLD}{len(local)}{RESET} 个")
    print(f"  {NEON_CYAN}║{RESET}  共享池:   {GOLD}{shared_hub_count}{RESET} 个 ({SHARED_HUB})")
    print(f"  {NEON_CYAN}║{RESET}  远程地址: {DIM}{REMOTE_URL}{RESET}")
    print(f"  {NEON_CYAN}║{RESET}")

    if local:
        print(f"  {NEON_CYAN}║{RESET}  {BOLD}本地晶体一览（按命中率）{RESET}")
        sorted_crystals = sorted(local, key=lambda c: -c['stats']['rate'])
        for c in sorted_crystals[:10]:
            t = c['trigger']
            s = c['stats']
            print(f"  {NEON_CYAN}║{RESET}    {GOLD}[{c['crystal_id']}]{RESET} "
                  f"{t.get('hexagram','?')}卦 阳{t.get('yang_count','?')}/6 → "
                  f"{c['outcome']}  {NEON_GREEN}{s['rate']*100:.0f}%{RESET} ({s['hits']}/{s['matches']})")
    print(f"  {NEON_CYAN}╚{'═' * 50}╝{RESET}\n")


def push():
    """把本地晶体推到共享池"""
    local = []
    if CRYSTALS_LOCAL.exists():
        with open(CRYSTALS_LOCAL, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        local.append(json.loads(line))
                    except Exception:
                        pass

    if not local:
        print(f"\n  {NEON_YELLOW}没有本地晶体可推送。先跑：python scripts/crystallize.py{RESET}\n")
        return

    SHARED_HUB.parent.mkdir(parents=True, exist_ok=True)
    # 合并：去重（按 crystal_id）
    existing_ids = set()
    if SHARED_HUB.exists():
        with open(SHARED_HUB, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        existing_ids.add(json.loads(line)["crystal_id"])
                    except Exception:
                        pass

    new_count = 0
    with open(SHARED_HUB, "a", encoding="utf-8") as f:
        for c in local:
            if c["crystal_id"] not in existing_ids:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
                new_count += 1

    print(f"\n  {NEON_GREEN}✓{RESET} 推送完成: 本地晶体 {len(local)} 个 → 共享池新增 {new_count} 个")
    print(f"  {DIM}位置: {SHARED_HUB}{RESET}\n")


def pull():
    """从远程拉晶体"""
    try:
        import requests
    except ImportError:
        print(f"\n  {RED}需要 requests，pip install requests{RESET}\n")
        return

    print(f"\n  从远程拉取: {DIM}{REMOTE_URL}{RESET}")
    try:
        r = requests.get(REMOTE_URL, timeout=10)
        if not r.ok:
            print(f"  {RED}拉取失败 (HTTP {r.status_code}){RESET}")
            print(f"  {DIM}（可能仓库还没建。你也可以手动维护 data/crystals_shared.jsonl）{RESET}\n")
            return
        new_crystals = []
        for line in r.text.splitlines():
            if line.strip():
                try:
                    new_crystals.append(json.loads(line))
                except Exception:
                    pass

        existing_ids = set()
        if CRYSTALS_SHARED.exists():
            with open(CRYSTALS_SHARED, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            existing_ids.add(json.loads(line)["crystal_id"])
                        except Exception:
                            pass

        CRYSTALS_SHARED.parent.mkdir(parents=True, exist_ok=True)
        added = 0
        with open(CRYSTALS_SHARED, "a", encoding="utf-8") as f:
            for c in new_crystals:
                if c.get("crystal_id") and c["crystal_id"] not in existing_ids:
                    f.write(json.dumps(c, ensure_ascii=False) + "\n")
                    added += 1

        print(f"  {NEON_GREEN}✓{RESET} 拉取完成: 远程 {len(new_crystals)} 个 → 本地新增 {added} 个\n")
    except Exception as e:
        print(f"  {RED}拉取出错: {e}{RESET}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["status", "push", "pull", "auto"],
                   help="status/push/pull/auto(=push+pull)")
    args = p.parse_args()

    if args.action == "status":
        status()
    elif args.action == "push":
        push()
    elif args.action == "pull":
        pull()
    elif args.action == "auto":
        # 完整闭环：先结晶，再推，再拉
        print(f"\n  [1/3] 结晶本地经验...")
        crystallize()
        print(f"\n  [2/3] 推送到共享池...")
        push()
        print(f"  [3/3] 拉取远程晶体...")
        pull()
        status()


if __name__ == "__main__":
    main()
