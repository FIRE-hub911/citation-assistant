#!/usr/bin/env python3
"""
Semantic Scholar API 搜索封装
用于根据语义查询搜索学术论文，以及获取作者信息
"""

import os
import requests
import json
from typing import Optional, List, Dict, Any
from urllib.parse import quote
from pathlib import Path

# 自动加载 .env 文件
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# API 配置
# 优先从环境变量读取，如果没有则使用 None（匿名请求，速率限制更严格）
# 用户可通过 export S2_API_KEY=your_key 或 .env 文件配置
API_KEY: Optional[str] = os.environ.get("S2_API_KEY")
BASE_URL = "https://api.semanticscholar.org/graph/v1"


def check_api_key() -> tuple[bool, str]:
    """
    检查 API Key 配置状态

    Returns:
        (is_configured, message): 是否已配置及提示信息
    """
    if API_KEY:
        return True, "API Key 已配置"
    else:
        return False, (
            "警告：未配置 Semantic Scholar API Key。"
            "匿名请求速率限制为 10 次/分钟。"
            "请设置环境变量 S2_API_KEY 或创建 .env 文件。"
            "获取 Key: https://www.semanticscholar.org/product/api/api-key"
        )

# 默认返回字段
DEFAULT_FIELDS = [
    "paperId", "title", "abstract", "year", "authors",
    "venue", "journal", "citationCount", "referenceCount",
    "influentialCitationCount", "isOpenAccess", "openAccessPdf",
    "externalIds", "url", "publicationDate", "publicationTypes",
    "publicationVenue", "fieldsOfStudy"
]

# 作者信息默认字段
DEFAULT_AUTHOR_FIELDS = [
    "authorId", "name", "url", "hIndex", "citationCount",
    "paperCount", "affiliations"
]


def search_papers(
    query: str,
    limit: int = 20,
    year_range: Optional[str] = None,
    venue: Optional[str] = None,
    fields: Optional[List[str]] = None,
    bulk: bool = False
) -> Dict[str, Any]:
    """
    搜索论文

    Args:
        query: 搜索查询（语义化描述）
        limit: 返回结果数量限制
        year_range: 年份范围，如 "2010-2024" 或 "2020-"
        venue: 期刊/会议名称
        fields: 需要返回的字段列表
        bulk: 是否使用 bulk search endpoint（适合大批量查询）

    Returns:
        API 响应字典
    """
    if fields is None:
        fields = DEFAULT_FIELDS

    endpoint = "/paper/search/bulk" if bulk else "/paper/search"
    url = f"{BASE_URL}{endpoint}"

    params = {
        "query": query,
        "limit": limit,
        "fields": ",".join(fields)
    }

    if year_range:
        params["year"] = year_range
    if venue:
        params["venue"] = venue

    headers = {"x-api-key": API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "data": None}


def get_paper_details(
    paper_id: str,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    获取单篇论文详情

    Args:
        paper_id: 论文ID（Semantic Scholar ID、DOI、或 CorpusID）
        fields: 需要返回的字段列表

    Returns:
        论文详情字典
    """
    if fields is None:
        fields = DEFAULT_FIELDS + ["citations", "references"]

    url = f"{BASE_URL}/paper/{paper_id}"
    params = {"fields": ",".join(fields)}
    headers = {"x-api-key": API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "data": None}


def batch_get_papers(
    paper_ids: List[str],
    fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    批量获取论文详情

    Args:
        paper_ids: 论文ID列表
        fields: 需要返回的字段列表

    Returns:
        论文详情列表
    """
    if fields is None:
        fields = DEFAULT_FIELDS

    url = f"{BASE_URL}/paper/batch"
    params = {"fields": ",".join(fields)}
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            json={"ids": paper_ids},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]


