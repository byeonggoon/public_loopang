"""공무국외출장연수정보시스템(BTIS) 결과보고서 수집기.

분석된 구조 (https://btis.mpm.go.kr/rpt/selectRptList.do):
  - 목록: 서버 렌더링 테이블, 제목 검색은 POST `title=<검색어>` 로 동작, pageIndex 페이징.
  - 상세(GET 가능): /rpt/selectRpt.do?report_id=..&use_report_id=0&pageIndex=1
      th/td 표에 [기관별 출장자(총 N명)][방문국가][출장기간][총여비/운임/체재비/…][보고서 요약]

정책:
  - 관심 키워드(config.BTIS_TITLE_KEYWORDS)로 제목 검색해 외유 의심 보고서를 포착.
  - 각 보고서의 상세를 추가 조회해 인원·국가·기간·비용·요약을 채운다.
  - 등록자 개인 성명은 저장하지 않는다 (인원 "수"만 추출).
"""
from __future__ import annotations

import os
import re

import requests
from bs4 import BeautifulSoup

from config import BTIS_TITLE_KEYWORDS
from normalize import build_record

BASE = "https://btis.mpm.go.kr"
LIST_URL = f"{BASE}/rpt/selectRptList.do"
DETAIL_URL = f"{BASE}/rpt/selectRpt.do"

PAGES_PER_KEYWORD = int(os.getenv("BTIS_PAGES_PER_KEYWORD", "5"))
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gov-trip-monitor/1.0)"}


def _detail_url(report_id: str) -> str:
    return f"{DETAIL_URL}?report_id={report_id}&use_report_id=0&pageIndex=1"


# ---------- 목록 파싱 ----------

def _parse_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    records: list[dict] = []
    for a in soup.select("a[onclick*='fn_inqire_rpt']"):
        onclick = a.get("onclick", "")
        try:
            report_id = onclick.split("(")[1].split(",")[1].strip()
        except IndexError:
            continue
        if not report_id.isdigit():
            continue

        title = (a.get("title") or a.get_text()).strip()
        row = a.find_parent("tr")
        category, agency, date = "", "", None
        if row:
            tds = row.find_all("td")
            if len(tds) >= 6:  # [번호, 분류, 제목, 등록자, 소속, 날짜]
                category = tds[1].get_text(strip=True)
                agency = " ".join(tds[4].stripped_strings)
                date = tds[5].get_text(strip=True) or None

        rec = build_record(
            source_type="gov_report",
            source_name="BTIS",
            title=title,
            summary=category,
            url=_detail_url(report_id),
            published_at=date,
            agency=agency,
            raw={"report_id": report_id, "category": category},
        )
        if rec:
            rec["_report_id"] = report_id
            records.append(rec)
    return records


# ---------- 상세 파싱 ----------

def _won(text: str) -> int | None:
    digits = re.sub(r"[^0-9]", "", text or "")
    return int(digits) if digits else None


def _ymd(text: str) -> str | None:
    s = re.sub(r"[^0-9]", "", text or "")
    if len(s) < 8:
        return None
    y, m, d = s[0:4], s[4:6], s[6:8]
    if not (1 <= int(m) <= 12 and 1 <= int(d) <= 31):  # 일/월 0 등 무효 날짜 방지
        return None
    return f"{y}-{m}-{d}"


