---
name: citation-assistant
description: |
  自动化 LaTeX 学术文献引用工作流。基于 Semantic Scholar API 进行语义化文献检索，
  整合 CCF 分级、JCR 分区、中科院分区、影响因子、作者学术影响力等多维度质量评估，
  生成 BibTeX 并提供清晰的中文推荐说明。

  触发场景：
  - 用户在 LaTeX 文稿中标记 [CITE] 占位符，需要查找合适的引用文献
  - 用户粘贴论文段落，需要为其中的 [CITE] 标记寻找引用
  - 用户查询某个期刊/会议的信息（如 "TMI 是什么期刊？质量怎么样？"）
  - 用户需要根据语义上下文而非仅关键词来查找学术引用
  - 用户需要按论文质量（CCF/JCR/IF/引用量/作者影响力）排序推荐文献
  - 用户提及 "文献引用"、"找引用"、"citation"、"bib"、"期刊查询" 等关键词
---

# Citation Assistant 学术文献引用助手

## 配置

### Semantic Scholar API Key

本技能使用 Semantic Scholar API 进行文献检索。建议配置 API Key 以获得更高速率限制。

**获取 API Key**：
1. 访问 https://www.semanticscholar.org/product/api/api-key
2. 注册/登录后生成 API Key
3. 免费配额：100 次/天

**配置方式**（任选其一）：

| 方式 | 操作 |
|------|------|
| 环境变量 | `export S2_API_KEY=your_key_here` |
| 临时指定 | `S2_API_KEY=your_key_here claude` |
| .env 文件 | 复制技能目录中的 `.env.example` 为 `.env` 并填入 key |

**注意**：API Key 是敏感信息，请勿提交到版本控制系统。技能自带 `.env.example` 模板。

**无 API Key 时**：技能仍可使用匿名模式（速率限制 10 次/分钟）。

**匿名模式使用建议**：
- 每次查询间隔约 6 秒，请耐心等待
- 如遇到速率限制，会自动 fallback 到 CrossRef API
- CrossRef 无速率限制，但缺少作者 h-index 等高级信息
- 强烈建议配置 API Key 以获得最佳体验

### Python 依赖

```bash
pip install python-dotenv requests impact_factor
```

| 包名 | 用途 |
|------|------|
| `python-dotenv` | 必需，读取 .env 配置文件 |
| `requests` | 必需，API 请求 |
| `impact_factor` | 必需，查询期刊影响因子和分区 |

## 工作流程概览

```
输入 ([CITE] 占位符) → 语义分析 → Semantic Scholar 检索 → 多维度质量排序 → BibTeX 生成 → 中文推荐报告
```

## 输入模式

支持两种输入方式：

**模式 A - 完整 .tex 文件**
```
用户提供 .tex 文件路径，自动扫描所有 [CITE] 占位符
```

**模式 B - 段落文本（更常用）**
```
用户直接粘贴包含 [CITE] 的段落文本
```

## 核心工作步骤

### Step 1: 解析 [CITE] 占位符

使用 `scripts/tex_parser.py` 提取占位符上下文：

- 识别 `[CITE]` 或 `[CITE:描述]` 格式
- 提取完整句子和周围段落
- 记录行号、列位置信息

### Step 2: 语义化查询构造

**关键原则**：理解引用意图，不只用关键词

分析上下文判断引用目的：
| 引用目的 | 查询策略示例 |
|----------|--------------|
| 事实背书 | "chest radiography most widely used imaging test globally statistics" |
| 方法引用 | "attention mechanism transformer neural machine translation" |
| 背景介绍 | "deep learning medical image analysis survey review" |
| 对比参照 | "BERT language model pretraining comparison" |

### Step 3: Semantic Scholar API 检索

使用 `scripts/s2_search.py` 调用 API：

```python
# 优先使用带 fallback 的搜索函数
from scripts.s2_search import search_with_fallback, search_papers, get_author_info, batch_get_authors

# 推荐：带自动 fallback 的搜索
results = search_with_fallback(
    query=semantic_query,
    limit=20,
    year_range="2018-"  # 可选：限制年份
)

# 或者直接使用 S2 API（无 fallback）
results = search_papers(
    query=semantic_query,
    limit=20,
    year_range="2018-"
)

# 获取作者信息（h-index, 论文数等）
author_info = batch_get_authors(author_ids, fields=["name", "hIndex", "citationCount", "paperCount"])
```

