"""소스별 원본 데이터를 공통 records 스키마로 변환 + 중복 제거."""
from __future__ import annotations

import re
from html import unescape

from classify import extract_region, make_tags

_TAG_RE = re.compile(r"<[^>]+>")


def clean(text: str) -> str:
    """HTML 태그/엔티티 제거 후 공백 정리."""
    if not text:
        return ""
    return _TAG_RE.sub("", unescape(text)).strip()


def build_record(
    *,
    source_type: str,
    source_name: str,
    title: str,
    summary: str,
    url: str,
    published_at: str | None,
    agency: str = "",
    raw: dict | None = None,
    people_count: int | None = None,
    countries: str = "",
    trip_start: str | None = None,
    trip_end: str | None = None,
    cost_total: int | None = None,
    cost_breakdown: dict | None = None,
) -> dict | None:
    """공통 스키마 dict 생성. title/url 없으면 None.

    출장 상세(people_count 등)는 BTIS 보고서에만 채워지고, 그 외 소스는 기본값.
    모든 레코드가 동일한 키를 갖도록 해 Supabase 일괄 upsert 키 불일치를 방지한다.
    """
    title = clean(title)
    url = (url or "").strip()
    if not title or not url:
        return None
    summary = clean(summary)
    blob = f"{title} {summary} {agency} {countries}"
    return {
        "source_type": source_type,
        "source_name": source_name,
        "title": title,
        "summary": summary,
        "url": url,
        "published_at": published_at,
        "agency": agency.strip(),
        "region": extract_region(blob),
        "tags": make_tags(blob),
        "people_count": people_count,
        "countries": countries.strip(),
        "trip_start": trip_start,
        "trip_end": trip_end,
        "cost_total": cost_total,
        "cost_breakdown": cost_breakdown or {},
        "raw": raw or {},
    }


def dedupe(records: list[dict]) -> list[dict]:
    """url 기준 중복 제거 (먼저 등장한 레코드 우선)."""
    seen: set[str] = set()
    out: list[dict] = []
    for rec in records:
        if not rec:
            continue
        url = rec["url"]
        if url in seen:
            continue
        seen.add(url)
        out.append(rec)
    return out


_KEY_RE = re.compile(r"[^0-9a-z가-힣]")


def _title_key(title: str) -> str:
    """제목을 정규화한 비교 키 (공백·기호·대소문자 무시, 앞 40자)."""
    return _KEY_RE.sub("", title.lower())[:40]


def dedupe_news_by_title(records: list[dict]) -> list[dict]:
    """뉴스의 near-중복(같은 기사가 여러 매체로 재게재) 제거.

    정규화된 제목이 같으면 한 건만 유지. 정부보고서는 동명(예: '학술대회 참석')이
    많아 서로 다른 출장이므로 제외하고 url 기준만 따른다.
    """
    seen: set[str] = set()
    out: list[dict] = []
    for rec in records:
        if rec.get("source_type") == "news":
            key = _title_key(rec["title"])
            if key and key in seen:
                continue
            seen.add(key)
        out.append(rec)
    return out
