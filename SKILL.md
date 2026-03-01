---
name: citation-assistant
description: |
  自动化 LaTeX 学术文献引用工作流。基于 Semantic Scholar API 进行语义化文献检索，
  整合 CCF 分级、JCR 分区、中科院分区、影响因子等多维度质量评估，
  生成 BibTeX 并提供清晰的中文推荐说明。

  触发场景：
  - 用户在 LaTeX 文稿中标记 [CITE] 占位符，需要查找合适的引用文献
  - 用户粘贴论文段落，需要为其中的 [CITE] 标记寻找引用
  - 用户查询某个期刊/会议的信息（如 "TMI 是什么期刊？质量怎么样？"）
  - 用户需要根据语义上下文而非仅关键词来查找学术引用
  - 用户需要按论文质量（CCF/JCR/IF/引用量）排序推荐文献
  - 用户提及 "文献引用"、"找引用"、"citation"、"bib"、"期刊查询" 等关键词
---

# Citation Assistant 学术文献引用助手

**零依赖版本** - 仅需 `curl`、`sqlite3`、`jq`（系统自带或常见工具）

## 配置

### Semantic Scholar API Key（推荐）

```bash
# 方式 1: 使用 .env 文件（推荐）
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 方式 2: 环境变量
export S2_API_KEY="your_key_here"

# 方式 3: 写入 shell 配置文件
echo 'export S2_API_KEY="your_key_here"' >> ~/.zshrc

# 获取 API Key: https://www.semanticscholar.org/product/api/api-key
```

| 模式 | 速率限制 | 推荐场景 |
|------|----------|----------|
| 有 API Key | 1 次/秒 (60 次/分钟) | 日常使用 |
| 无 API Key | 与所有无 Key 用户共享限额 | 不推荐（极易触发 429） |

> ⚠️ **注意**：即使有 API Key，连续快速发送多个请求仍可能触发 429。建议在连续请求之间添加 `sleep 1` 间隔。

### 依赖检查

```bash
# 检查工具是否可用
which curl sqlite3 jq

# 如需安装 jq
brew install jq  # macOS
```

## ⚠️ 初始化步骤（必须首先执行）

在执行任何 API 命令之前，**必须先运行以下初始化**来加载 API Key：

```bash
# 加载 API Key 和设置路径变量（每个新 shell 会话都需要执行）
source "$HOME/.claude/skills/citation-assistant/.env"
SKILL_DIR="$HOME/.claude/skills/citation-assistant"
DATA_DIR="$SKILL_DIR/data"
```

**重要提示**：
- Claude Code 的 Bash 工具每次执行都是新的 shell 会话，不会自动加载 `.env`
- 因此**每条命令都需要先执行初始化**，或使用下面「自包含命令」格式

## 核心命令

以下命令均为**自包含格式**，可直接复制执行（已内置初始化步骤）。

### 1. 论文搜索（Semantic Scholar）

```bash
# 初始化 + 搜索（自包含命令，可直接执行）
source "$HOME/.claude/skills/citation-assistant/.env" && \
QUERY="attention mechanism transformer" && \
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&limit=10&fields=paperId,title,year,authors,venue,journal,citationCount,externalIds,url,abstract" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} | jq '.data[]? | {title, year, venue, citations: .citationCount, doi: .externalIds.DOI, abstract}'
```

> **注意**：包含 `abstract` 字段可以更好地判断文献相关性。

### 1.1 论文批量搜索（推荐，更高效）

使用 `/paper/search/bulk` 端点可以减少 API 压力，支持更多过滤参数：

```bash
# 批量搜索（推荐用于多次查询场景）
source "$HOME/.claude/skills/citation-assistant/.env" && \
QUERY="medical AI sensitivity specificity" && \
curl -s "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&fields=title,year,venue,citationCount,externalIds,url,abstract&year=2020-&sort=citationCount:desc" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} | jq '.data[]? | {title, year, venue, citations: .citationCount, doi: .externalIds.DOI, abstract}'
```

