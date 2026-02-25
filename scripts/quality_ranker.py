#!/usr/bin/env python3
"""
论文质量评估与排序模块
整合 CCF 分级、JCR 分区、中科院分区、IF、引用量等多维度指标
"""

import os
import json
import sqlite3
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from functools import lru_cache

# 技能根目录（相对于本脚本的位置）
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(SKILL_ROOT, 'data')

# CCF 数据文件路径
CCF_SQLITE = os.path.join(DATA_DIR, 'ccf_2022.sqlite')
CCF_JSONL = os.path.join(DATA_DIR, 'ccf_2022.jsonl')


@dataclass
class QualityMetrics:
    """论文质量指标"""
    # 基础信息
    title: str = ""
    year: int = 0
    venue: str = ""
    journal: str = ""

    # Semantic Scholar 指标
    citation_count: int = 0
    influential_citation_count: int = 0
    reference_count: int = 0

    # CCF 分级
    ccf_rank: Optional[str] = None  # A, B, C
    ccf_field: Optional[str] = None
    ccf_type: Optional[str] = None  # conference/journal

    # JCR 指标
    jcr_quartile: Optional[str] = None  # Q1, Q2, Q3, Q4
    impact_factor: Optional[float] = None

    # 中科院分区
    cas_quartile: Optional[str] = None  # 1区, 2区, 3区, 4区
    cas_category: Optional[str] = None

    # 作者影响力指标
    first_author_h_index: Optional[int] = None
    first_author_name: Optional[str] = None
    corresponding_author_h_index: Optional[int] = None
    corresponding_author_name: Optional[str] = None

    # 其他
    is_arxiv: bool = False
    has_published_version: bool = False

    # 计算得分
    score: float = 0.0


class CCFLookup:
    """CCF 分级查询"""

    def __init__(self, db_path: str = None, jsonl_path: str = None):
        """
        初始化 CCF 查询

        Args:
            db_path: SQLite 数据库路径，默认使用技能目录中的 ccf_2022.sqlite
            jsonl_path: JSONL 文件路径，默认使用技能目录中的 ccf_2022.jsonl
        """
        self.db_path = db_path or CCF_SQLITE
        self.jsonl_path = jsonl_path or CCF_JSONL
        self._data = None

        if self.db_path and os.path.exists(self.db_path):
            self._use_db = True
        elif self.jsonl_path and os.path.exists(self.jsonl_path):
            self._use_db = False
            self._load_jsonl()
        else:
            self._use_db = False
            self._data = []

    def _load_jsonl(self):
        """加载 JSONL 数据"""
        self._data = []
        with open(self.jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    self._data.append(json.loads(line))

    def lookup_by_venue(self, venue_name: str) -> Optional[Dict[str, Any]]:
        """
        根据期刊/会议名称查询 CCF 分级

        Args:
            venue_name: 期刊或会议名称

        Returns:
            CCF 信息字典，未找到返回 None
        """
        if not venue_name:
            return None

        # 处理 venue_name 可能是 dict 的情况
        if isinstance(venue_name, dict):
            venue_name = venue_name.get('name', '')
            if not venue_name:
                return None

        venue_lower = venue_name.lower()
        venue_alnum = re.sub(r'[^a-z0-9]', '', venue_lower)

        if self._use_db:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 尝试精确匹配简称
            cursor.execute(
                "SELECT * FROM ccf_2022 WHERE acronym_alnum = ?",
                (venue_alnum,)
            )
            result = cursor.fetchone()
            if result:
                conn.close()
                return self._row_to_dict(result, cursor)

            # 模糊匹配
            cursor.execute(
                "SELECT * FROM ccf_2022 WHERE acronym_alnum LIKE ? OR name LIKE ?",
                (f"%{venue_alnum}%", f"%{venue_lower}%")
            )
            result = cursor.fetchone()
            conn.close()
            if result:
                return self._row_to_dict(result, cursor)
        else:
            # JSONL 查询 - 优先精确匹配
            for item in self._data:
                if item.get('acronym_alnum') == venue_alnum:
                    return item

            # 其次模糊匹配
            for item in self._data:
                if venue_alnum in item.get('acronym_alnum', ''):
                    return item
                if venue_lower in item.get('name', '').lower():
                    return item

        return None

    def _row_to_dict(self, row, cursor) -> Dict[str, Any]:
        """将数据库行转为字典"""
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))


