"""중앙선거관리위원회(선관위) 공무국외출장보고서 수집기.

선관위는 헌법기관이라 BTIS(인사혁신처)에 등록하지 않고 자체 사이트에 공개한다.
게시판: https://www.nec.go.kr/site/nec/ex/bbs/List.do?cbIdx=1107  (총 ~60여건)

구조 (ul > li):
  span.title a[href=View.do?cbIdx=1107&bcIdx=..] -> 제목 + 상세 idx
  span.fileDown a[href=/common/board/Download.do..pdf] -> PDF
  span.date -> 날짜

정책: PDF 본문 미복제. 제목·날짜 + 상세/PDF 링크만 저장.
"""
from __future__ import annotations

import os

import requests
from bs4 import BeautifulSoup

import pdf_detail
from normalize import build_record

BASE = "https://www.nec.go.kr"
LIST_URL = f"{BASE}/site/nec/ex/bbs/List.do"
CB_IDX = "1107"

MAX_PAGES = int(os.getenv("NEC_MAX_PAGES", "10"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gov-trip-monitor/1.0)"}


def _abs(href: str) -> str:
    href = href.replace("&amp;", "&")
    return href if href.startswith("http") else f"{BASE}{href}"


def _parse_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    for li in soup.select("div.tableList li"):
        a = li.select_one("span.title a[href*='View.do']")
        if not a:
            continue
        title = a.get_text(strip=True)
        date_el = li.select_one("span.date")
        date = date_el.get_text(strip=True) if date_el else None
        pdf_el = li.select_one("span.fileDown a[href]")
        pdf_url = _abs(pdf_el.get("href", "")) if pdf_el else ""

        rec = build_record(
            source_type="gov_report",
            source_name="선관위",
            title=title,
            summary="공무국외출장보고서",
            url=_abs(a.get("href", "")),
            published_at=date,
            agency="중앙선거관리위원회",
            raw={"pdf_url": pdf_url} if pdf_url else {},
        )
        if rec:
            records.append(rec)
    return records


def fetch() -> list[dict]:
    records: list[dict] = []
    seen: set[str] = set()
    session = requests.Session()
    for page in range(1, MAX_PAGES + 1):
        try:
            resp = session.get(
                LIST_URL, params={"cbIdx": CB_IDX, "pageIndex": page}, headers=HEADERS, timeout=20
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[nec] page {page} 실패: {exc}")
            break
        rows = _parse_rows(resp.text)
        fresh = [r for r in rows if r["url"] not in seen]
        if not fresh:
            break
        for r in fresh:
            seen.add(r["url"])
            records.append(r)
        print(f"[nec] page {page}: {len(fresh)}건")
    # PDF 상세 보강 (선관위는 목록에 직접 PDF 링크 보유)
    return pdf_detail.enrich_all(
        records, "선관위", lambda r: (r.get("raw") or {}).get("pdf_url", "")
    )


if __name__ == "__main__":
    for r in fetch()[:8]:
        print(r["published_at"], "|", r["title"])