**重要**：优先使用 `search_with_fallback()` 而非 `search_papers()`，它会自动处理：
- 速率限制（429 错误）时自动重试
- S2 API 不可用时自动 fallback 到 CrossRef
- 返回结果中包含 `source` 字段标识数据来源

优先使用Semantic Scholar API而非tavily/web search来检索相关文献

**返回字段**：title, authors, year, venue, citationCount, journal, externalIds, DOI, publicationDate

**作者信息字段**：name, hIndex, citationCount, paperCount, url

#### Semantic Scholar API 官方文档

当需要更细致的 API 使用时，请参考官方文档：

| 文档 | 链接 |
|------|------|
| API 文档主页 | https://api.semanticscholar.org/api-docs/ |
| Academic Graph API | https://api.semanticscholar.org/api-docs/graph |
| Recommendations API | https://api.semanticscholar.org/api-docs/recommendations |
| Datasets API | https://api.semanticscholar.org/api-docs/datasets |
| 交互式教程 | https://www.semanticscholar.org/product/api%2Ftutorial |

**常用 Endpoint**：
- 论文搜索：`GET /paper/search` - 语义化论文检索
- 论文详情：`GET /paper/{paper_id}` - 获取单篇论文完整信息
- 批量论文：`POST /paper/batch` - 批量获取论文信息
- 作者信息：`POST /author/batch` - 批量获取作者信息（含 hIndex）
- 推荐论文：`GET /recommendations/v1/papers` - 基于种子论文推荐

### Step 4: 多维度质量排序

使用 `scripts/quality_ranker.py` 进行评估。详见 `references/quality_metrics.md`。

**评分维度**：
1. **CCF 分级** (A=100, B=70, C=40) - 计算机/CS 领域
2. **JCR 分区** (Q1=80, Q2=60, Q3=40, Q4=20)
3. **中科院分区** (1区=90, 2区=70, 3区=50, 4区=30)
4. **影响因子 IF** (IF × 5, 上限 50)
5. **引用量** (log₁₀(citations+1) × 10, 上限 50)
6. **年份新近度** ((year-2015) × 2, 上限 30)
7. **作者学术影响力** (第一/通讯作者 h-index × 0.5, 上限 30)

**arXiv 处理**：
- 有正式发表版本 → 优先引用正式版本
- 无正式版本但高影响力 → 可引用
- 低引用 arXiv → 降低优先级 (-20 分)

### Step 5: BibTeX 生成

使用 `scripts/doi_to_bibtex.py` 通过 DOI 内容协商获取：

```bash
curl -LH "Accept: text/bibliography; style=bibtex" https://doi.org/{DOI}
```

**处理流程**：
1. 从 Semantic Scholar 结果获取 DOI
2. 调用 DOI API 获取标准 BibTeX
3. 处理 cite key 冲突
4. 合并到用户的 .bib 文件

### Step 6: 生成中文推荐报告

**输出格式**（不自动修改 LaTeX）：

