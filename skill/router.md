# 任务路由规则

用户问题 → 深度级别 + 任务类型 → 数据策略 + Playbook 调用顺序

## 第一步：深度级别判断

在判断任务类型之前，先判断用户意图的深度级别。深度级别决定数据采集策略和输出模板。

### 意图信号识别

| 意图信号 | 深度级别 | 说明 |
|---------|---------|------|
| "入门""框架""怎么分析""什么指标""基础""概念""ABC""扫盲""概述" | **L1 框架速览** | 用户要的是理解框架和概念，不需要具体公司数据 |
| "分析XX公司""对比A和B""看看XX的财报""XX怎么样" | **L2 定量分析** | 用户要的是具体数据支撑的分析 |
| "深度报告""尽调""全面分析""完整分析""深度研究" | **L3 深度报告** | 用户要的是全流程深度分析 |
| 无明确深度信号 | **默认 L1** | 先给框架，再追问是否需要深入 |

### L3 触发信号拓宽

以下任务类型即使没有"深度""尽调"等显式信号，也**默认倾向 L3**（因为结论高度依赖假设，Council 多视角价值大）：

| 任务类型 | 关键词示例 | 倾向 L3 的原因 |
|---------|-----------|---------------|
| 行业商业建模 | "行业分析""商业模式拆解""行业研究" | 系统性判断，假设依赖度高 |
| 商业模式评估 | "商业模式""单位经济""盈利模式""规模效应" | 叙事自洽风险高，需要证伪 |
| 战略选择 | "要不要进入""战略选择""方向""资源配置" | 决策影响大，Red Team 必须深度 |
| 投资判断 | "估值""值不值得投""投资分析" | 逆向思维对投资不可或缺 |
| 竞争对手对比 | "对比""和XX比""竞品分析""商业模式差异" | 容易锚定单一视角 |

**操作**：当识别到以上任务类型时，主动向用户确认深度：

> "这个问题涉及 [行业建模/商业模式评估/战略选择]，建议用深度分析模式（L3），会包含完整的对抗性审查和多视角分析。可以吗？"
> A) L3 深度分析（推荐）
> B) L2 定量分析（更快，轻量审查）

### 深度级别对应策略

| 级别 | 数据采集 | 输出模板 | MCP 查询 | Council 模式 | 预期响应时间 |
|-----|---------|---------|---------|------------|------------|
| L1 | 跳过，直接用 knowledge 库 | quick_card 模板 | 不触发 | 不触发 | <5 秒 |
| L2 | 按需查询必查项 | 标准模板 | 必查项并行，选查按需 | 轻量 Council（5 项审查 + 1-2 Bull/Bear） | 10-20 秒 |
| L3 | 完整执行 mcp_queries.md | 完整报告模板 | 全流程按序/并行 | 完整 Council（7 类谬误 + 全覆盖 Bull/Bear + Chairman） | 30-60 秒 |

### 深度提升追问

L1 输出后，主动追问是否深入：

```
"需要深入某个方向吗？"
A) 用实时数据分析某家具体公司（→ 升级到 L2）
B) 深入某个子话题（→ L2 定向分析）
C) 完整行业深度报告（→ 升级到 L3）
D) 够了，不需要深入
```

## 第二步：任务类型路由

### 路由矩阵

| 用户问题特征 | 主要任务类型 | 主 Playbook | 辅助 Playbook | L1 快速模板 | L2/L3 标准模板 | L3 倾向 |
|------------|-------------|-----------|--------------|------------|--------------|--------|
| 指标下降/上升/波动/异常 | 指标异动诊断 | data_analysis | business_analysis, product_ops_analysis | framework_quick_card | metric_diagnosis | — |
| 留存/激活/PMF/增长瓶颈 | PMF/增长诊断 | product_ops_analysis | data_analysis, business_analysis | framework_quick_card | pmf_growth_report | — |
| 商业模式/如何赚钱/UE/LTV/CAC | 商业模式评估 | business_analysis | product_ops_analysis | framework_quick_card | business_model_eval | ★ 推荐 L3 |
| 是否进入/是否做/战略选择 | 战略分析 | strategy_analysis | business_analysis, product_ops_analysis | framework_quick_card | strategy_memo | ★ 推荐 L3 |
| 市场规模/TAM/竞争格局 | 市场/战略分析 | strategy_analysis | business_analysis | framework_quick_card | strategy_memo | ★ 推荐 L3 |
| 流程低效/协同问题/组织治理 | 流程优化 | process_analysis | data_analysis | framework_quick_card | process_diagnosis | — |
| 财报/现金流/利润/风险/排雷 | 财报分析 | finance_industry_analysis | business_analysis | framework_quick_card | finance_risk_report | — |
| 估值/值多少钱/贵不贵/内在价值 | 估值分析 | valuation | finance_industry_analysis, scenario_sensitivity_analysis, competitive_analysis | framework_quick_card | valuation_report | ★ 推荐 L3 |
| 估值/是否值得投 | 投资分析 | finance_industry_analysis, scenario_sensitivity_analysis | strategy_analysis | framework_quick_card | finance_risk_report + scenario_analysis_report | ★ 推荐 L3 |
| 行业对标/行业特性 | 行业分析 | finance_industry_analysis, competitive_analysis | strategy_analysis | framework_quick_card | competitive_analysis_report | ★ 推荐 L3 |
| 对比/和XX比/谁更强/对标 | 竞争对手对比 | competitive_analysis | business_analysis, finance_industry_analysis | framework_quick_card | competitive_analysis_report | ★ 推荐 L3 |
| 未来预测/估值/情景/如果XX | 情景/敏感性分析 | scenario_sensitivity_analysis | finance_industry_analysis, strategy_analysis | framework_quick_card | scenario_analysis_report | ★ 推荐 L3 |
| 行业建模/行业分析/金融/物流/游戏/广告/消费电子/尽调 | 行业商业建模 | industry_modeling | 视行业选辅助 playbook | industry_quick_card | industry_modeling_report | ★ 推荐 L3 |
| 通用决策/多方案对比 | 决策支持 | 视具体问题 | 多 playbook 组合 | framework_quick_card | decision_memo | — |

