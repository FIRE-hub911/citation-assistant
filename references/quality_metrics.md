# 论文质量评估指标体系

## 评估维度

### 1. CCF 分级 (中国计算机学会推荐目录)

| 等级 | 含义 | 得分权重 |
|------|------|----------|
| A类 | 国际顶级会议/期刊 | 100 |
| B类 | 国际重要会议/期刊 | 70 |
| C类 | 国际知名会议/期刊 | 40 |

**适用范围**: 主要覆盖计算机科学相关领域

### 2. JCR 分区 (Journal Citation Reports)

| 分区 | 含义 | 得分权重 |
|------|------|----------|
| Q1 | 学科前25% | 80 |
| Q2 | 学科25%-50% | 60 |
| Q3 | 学科50%-75% | 40 |
| Q4 | 学科后25% | 20 |

**数据来源**: Clarivate Analytics Web of Science

### 3. 中科院分区

| 分区 | 含义 | 得分权重 |
|------|------|----------|
| 1区 | 顶级期刊 | 90 |
| 2区 | 重要期刊 | 70 |
| 3区 | 一般期刊 | 50 |
| 4区 | 其他期刊 | 30 |

**特点**:
- 采用金字塔分区方式
- 1区期刊仅占前5%
- 比JCR分区更严格

### 4. 影响因子 (Impact Factor, IF)

- 计算公式: 某期刊前两年论文在当年被引用次数 / 前两年论文总数
- 得分计算: `min(50, IF × 5)`
- 权重: 30%

**典型 IF 参考**:
- Nature/Science: 40-60+
- 顶级领域期刊: 10-20
- 一般 SCI 期刊: 2-5

### 5. 引用量 (Citation Count)

- 反映论文的学术影响力
- 得分计算: `min(50, log10(citation_count + 1) × 10)`
- 权重: 20%

**参考标准**:
- 高被引论文: >100 引用
- 热门论文: >500 引用
- 经典论文: >1000 引用

### 6. 发表年份

- 越新的论文越能反映最新研究进展
- 得分计算: `min(30, max(0, (year - 2015) × 2))`
- 权重: 10%

### 7. 作者学术影响力

- 通过 Semantic Scholar API 获取作者的 h-index、引用量和发表论文数
- 主要关注第一作者和通讯作者（通常为最后一位作者）的 h-index
- 得分计算: `min(30, max_h_index × 0.5)`
- 权重: 20%

**参考标准**:
| h-index 范围 | 学术地位 | 说明 |
|-------------|----------|------|
| > 60 | 领域权威 | 顶尖学者，论文影响力极高 |
| 30-60 | 资深研究者 | 教授/高级研究员级别 |
| 15-30 | 中级研究者 | 副教授/高级讲师级别 |
| 5-15 | 青年学者 | 博士后/助理教授级别 |
| < 5 | 初级研究者 | 博士生/初级博士后 |

**数据获取方式**:
```python
from scripts.s2_search import get_author_info, batch_get_authors, get_paper_author_impact

# 获取单个作者信息
author_info = get_author_info(author_id, fields=["name", "hIndex", "citationCount", "paperCount"])

# 批量获取作者信息
authors_info = batch_get_authors(author_ids)

# 获取论文作者影响力（自动获取第一作者和最后作者信息）
impact = get_paper_author_impact(paper)
```

### 8. arXiv 处理策略

| 情况 | 处理方式 |
|------|----------|
| 有期刊/会议发表版本 | 优先引用正式版本 |
| 无正式版本但高影响力 | 可以引用，接受度较高 |
| 低引用 arXiv 预印本 | 降低优先级，建议寻找替代 |

**arXiv 惩罚**: -20 分（仅当无正式版本时）

## 综合得分公式

```
score = max(CCF得分, JCR得分, 中科院得分)
        + IF得分 × 0.3
        + 引用得分 × 0.2
        + 年份得分 × 0.1
        + 作者影响力得分 × 0.2
        - arXiv惩罚（如适用）
```

## 使用 impact_factor 库

```python
# 安装
pip install impact_factor

# 使用
from impact_factor.core import Factor
fa = Factor()

# 查询期刊
result = fa.search('nature')
info = fa.search('nature communications')

# 返回字段包括：
# - impact_factor (影响因子)
# - jcr_quartile (JCR 分区)
# - cas_quartile (中科院分区)
```

## 推荐排序逻辑

1. **优先级**:
   - CCF A/B 类 > JCR Q1/Q2 > 高 IF > 高引用
   - 正式发表版本 > arXiv 预印本

2. **领域匹配**:
   - 优先推荐与论文主题相关的顶级 venue

3. **时效性**:
   - 在质量相近的情况下，优先推荐近年论文

4. **引用目的**:
   - 背景知识：经典高引用论文
   - 最新进展：近年顶级会议论文
   - 方法对比：相关领域的代表性工作
