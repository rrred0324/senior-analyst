# 行业商业建模 Playbook

> 触发条件：用户问题涉及特定行业深度建模（金融/物流/游戏/广告/消费电子/尽调等），或参数中包含行业关键词/--industry 标志

## 行业注册表

| 行业关键词 | 加载 knowledge 文件 | 特殊说明 |
|---|---|---|
| 金融/银行/保险/信贷/消费金融/助贷/风控/牌照 | industries/finance.md | 必须先看监管，再看利润 |
| 物流/快递/仓配/供应链/即时零售/货运/冷链 | industries/logistics.md | 需拆子赛道 |
| 游戏/手游/端游/IAP/IAA/买量/游戏运营 | industries/gaming.md | 生命周期是核心变量 |
| 广告/流量变现/程序化/ADX/DSP/广告主/加载率 | industries/internet_advertising.md | 流量-广告负载-ROI 三角 |
| 消费电子/手机/耳机/智能家居/硬件/品牌/渠道 | industries/consumer_electronics.md | 产品周期+渠道库存是风险核心 |
| 大模型/基础模型/LLM/Foundation Model/多模态/模型公司 | industries/ai_foundation_model.md | 模型能力vs商业化能力是核心矛盾 |
| AI应用/AI Agent/Copilot/AI办公/AI客服/AI编程/垂直Agent | industries/ai_application_agent.md | 留存和工作流嵌入是核心 |
| AI Infra/算力/GPU云/推理服务/MLOps/模型平台 | industries/ai_infra_compute.md | 利用率决定盈利能力 |
| 具身智能/人形机器人/机器人/RaaS/通用机器人 | industries/embodied_intelligence_robot.md | 场景ROI+单台economics是核心 |
| 工业智能/机器视觉/工业AI/质检/边缘智能/产线智能化 | industries/industrial_intelligence_vision.md | ROI导向+标准化是分水岭 |
| 智能汽车/自动驾驶/智驾/域控/车载算法/Robotaxi | industries/smart_vehicle_autonomous.md | 前装定点+SOP量产是关键拐点 |
| 半导体/芯片/EDA/Fabless/IDM/封测/设备材料 | industries/semiconductor.md | 良率+客户导入+周期性是核心 |
| 医疗科技/AI医疗/医疗器械/数字医疗/院内SaaS | industries/medtech_ai_healthcare.md | 监管准入+付费链条是关键 |
| 尽调/投资判断/投资决策 | investment_due_diligence.md | 投资尽调流程 |
| 不在上述注册表中的行业 | industry_methodology.md | 用十步法从零建模 |

## 分析流程

### Step 0: 行业识别与知识加载

1. 从用户问题中识别目标行业
2. 查行业注册表，确定加载哪个 knowledge 文件
3. 若命中行业注册表 → 加载对应 industries/xxx.md
4. 若未命中 → 加载 industry_methodology.md，使用十步法
5. 若涉及投资尽调 → 额外加载 investment_due_diligence.md

**同时加载**：business_modeling_overview.md（商业建模五层结构，作为顶层框架）

### Step 1: 行业认知建立

按行业 knowledge 文件的结构建立认知：

```
行业本质（这个行业的赚钱逻辑）
  → 价值链（上中下游流转）
    → 商业模式分类（子行业/子赛道拆分）
      → 收入成本模型（收入公式+成本结构）
```

**必须回答**：
- 这个行业怎么赚钱？
- 价值链怎么流转？
- 行业关键约束是什么？

### Step 2: 公司业务建模

用行业模板中的收入模型、成本模型拆解目标公司：

1. **收入拆解**：用行业收入公式，逐变量拆解目标公司收入
2. **成本拆解**：按行业成本结构，识别固定/变动比例
3. **指标映射**：将公司业务行为映射到行业核心指标体系
4. **单位经济**：计算目标公司的单位经济模型

**输出**：收入成本公式（带变量值）、核心指标现状、单位经济画像

### Step 3: 经营机制建模

1. **经营杠杆识别**：从竞争优势全景框架中识别目标公司的优势来源
   - 规模效应 / 品牌 / 技术 / 渠道 / 转换成本 / 数据飞轮 / 供应链 / 牌照
2. **竞争格局分析**：在行业龙头对比框架下定位目标公司
3. **映射链建立**：业务行为 → 经营指标 → 单位经济 → 财务报表

**关键**：必须解释"为什么"而不只是"是什么"。机制解释需包含因果链、对比验证、具体例证。

### Step 4: 财务映射与验证

1. **业务→财务映射**：将 Step 2-3 的业务模型映射到财务报表结构
2. **行业特有财务分析**：
   - 金融：看资本充足率/偿付能力/NPL/Vintage
   - 物流：看重资产/现金转换周期/季节性
   - 游戏：看递延收入/研发资本化/渠道分成
   - 广告：看流量成本/ARPU 趋势/广告主集中度
   - 消费电子：看存货周转/渠道压货/BOM 成本趋势
3. **红旗扫描**：使用行业特有风险清单扫描

### Step 5: 投资尽调层（可选）

**触发条件**：用户问题涉及投资判断、估值、尽调时激活。

1. 加载 investment_due_diligence.md
2. 按三层框架推进：
   - 行业建模（6 问）
   - 公司建模（8 问）
   - 财务建模（8 问）
3. 输出公司商业建模卡
4. 若涉及估值判断，需设定 Bull/Base/Bear 三情景

### Step 6: 输出

使用 templates/industry_modeling_report.md 格式输出。

**必须包含**：
- 行业定位与本质
- 商业模式拆解（收入公式+成本结构）
- 核心指标体系
- 经营机制与竞争格局
- 财务映射与验证
- 参考来源表（标注数据来源和可信度）

## 与其他 playbook 的协作

| 场景 | 主 playbook | 辅助 playbook |
|------|-------------|---------------|
| 行业深度建模 | industry_modeling | — |
| 行业+战略选择 | industry_modeling | strategy_analysis |
| 行业+竞争对手对比 | industry_modeling | competitive_analysis |
| 行业+投资判断 | industry_modeling | finance_industry_analysis + scenario_sensitivity_analysis |
| 行业+财报分析 | industry_modeling | finance_industry_analysis |

## 自检清单

- [ ] 是否加载了对应行业知识库？
- [ ] 是否按"行业本质→价值链→商业模式→收入成本"顺序建立认知？
- [ ] 是否包含行业特有的收入成本模型？
- [ ] 是否使用了行业特有的指标体系？
- [ ] 是否识别了行业特有的风险信号？
- [ ] 金融行业分析是否先看监管和风险？
- [ ] 是否建立了业务→指标→财务的映射链？
- [ ] 是否对关键现象做了机制解释（因果链+对比验证+例证）？
- [ ] 是否输出了参考来源表？
