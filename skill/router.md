# 任务路由规则

用户问题 → 任务类型 → Playbook 调用顺序

## 路由矩阵

| 用户问题特征 | 主要任务类型 | 主 Playbook | 辅助 Playbook | 输出模板 |
|------------|-------------|-----------|--------------|---------|
| 指标下降/上升/波动/异常 | 指标异动诊断 | data_analysis | business_analysis, product_ops_analysis | metric_diagnosis |
| 留存/激活/PMF/增长瓶颈 | PMF/增长诊断 | product_ops_analysis | data_analysis, business_analysis | pmf_growth_report |
| 商业模式/如何赚钱/UE/LTV/CAC | 商业模式评估 | business_analysis | product_ops_analysis | business_model_eval |
| 是否进入/是否做/战略选择 | 战略分析 | strategy_analysis | business_analysis, product_ops_analysis | strategy_memo |
| 市场规模/TAM/竞争格局 | 市场/战略分析 | strategy_analysis | business_analysis | strategy_memo |
| 流程低效/协同问题/组织治理 | 流程优化 | process_analysis | data_analysis | process_diagnosis |
| 财报/现金流/利润/风险/排雷 | 财报分析 | finance_industry_analysis | business_analysis | finance_risk_report |
| 估值/是否值得投 | 投资分析 | finance_industry_analysis, scenario_sensitivity_analysis | strategy_analysis | finance_risk_report + scenario_analysis_report |
| 行业对标/行业特性 | 行业分析 | finance_industry_analysis, competitive_analysis | strategy_analysis | competitive_analysis_report |
| 对比/和XX比/谁更强/对标 | 竞争对手对比 | competitive_analysis | business_analysis, finance_industry_analysis | competitive_analysis_report |
| 未来预测/估值/情景/如果XX | 情景/敏感性分析 | scenario_sensitivity_analysis | finance_industry_analysis, strategy_analysis | scenario_analysis_report |
| 通用决策/多方案对比 | 决策支持 | 视具体问题 | 多 playbook 组合 | decision_memo |

## 混合型问题处理

当用户问题跨多个领域时，按以下优先级组合：

### 增长类混合问题
**例**："我们用户增长了但利润没增长，怎么办？"
→ 主：product_ops_analysis（增长诊断）
→ 辅：business_analysis（单位经济）+ finance_industry_analysis（利润结构）
→ 输出：pmf_growth_report + business_model_eval 组合

### 战略类混合问题
**例**："我们要不要进入海外市场？"
→ 主：strategy_analysis（市场选择）
→ 辅：business_analysis（商业模式适配性）+ finance_industry_analysis（财务可行性）
→ 输出：strategy_memo + decision_memo

### 产品类混合问题
**例**："我们产品做 B 端还是 C 端？"
→ 主：product_ops_analysis（产品定位）
→ 辅：strategy_analysis（市场选择）+ business_analysis（商业模式）
→ 输出：strategy_memo + pmf_growth_report

### 投资类混合问题
**例**："这家公司值不值得投？"
→ 主：finance_industry_analysis（财务质量）+ scenario_sensitivity_analysis（情景分析）
→ 辅：competitive_analysis（竞争优势对比）+ strategy_analysis（护城河判断）
→ 输出：finance_risk_report + scenario_analysis_report + competitive_analysis_report

### 竞争类混合问题
**例**："我们和竞品差距在哪？怎么追？"
→ 主：competitive_analysis（竞争对手对比）
→ 辅：product_ops_analysis（产品差距）+ business_analysis（商业模式差异）
→ 输出：competitive_analysis_report + strategy_memo

## 关键词识别规则

### 触发「指标异动诊断」
关键词：下降、下滑、上升、波动、异常、突然、不正常

### 触发「PMF/增长诊断」
关键词：PMF、留存、激活、增长、获客、转化、漏斗、病毒、NSM

### 触发「商业模式评估」
关键词：商业模式、赚钱、变现、单位经济、UE、LTV、CAC、回本、盈利

### 触发「战略分析」
关键词：战略、要不要做、是否进入、方向、选择、优先级、赛道、TAM

### 触发「流程分析」
关键词：流程、协同、效率、SOP、瓶颈、返工、治理、组织

### 触发「财报分析」
关键词：财报、年报、现金流、利润、资产、负债、ROE、毛利、估值、造假、排雷

### 触发「竞争对手对比」
关键词：对比、和XX比、谁更强、对标、同行、竞品、竞争对手、行业对比、差距、领先、落后

### 触发「情景/敏感性分析」
关键词：未来预测、估值、情景、如果XX会怎样、最好情况、最坏情况、Bull、Bear、敏感、假设变化、稳健性

## 问题类型不明确时

如果无法从用户问题中明确识别任务类型，优先：
1. 反问用户，澄清目标
2. 列出 2-3 种可能的分析方向
3. 让用户选择或提供更多信息

**不要**猜测后直接给一个可能错误的分析框架。
