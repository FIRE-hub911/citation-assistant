# Citation Assistant

> Claude Code Skill for automated LaTeX academic citation workflow

基于 Semantic Scholar API 的语义化文献检索，整合 CCF 分级、JCR 分区、中科院分区、影响因子、作者学术影响力等多维度质量评估，生成 BibTeX 并提供清晰的中文推荐说明。

## Features

- **Semantic Search** - 基于语义理解而非仅关键词的文献检索
- **Multi-dimensional Ranking** - CCF/JCR/中科院分区/IF/引用量/作者 h-index 综合评分
- **BibTeX Generation** - 通过 DOI 自动生成标准 BibTeX
- **Chinese Reports** - 生成清晰的中文推荐报告

## Quick Start

在 Claude Code 中运行：

```
帮我根据 https://github.com/ZhangNy301/citation-assistant/blob/main/install.md 安装这个 skill
```

或者手动安装：

```bash
git clone https://github.com/ZhangNy301/citation-assistant.git ~/.claude/skills/citation-assistant
cp ~/.claude/skills/citation-assistant/.env.example ~/.claude/skills/citation-assistant/.env
pip install python-dotenv requests impact_factor
```

## API Key Configuration (Required)

Semantic Scholar API Key 是免费的，申请步骤：

1. 访问 https://www.semanticscholar.org/product/api
2. 滚动到页面底部，填写 **API Key 申请表**（api-key-form）
3. 提交后，API Key 会通过邮件发送给你

配置方式：

```bash
# 编辑 .env 文件
nano ~/.claude/skills/citation-assistant/.env

# 填入你的 API Key
S2_API_KEY=your_key_here
```

**注意**：不配置 API Key 也可以使用（匿名模式，速率限制 10 次/分钟）

## Usage

### 方式 1：直接触发

在 Claude Code 中输入 `/citation-assistant` 或提及"文献引用"、"找引用"等关键词

### 方式 2：粘贴 LaTeX 段落

```
End-to-end deep learning has revolutionized medical image analysis [CITE].
Vision-language models now generate radiologist-quality reports [CITE].
```

### 方式 3：查询期刊信息

```
TMI 是什么期刊？质量怎么样？
```

## Requirements

- Python 3.8+
- Claude Code CLI

## Files

```
citation-assistant/
├── SKILL.md           # Skill 定义（Claude Code 读取）
├── install.md         # Agent 安装指令
├── .env.example       # API Key 配置模板
├── requirements.txt   # Python 依赖
├── data/
│   ├── ccf_2022.sqlite   # CCF 分级数据库
│   └── ccf_2022.jsonl    # CCF 分级数据
├── scripts/
│   ├── s2_search.py      # Semantic Scholar API
│   ├── quality_ranker.py # 质量评估排序
│   ├── doi_to_bibtex.py  # DOI 转 BibTeX
│   └── tex_parser.py     # LaTeX 占位符解析
└── references/
    ├── ccf_guide.md      # CCF 使用指南
    └── quality_metrics.md # 质量指标说明
```

## License

MIT
