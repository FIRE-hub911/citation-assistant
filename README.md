# Citation Assistant 学术文献引用助手

> Claude Code Skill/Plugin for automated LaTeX academic citation workflow

基于 Semantic Scholar API 的语义化文献检索，整合 CCF 分级、JCR 分区、中科院分区、影响因子等多维度质量评估，生成 BibTeX 并提供清晰的中文推荐说明。

---

## 📦 两种使用方式

本仓库提供两种使用方式，请根据你的需求选择：

| 使用方式 | 适用平台 | 特点 | 安装难度 |
|---------|---------|------|---------|
| **方式一：Skill（零依赖）** | Claude Code, Cursor, 其他平台 | 单一文件，复制即用 | ⭐ 最简单 |
| **方式二：Plugin（全功能）** | Claude Code 专用 | Commands + Skills 分层，功能更强大 | ⭐⭐ 简单 |

---

## 方式一：Skill 版本（推荐跨平台用户）

**特点**：零依赖，仅需 `curl` + `sqlite3` + `jq`（系统自带或常见工具）

**适用场景**：
- 使用 Cursor 等其他 AI 编辑器
- 希望最简单快速的安装
- 不需要独立的 Command 功能

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/ZhangNy301/citation-assistant.git

# 方式 A：复制到 Claude Code Skills 目录（推荐）
cp citation-assistant/SKILL.md ~/.claude/skills/
cp -r citation-assistant/data ~/.claude/skills/

# 方式 B：直接在仓库目录使用
# 进入仓库目录后，Claude Code 会自动识别 SKILL.md
```

### 使用方法

1. **触发 Skill**：输入 `/citation-assistant` 或提及"文献引用"、"找引用"
2. **粘贴 LaTeX 段落**：包含 `[CITE]` 占位符的文本
3. **查询期刊信息**：如"TMI 是什么期刊？质量怎么样？"

---

## 方式二：Plugin 版本（推荐 Claude Code 用户）

**特点**：分层架构，Commands 可独立调用，更稳定可预测

**适用场景**：
- 使用 Claude Code CLI
- 希望使用独立的 Commands（如 `/citation:search`）
- 需要更结构化的工作流

### 安装步骤

```bash
# 1. 添加 Marketplace（只需要做一次）
/plugin marketplace add ZhangNy301/citation-assistant

# 2. 安装 Plugin
/plugin install citation-assistant@ZhangNy301/citation-assistant

# 3. 重启 Claude Code 生效
```

### 可用 Commands

| Command | 功能 | 示例 |
|---------|------|------|
| `/citation:search` | 语义搜索文献 | `/citation:search "attention mechanism"` |
| `/citation:search-bulk` | 批量搜索 | `/citation:search-bulk "transformer" --limit 50` |
| `/citation:evaluate` | 质量评估 | `/citation:evaluate "ICML"` |
| `/citation:bibtex` | 获取 BibTeX | `/citation:bibtex 10.1148/radiol.2020191075` |
| `/citation:venue-info` | 查询期刊信息 | `/citation:venue-info TMI` |
| `/citation:parse` | 解析占位符 | `/citation:parse "text with [CITE]"` |

### 使用 Skill 工作流

输入包含 `[CITE]` 占位符的文本，自动触发完整工作流：

```
End-to-end deep learning has revolutionized medical image analysis [CITE].
```

Skill 将自动：
1. 解析 `[CITE]` 占位符
2. 构造语义查询
3. 搜索 Semantic Scholar
4. 多维度质量排序
5. 生成 BibTeX
6. 输出中文推荐报告

---

## 📁 文件结构

```
citation-assistant/
├── README.md              # 本文件
├── SKILL.md               # 🎯 Skill 版本（零依赖，跨平台）
├── data/                  # 📦 共享数据
│   ├── ccf_2022.sqlite       # CCF 分级数据库
│   └── ccf_2022.jsonl
├── references/            # 📚 参考文档
│   ├── ccf_guide.md
│   └── quality_metrics.md
│
└── claude-code-plugin/    # 🚀 Plugin 版本（Claude Code 专用）
    ├── .claude-plugin/
    │   └── plugin.json
    ├── commands/             # 独立 Commands
    ├── skills/               # Plugin 内的 Skills
    └── scripts/              # Python 脚本
```

---

## ⚙️ 配置（两种方式通用）

### Semantic Scholar API Key（推荐）

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 填入你的 API Key
# 获取地址：https://www.semanticscholar.org/product/api-api-key
```

| 模式 | 速率限制 |
|------|----------|
| 有 API Key | 100 次/分钟 |
| 无 API Key | 10 次/分钟 |

---

## 🔀 版本对比

| 特性 | Skill 版本 | Plugin 版本 |
|------|-----------|------------|
| **安装方式** | 复制文件 | `/plugin install` |
| **跨平台** | ✅ Cursor 等可用 | ❌ 仅 Claude Code |
| **独立 Commands** | ❌ | ✅ `/citation:search` 等 |
| **Skill 触发** | ✅ | ✅ |
| **依赖** | curl/sqlite3/jq | 同上 |
| **维护状态** | ✅ 稳定维护 | ✅ 持续更新 |

---

## 📜 版本历史

- **v2.0.0** (当前) - 新增 Plugin 架构，保留 Skill 兼容
- **v1.0.0** - 初始版本，单一 Skill 架构

---

## 🙏 致谢

- [Semantic Scholar](https://www.semanticscholar.org/) - Academic paper search API
- [impact_factor](https://github.com/suqingdong/impact_factor) - Journal impact factor database
- [CrossRef](https://www.crossref.org/) - DOI metadata API

## License

MIT
