# 设计规格：senior_analyst 行业商业建模能力增强

> 日期：2026-04-26
> 状态：设计完成，待实施

## 背景

当前 senior_analyst skill 的分析能力以通用框架为主（商业模式画布、单位经济、杜邦分解等），缺乏行业特化的商业建模能力。用户分析金融、物流、游戏等特定行业时，通用框架无法捕捉行业核心逻辑（如金融的"风险定价+杠杆经营"、游戏的"内容产品+流量获取+生命周期运营"）。

参考 `/Users/red/ai-project/minds_for_ai/md/senior_analyst skill改进建议.md`（约4600行），提取核心内容落地到 skill 中。

## 目标

1. 新增行业商业建模知识库（5个行业模板）
2. 新增商业建模总论和快速建模方法论
3. 新增投资尽调商业建模框架
4. 行业建模流程入口（playbook + router 联动）
5. 更新 README 展示新增能力

## 架构决策

**采用两层架构**：knowledge/ 放行业知识，playbooks/industry_modeling.md 做流程入口。

- 流程和知识分离但联动
- 新增行业只需加 knowledge/industries/xxx.md + 在 playbook 注册表中加一行
- 避免知识内容与流程逻辑混杂

## 目录结构

```
skill/
├── knowledge/                              # 新增目录
│   ├── business_modeling_overview.md        # 商业建模总论
│   ├── industry_methodology.md              # 新行业快速建模方法论
│   ├── investment_due_diligence.md          # 投资尽调商业建模框架
│   ├── industry_model_card_template.md      # 一页纸商业建模卡模板
│   └── industries/                          # 行业模板
│       ├── finance.md                       # 金融（银行/保险/信贷）
│       ├── logistics.md                     # 物流与供应链
│       ├── gaming.md                        # 游戏
│       ├── internet_advertising.md          # 互联网广告
│       └── consumer_electronics.md          # 消费电子
├── playbooks/
│   ├── ... (现有不变)
│   └── industry_modeling.md                 # 新增：行业建模流程入口
├── router.md                                # 更新：增加行业建模路由
├── SKILL.md                                 # 更新：增加行业建模原则
├── templates/
│   ├── ... (现有不变)
│   └── industry_modeling_report.md          # 新增：行业建模报告模板
└── rubrics/
    └── completeness_checklist.md             # 更新：增加行业建模检查项
```

## 新增文件详细设计

### 1. playbooks/industry_modeling.md

行业建模流程入口，定义分析流程：

```
Step 0: 行业识别
    └─ 从用户问题中识别目标行业
    └─ 查行业注册表，确定加载哪个 knowledge/industries/ 文件
    └─ 若不在注册表中 → 加载 industry_methodology.md，用十步法建模

Step 1: 行业认知建立
    └─ 加载对应行业 knowledge 文件
    └─ 按"行业本质 → 价值链 → 商业模式分类 → 收入成本模型"顺序建立认知

Step 2: 公司业务建模
    └─ 用行业模板中的收入模型、成本模型拆解目标公司
    └─ 映射到核心指标体系
    └─ 计算单位经济

Step 3: 经营机制建模
    └─ 识别关键经营杠杆
    └─ 分析竞争格局与护城河
    └─ 建立业务→指标→财务的映射链

Step 4: 财务映射与验证
    └─ 将业务模型映射到财务报表结构
    └─ 行业特有财务分析
    └─ 红旗信号扫描（使用行业特有风险清单）

Step 5: 投资尽调层（可选，当用户涉及投资判断时激活）
    └─ 加载 investment_due_diligence.md
    └─ 市场空间 → 单位经济 → 财务质量 → 风险 → 投资结论
    └─ 输出公司商业建模卡

Step 6: 输出
    └─ 使用 templates/industry_modeling_report.md
```

**行业注册表**：

