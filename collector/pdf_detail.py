"""게시판 소스(선관위·NABO·방통위)의 첨부 PDF에서 출장 상세를 추출.

BTIS와 달리 이들 보고서는 PDF라 본문에서 정규식으로 뽑는다.
표준 공무국외출장 보고서의 '출장개요'(보통 앞 몇 쪽)를 대상으로 한다.
양식이 기관마다 조금씩 달라 100%는 아니며, 못 찾으면 해당 항목은 비운다.

정책: PDF 본문 전체를 저장하지 않는다. 추출한 사실(기간/국가/인원/예산)만 반환.
"""
from __future__ import annotations

import re

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; gov-trip-monitor/1.0)"}
MAX_PAGES = 6  # 출장개요는 보통 앞쪽

# 제목에서 방문국가를 잡기 위한 국가명 사전 (제목 괄호는 방통위처럼 비국가 내용이 섞여 부정확).
COUNTRY_NAMES = [
    "미국", "중국", "일본", "영국", "프랑스", "독일", "스페인", "이탈리아", "네덜란드",
    "벨기에", "스위스", "오스트리아", "스웨덴", "덴마크", "노르웨이", "핀란드", "러시아",
    "캐나다", "호주", "뉴질랜드", "싱가포르", "말레이시아", "태국", "베트남", "인도네시아",
    "필리핀", "인도", "대만", "홍콩", "아랍에미리트", "카타르", "사우디아라비아", "튀르키예",
    "터키", "그리스", "포르투갈", "체코", "폴란드", "헝가리", "크로아티아", "아일랜드",
    "멕시코", "브라질", "아르헨티나", "칠레", "이집트", "케냐", "몽골", "카자흐스탄",
    "우즈베키스탄", "캄보디아", "라오스", "미얀마", "방글라데시", "네팔", "이스라엘",
    "룩셈부르크", "슬로바키아", "슬로베니아", "루마니아", "불가리아", "세르비아",
    "에스토니아", "라트비아", "리투아니아", "아이슬란드", "페루", "콜롬비아", "남아프리카공화국",
]


def countries_from_title(title: str) -> str:
    """제목에 등장하는 국가명을 순서대로 추출 (예: '스웨덴·독일 …' → '스웨덴, 독일')."""
    found = [(title.find(c), c) for c in COUNTRY_NAMES if c in title]
    # '남아프리카공화국' 같이 다른 국가명을 포함하는 경우 중복 방지: 위치순 정렬 후 부분문자열 제거
    found.sort()
    names = [c for _, c in found]
    names = [c for c in names if not any(c != o and c in o for o in names)]
    return ", ".join(dict.fromkeys(names))[:60]


def _text(pdf_bytes: bytes) -> str:
    from io import BytesIO

    from pypdf import PdfReader

    reader = PdfReader(BytesIO(pdf_bytes))
    parts = []
    for page in reader.pages[:MAX_PAGES]:
        try:
            parts.append(page.extract_text() or "")
        except Exception:  # noqa: BLE001
            continue
    return re.sub(r"\s+", " ", " ".join(parts))


def _iso(y: str, m: str, d: str) -> str:
    return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"


_TILDE = re.compile(r"[~∼〜～]")
# "기 간", "출 장 기 간" 처럼 글자 사이 공백이 있어도 잡도록 라벨을 유연하게.
_PERIOD_LABEL = re.compile(
    r"기\s*간[^0-9]{0,8}"
    r"(\d{4})[.\s]*(\d{1,2})[.\s]*(\d{1,2})"      # 시작일
    r"[^~0-9]{0,20}~\s*(?:(\d{4})[.\s]*)?(\d{1,2})[.\s]*(\d{1,2})"  # 종료일(연도 생략 가능)
)
# 라벨이 없을 때: 요일 표기가 붙은 날짜 범위
_PERIOD_DOW = re.compile(
    r"(\d{4})[.\s]*(\d{1,2})[.\s]*(\d{1,2})\s*\([월화수목금토일]\)"
    r"[^~0-9]{0,15}~\s*(?:(\d{4})[.\s]*)?(\d{1,2})[.\s]*(\d{1,2})"
)


def _period(text: str) -> tuple[str | None, str | None]:
    """'출 장 기 간 2023. 9. 6. ∼ 9. 14.' → (2023-09-06, 2023-09-14). 공백/물결표 변형 처리."""
    t = _TILDE.sub("~", text)
    m = _PERIOD_LABEL.search(t) or _PERIOD_DOW.search(t)
    if not m:
        return None, None
    y0, m0, d0, y1, m1, d1 = m.groups()
    return _iso(y0, m0, d0), _iso(y1 or y0, m1, d1)


