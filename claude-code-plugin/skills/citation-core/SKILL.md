---
name: citation-core
description: |
  Citation Assistant 核心工作流 Skill。

  触发场景：
  - 用户在 LaTeX 文稿中标记 [CITE] 占位符，需要查找合适的引用文献
  - 用户粘贴论文段落，需要为其中的 [CITE] 标记寻找引用
  - 用户需要根据语义上下文查找学术引用
  - 用户需要按论文质量（CCF/JCR/IF/引用量）排序推荐文献
  - 用户提及 "文献引用"、"找引用"、"citation"、"bib" 等关键词
  - 用户需要完整的引用推荐到 BibTeX 生成的端到端服务
---

# Citation Core - 学术引用工作流

## 工作流概览

```
输入 ([CITE] 占位符) → 语义分析 → 文献检索 → 质量排序 → BibTeX 生成 → 中文推荐报告
```

## 输入模式

**模式 A - 完整 .tex 文件**
用户提供 .tex 文件路径，自动扫描所有 [CITE] 占位符

**模式 B - 段落文本（更常用）**
用户直接粘贴包含 [CITE] 的段落文本

## 工作步骤

### Step 1: 解析 [CITE] 占位符

使用 Command `/citation:parse` 提取占位符上下文：
- 识别 `[CITE]` 或 `[CITE:描述]` 格式
- 提取完整句子和周围段落
- 记录行号、列位置信息

### Step 2: 语义化查询构造

**关键原则**：理解引用意图，不只用关键词

分析上下文判断引用目的，构造语义查询：
| 引用目的 | 查询策略示例 |
|----------|--------------|
| 事实背书 | "chest radiography most widely used imaging test globally statistics" |
| 方法引用 | "attention mechanism transformer neural machine translation" |
| 背景介绍 | "deep learning medical image analysis survey review" |
| 对比参照 | "BERT language model pretraining comparison" |

### Step 3: 文献检索

调用 `/citation:search` 或 `/citation:search-bulk` Command：
- 使用 Semantic Scholar API 进行语义化检索
- 支持年份范围过滤
- 自动处理速率限制和 fallback

### Step 4: 多维度质量排序

调用 `/citation:evaluate` Command 进行评估：

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

调用 `/citation:bibtex` Command：
- 通过 DOI 内容协商获取标准 BibTeX
- 处理 cite key 冲突
- 返回格式化 BibTeX 条目

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

**推荐理由**：顶级期刊发表，极高影响因子和引用量，直接支持原文论点，为该领域权威研究。

---

**生成 BibTeX**：
```bibtex
@article{Wu2020,
  title={CheXpert: A large chest radiograph dataset...},
  ...
}
```

**建议用法**：将 `[CITE]` 替换为 `~\cite{Wu2020}`
```

## 可用 Commands

| Command | 功能 | 使用场景 |
|---------|------|----------|
| `/citation:search` | 单条语义搜索 | 快速查找相关文献 |
| `/citation:search-bulk` | 批量搜索 | 大批量文献检索 |
| `/citation:evaluate` | 质量评估 | 对搜索结果进行多维度排序 |
| `/citation:bibtex` | BibTeX 生成 | 通过 DOI 获取引用格式 |
| `/citation:venue-info` | 期刊信息 | 查询特定期刊的 CCF/IF 等级 |
| `/citation:crossref` | CrossRef 搜索 | S2 API 不可时的 fallback |
| `/citation:parse` | 解析占位符 | 提取 [CITE] 上下文 |

## 注意事项

1. **不自动修改文稿**：所有推荐需用户确认后再应用
2. **语义优先**：避免仅用关键词检索，理解引用意图
3. **质量把关**：综合多维度指标，不唯引用量论
4. **arXiv 审慎**：期刊投稿应控制 arXiv 引用比例
5. **API 限制**：Semantic Scholar 免费版有限率，批量查询需注意

## 配置说明

本 Skill 依赖以下 Commands，请确保已安装 citation-assistant Plugin：
- `/citation:search`
- `/citation:evaluate`
- `/citation:bibtex`
