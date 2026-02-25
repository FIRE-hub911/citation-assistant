# CCF 分级数据使用指南

## 数据文件位置

CCF 分级数据已包含在本 skill 的 `data/` 目录中，无需额外下载。

## 可用格式

| 格式 | 文件 | 用途 |
|------|------|------|
| SQLite | `ccf_2022.sqlite` | 推荐，支持高效索引查询 |
| JSONL | `ccf_2022.jsonl` | 适合 Python 直接加载 |
| CSV | `ccf_2022.csv` | 适合 pandas 分析 |
| MD | `ccf_2022.md` | 人类可读参考 |

## 字段说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `year` | 版本年份 | 2022 |
| `type` | 类型 | journal / conference |
| `type_zh` | 类型(中文) | 期刊 / 会议 |
| `field` | CCF 领域 | 人工智能 |
| `rank` | CCF 等级 | A / B / C |
| `rank_zh` | 等级(中文) | A类 / B类 / C类 |
| `acronym` | 简称 | ICML, ACL |
| `acronym_alnum` | 简称(仅字母数字) | icml, acl |
| `name` | 全称 | International Conference on Machine Learning |
| `publisher` | 出版社 | ACM, IEEE |
| `url` | 官网链接 | https://icml.cc |

## 查询示例

### SQLite 查询

```sql
-- 按简称查询
SELECT * FROM ccf_2022 WHERE acronym_alnum = 'icml';

-- 按领域+等级查询
SELECT * FROM ccf_2022 WHERE field='人工智能' AND rank='A';

-- 模糊匹配
SELECT * FROM ccf_2022 WHERE name LIKE '%vision%';
```

### Python 查询

```python
import sqlite3
import pandas as pd

# 方式1：SQLite
conn = sqlite3.connect('ccf_2022.sqlite')
df = pd.read_sql("SELECT * FROM ccf_2022 WHERE acronym_alnum = 'icml'", conn)

# 方式2：JSONL
import json
data = [json.loads(line) for line in open('ccf_2022.jsonl')]
matches = [d for d in data if 'icml' in d.get('acronym_alnum', '')]
```

## CCF 领域列表

- 人工智能
- 计算机体系结构/并行与分布计算/存储系统
- 计算机网络
- 计算机图形学与多媒体
- 计算机安全
- 计算机软件工程/系统软件/程序设计语言
- 计算机应用技术
- 数据库/数据挖掘/内容检索
- 理论计算机科学

## 期刊/会议匹配策略

1. **精确匹配**: 使用 `acronym_alnum` 字段
2. **模糊匹配**: 使用 `LIKE` 或正则匹配 `name`
3. **别名处理**: 常见别名映射
   - `AAAI` → `AAAI Conference on Artificial Intelligence`
   - `NeurIPS` / `NIPS` → `Neural Information Processing Systems`
   - `CVPR` → `IEEE Conference on Computer Vision and Pattern Recognition`
   - `ACL` → `Annual Meeting of the Association for Computational Linguistics`