| 行业关键词 | 加载 knowledge 文件 | 特殊说明 |
|---|---|---|
| 金融/银行/保险/信贷/消费金融/助贷/风控/牌照 | finance.md | 必须先看监管，再看利润 |
| 物流/快递/仓配/供应链/即时零售/货运/冷链 | logistics.md | 需拆子赛道 |
| 游戏/手游/端游/IAP/IAA/买量/游戏运营 | gaming.md | 生命周期是核心变量 |
| 广告/流量变现/程序化/ADX/DSP/广告主/加载率 | internet_advertising.md | 流量-广告负载-ROI 三角 |
| 消费电子/手机/耳机/智能家居/硬件/品牌/渠道 | consumer_electronics.md | 产品周期+渠道库存是风险核心 |

**与现有 playbook 的关系**：
- 行业深度建模 → industry_modeling
- 跨行业通用问题 → 现有 playbook
- 混合场景 → industry_modeling 主 + 对应辅助 playbook

### 2. knowledge/business_modeling_overview.md

商业建模总论，定义通用框架：
- 商业建模 vs 数据分析 vs 财务分析
- 商业建模五层结构：行业 → 公司 → 经营 → 财务 → 决策
- 标准输出：商业模式图、收入成本公式、指标树、财务映射、风险清单、推演假设
- 映射链：业务行为 → 经营指标 → 单位经济 → 财务报表 → 估值/决策
- 竞争优势全景框架（9 种优势来源）

### 3. knowledge/industry_methodology.md

新行业快速建模方法论：
- 十步法：定义边界→画价值链→分模式→拆收入→拆成本→找约束→建指标树→看规模效应→做公司对比→形成结论
- 行业学习 8 问
- 行业建模一页纸模板

### 4. knowledge/investment_due_diligence.md

投资尽调商业建模框架：
- 尽调总框架：市场空间→竞争格局→公司模式→单位经济→财务质量→风险→投资结论
- 市场空间预测方法（自上而下 + 自下而上 + 情景分析）
- 公司商业建模卡模板
- 投资决策备忘录模板

### 5. knowledge/industry_model_card_template.md

通用一页纸商业建模卡模板，适用于任何行业。

### 6. knowledge/industries/ 各行业模板

每个行业文件统一结构：

```
# [行业名称] 商业建模知识库

## 一、行业总论
  - 商业本质
  - 与普通行业的核心差异
  - 行业分析总框架

## 二、商业模式分类
  - 子行业/子赛道拆分
  - 商业模式分类
  - 收入来源与利润来源

## 三、收入与成本模型
  - 收入公式（带变量拆解）
  - 成本结构
  - 单位经济模型

## 四、核心指标体系
  - 结果指标（行业北极星）
  - 过程指标
  - 护栏指标
  - 行业特有指标解释

## 五、经营杠杆与竞争格局
  - 关键竞争优势来源
  - 规模效应类型
  - 龙头公司模式对比

## 六、财务分析映射
  - 行业特有财务分析重点
  - 行业特有会计科目与风险
  - 财务报表与业务指标映射

## 七、风险信号清单
  - 行业特有红旗信号
  - 常见分析误区

## 八、投资尽调问题清单

## 九、行业快速分析卡
  - 一页纸速查表
```

#### 6.1 finance.md 重点内容

- 金融行业本质：风险定价 + 杠杆经营 + 资金期限管理
- 三大子行业：银行、保险、信贷/消费金融/助贷
- 银行：净息差模型、资产质量（NPL、拨备覆盖）、资本充足率
- 保险：承保端+投资端双轮驱动、综合成本率、NBV/EV、偿付能力
- 信贷：Vintage 分析、风险迁徙、资金成本+风险成本+运营成本三段拆分
- 金融行业特有风险：监管变动、流动性、信用风险、利率风险
- 常见分析误区：拿普通行业财务指标套金融公司、忽视监管约束

#### 6.2 logistics.md 重点内容

- 物流行业本质：空间效用 + 时间效用 + 规模密度
- 五大子赛道：快递物流、即时零售履约、仓配与供应链、冷链物流、货运/跨境
- 核心指标：时效、妥投率、单票成本、人效、坪效、履约成本
- 龙头对比：顺丰 vs 中通 vs 京东物流 vs 美团配送
- 约束：路由密度、末端成本、季节波动、政策合规

