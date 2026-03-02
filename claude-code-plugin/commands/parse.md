---
description: 解析 LaTeX 文本中的 [CITE] 占位符
argument-hint: 包含 [CITE] 的文本或文件路径
allowed-tools: Read, Bash
---

# /citation:parse

从 LaTeX 文本中提取 [CITE] 占位符及其上下文信息。

## 参数

**$ARGUMENTS**:
- 包含 [CITE] 的文本内容，或
- `.tex` 文件路径（将自动读取文件）

支持格式：
- `[CITE]` - 基本占位符
- `[CITE:描述]` - 带描述的占位符

## 执行

```python
import re
import sys

input_text = '''$ARGUMENTS'''

# 检查是否为文件路径
if input_text.strip().endswith('.tex') and len(input_text.split()) == 1:
    try:
        with open(input_text.strip(), 'r') as f:
            text = f.read()
        print(f"已读取文件: {input_text.strip()}")
    except FileNotFoundError:
        text = input_text
except:
    text = input_text

lines = text.split('\n')
pattern = re.compile(r'\[CITE(?::([^\]]+))?\]', re.IGNORECASE)
placeholders = []

for line_idx, line in enumerate(lines):
    for match in pattern.finditer(line):
        marker = match.group(0)
        description = match.group(1)
        col = match.start()

        # 构造查询文本（移除 LaTeX 命令）
        query_text = line
        query_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', query_text)
        query_text = re.sub(r'\\[a-zA-Z]+', '', query_text)
        query_text = re.sub(r'[{}$~\\]', ' ', query_text)
        query_text = re.sub(r'\[CITE(?::[^\]]+)?\]', '', query_text, flags=re.IGNORECASE)
        query_text = re.sub(r'\s+', ' ', query_text).strip()

        placeholders.append({
            'line': line_idx + 1,
            'column': col,
            'marker': marker,
            'description': description,
            'context_before': line[:col].strip()[-50:] if col > 0 else '',
            'context_after': line[match.end():].strip()[:50] if match.end() < len(line) else '',
            'suggested_query': query_text
        })

if not placeholders:
    print("未找到 [CITE] 占位符")
else:
    print(f"找到 {len(placeholders)} 个 [CITE] 占位符:\n")
    for i, p in enumerate(placeholders, 1):
        print(f"[{i}] 第 {p['line']} 行, 第 {p['column']} 列")
        print(f"    标记: {p['marker']}")
        if p['description']:
            print(f"    描述: {p['description']}")
        print(f"    上下文: ...{p['context_before']}[CITE]{p['context_after']}...")
        print(f"    建议查询: {p['suggested_query'][:80]}...")
        print()
```

## 输出示例

```
找到 2 个 [CITE] 占位符:

[1] 第 5 行, 第 45 列
    标记: [CITE]
    上下文: ...chest radiography---arguably the most widely used imaging test globally [CITE]---...
    建议查询: chest radiography arguably the most widely used imaging test globally ...

[2] 第 8 行, 第 32 列
    标记: [CITE:transformer]
    描述: transformer
    上下文: ...attention mechanism was introduced in [CITE:transformer] for neural machine...
    建议查询: attention mechanism was introduced in for neural machine ...
```

## 使用场景

```
# 直接粘贴文本
/citation:parse "In chest radiography [CITE], deep learning..."

# 读取 .tex 文件
/citation:parse /path/to/paper.tex
```
