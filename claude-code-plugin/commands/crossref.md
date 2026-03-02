---
description: 使用 CrossRef API 搜索论文（作为 Semantic Scholar 的 fallback）
argument-hint: 搜索关键词
allowed-tools: Bash
---

# /citation:crossref

使用 CrossRef API 搜索学术论文。作为 Semantic Scholar API 不可用的 fallback 方案。

## 参数

**$ARGUMENTS**: 搜索查询语句

可选：使用 `--limit N` 指定返回数量（默认 20）

## 执行

```bash
QUERY="$ARGUMENTS"; \
LIMIT=$(echo "$QUERY" | grep -o -- '--limit [0-9]*' | awk '{print $2}' || echo "20"); \
QUERY=$(echo "$QUERY" | sed 's/ --limit [0-9]*//g'); \
ENCODED_QUERY=$(python3 -c "import urllib.parse; print(urllib.parse.quote('''$QUERY'''))" 2>/dev/null || echo "$QUERY"); \
curl -s "https://api.crossref.org/works?query=${ENCODED_QUERY}&rows=${LIMIT}&select=DOI,title,author,published-print,published-online,container-title,is-referenced-by-count" | \
python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('message', {}).get('items', [])
if not items:
    print('No results found')
    sys.exit(0)
for i, item in enumerate(items, 1):
    title = item.get('title', ['N/A'])[0] if item.get('title') else 'N/A'
    year = 'N/A'
    if item.get('published-print'):
        year = item['published-print'].get('date-parts', [[None]])[0][0]
    elif item.get('published-online'):
        year = item['published-online'].get('date-parts', [[None]])[0][0]
    venue = item.get('container-title', ['N/A'])[0] if item.get('container-title') else 'N/A'
    citations = item.get('is-referenced-by-count', 0)
    doi = item.get('DOI', 'N/A')
    authors = ', '.join([f\"{a.get('given', '')} {a.get('family', '')}\".strip()
                        for a in item.get('author', [])[:3]])
    if len(item.get('author', [])) > 3:
        authors += ' et al.'

    print(f\"{i}. {title}\")
    print(f\"   Year: {year} | Venue: {venue}\")
    print(f\"   Citations: {citations} | DOI: {doi}\")
    print(f\"   Authors: {authors}\")
    print()
"
```

## 说明

- CrossRef 是免费的学术文献数据库，无严格速率限制
- 与 Semantic Scholar 相比，缺少作者 h-index 等高级信息
- 当 `/citation:search` 遇到 429 错误时，会自动建议使用此命令

## 使用场景

```
# 当 Semantic Scholar API 受限时
/citation:search "attention mechanism"  # 可能返回 429
/citation:crossref "attention mechanism"  # 使用 fallback
```