#### 6.3 gaming.md 重点内容

- 游戏行业本质：内容产品 + 流量获取 + 生命周期运营
- 模式分类：IAP（内购）、IAA（广告变现）
- 收入公式：DAU × 付费率 × ARPPU / 广告展示 × eCPM
- 核心指标：留存率（D1/D7/D30）、LTV、CAC、ROAS、生命周期
- 财务映射：递延收入、研发资本化、渠道分成
- 风险：爆款依赖、买量 ROI 恶化、版号政策

#### 6.4 internet_advertising.md 重点内容

- 互联网广告本质：流量变现 + 广告匹配 + 广告主 ROI
- 核心矛盾：用户体验 vs 广告负载 vs 变现效率
- 收入公式：流量 × 广告加载率 × 填充率 × eCPM
- 技术链路：ADX/DSP/DMP/SSP
- 风险：流量见顶、广告负载过高、广告主集中、隐私政策

#### 6.5 consumer_electronics.md 重点内容

- 消费电子本质：产品定义 + 供应链效率 + 品牌/渠道
- 收入公式：销量 × ASP
- 成本拆分：BOM + 制造 + 渠道返利 + 物流售后
- 核心指标：ASP、毛利率、库存周转、渠道结构
- 风险：存货积压、产品周期、渠道压货、供应链断裂

### 7. templates/industry_modeling_report.md

行业建模分析报告模板：

```markdown
# [公司/行业名称] 行业商业建模报告

## 一、核心结论
- 一句话结论
- 关键判断 1-3 条
- 风险等级

## 二、行业定位与本质
- 行业商业本质
- 价值链与利润分配
- 子赛道归属

## 三、商业模式拆解
- 收入模型与公式
- 成本结构与边际分析
- 单位经济

## 四、核心指标体系
- 结果指标
- 过程指标
- 护栏指标

## 五、经营机制与竞争格局
- 关键经营杠杆
- 竞争优势来源
- 龙头公司对比

## 六、财务映射与验证
- 业务→财务映射链
- 行业特有财务分析
- 红旗信号扫描

## 七、投资尽调判断（如适用）
- 市场空间评估
- 单位经济健康度
- 投资结论

## 八、假设与不确定性
- 核心假设
- 证伪条件
- 数据缺口

## 九、行动建议
- 立即动作
- 短期动作
- 长期动作

## 十、参考来源
| 序号 | 来源 | 类型 | 可信度 |
```

## 行业建模快捷触发设计

Claude Code 不支持 colon 语法的子 skill（如 `/senior_analyst:industry_model`）。采用**内部子命令**方案：在 SKILL.md 的交互模式中扩展参数识别，让用户通过行业关键词自动触发行业建模流程。

### 触发方式

| 用户输入 | 识别逻辑 | 触发流程 |
|---|---|---|
| `/senior_analyst 腾讯` | 通用公司名 | 通用分析流程（现有） |
| `/senior_analyst 金融 平安` | 命中行业关键词 | 行业建模流程 |
| `/senior_analyst 保险 中国人寿` | 命中行业关键词 | 行业建模流程 |
| `/senior_analyst 物流 顺丰` | 命中行业关键词 | 行业建模流程 |
| `/senior_analyst 游戏 米哈游` | 命中行业关键词 | 行业建模流程 |
| `/senior_analyst --industry 信贷` | 显式指定行业建模模式 | 行业建模流程 |
| `/senior_analyst 尽调 某公司` | 命中尽调关键词 | 行业建模流程（投资尽调层） |

### SKILL.md 交互模式扩展

在现有"带参数模式"和"引导模式"基础上，新增"行业建模模式"：

```markdown
### 行业建模模式
用户输入：`/senior_analyst 金融 平安` 或 `/senior_analyst --industry 信贷`
→ 识别到行业关键词或 --industry 标志
→ 直接进入 industry_modeling playbook
→ 根据行业关键词加载对应 knowledge/industries/ 文件
→ 按行业建模六步流程推进
```

