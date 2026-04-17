# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/) 精神 + [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### Added
- `scripts/error_log.py` — 轻量 JSONL 错误日志（含 `--resolve` CLI + priority/status 字段），接入 `backfill` 守护循环、`fetch_actual_result`、`core/llm.py` 三个 except 点
- 晶体 schema v2：新增 `first_seen` / `last_seen` / `recurrence_count` 字段；`match_crystal` 命中时回写 `crystals_local.jsonl`（实战复用次数可观测）
- `scripts/predict.py` 预测输出显示晶体被复用次数 + 首见年龄（高复用标 ⭐）
- `scripts/crystallize.py --dry-run` 预览结晶结果不写入
- `scripts/stats.py --crystals` 晶体排行 + stale 监控
- `scripts/stats.py --errors` 最近错误摘要
- README.md §全平台兼容 扩展为每宿主（Claude Code / Cursor / OpenClaw / Hermes / 纯 Python）可复制的接入片段

### Changed
- 内部：`crystallize(verbose, write=True)` 新增 `write` 参数支持 dry-run
- 内部：`match_crystal()` 返回带更新后 counters 的副本（调用方能拿到最新 recurrence_count）

### Notes
- 本节包含 v1.0.3 之后、下一次发版（v1.0.4）之前的所有改动
- 改动均向后兼容：旧的 v1 晶体无 new 字段时 load 正常；error_log 老条目无 priority/status 时 summary 显示 `?`

---

## [v1.0.3] — 2026-04-17 · 视觉素材升级

- 新增 `assets/demo.png` — 诸葛亮推演引擎实录截图（启动动画 + 6 维爻位实时评分）
- README 顶部嵌入演示截图，一眼看清 skill 的"一句话预测闭环"
- 无代码变更

## [v1.0.2] — 2026-04-17 · 文档一致性修正

- 修复 SKILL.md 与 PRIVACY.md 自相矛盾点：原 §晶体共享 节仍沿用 v1.0.0 "有上传功能、默认关闭"的旧描述，与 v1.0.1 的代码事实（`push` 已移除）不一致，已重写为 §晶体拉取 与本地导出，对齐代码
- 数据流向表：`sync.py` 改为 `pull`（只 GET），`share.py` 标为纯本地导出
- 自学习闭环图修正：`sync 推/拉` → `sync 拉公共晶体（只入）`
- 审计 grep 命令扩展到 4 条，加入"全仓库扫上传端点"一项
- 代码层面零变更，仅文档修正

## [v1.0.1] — 2026-04-17 · 透明度升级

- 新增 §环境变量清单（12 个 LLM + 2 个数据源，每个用途 / 获取地址 / 降级行为说明）
- 新增 §安全与隐私（数据流向表 + 每个脚本是否向外发数据）
- 明确 LLM 中转风险（relay 模式数据流向第三方）
- **架构级隐私合约**：`sync.py` 的 `push` 函数从代码中移除，固化为单向消费架构（只 pull 不 push）
- `sync.py` 子命令简化为 `pull`（从公开 URL 只读拉取）和 `status`（本地查看）
- `share.py` 明确为本地导出工具（生成 `exports/*.md|json`），不联网
- 新增 [PRIVACY.md](./PRIVACY.md)：详细列出网络调用清单、作者数据可见度矩阵、fork 者脱敏白名单
- 新增 §如何审计（4 行 grep 命令自查）

## [v1.0.0] — 2026-04-17 · Initial release on ClawHub

- 5-source data fusion + 64-hexagram reasoning + experience crystallization
- 12+ LLM provider support
- Guardian mode + crystal pool (pull-only from v1.0.1)

---

*SKILL.md 的 "## 更新日志" 一节将在下一次发版时裁剪为只保留最新 2 个版本，其余迁移到本文件。*