**Bulk 端点特有参数**：
| 参数 | 说明 | 示例 |
|------|------|------|
| `year` | 年份范围 | `2020-` (2020年及以后), `2018-2022` |
| `sort` | 排序方式 | `citationCount:desc`, `publicationDate:asc` |
| `minCitationCount` | 最小引用数 | `10` |
| `venue` | 发表场所 | `Nature`, `NeurIPS` |
| `fieldsOfStudy` | 研究领域 | `Computer Science`, `Medicine` |
| `publicationTypes` | 出版类型 | `JournalArticle`, `Conference` |
| `openAccessPdf` | 开放获取 PDF | `true` |
| `token` | 分页令牌 | 从上次响应中获取 |

**分页示例**（获取下一页）：
```bash
# 首次请求会返回 token，用于获取下一页
source "$HOME/.claude/skills/citation-assistant/.env" && \
QUERY="deep learning medical imaging" && \
RESPONSE=$(curl -s "https://api.semanticscholar.org/graph/v1/paper/search/bulk?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&fields=title,year,venue,citationCount,abstract" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"}) && \
echo "$RESPONSE" | jq '.data[]? | {title, year, citations: .citationCount}' && \
echo "Next token: $(echo "$RESPONSE" | jq -r '.token // "none"')"
```

### 2. 期刊/会议信息查询

```bash
# 初始化 + CCF 分级查询
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
NAME="TMI" && \
sqlite3 "$SKILL_DIR/data/ccf_2022.sqlite" \
  "SELECT acronym, name, rank, field, type FROM ccf_2022 WHERE acronym LIKE '%$NAME%' OR name LIKE '%$NAME%';"
```

```bash
# 初始化 + 影响因子查询
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
NAME="Nature Medicine" && \
sqlite3 "$SKILL_DIR/data/impact_factor.sqlite3" \
  "SELECT journal, factor, jcr, zky FROM factor WHERE journal LIKE '%$NAME%' LIMIT 5;"
```

```bash
# 综合查询（CCF + IF）
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
NAME="NeurIPS" && \
echo "=== CCF 分级 ===" && \
sqlite3 "$SKILL_DIR/data/ccf_2022.sqlite" "SELECT acronym, name, rank, field, type FROM ccf_2022 WHERE acronym LIKE '%$NAME%' OR name LIKE '%$NAME%';" && \
echo "" && \
echo "=== 影响因子 ===" && \
sqlite3 "$SKILL_DIR/data/impact_factor.sqlite3" "SELECT journal, factor, jcr, zky FROM factor WHERE journal LIKE '%$NAME%' LIMIT 5;"
```

### 3. DOI 转 BibTeX

```bash
# 通过 DOI 获取 BibTeX（无需 API Key）
DOI="10.1038/nature12373" && \
curl -sLH "Accept: text/bibliography; style=bibtex" "https://doi.org/$DOI"
```

### 4. CrossRef 搜索（Fallback，无速率限制）

当 Semantic Scholar 返回 429 错误时使用：

```bash
# CrossRef 搜索（不需要 API Key，无速率限制）
QUERY="medical imaging deep learning" && \
curl -s "https://api.crossref.org/works?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&rows=10" | \
  jq '.message.items[] | {title: .title[0], year: (.["published-print"]["date-parts"][0][0] // .["published-online"]["date-parts"][0][0]), doi: .DOI, citations: .["is-referenced-by-count"]}'
```

### 5. 批量获取作者信息

```bash
# 获取作者 h-index 等
source "$HOME/.claude/skills/citation-assistant/.env" && \
IDS="2280176042,2280143067" && \
curl -s -X POST "https://api.semanticscholar.org/graph/v1/author/batch?fields=name,hIndex,citationCount,paperCount" \
  -H "Content-Type: application/json" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} \
  -d "{\"ids\": $(echo "$IDS" | jq -R 'split(",")')}" | jq .
```

