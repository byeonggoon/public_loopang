"""네이버 뉴스 검색 API 수집기.

문서: https://developers.naver.com/docs/serviceapi/search/news/news.md
"""
from __future__ import annotations

from email.utils import parsedate_to_datetime

import requests

from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET, NEWS_DISPLAY, NEWS_KEYWORDS
from normalize import build_record

API_URL = "https://openapi.naver.com/v1/search/news.json"


def _parse_pubdate(value: str) -> str | None:
    """RFC 1123 형식(Mon, 16 Jun 2026 ...)을 ISO 문자열로."""
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return None


def fetch() -> list[dict]:
    """모든 키워드에 대해 뉴스 검색 후 공통 레코드 리스트 반환."""
    if not (NAVER_CLIENT_ID and NAVER_CLIENT_SECRET):
        print("[naver_news] 키 없음 — 건너뜀")
        return []

    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    records: list[dict] = []
    for keyword in NEWS_KEYWORDS:
        params = {"query": keyword, "display": NEWS_DISPLAY, "sort": "date"}
        try:
            resp = requests.get(API_URL, headers=headers, params=params, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[naver_news] '{keyword}' 요청 실패: {exc}")
            continue

        items = resp.json().get("items", [])
        for item in items:
            rec = build_record(
                source_type="news",
                source_name="네이버뉴스",
                title=item.get("title", ""),
                summary=item.get("description", ""),
                # 원문(originallink) 우선, 없으면 네이버 링크.
                url=item.get("originallink") or item.get("link", ""),
                published_at=_parse_pubdate(item.get("pubDate", "")),
                raw={"keyword": keyword, **item},
            )
            if rec:
                records.append(rec)
        print(f"[naver_news] '{keyword}': {len(items)}건")
    return records


if __name__ == "__main__":
    for r in fetch()[:3]:
        print(r["published_at"], r["title"])
