"""방송통신위원회(방통위) 국외출장보고서 수집기.

게시판: https://www.kcc.go.kr/user.do?boardId=1127&page=A02060700&dc=K02060700
구조: 서버렌더링 테이블, cp 파라미터로 페이징 (~120건).
  행: [번호][제목 a(boardSeq)][담당부서][유형][첨부][날짜]
  상세(GET): /user.do?mode=view&boardId=1127&page=A02060700&dc=K02060700&boardSeq=..

정책: PDF 본문 미복제. 제목·날짜·담당부서 + 상세 링크만 저장.
"""
from __future__ import annotations

import os
import re

import requests
from bs4 import BeautifulSoup

import pdf_detail
from normalize import build_record

BASE = "https://www.kcc.go.kr"
LIST_PARAMS = {"boardId": "1127", "page": "A02060700", "dc": "K02060700"}

MAX_PAGES = int(os.getenv("KCC_MAX_PAGES", "15"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gov-trip-monitor/1.0)"}


def _detail_url(seq: str) -> str:
    return (
        f"{BASE}/user.do?mode=view&boardId=1127"
        f"&page=A02060700&dc=K02060700&boardSeq={seq}"
    )


def _parse_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    seen_seq: set[str] = set()
    for a in soup.select("a[href*='boardSeq=']"):
        m = re.search(r"boardSeq=(\d+)", a.get("href", ""))
        if not m:
            continue
        seq = m.group(1)
        title = a.get_text(strip=True)
        if not title or seq in seen_seq:  # 보고서당 앵커 중복 제거
            continue
        seen_seq.add(seq)
        row = a.find_parent("tr")
        dept, date = "", None
        if row:
            tds = row.find_all("td")
            # [번호, 제목, 담당부서, 유형, 첨부, 날짜]
            if len(tds) >= 6:
                dept = tds[2].get_text(strip=True)
                date = tds[5].get_text(strip=True) or None

        agency = f"방송통신위원회 [{dept}]" if dept else "방송통신위원회"
        rec = build_record(
            source_type="gov_report",
            source_name="방통위",
            title=title,
            summary="국외출장보고서",
            url=_detail_url(seq),
            published_at=date,
            agency=agency,
            raw={"board_seq": seq},
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
                f"{BASE}/user.do", params={**LIST_PARAMS, "cp": page},
                headers=HEADERS, timeout=20,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[kcc] page {page} 실패: {exc}")
            break
        rows = _parse_rows(resp.text)
        fresh = [r for r in rows if r["url"] not in seen]
        if not fresh:
            break
        for r in fresh:
            seen.add(r["url"])
            records.append(r)
        print(f"[kcc] page {page}: {len(fresh)}건")
    # 상세페이지에서 PDF(download.do?fileSeq=) 링크를 찾아 보강
    return pdf_detail.enrich_all(
        records, "방통위",
        lambda r: pdf_detail.detail_pdf_url(r["url"], r"download\.do[^\"']*?fileSeq=\d+", BASE),
    )


if __name__ == "__main__":
    for r in fetch()[:8]:
        print(r["published_at"], "|", r["agency"], "|", r["title"][:40])
