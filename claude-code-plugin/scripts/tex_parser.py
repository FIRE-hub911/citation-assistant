#!/usr/bin/env python3
"""
LaTeX 文件解析模块
提取 [CITE] 占位符及其上下文
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CitationPlaceholder:
    """引用占位符"""
    line_number: int
    column: int
    context_before: str  # 占位符前的上下文
    context_after: str   # 占位符后的上下文
    full_sentence: str   # 完整句子
    surrounding_paragraph: str  # 周围段落
    original_marker: str  # 原始标记（如 [CITE] 或 [CITE:description]）


def extract_cite_placeholders(text: str) -> List[CitationPlaceholder]:
    """
    从文本中提取所有 [CITE] 占位符

    支持：
    - [CITE] - 基本占位符
    - [CITE:描述] - 带描述的占位符
    - [CITE?key1=val1&key2=val2] - 带参数的占位符

    Args:
        text: 输入文本（可以是完整 .tex 文件或段落）

    Returns:
        CitationPlaceholder 列表
    """
    placeholders = []
    lines = text.split('\n')

    # 更灵活的正则：支持各种 [CITE] 变体
    pattern = re.compile(r'\[CITE(?::([^\]]+))?\]', re.IGNORECASE)

    for line_idx, line in enumerate(lines):
        for match in pattern.finditer(line):
            marker = match.group(0)
            description = match.group(1)  # 可能为 None

            # 获取上下文
            col = match.start()

            # 完整句子（向前向后扩展直到句号）
            sentence_start, sentence_end = find_sentence_bounds(text, line_idx, col, match.end())

            # 段落上下文
            para_start, para_end = find_paragraph_bounds(text, line_idx)

            placeholders.append(CitationPlaceholder(
                line_number=line_idx + 1,
                column=col,
                context_before=line[:col].strip()[-100:] if col > 0 else "",
                context_after=line[match.end():].strip()[:100] if match.end() < len(line) else "",
                full_sentence=text[sentence_start:sentence_end].strip(),
                surrounding_paragraph=text[para_start:para_end].strip(),
                original_marker=marker
            ))

    return placeholders


def find_sentence_bounds(text: str, line_idx: int, col_start: int, col_end: int) -> Tuple[int, int]:
    """
    找到包含指定位置的完整句子边界

    Args:
        text: 完整文本
        line_idx: 行索引
        col_start: 起始列
        col_end: 结束列

    Returns:
        (start_pos, end_pos) 句子在全文中的位置
    """
    lines = text.split('\n')

    # 计算绝对位置
    abs_start = sum(len(lines[i]) + 1 for i in range(line_idx)) + col_start
    abs_end = sum(len(lines[i]) + 1 for i in range(line_idx)) + col_end

    # 向前找句子开始
    search_start = max(0, abs_start - 500)
    prefix = text[search_start:abs_start]

    # 查找最近的句末标记
    sentence_start_markers = list(re.finditer(r'[.!?。！？]\s+', prefix))
    if sentence_start_markers:
        sentence_start = search_start + sentence_start_markers[-1].end()
    else:
        sentence_start = search_start

    # 向后找句子结束
    search_end = min(len(text), abs_end + 500)
    suffix = text[abs_end:search_end]

    sentence_end_match = re.search(r'[.!?。！？]\s+', suffix)
    if sentence_end_match:
        sentence_end = abs_end + sentence_end_match.end()
    else:
        sentence_end = search_end

    return sentence_start, sentence_end


def find_paragraph_bounds(text: str, line_idx: int) -> Tuple[int, int]:
    """
    找到包含指定行的段落边界

    Args:
        text: 完整文本
        line_idx: 行索引

    Returns:
        (start_pos, end_pos) 段落在全文中的位置
    """
    lines = text.split('\n')

    # 向前找段落开始（空行）
    para_start_line = line_idx
    while para_start_line > 0 and lines[para_start_line - 1].strip():
        para_start_line -= 1

    # 向后找段落结束
    para_end_line = line_idx
    while para_end_line < len(lines) - 1 and lines[para_end_line + 1].strip():
        para_end_line += 1

    # 计算绝对位置
    start_pos = sum(len(lines[i]) + 1 for i in range(para_start_line))
    end_pos = sum(len(lines[i]) + 1 for i in range(para_end_line + 1))

    return start_pos, end_pos


def construct_search_query(placeholder: CitationPlaceholder) -> str:
    """
    根据占位符上下文构造语义化搜索查询

    Args:
        placeholder: 引用占位符实例

    Returns:
        搜索查询字符串
    """
    # 优先使用完整句子
    query_text = placeholder.full_sentence

    # 移除 LaTeX 命令
    query_text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', query_text)
    query_text = re.sub(r'\\[a-zA-Z]+', '', query_text)
    query_text = re.sub(r'[{}$~\\]', ' ', query_text)

    # 移除占位符本身
    query_text = re.sub(r'\[CITE(?::[^\]]+)?\]', '', query_text, flags=re.IGNORECASE)

    # 清理多余空白
    query_text = re.sub(r'\s+', ' ', query_text).strip()

    # 如果句子太短，使用段落上下文
    if len(query_text.split()) < 10:
        para = placeholder.surrounding_paragraph
        para = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', para)
        para = re.sub(r'\\[a-zA-Z]+', '', para)
        para = re.sub(r'[{}$~\\]', ' ', para)
        para = re.sub(r'\[CITE(?::[^\]]+)?\]', '', para, flags=re.IGNORECASE)
        query_text = para.strip()

    return query_text


if __name__ == "__main__":
    # 测试
    test_text = """
    End-to-end deep learning has revolutionized medical image analysis, achieving expert-level performance in diagnostic tasks ranging from diabetic retinopathy detection to skin cancer classification.

    In chest radiography---arguably the most widely used imaging test globally [CITE]---vision--language models (VLMs) now generate radiologist-quality reports by mapping pixels directly to free-text narratives.
    """

    placeholders = extract_cite_placeholders(test_text)
    for p in placeholders:
        print(f"Line {p.line_number}: {p.original_marker}")
        print(f"  Context: {p.context_before}...{p.context_after}")
        print(f"  Query: {construct_search_query(p)}")
        print()