def find_published_version(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """
    查找 arXiv 论文的已发表版本

    Args:
        arxiv_id: arXiv ID（如 "2301.12345" 或 "2023.12345"）

    Returns:
        已发表版本的论文信息，如果没有则返回 None
    """
    # 首先获取 arXiv 论文信息
    s2_id = f"ARXIV:{arxiv_id}"
    paper = get_paper_details(s2_id, fields=["title", "authors", "year", "venue", "journal", "externalIds"])

    if "error" in paper:
        return None

    # 检查是否已有 venue 或 journal
    if paper.get("venue") or paper.get("journal"):
        # 过滤掉 venue 为 "arXiv" 的情况
        venue = paper.get("venue", "").lower()
        if "arxiv" not in venue:
            return paper

    # 用标题搜索可能的已发表版本
    if paper.get("title"):
        results = search_papers(
            query=paper["title"],
            limit=10,
            fields=["title", "year", "venue", "journal", "externalIds", "citationCount"]
        )

        if results.get("data"):
            for result in results["data"]:
                # 跳过 arXiv 版本
                ext_ids = result.get("externalIds", {})
                if ext_ids.get("ArXiv") == arxiv_id:
                    continue
                # 检查标题相似度
                if result.get("venue") and "arxiv" not in result["venue"].lower():
                    return result

    return None


def get_author_info(
    author_id: str,
    fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    获取单个作者的信息

    Args:
        author_id: 作者ID（Semantic Scholar Author ID）
        fields: 需要返回的字段列表，默认包含 name, hIndex, citationCount, paperCount

    Returns:
        作者信息字典
    """
    if fields is None:
        fields = DEFAULT_AUTHOR_FIELDS

    url = f"{BASE_URL}/author/{author_id}"
    params = {"fields": ",".join(fields)}
    headers = {"x-api-key": API_KEY}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "data": None}


def batch_get_authors(
    author_ids: List[str],
    fields: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    批量获取作者信息

    Args:
        author_ids: 作者ID列表
        fields: 需要返回的字段列表，默认包含 name, hIndex, citationCount, paperCount

    Returns:
        作者信息列表
    """
    if fields is None:
        fields = DEFAULT_AUTHOR_FIELDS

    url = f"{BASE_URL}/author/batch"
    params = {"fields": ",".join(fields)}
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            url,
            params=params,
            headers=headers,
            json={"ids": author_ids},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]


def get_paper_author_impact(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取论文作者的影响力信息（第一作者和通讯作者）

    Args:
        paper: 论文信息字典，需包含 authors 字段

    Returns:
        包含第一作者和通讯作者影响力的字典
    """
    authors = paper.get("authors", [])
    if not authors:
        return {"first_author": None, "corresponding_author": None}

    result = {"first_author": None, "corresponding_author": None}

    # 获取第一作者信息
    if len(authors) > 0:
        first_author_id = authors[0].get("authorId")
        if first_author_id:
            first_author_info = get_author_info(first_author_id)
            if "error" not in first_author_info:
                result["first_author"] = {
                    "name": first_author_info.get("name"),
                    "hIndex": first_author_info.get("hIndex"),
                    "citationCount": first_author_info.get("citationCount"),
                    "paperCount": first_author_info.get("paperCount")
                }

    # 注意：Semantic Scholar API 不直接提供通讯作者信息
    # 最后一个作者通常可能是通讯作者（在某些领域惯例中）
    if len(authors) > 1:
        last_author_id = authors[-1].get("authorId")
        if last_author_id:
            last_author_info = get_author_info(last_author_id)
            if "error" not in last_author_info:
                result["corresponding_author"] = {
                    "name": last_author_info.get("name"),
                    "hIndex": last_author_info.get("hIndex"),
                    "citationCount": last_author_info.get("citationCount"),
                    "paperCount": last_author_info.get("paperCount")
                }

    return result


if __name__ == "__main__":
    # 测试搜索
    results = search_papers(
        query="chest radiography most widely used imaging test globally",
        limit=5
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))
