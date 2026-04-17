"""
经验结晶引擎 — 把分散预测提炼为可复用的「晶体」

工作原理：
1. 扫描经验库所有已回传的记录
2. 用维度组合分桶（卦象 + 关键爻位区间）
3. 当某桶累积 ≥ N 场且命中率 ≥ X%，提炼为「晶体」
4. 晶体可应用于未来预测（加权 / 否决 / 增强）
5. 晶体可导出共享（共同进化）

晶体格式：
{
  "crystal_id": "xtl-abc123",
  "version": "v1",
  "trigger": {
    "hexagram": "履",
    "yang_count_min": 5,
    "yao_constraints": {"赔率": [0.55, 1.0]}
  },
  "outcome": "1x2=home",
  "stats": {
    "matches": 12,
    "hits": 10,
    "rate": 0.833,
    "confidence_interval": [0.65, 0.95]
  },
  "discovered_at": "2026-04-17T...",
  "discovered_by": "agent_id_or_user",
  "tags": ["football", "italian-serie-a"]
}
"""
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "experience.jsonl"
SEED = ROOT / "data" / "seed_experience.jsonl"
CRYSTALS_LOCAL = ROOT / "data" / "crystals_local.jsonl"
CRYSTALS_SHARED = ROOT / "data" / "crystals_shared.jsonl"


# 结晶阈值
MIN_SAMPLES = 3       # 至少 N 场才能结晶
MIN_HIT_RATE = 0.60   # 命中率 ≥ 60% 才算晶体
CONFIDENCE_Z = 1.96   # 95% 置信区间


def _load_records() -> list:
    records = []
    for path in [SEED, DB]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            records.append(json.loads(line))
                        except Exception:
                            pass
    return records


def _wilson_ci(hits: int, n: int, z: float = CONFIDENCE_Z):
    """Wilson 置信区间（小样本更准）"""
    if n == 0:
        return (0, 0)
    p = hits / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * ((p * (1 - p) + z**2 / (4 * n)) / n)**0.5 / denom
    return (max(0, center - spread), min(1, center + spread))


def crystallize(verbose=True) -> List[Dict]:
    """从历史回传记录中提炼晶体"""
    records = [r for r in _load_records()
               if (r.get("prediction_correct") or {}).get("1x2") is not None]

    if len(records) < MIN_SAMPLES:
        if verbose:
            print(f"  样本不足（{len(records)} < {MIN_SAMPLES}），无法结晶")
        return []

    # 按 (卦象, 阳爻数) 分桶
    buckets = defaultdict(list)
    for r in records:
        key = (r.get("hexagram_name"), r.get("yang_count"),
               r.get("predictions", {}).get("1x2"))
        buckets[key].append(r)

    crystals = []
    for (hex_name, yang, sel), group in buckets.items():
        if len(group) < MIN_SAMPLES:
            continue
        hits = sum(1 for r in group if r["prediction_correct"]["1x2"])
        rate = hits / len(group)
        if rate < MIN_HIT_RATE:
            continue

        ci_lo, ci_hi = _wilson_ci(hits, len(group))

        crystal = {
            "crystal_id": f"xtl-{hashlib.md5(f'{hex_name}{yang}{sel}'.encode()).hexdigest()[:8]}",
            "version": "v1",
            "trigger": {
                "hexagram": hex_name,
                "yang_count": yang,
            },
            "outcome": f"1x2={sel}",
            "stats": {
                "matches": len(group),
                "hits": hits,
                "rate": round(rate, 3),
                "ci_95": [round(ci_lo, 3), round(ci_hi, 3)],
            },
            "discovered_at": datetime.now(timezone.utc).isoformat(),
            "tags": ["football"],
        }
        crystals.append(crystal)

    # 写入本地晶体库
    CRYSTALS_LOCAL.parent.mkdir(parents=True, exist_ok=True)
    with open(CRYSTALS_LOCAL, "w", encoding="utf-8") as f:
        for c in crystals:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    if verbose:
        print(f"  发现 {len(crystals)} 个晶体（已存入 data/crystals_local.jsonl）")
        for c in crystals[:5]:
            print(f"    [{c['crystal_id']}] {c['trigger']['hexagram']}卦 阳{c['trigger']['yang_count']}/6 → "
                  f"{c['outcome']}  命中率 {c['stats']['rate']*100:.0f}% "
                  f"({c['stats']['hits']}/{c['stats']['matches']})")

    return crystals


def load_crystals() -> List[Dict]:
    """加载所有晶体（本地 + 共享）"""
    crystals = []
    for path in [CRYSTALS_LOCAL, CRYSTALS_SHARED]:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            crystals.append(json.loads(line))
                        except Exception:
                            pass
    return crystals


def match_crystal(hex_result: Dict) -> Optional[Dict]:
    """检查推演结果是否触发某个晶体"""
    crystals = load_crystals()
    matched = []
    for c in crystals:
        t = c["trigger"]
        if t.get("hexagram") and t["hexagram"] != hex_result.get("hexagram_name"):
            continue
        if t.get("yang_count") is not None and t["yang_count"] != hex_result.get("yang_count"):
            continue
        matched.append(c)

    if not matched:
        return None
    # 返回命中率最高的
    return max(matched, key=lambda c: c["stats"]["rate"])