def _countries(text: str) -> str:
    m = re.search(r"(?:출장|방문)\s*국가[^:：]{0,6}[:：]\s*([가-힣A-Za-z,·\s]{2,40}?)(?:의|\s*선거|\s*방문|\s*출장|\s*[ⅠⅡ가나]|$)", text)
    if not m:
        return ""
    raw = re.split(r"[·,]", m.group(1))
    names = [c.strip() for c in raw if c.strip()]
    return ", ".join(dict.fromkeys(names))[:60]


# 출장자 표의 직급 명칭 (5급/6급이 아닌 서기관·주사보 형식 대응)
_RANK_TITLES = re.compile(r"이사관|서기관|사무관|주사보|주사|연구관|연구사|주무관")


def _people(text: str) -> int | None:
    for pat in (r"출장\s*인원[^0-9]{0,5}(\d+)\s*명", r"총\s*(\d+)\s*명", r"등\s*(\d+)\s*명"):
        m = re.search(pat, text)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 200:
                return n
    # 폴백: '출장자' 라벨이 여러 번(목차 포함) 나올 수 있으므로 각 구간을 보고
    # 직급 토큰이 있는(=실제 표) 구간의 인원수를 택한다.
    starts = [m.start() for m in re.finditer(r"출\s*장\s*자", text)] or [0]
    best = 0
    for s in starts:
        region = text[s : s + 500]
        n = len(re.findall(r"\d급", region))  # 5급/6급 형식
        if not (1 <= n <= 60):
            n = len(_RANK_TITLES.findall(region))  # 서기관/주사보 형식
        if 1 <= n <= 60:
            best = max(best, n)
    return best or None


def _cost(text: str) -> int | None:
    m = re.search(
        r"(?:소요\s*예산|총\s*경비|소요\s*경비|예산\s*총액|총\s*소요\s*경비)[^0-9]{0,12}([0-9,]+)\s*(천원|만원|원)?",
        text,
    )
    if not m:
        return None
    amount = int(m.group(1).replace(",", ""))
    unit = m.group(2)
    if unit == "천원":
        amount *= 1000
    elif unit == "만원":
        amount *= 10000
    return amount


def detail_pdf_url(detail_url: str, pattern: str, base: str) -> str:
    """상세페이지를 받아 그 안의 단일 PDF 다운로드 링크(정규식 매칭)를 절대경로로 반환."""
    try:
        html = requests.get(detail_url, headers=HEADERS, timeout=20).text
    except requests.RequestException:
        return ""
    m = re.search(pattern, html)
    if not m:
        return ""
    href = m.group(0).replace("&amp;", "&")
    # jsessionid 제거
    href = re.sub(r";jsessionid=[^?]*", "", href)
    if href.startswith("http"):
        return href
    return base + ("" if href.startswith("/") else "/") + href


def extract(pdf_url: str) -> dict:
    """PDF URL을 받아 {trip_start, trip_end, countries, people_count, cost_total} 반환."""
    if not pdf_url:
        return {}
    try:
        resp = requests.get(pdf_url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        text = _text(resp.content)
    except Exception:  # noqa: BLE001 - 다운로드/파싱 실패는 조용히 건너뜀
        return {}

    out: dict = {}
    ts, te = _period(text)
    if ts:
        out["trip_start"] = ts
    if te:
        out["trip_end"] = te
    c = _countries(text)
    if c:
        out["countries"] = c
    p = _people(text)
    if p:
        out["people_count"] = p
    cost = _cost(text)
    if cost:
        out["cost_total"] = cost
    return out


def enrich_all(records: list[dict], source_name: str, pdf_url_fn) -> list[dict]:
    """게시판 레코드들에 PDF 상세를 보강. 이미 보강된 url은 제외(증분).

    pdf_url_fn(record) -> 단일 PDF url. 국가는 제목에서 우선 추출.
    반환: 이번에 새로 보강한(또는 미보강이던) 레코드만.
    """
    from upload import detailed_urls, upload

    done = detailed_urls(source_name)
    out: list[dict] = []
    batch: list[dict] = []
    todo = [r for r in records if r["url"] not in done]
    for i, rec in enumerate(todo, 1):
        title_countries = countries_from_title(rec["title"])
        if title_countries:
            rec["countries"] = title_countries
        try:
            pdf = pdf_url_fn(rec)
            if pdf:
                rec.update(extract(pdf))
                if title_countries:  # 제목 국가를 PDF보다 우선
                    rec["countries"] = title_countries
        except Exception:  # noqa: BLE001
            pass
        out.append(rec)
        batch.append(rec)
        # 25건마다 업로드(체크포인트) — 중단되어도 재실행 시 이어짐
        if len(batch) >= 25:
            upload(batch)
            batch = []
            print(f"[{source_name}] 상세 {i}/{len(todo)} (체크포인트 업로드)")
    if batch:
        upload(batch)
    print(f"[{source_name}] 보강 완료: {len(out)}건 (기존 {len(records) - len(out)}건 스킵)")
    return out


if __name__ == "__main__":
    import sys

    print(extract(sys.argv[1]))