## 工作流程

### Step 1: 解析 [CITE] 占位符

识别用户提供的段落中的 `[CITE]` 或 `[CITE:描述]` 标记，提取上下文。

### Step 2: 构造语义化查询

| 引用目的 | 查询策略示例 |
|----------|--------------|
| 事实背书 | "chest radiography most widely used imaging test globally statistics" |
| 方法引用 | "attention mechanism transformer neural machine translation" |
| 背景介绍 | "deep learning medical image analysis survey review" |
| 对比参照 | "BERT language model pretraining comparison" |

### Step 3: 执行搜索

```bash
# 自包含搜索命令（可直接执行）
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
DATA_DIR="$SKILL_DIR/data" && \
QUERY="YOUR_QUERY_HERE" && \
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&limit=20&fields=paperId,title,year,authors,venue,journal,citationCount,externalIds,url,abstract" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} | jq '.data[]? | {title, year, venue, citations: .citationCount, doi: .externalIds.DOI, abstract}'
```

### Step 4: 质量评估

对搜索结果进行多维度评估：

**评分维度**：
1. **CCF 分级** (A=100, B=70, C=40) - 计算机/CS 领域
2. **JCR 分区** (Q1=80, Q2=60, Q3=40, Q4=20)
3. **中科院分区** (1区=90, 2区=70, 3区=50, 4区=30)
4. **影响因子 IF** (IF × 5, 上限 50)
5. **引用量** (log₁₀(citations+1) × 10, 上限 50)
6. **年份新近度** ((year-2015) × 2, 上限 30)

**查询期刊质量**：
```bash
# 初始化 + 查询某个期刊/会议的完整信息（自包含命令）
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
DATA_DIR="$SKILL_DIR/data" && \
VENUE="Nature Medicine" && \
echo "=== CCF 分级 ===" && \
sqlite3 "$DATA_DIR/ccf_2022.sqlite" "SELECT * FROM ccf_2022 WHERE name LIKE '%$VENUE%' OR acronym LIKE '%$VENUE%';" && \
echo "" && \
echo "=== 影响因子和分区 ===" && \
sqlite3 "$DATA_DIR/impact_factor.sqlite3" "SELECT journal, factor as IF, jcr, zky as CAS FROM factor WHERE journal LIKE '%$VENUE%';"
```

### Step 5: 生成 BibTeX

```bash
# 从搜索结果提取 DOI，然后获取 BibTeX
doi=$(echo "$results" | jq -r '.data[0].externalIds.DOI')
curl -sLH "Accept: text/bibliography; style=bibtex" "https://doi.org/$doi"
```

### Step 6: 生成中文推荐报告

输出格式示例：

```markdown
## 引用推荐报告

### [CITE] 位置 1

**原文上下文**：
> End-to-end attention was never trained to ignore irrelevant context [CITE]

**推荐文献**：

#### 推荐 1: Attention Is All You Need (2017)

**质量指标**：
| 维度 | 值 | 说明 |
|------|-----|------|
| CCF 分级 | A | 顶级会议 |
| 引用量 | 100000+ | 极高被引 |
| 发表年份 | 2017 | 经典文献 |

**推荐理由**：Transformer 开山之作，直接支持原文关于 attention 机制的论点。

---

**生成 BibTeX**：
```bibtex
@inproceedings{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and others},
  booktitle={NeurIPS},
  year={2017}
}
```

**建议用法**：将 `[CITE]` 替换为 `~\cite{vaswani2017attention}`
```

## 数据资源

### CCF 分级数据

位置：`data/ccf_2022.sqlite`

