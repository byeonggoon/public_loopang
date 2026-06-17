"""국회예산정책처(NABO) 공무국외출장 결과보고서 수집기.

분석된 구조 (https://www.nabo.go.kr/ko/report/officialTripList.do):
  - GET 페이징: ?pageIndex=N
  - 목록 <li> 항목에 필요한 정보가 모두 존재:
      .report_name a[href=officialTripView.do?idx=..]  -> 제목 + 상세 idx
      .date                                            -> 날짜
      .file a.btn_down[href=/board/file/bulkDown.do..] -> PDF(첨부) 다운로드
      .department_name (등록자 성명)                    -> 저장하지 않음

정책:
  - PDF 본문을 복제 저장하지 않는다. 제목·날짜 + 원문(상세/PDF) 링크만 저장.
  - 등록자 개인 성명은 저장하지 않는다.
"""
from __future__ import annotations

import os

import requests
from bs4 import BeautifulSoup

import pdf_detail
from normalize import build_record

BASE = "https://www.nabo.go.kr"
LIST_URL = f"{BASE}/ko/report/officialTripList.do"

MAX_PAGES = int(os.getenv("NABO_MAX_PAGES", "20"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gov-trip-monitor/1.0)"}


def _abs(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return f"{BASE}{href}"
    return f"{BASE}/ko/report/{href}"


def _parse_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    for a in soup.select("div.report_name a[href*='officialTripView']"):
        href = a.get("href", "")
        title = a.get_text(strip=True)
        li = a.find_parent("li")
        date, pdf_url = None, ""
        if li:
            date_el = li.select_one(".date")
            if date_el:
                date = date_el.get_text(strip=True) or None
            file_el = li.select_one(".file a[href]")
            if file_el:
                pdf_url = _abs(file_el.get("href", ""))
            # .department_name(등록자 성명)은 의도적으로 저장하지 않음.

        rec = build_record(
            source_type="gov_report",
            source_name="NABO",
            title=title,
            summary="공무국외출장 결과보고서",
            url=_abs(href),
            published_at=date,
            agency="국회예산정책처",
            raw={"pdf_url": pdf_url} if pdf_url else {},
        )
        if rec:
            records.append(rec)
    return records


def fetch() -> list[dict]:
    records: list[dict] = []
    for page in range(1, MAX_PAGES + 1):
        try:
            resp = requests.get(
                LIST_URL, params={"pageIndex": page}, headers=HEADERS, timeout=20
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[nabo] page {page} 요청 실패: {exc}")
            break
        page_records = _parse_rows(resp.text)
        if not page_records:
            print(f"[nabo] page {page} 항목 없음 — 중단")
            break
        records.extend(page_records)
        print(f"[nabo] page {page}: {len(page_records)}건")
    # 상세페이지에서 단일 PDF(down.do?fid=) 링크를 찾아 보강
    return pdf_detail.enrich_all(
        records, "NABO",
        lambda r: pdf_detail.detail_pdf_url(r["url"], r"/board/file/down\.do\?fid=\d+", BASE),
    )


if __name__ == "__main__":
    for r in fetch()[:5]:
        print(r["published_at"], "|", r["title"])
