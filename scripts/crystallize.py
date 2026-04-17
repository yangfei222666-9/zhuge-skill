"""
经验结晶 — 入口脚本

调用 core/crystallizer.py 把历史回传记录提炼成晶体。

用法:
    python scripts/crystallize.py            # 结晶
    python scripts/crystallize.py --share    # 结晶 + 推到共享池
"""
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.crystallizer import crystallize
from core.welcome import NEON_CYAN, NEON_GREEN, GOLD, DIM, BOLD, RESET


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--share", action="store_true",
                   help="结晶后立即推到共享池")
    args = p.parse_args()

    print(f"\n  {NEON_CYAN}╔═══ 经验结晶引擎 启动 {' ' * 22}═══╗{RESET}")
    print(f"  {NEON_CYAN}║{RESET}")
    crystals = crystallize(verbose=True)
    print(f"  {NEON_CYAN}╚{'═' * 50}╝{RESET}\n")

    if args.share and crystals:
        from scripts.sync import push
        push()


if __name__ == "__main__":
    main()