class ImpactFactorLookup:
    """影响因子查询（基于 impact_factor 库）"""

    def __init__(self):
        self._factor = None

    def _init_factor(self):
        """延迟初始化"""
        if self._factor is None:
            try:
                from impact_factor.core import Factor
                self._factor = Factor()
            except ImportError:
                self._factor = None

    def lookup(self, journal_name: str) -> Optional[Dict[str, Any]]:
        """
        查询期刊的影响因子和分区信息

        Args:
            journal_name: 期刊名称

        Returns:
            包含 IF、JCR 分区、中科院分区的字典
        """
        self._init_factor()

        if self._factor is None:
            return None

        try:
            result = self._factor.search(journal_name)
            if result:
                # result 是列表，取第一个匹配
                item = result[0] if isinstance(result, list) else result
                return {
                    'impact_factor': item.get('factor') or item.get('impact_factor'),
                    'jcr_quartile': item.get('jcr_quartile') or item.get('jcr'),
                    'cas_quartile': item.get('cas_quartile') or item.get('cas'),
                    'issn': item.get('issn'),
                }
        except Exception:
            pass

        return None


def calculate_quality_score(metrics: QualityMetrics) -> float:
    """
    计算综合质量得分

    评分逻辑：
    1. CCF 分级: A=100, B=70, C=40
    2. JCR 分区: Q1=80, Q2=60, Q3=40, Q4=20
    3. 中科院分区: 1区=90, 2区=70, 3区=50, 4区=30
    4. 影响因子: IF * 5 (上限50)
    5. 引用量: log10(citation_count + 1) * 10 (上限50)
    6. 年份新近度: max(0, (year - 2015) * 2) (上限30)
    7. 作者影响力: h-index * 0.5 (上限30)
    8. arXiv 惩罚: -20 (如有已发表版本则不惩罚)

    最终得分取各项最高分
    """
    import math
    score = 0.0

    # CCF 分级得分
    ccf_score = {
        'A': 100,
        'B': 70,
        'C': 40
    }.get(metrics.ccf_rank, 0)

    # JCR 分区得分
    jcr_score = {
        'Q1': 80,
        'Q2': 60,
        'Q3': 40,
        'Q4': 20
    }.get(metrics.jcr_quartile, 0)

    # 中科院分区得分
    cas_score = {
        '1区': 90,
        '2区': 70,
        '3区': 50,
        '4区': 30
    }.get(metrics.cas_quartile, 0)

    # IF 得分
    if_score = min(50, (metrics.impact_factor or 0) * 5)

    # 引用量得分（使用对数计算）
    citation_score = min(50, math.log10(metrics.citation_count + 1) * 10) if metrics.citation_count > 0 else 0

    # 年份得分（越新越好）
    year_score = min(30, max(0, (metrics.year - 2015) * 2)) if metrics.year else 0

    # 作者影响力得分（取第一作者和通讯作者的较大 h-index）
    max_h_index = max(
        metrics.first_author_h_index or 0,
        metrics.corresponding_author_h_index or 0
    )
    author_score = min(30, max_h_index * 0.5)

    # 综合得分：取各项最高分
    score = max(ccf_score, jcr_score, cas_score) + if_score * 0.3 + citation_score * 0.2 + year_score * 0.1 + author_score * 0.2

    # arXiv 处理
    if metrics.is_arxiv and not metrics.has_published_version:
        score -= 20

    return round(score, 2)


def rank_papers(
    papers: List[Dict[str, Any]],
    ccf_lookup: CCFLookup,
    if_lookup: ImpactFactorLookup,
    prefer_recent: bool = True,
    max_arxiv_ratio: float = 0.3
) -> List[Tuple[Dict[str, Any], QualityMetrics]]:
    """
    对论文列表进行质量排序

    Args:
        papers: 论文信息列表（来自 Semantic Scholar）
        ccf_lookup: CCF 查询实例
        if_lookup: 影响因子查询实例
        prefer_recent: 是否优先推荐近年论文
        max_arxiv_ratio: arXiv 论文的最大比例

    Returns:
        排序后的 (论文信息, 质量指标) 元组列表
    """
    results = []

    for paper in papers:
        metrics = QualityMetrics()

        # 基础信息 - 使用 or {} 确保 paper 不是 None
        paper = paper or {}
        metrics.title = paper.get('title', '') or ''
        metrics.year = paper.get('year') or 0

        # venue/journal 可能是 dict 或 string 或 None
        venue_val = paper.get('venue') or ''
        if isinstance(venue_val, dict):
            metrics.venue = venue_val.get('name', '') or ''
        else:
            metrics.venue = str(venue_val) if venue_val else ''

        journal_val = paper.get('journal') or ''
        if isinstance(journal_val, dict):
            metrics.journal = journal_val.get('name', '') or ''
        else:
            metrics.journal = str(journal_val) if journal_val else ''

        # Semantic Scholar 指标
        metrics.citation_count = paper.get('citationCount', 0)
        metrics.influential_citation_count = paper.get('influentialCitationCount', 0)
        metrics.reference_count = paper.get('referenceCount', 0)

        # CCF 查询（需要在 arXiv 判断之前）
        venue_to_check = metrics.journal or metrics.venue
        ccf_info = ccf_lookup.lookup_by_venue(venue_to_check)
        if ccf_info:
            metrics.ccf_rank = ccf_info.get('rank')
            metrics.ccf_field = ccf_info.get('field')
            metrics.ccf_type = ccf_info.get('type')

        # 判断是否为"纯 arXiv"（无正式发表版本）
        ext_ids = paper.get('externalIds') or {}
        venue_lower = (metrics.venue or '').lower()
        journal_lower = (metrics.journal or '').lower()

        # 如果 venue 是 arXiv 或无有效 venue，则为纯 arXiv
        # 但如果有 CCF 认证的 venue，则不算纯 arXiv
        if metrics.ccf_rank:
            # 已被 CCF 收录，不是纯 arXiv
            metrics.is_arxiv = False
        elif 'arxiv' in venue_lower or (not metrics.venue and not metrics.journal):
            metrics.is_arxiv = True
        else:
            metrics.is_arxiv = False

        # 影响因子查询
        journal_name = metrics.journal or metrics.venue
        if journal_name and not metrics.is_arxiv:
            if_info = if_lookup.lookup(journal_name)
            if if_info:
                metrics.impact_factor = if_info.get('impact_factor')
                metrics.jcr_quartile = if_info.get('jcr_quartile')
                metrics.cas_quartile = if_info.get('cas_quartile')

        # 计算得分
        metrics.score = calculate_quality_score(metrics)

        results.append((paper, metrics))

    # 按得分排序
    results.sort(key=lambda x: x[1].score, reverse=True)

    # 控制 arXiv 比例：在保持分数排序的前提下，限制 arXiv 数量
    if max_arxiv_ratio < 1.0:
        max_arxiv = max(1, int(len(results) * max_arxiv_ratio))
        arxiv_count = 0
        filtered_results = []

        for paper, metrics in results:
            if metrics.is_arxiv:
                if arxiv_count < max_arxiv:
                    filtered_results.append((paper, metrics))
                    arxiv_count += 1
                # else: 跳过超出配额的 arXiv 论文
            else:
                filtered_results.append((paper, metrics))

        results = filtered_results

    return results