### 识别逻辑

1. 参数中包含 `--industry` → 强制进入行业建模模式
2. 参数中包含行业注册表关键词 → 自动进入行业建模模式
3. 参数仅为公司名（无行业关键词）→ 通用分析流程，router 在 Step 1 中也可能根据公司特征路由到行业建模
4. 无参数 → 引导模式（现有逻辑不变）

行业注册表关键词与 playbook 中的一致：金融/银行/保险/信贷/物流/快递/游戏/广告/消费电子/尽调 等。

## 现有文件更新

### router.md

1. 路由矩阵新增一行：
   - 行业建模/行业分析 → industry_modeling → 视行业选辅助 → industry_modeling_report
2. 新增关键词识别规则：
   - 金融/银行/保险/信贷/消费金融/助贷
   - 物流/快递/供应链/仓配
   - 游戏/手游/买量
   - 广告/流量变现/程序化
   - 消费电子/硬件/渠道
   - 尽调/投资判断
3. 新增混合型问题：
   - 行业+战略选择 → industry_modeling 主 + strategy_analysis 辅 → industry_modeling_report + strategy_memo
   - 行业+竞争对手对比 → industry_modeling 主 + competitive_analysis 辅 → industry_modeling_report + competitive_analysis_report
   - 行业+投资判断 → industry_modeling 主 + finance_industry_analysis + scenario_sensitivity_analysis 辅 → industry_modeling_report + scenario_analysis_report
   - 行业+财报分析 → industry_modeling 主 + finance_industry_analysis 辅 → industry_modeling_report + finance_risk_report

### SKILL.md

1. 新增原则 #16：行业建模必须先理解行业本质
2. 新增原则 #17：金融行业分析必须先看监管和风险
3. Step 2 框架调用中新增：行业建模类 → playbooks/industry_modeling.md
4. Step 5 产物输出中新增：行业建模 → templates/industry_modeling_report.md
5. 禁止事项新增：不跨行业硬套通用分析框架
6. 交互模式扩展：新增"行业建模模式"，参数中包含行业关键词或 --industry 标志时，直接进入 industry_modeling playbook

### rubrics/completeness_checklist.md

新增检查项：
- 行业建模报告是否加载了对应行业知识库？
- 是否包含行业特有的收入成本模型？
- 是否使用了行业特有的指标体系？
- 是否识别了行业特有的风险信号？
- 金融行业分析是否先看监管和风险？
- 是否输出了参考来源表？

### README.md

新增"行业建模能力"板块，展示：
1. 5 大行业模板（金融/物流/游戏/互联网广告/消费电子）
2. 商业建模五层结构图
3. 新行业快速建模十步法
4. 投资尽调框架
5. 一页纸商业建模卡
6. 使用示例：
   - `/senior_analyst 金融 平安` → 行业建模模式，分析金融行业
   - `/senior_analyst --industry 某公司` → 显式行业建模模式
   - `/senior_analyst 保险 平安` → 行业建模模式，分析保险行业

## 数据来源

所有行业知识内容基于改进建议文件（`/Users/red/ai-project/minds_for_ai/md/senior_analyst skill改进建议.md`），提取并重组为统一结构。每个行业模板的内容来源：

- 金融行业：文件第 2607-3931 行、第 4662-5232 行
- 物流行业：文件第 1815-2074 行、第 2079-2207 行
- 游戏行业：文件第 2833-2957 行、第 3942-4154 行
- 互联网广告：文件第 2957-3065 行、第 4155-4341 行
- 消费电子：文件第 3065-3232 行、第 4342-4527 行
- 商业建模总论：文件第 2415-2434 行
- 行业方法论：文件第 1717-1729 行、第 2437-2452 行
- 投资尽调：文件第 2207-2307 行、第 2464-2482 行
- 商业建模卡：文件第 2307-2364 行、第 4557-4597 行
