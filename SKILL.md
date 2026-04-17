# 诸葛亮 · AI 推演军师 (zhuge-skill) v0.1.1

> 五数据源融合 · 六十四卦决策 · 经验自学习 · 共同进化

## 你能让我做什么

我是一个能分析数据 + 推演决策 + 持续自学习的 AI 助手。当前主要场景是**足球比赛预测**，但底层是通用的 64 卦推演引擎，可扩展到任何决策场景。

### 核心能力

| 能力 | 命令 | 说明 |
|------|------|------|
| 单场预测 | `python start.py predict "Napoli vs Lazio"` | 拉数据 → 6 维爻位 → 卦象 → 决策 |
| 批量预测 | `python scripts/batch.py "A vs B" "C vs D"` | 一次跑多场 |
| 结果回传 | `python scripts/backfill.py` | 比赛后回填实际结果，更新命中率 |
| 命中率统计 | `python scripts/stats.py` | 看历史表现 |
| **经验结晶** | `python scripts/crystallize.py` | 提炼成功模式为「晶体」 |
| **共同进化** | `python scripts/sync.py auto` | 推/拉晶体到共享池，与其他 Agent 共享 |
| 权重校准 | `python scripts/calibrate.py` | 用回传数据自动调爻位权重 |
| 战报 | `python scripts/report.py --llm` | LLM 写古风周报/月报 |
| 守护模式 | `python scripts/backfill.py --loop 30` | 每 30 分钟自动回传 |

### 调用示例

**给 Agent 的提示词：**
> "用诸葛亮 skill 预测明天的 Napoli vs Lazio"

Agent 应该调用：
```bash
python start.py predict "Napoli vs Lazio" --league serie-a
```

**输出要点：**
- 6 维爻位评分（攻防/士气/伤停/主客场/交锋/赔率）
- 卦象（64 卦之一）+ 阳爻数
- 孔明评语（可选 LLM 增强）
- 推荐：1X2 + 大小球
- **晶体匹配**：如果触发历史晶体，显示历史命中率

### 自学习闭环

```
预测 → 写经验库 → 等结果 → backfill 回传 → stats 看准确率
                                            ↓
共同进化 ← sync 推/拉晶体  ←  crystallize 结晶  ← calibrate 校准权重
```

### 文件结构

- `start.py` — 一键入口（带欢迎动画 + wizard）
- `core/` — 核心算法（卦象/爻位/LLM 适配/孔明/结晶）
- `adapters/` — 数据源（API-Football/The Odds API/Understat）
- `scripts/` — 入口脚本
- `data/` — 64 卦表 + 种子经验库 + 晶体池
- `.env.example` — 配置模板（12 个 LLM 供应商 + 3 个数据源）

### 兼容性

✓ Hermes Agent / OpenClaw / Claude Code / Cursor / 任何 Python 环境
✓ 12 LLM 供应商（豆包/Kimi/通义/智谱/Yi/百川/MiniMax/DeepSeek/OpenAI/Claude/Gemini/中转）
✓ 三种配置方式：.env / 环境变量 / 命令行参数
✓ 网络降级：任何外部 API 失败都不阻塞核心流程
