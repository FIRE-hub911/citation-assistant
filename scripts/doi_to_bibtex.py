#!/usr/bin/env python3
"""
DOI 内容协商 API 封装
用于从 DOI 获取标准 BibTeX 格式
"""

import requests
import re
from typing import Optional, Dict, Any


def doi_to_bibtex(doi: str) -> Optional[str]:
    """
    通过 DOI 内容协商 API 获取 BibTeX 格式

    Args:
        doi: DOI 字符串（如 "10.18653/v1/2020.acl-main.447"）

    Returns:
        BibTeX 字符串，失败返回 None
    """
    if not doi:
        return None

    # 清理 DOI
    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")
    if doi.startswith("http://doi.org/"):
        doi = doi.replace("http://doi.org/", "")

    url = f"https://doi.org/{doi}"
    headers = {
        "Accept": "text/bibliography; style=bibtex"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text.strip()
        return None
    except requests.exceptions.RequestException:
        return None


def get_metadata_json(doi: str) -> Optional[Dict[str, Any]]:
    """
    获取 DOI 的 CSL-JSON 元数据

    Args:
        doi: DOI 字符串

    Returns:
        元数据字典，失败返回 None
    """
    if not doi:
        return None

    doi = doi.strip()
    if doi.startswith("https://doi.org/"):
        doi = doi.replace("https://doi.org/", "")

    url = f"https://doi.org/{doi}"
    headers = {
        "Accept": "application/vnd.citationstyles.csl+json"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def generate_cite_key(bibtex: str, existing_keys: set = None) -> str:
    """
    从 BibTeX 生成引用 key

    Args:
        bibtex: BibTeX 字符串
        existing_keys: 已存在的 key 集合，用于避免重复

    Returns:
        cite key 字符串
    """
    if existing_keys is None:
        existing_keys = set()

    # 提取原始 key
    match = re.match(r'@\w+\{([^,]+),', bibtex)
    if not match:
        return "unknown_key"

    original_key = match.group(1)

    # 如果 key 不冲突，直接返回
    if original_key not in existing_keys:
        return original_key

    # 处理冲突：添加后缀
    base_key = original_key
    counter = ord('a')
    while f"{base_key}{chr(counter)}" in existing_keys:
        counter += 1
        if counter > ord('z'):
            base_key = f"{original_key}_{counter - ord('a')}"
            counter = ord('a')

    return f"{base_key}{chr(counter)}"


def update_bibtex_key(bibtex: str, new_key: str) -> str:
    """
    更新 BibTeX 中的引用 key

    Args:
        bibtex: 原始 BibTeX 字符串
        new_key: 新的引用 key

    Returns:
        更新后的 BibTeX 字符串
    """
    return re.sub(r'(@\w+)\{[^,]+,', f'\\1{{{new_key},', bibtex, count=1)


def clean_bibtex(bibtex: str) -> str:
    """
    清理和规范化 BibTeX 格式

    Args:
        bibtex: 原始 BibTeX 字符串

    Returns:
        清理后的 BibTeX 字符串
    """
    # 移除多余的空行
    bibtex = re.sub(r'\n{3,}', '\n\n', bibtex)
    # 确保结尾只有一个换行
    bibtex = bibtex.strip() + '\n'
    return bibtex


if __name__ == "__main__":
    # 测试
    test_doi = "10.18653/v1/2020.acl-main.447"
    bibtex = doi_to_bibtex(test_doi)
    if bibtex:
        print("=== BibTeX ===")
        print(bibtex)
        print("\n=== Cite Key ===")
        print(generate_cite_key(bibtex))
    else:
        print(f"Failed to get BibTeX for DOI: {test_doi}")
