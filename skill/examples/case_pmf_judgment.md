# 示例：PMF 判断

## 用户输入
"我们产品月活 50 万，30 日留存 20%，算不算达到 PMF？"

## Skill 响应

### Step 1: 路由识别
关键词：PMF、留存 → 触发「PMF 诊断」
调用：`playbooks/product_ops_analysis.md`
模板：`templates/pmf_growth_report.md`

### Step 2: 关键反问
> 在判断 PMF 前，我需要确认：
> 1. 增长是自然增长还是靠补贴/投放驱动？
> 2. NPS 或口碑推荐数据如何？
> 3. 是否有付费环节？付费转化率？
> 4. 产品属于哪个行业/类型（工具/社交/电商/SaaS）？
> 5. 30 日留存是 Cohort 口径还是滚动口径？

### Step 3: 分析逻辑
30% 留存在消费互联网是中等水平，但必须检查：
- 是否取消补贴后仍能保持？（伪 PMF 检查）
- 自然获客占比？
- NPS 是否为正？

### Step 4: 输出评级
使用 `pmf_strength_rubric.md` 五维度评分。