```markdown
## 引用推荐报告

### [CITE] 位置 1 (第 X 行)

**原文上下文**：
> In chest radiography---arguably the most widely used imaging test globally [CITE]---

**推荐文献**：

#### 推荐 1: Wu2020 - CheXpert: A large chest radiograph dataset...

**质量指标**：
| 维度 | 值 | 说明 |
|------|-----|------|
| CCF 分级 | N/A | 非CS领域期刊 |
| JCR 分区 | Q1 | 顶级医学影像期刊 |
| 中科院分区 | 1区 | 影像学最高级别 |
| 影响因子 IF | 29.1 | 极高影响力 |
| 引用量 | 3500+ | 高被引文献 |
| 发表年份 | 2020 | 近期发表 |
| 第一作者 h-index | 45 | 资深研究者 |

**相关性分析**：
- 该文献提供了胸部X光检查作为全球最广泛使用的影像学检查的直接证据
- 通过大型数据集 CheXpert（包含 224,316 张胸部 X 光片）支撑了论点
- 原文论断与该研究的统计结论高度一致

**推荐理由**：顶级期刊发表，极高影响因子和引用量，直接支持原文论点，为该领域权威研究。

---

#### 推荐 2: McAdams2006 - Radiation dose and image quality...

**质量指标**：
| 维度 | 值 | 说明 |
|------|-----|------|
| CCF 分级 | N/A | 非CS领域期刊 |
| JCR 分区 | Q2 | 知名影像学期刊 |
| 中科院分区 | 2区 | 影像学高级别 |
| 影响因子 IF | 5.2 | 中等影响力 |
| 引用量 | 1200+ | 经典引用 |
| 发表年份 | 2006 | 经典文献 |
| 通讯作者 h-index | 68 | 领域权威 |

**相关性分析**：
- 提供了胸部X光检查使用频率的历史数据支撑
- 分析了全球范围内影像学检查的分布情况
- 可作为历史背景引用，补充近期研究

**推荐理由**：经典研究，作者为领域权威，提供历史数据支撑，适合作为补充引用。

---

**生成 BibTeX**：
```bibtex
@article{Wu2020,
  title={CheXpert: A large chest radiograph dataset for chest radiograph interpretation},
  author={Wu, Joy T and Wong, Justin and Hsu, William and others},
  journal={Radiology},
  volume={295},
  number={3},
  pages={605--617},
  year={2020},
  publisher={Radiological Society of North America}
}
```

**建议用法**：将 `[CITE]` 替换为 `~\cite{Wu2020,McAdams2006}`
```

## 数据资源

### CCF 分级数据

位置：`data/` 目录（技能目录内）

| 文件 | 格式 | 用途 |
|------|------|------|
| `ccf_2022.sqlite` | SQLite | 推荐，高效索引查询，表名：`ccf_2022` |
| `ccf_2022.jsonl` | JSONL | Python 直接加载 |

**SQLite 表结构**：
```sql
CREATE TABLE ccf_2022 (
    acronym       -- 期刊/会议简称（如 TMI, ICML）
    name          -- 期刊/会议全称
    rank          -- CCF 等级（A/B/C）
    field         -- 所属领域
    type          -- 类型（journal/conference）
    ...
);
```

查询示例：
```python
# 按简称查询
SELECT * FROM ccf_2022 WHERE acronym = 'TMI'

# 按全称模糊查询
SELECT * FROM ccf_2022 WHERE name LIKE '%Medical Imaging%'
```

详见 `references/ccf_guide.md`

### 影响因子库

```bash
pip install impact_factor
```

```python
from impact_factor.core import Factor
fa = Factor()
fa.search('nature')  # 返回 IF、JCR分区、中科院分区
```

## 使用示例

**示例 1：段落引用**

```
用户输入：
"End-to-end deep learning has revolutionized medical image analysis [CITE].
Vision-language models now generate radiologist-quality reports [CITE]."

执行流程：
1. 解析两个 [CITE] 占位符
2. 分别构造语义查询
3. 检索并排序文献
4. 生成推荐报告和 BibTeX
```

**示例 2：arXiv 论文处理**

```
发现 arXiv:2301.12345 高引用论文：
1. 检查是否有期刊/会议发表版本
2. 如有 → 获取正式版本 DOI 并引用
3. 如无但引用 >100 → 降低优先级但仍可作为候选
```

## 脚本参考

| 脚本 | 功能 | 主要函数 |
|------|------|----------|
| `s2_search.py` | Semantic Scholar API | `search_papers()`, `get_paper_details()`, `batch_get_authors()`, `get_author_info()` |
| `doi_to_bibtex.py` | DOI 转 BibTeX | `doi_to_bibtex()`, `generate_cite_key()` |
| `quality_ranker.py` | 质量评估排序 | `rank_papers()`, `calculate_quality_score()` |
| `tex_parser.py` | LaTeX 占位符解析 | `extract_cite_placeholders()` |

## 注意事项

1. **不自动修改文稿**：所有推荐需用户确认后再应用
2. **语义优先**：避免仅用关键词检索，理解引用意图
3. **质量把关**：综合多维度指标，不唯引用量论
4. **arXiv 审慎**：期刊投稿应控制 arXiv 引用比例
5. **API 限制**：Semantic Scholar 免费版有限率，批量查询需注意