★ 标记的任务类型：即使无"深度""尽调"等显式信号，也默认推荐 L3（Council 多视角价值大），在 Step 1 主动向用户确认深度。

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

### 行业+战略选择
**例**："这家保险公司要不要进入健康险赛道？"
→ 主：industry_modeling（行业建模）
→ 辅：strategy_analysis（战略选择）
→ 输出：industry_modeling_report + strategy_memo

### 行业+竞争对手对比
**例**："顺丰和中通的商业模式差异在哪？"
→ 主：industry_modeling（行业建模）
→ 辅：competitive_analysis（竞争对手对比）
→ 输出：industry_modeling_report + competitive_analysis_report

### 行业+投资判断
**例**："这家游戏公司值不值得投？"
→ 主：industry_modeling（行业建模）
→ 辅：finance_industry_analysis + scenario_sensitivity_analysis
→ 输出：industry_modeling_report + scenario_analysis_report

### 行业+财报分析
**例**："这家银行的财报有没有问题？"
→ 主：industry_modeling（行业建模）
→ 辅：finance_industry_analysis（财报分析）
→ 输出：industry_modeling_report + finance_risk_report

## 关键词识别规则

### 深度级别识别（优先于任务类型识别）

#### 触发 L1（框架速览）
关键词：入门、框架、怎么分析、什么指标、基础、概念、ABC、扫盲、概述、介绍、指南、方法论、思路、如何看、怎么看、从哪入手、核心指标、关键指标

上下文信号：
- 问题中无具体公司名/股票代码
- 问题形式为"XX行业怎么分析"而非"XX公司怎么样"
- 用户使用泛指而非特指（"即时零售行业" vs "叮咚买菜"）

#### 触发 L2（定量分析）
关键词：分析XX公司、对比A和B、看看XX的财报、XX怎么样、XX数据、查一下XX

上下文信号：
- 问题中包含具体公司名或股票代码
- 要求对比两家以上公司
- 询问特定财务数据或经营数据

#### 触发 L3（深度报告）
关键词：深度报告、尽调、全面分析、完整分析、深度研究、投资分析、综合评估

上下文信号：
- 明确要求全面/深度/完整
- 投资决策场景
- 尽调场景

#### 默认规则
- 无法判断深度时，默认 L1
- L1 输出后主动追问是否升级

### 任务类型识别

#### 触发「指标异动诊断」
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

### 触发「估值分析」
关键词：估值、值多少钱、贵不贵、内在价值、DCF、折现、自由现金流、WACC、可比公司、倍数、PE估值、安全边际、折价、溢价

### 触发「行业商业建模」
关键词：行业建模、行业分析、商业模式拆解、行业研究、行业模板、
      金融、银行、保险、信贷、消费金融、助贷、风控、牌照、
      物流、快递、供应链、仓配、货运、冷链、
      游戏、手游、端游、IAP、IAA、买量、游戏运营、
      广告、流量变现、程序化、ADX、DSP、广告主、加载率、
      消费电子、手机、耳机、智能家居、硬件、品牌、渠道、
      尽调、投资判断、投资决策

## 问题类型不明确时

如果无法从用户问题中明确识别任务类型，优先：
1. 反问用户，澄清目标
2. 列出 2-3 种可能的分析方向
3. 让用户选择或提供更多信息

**不要**猜测后直接给一个可能错误的分析框架。
