---
name: senior_analyst
description: 商业分析专家 — 财报分析、竞争对比、行业建模、战略评估。支持定量分析、快速模式、行业深度、引导式上手。
---

# Senior Analyst — 商业分析专家（Codex 版）

## 版本检测（自动触发）

每次加载本 skill 时，执行以下命令自动检测版本：

```bash
_UC=""
if [ -x "$HOME/.local/bin/senior_analyst-update-check" ]; then
    _UC=$("$HOME/.local/bin/senior_analyst-update-check" 2>/dev/null || true)
elif [ -x "$HOME/ai-project/senior-analyst/bin/senior_analyst-update-check" ]; then
    _UC=$("$HOME/ai-project/senior-analyst/bin/senior_analyst-update-check" 2>/dev/null || true)
fi
[ -n "$_UC" ] && echo "$_UC" || true
```

**输出的语义**：
- `UPGRADE_AVAILABLE <old> <new>` → 告知用户："senior_analyst 有新版本可用：v{old} → v{new}。运行 `/senior_analyst --upgrade` 进行升级。"
- `JUST_UPGRADED <old> <new>` → 显示 "Running senior_analyst v{new} (just updated from v{old})!" 并继续当前任务
- 空 → 继续当前任务

结构化商业与财务分析工具，整合 9 个数据源（FMP、Alpha Vantage、NewsAPI、FRED、World Bank、stats_gov_cn、CoinGecko、yfinance、akshare），提供财报分析、竞争对比、行业建模、宏观研究、情景推演等能力。

## 使用方式

本 skill 支持多种分析模式，通过自然语言触发：

- **默认模式（定量分析）**：完整的 6 步工作流，包含 Red Team 审查。适合深度分析、投资尽调、战略评估。
  - 触发：直接描述分析任务，例如"分析滴滴的财务状况"、"对比美团和饿了么"
  
- **快速模式**：3 步快速通道，跳过 Red Team，适合时间紧迫的初步判断。
  - 触发：明确说"快速分析"、"快速看一下"、"简要评估"
  
- **行业建模**：针对特定行业的深度研究，包含行业结构、竞争格局、关键驱动因素。
  - 触发：说"行业分析"、"行业研究"、"行业建模"，并指定行业
  
- **引导式上手**：首次使用的交互式引导，帮助理解工具能力和最佳实践。
  - 触发：说"我是第一次用"、"怎么开始"、"引导我"

详细工作流程和原则请参考对应的 references 文档。

## 版本查询

当前版本：请查看 VERSION 文件（安装目录下）。

如需查询版本，可以问"senior_analyst 是什么版本"或"当前版本号"。