if __name__ == "__main__":
    # 测试 - 使用默认路径（技能目录中的 data/）
    ccf = CCFLookup()  # 自动使用 data/ccf_2022.sqlite
    result = ccf.lookup_by_venue("TMI")
    print(f"TMI CCF: {result}")

    result = ccf.lookup_by_venue("ICML")
    print(f"ICML CCF: {result}")


# ============== 便捷函数 ==============
# 提供给 Claude 直接调用，避免动态生成复杂代码

def get_paper_quality_report(paper: Dict[str, Any]) -> Dict[str, Any]:
    """
    获取单篇论文的完整质量报告（便捷函数）

    Args:
        paper: 论文信息字典（来自 Semantic Scholar API）

    Returns:
        包含所有质量指标的字典，可直接用于生成报告
    """
    ccf_lookup = CCFLookup()
    if_lookup = ImpactFactorLookup()

    results = rank_papers([paper], ccf_lookup, if_lookup)
    if not results:
        return {"error": "Failed to evaluate paper"}

    _, metrics = results[0]

    return {
        "title": metrics.title,
        "year": metrics.year,
        "venue": metrics.venue,
        "journal": metrics.journal,
        "citation_count": metrics.citation_count,
        "ccf_rank": metrics.ccf_rank,
        "ccf_field": metrics.ccf_field,
        "jcr_quartile": metrics.jcr_quartile,
        "cas_quartile": metrics.cas_quartile,
        "impact_factor": metrics.impact_factor,
        "first_author": {
            "name": metrics.first_author_name,
            "h_index": metrics.first_author_h_index
        } if metrics.first_author_name else None,
        "corresponding_author": {
            "name": metrics.corresponding_author_name,
            "h_index": metrics.corresponding_author_h_index
        } if metrics.corresponding_author_name else None,
        "is_arxiv": metrics.is_arxiv,
        "quality_score": metrics.score
    }


def batch_quality_report(papers: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    批量获取论文质量报告（便捷函数）

    Args:
        papers: 论文列表（来自 Semantic Scholar API）
        top_n: 返回前 N 篇

    Returns:
        排序后的质量报告列表
    """
    ccf_lookup = CCFLookup()
    if_lookup = ImpactFactorLookup()

    results = rank_papers(papers, ccf_lookup, if_lookup)

    reports = []
    for paper, metrics in results[:top_n]:
        reports.append({
            "title": metrics.title,
            "year": metrics.year,
            "venue": metrics.venue or metrics.journal,
            "citation_count": metrics.citation_count,
            "ccf_rank": metrics.ccf_rank or "N/A",
            "jcr_quartile": metrics.jcr_quartile or "N/A",
            "cas_quartile": metrics.cas_quartile or "N/A",
            "impact_factor": metrics.impact_factor,
            "quality_score": metrics.score,
            "doi": paper.get("externalIds", {}).get("DOI"),
            "url": paper.get("url")
        })

    return reports