```bash
# 查询示例
sqlite3 "$DATA_DIR/ccf_2022.sqlite" "SELECT * FROM ccf_2022 WHERE acronym = 'TMI';"
sqlite3 "$DATA_DIR/ccf_2022.sqlite" "SELECT acronym, name, rank FROM ccf_2022 WHERE rank = 'A' AND type = 'conference';"
```

### 影响因子数据

位置：`data/impact_factor.sqlite3`（约 20,000 条期刊记录）

```bash
# 查询示例
sqlite3 "$DATA_DIR/impact_factor.sqlite3" "SELECT journal, factor, jcr, zky FROM factor WHERE jcr = 'Q1' ORDER BY factor DESC LIMIT 10;"
```

## 完整示例

**场景**：用户需要为 "attention cannot ignore irrelevant context" 找引用

```bash
# Step 1: 初始化 + 搜索论文（自包含命令）
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
DATA_DIR="$SKILL_DIR/data" && \
QUERY="attention mechanism ignore irrelevant context" && \
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&limit=10&fields=paperId,title,year,venue,citationCount,externalIds,abstract" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} | jq '.data[]? | {title, year, venue, citations: .citationCount, doi: .externalIds.DOI, abstract}'
```

```bash
# Step 2: 查询期刊质量（自包含命令）
source "$HOME/.claude/skills/citation-assistant/.env" && \
SKILL_DIR="$HOME/.claude/skills/citation-assistant" && \
sqlite3 "$SKILL_DIR/data/impact_factor.sqlite3" "SELECT journal, factor, jcr FROM factor WHERE journal LIKE '%Transactions%' LIMIT 5;"
```

```bash
# Step 3: 获取 BibTeX（无需初始化）
curl -sLH "Accept: text/bibliography; style=bibtex" "https://doi.org/10.1000/xyz123"
```

## 错误处理

### 429 Too Many Requests

如果 Semantic Scholar API 返回 429 错误，说明速率限制已触发。

**速率限制说明**：
- 有 API Key：1 次/秒（即每次请求后需等待 1 秒）
- 无 API Key：与所有无 Key 用户共享限额，极易触发 429

**处理策略**：

1. **等待后重试**（推荐等待 1-2 秒）：
```bash
sleep 2 && \
source "$HOME/.claude/skills/citation-assistant/.env" && \
QUERY="YOUR_QUERY" && \
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&limit=10&fields=paperId,title,year,venue,citationCount,externalIds,abstract" \
  ${S2_API_KEY:+-H "x-api-key: $S2_API_KEY"} | jq '.data[]?'
```

2. **使用 CrossRef 作为 Fallback**（无需 API Key，无严格速率限制）：
```bash
QUERY="medical imaging deep learning" && \
curl -s "https://api.crossref.org/works?query=$(printf '%s' "$QUERY" | jq -sRr @uri)&rows=10" | \
  jq '.message.items[] | {title: .title[0], year: (.["published-print"]["date-parts"][0][0] // .["published-online"]["date-parts"][0][0]), doi: .DOI, citations: .["is-referenced-by-count"]}'
```

**预防措施**：
- 避免短时间内连续发送多个请求
- 在多个搜索请求之间添加 `sleep 1` 间隔
- 优先使用 batch/bulk 端点（如 `/paper/search/bulk`）

### jq 解析错误

如果 jq 报错 `Cannot iterate over null`，说明 API 返回了错误响应而非预期数据。

**调试方法**：
```bash
# 先查看原始响应
curl -s "https://api.semanticscholar.org/graph/v1/paper/search?query=YOUR_QUERY&limit=5" | jq '.'
```

## 注意事项

1. **不自动修改文稿**：所有推荐需用户确认后再应用
2. **语义优先**：避免仅用关键词检索，理解引用意图
3. **质量把关**：综合多维度指标，不唯引用量论
4. **arXiv 审慎**：期刊投稿应控制 arXiv 引用比例
5. **速率限制**：有 API Key 时限制为 1 次/秒，连续请求需添加间隔；无 API Key 极易触发 429
