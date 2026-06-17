"""규칙 기반 지역/기관 추출 및 태깅.

주의: 개인 실명에 '부정/scam' 같은 단정 라벨을 붙이지 않는다.
태그는 기사/보고서 텍스트의 사실적 키워드에만 기반한다.
"""
from __future__ import annotations

from config import REGIONS, TAG_RULES


def extract_region(text: str) -> str:
    """텍스트에서 첫 번째로 등장하는 광역 시·도를 반환."""
    if not text:
        return ""
    for region in REGIONS:
        if region in text:
            return region
    return ""


def make_tags(text: str) -> list[str]:
    """텍스트에 포함된 키워드 규칙으로 태그 목록 생성."""
    if not text:
        return []
    tags = []
    for tag, keywords in TAG_RULES.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    return tags