def _parse_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    pairs: dict[str, str] = {}
    for th in soup.find_all("th"):
        td = th.find_next_sibling("td")
        if td:
            pairs[th.get_text(strip=True)] = " ".join(td.stripped_strings)

    out: dict = {}

    # 인원수: "기관별 출장자" 칸은 "총 N명 · {기관} {대표} 등 K명 · ..." 형태.
    # 맨 앞 "총 N명"은 기관 수에 가까워 실제 인원과 다르다(예: "총 1명 · 국방부 김영호 등 80명").
    # → '·'로 나눈 각 기관 항목에서 "등 K명"을 합산(없으면 1명)해 실제 인원을 구한다.
    people_text = pairs.get("기관별 출장자", "")
    entries = [e for e in people_text.split("·")[1:] if e.strip()]  # 앞의 "총 N명" 헤더 제외
    total_people = 0
    for entry in entries:
        m = re.search(r"등\s*(\d+)\s*명", entry)
        total_people += int(m.group(1)) if m else 1
    if total_people:
        out["people_count"] = total_people
    elif re.search(r"총\s*(\d+)\s*명", people_text):  # 폴백
        out["people_count"] = int(re.search(r"총\s*(\d+)\s*명", people_text).group(1))

    # 방문국가: "· 일본 · 미국" → "일본, 미국"
    raw_country = pairs.get("방문국가", "")
    countries = [c.strip() for c in re.split(r"[·,]", raw_country) if c.strip()]
    if countries:
        out["countries"] = ", ".join(countries)

    # 출장기간: "20260527 ~ 20260531"
    period = pairs.get("출장기간", "")
    if "~" in period:
        a, b = period.split("~", 1)
        out["trip_start"] = _ymd(a)
        out["trip_end"] = _ymd(b)

    # 비용
    out["cost_total"] = _won(pairs.get("총여비", ""))
    breakdown = {}
    for label in ("운임", "체재비", "준비금 및 기타 비용"):
        v = _won(pairs.get(label, ""))
        if v is not None:
            breakdown[label] = v
    if pairs.get("초청기관부담"):
        breakdown["초청기관부담"] = pairs["초청기관부담"]
    if breakdown:
        out["cost_breakdown"] = breakdown

    # 요약: 분류명 대신 실제 보고서 요약
    summary = pairs.get("보고서 요약", "")
    if summary:
        out["summary"] = summary[:500]

    return out


def _enrich(rec: dict, session: requests.Session) -> None:
    report_id = rec.get("raw", {}).get("report_id", "")
    if not report_id:
        return
    try:
        resp = session.get(_detail_url(report_id), headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException:
        return
    rec.update(_parse_detail(resp.text))


# ---------- 오케스트레이션 ----------

def _fetch_keyword(keyword: str, seen: set[str], session: requests.Session) -> list[dict]:
    out: list[dict] = []
    for page in range(1, PAGES_PER_KEYWORD + 1):
        try:
            resp = session.post(
                LIST_URL, data={"pageIndex": page, "title": keyword}, headers=HEADERS, timeout=20
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[btis] '{keyword}' p{page} 실패: {exc}")
            break

        rows = _parse_rows(resp.text)
        fresh = [r for r in rows if r["_report_id"] not in seen]
        if not fresh:
            break
        for r in fresh:
            seen.add(r["_report_id"])
            r.pop("_report_id", None)
            out.append(r)
        if len(rows) < 10:
            break
    return out


def fetch() -> list[dict]:
    from upload import detailed_urls

    done = detailed_urls("BTIS")  # 이미 상세가 채워진 보고서 url (증분 스킵용)
    records: list[dict] = []
    seen: set[str] = set()
    session = requests.Session()
    for keyword in BTIS_TITLE_KEYWORDS:
        found = _fetch_keyword(keyword, seen, session)
        print(f"[btis] '{keyword}': {len(found)}건")
        records.extend(found)

    # 증분: 이미 상세가 있는 보고서는 재조회 생략, 신규만 상세 보강.
    todo = [r for r in records if r["url"] not in done]
    print(f"[btis] 수집 {len(records)}건 중 신규 {len(todo)}건 상세 조회")
    for i, rec in enumerate(todo, 1):
        _enrich(rec, session)
        if i % 50 == 0:
            print(f"[btis]   상세 {i}/{len(todo)}")
    print(f"[btis] 상세 보강 {len(todo)}건 (기존 {len(records) - len(todo)}건 스킵)")
    return todo


if __name__ == "__main__":
    for r in fetch()[:8]:
        print(
            r["published_at"], r["agency"], "|", r["title"],
            "| 인원", r.get("people_count"), "| 총여비", r.get("cost_total"),
        )
