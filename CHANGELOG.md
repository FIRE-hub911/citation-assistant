# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.0.0] - 2025-03-02

### Added
- 新增 Plugin 架构版本，位于 `claude-code-plugin/` 目录
- 新增独立 Commands：`/citation:search`, `/citation:evaluate`, `/citation:bibtex`, `/citation:venue-info`, `/citation:parse`, `/citation:search-bulk`, `/citation:crossref`
- 支持通过 Marketplace 安装：`/plugin marketplace add ZhangNy301/citation-assistant`
- 保留原有 Skill 版本在根目录，确保向后兼容

### Changed
- 项目结构重组：根目录保留 Skill 版本，新增 `claude-code-plugin/` 子目录存放 Plugin 版本
- 更新 README，详细说明两种使用方式

### Compatibility
- ✅ Skill 版本（根目录 SKILL.md）：兼容 Claude Code, Cursor 等平台
- ✅ Plugin 版本（claude-code-plugin/）：仅适用于 Claude Code CLI

## [1.0.0] - 2025-02-XX

### Added
- 初始版本发布
- 单一 Skill 架构（`SKILL.md`）
- 零依赖设计：仅需 curl + sqlite3 + jq
- 支持语义化文献搜索
- 支持 CCF/JCR/中科院分区/影响因子多维度评估
- 支持 BibTeX 生成
- 中文推荐报告输出

### Features
- `[CITE]` 占位符解析
- Semantic Scholar API 集成
- 期刊信息查询
- LaTeX 上下文理解
