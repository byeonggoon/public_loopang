"""공공데이터포털(data.go.kr) 국외출장보고서 수집기.

대상 예시: 인사혁신처 국가공무원 국외출장보고서 목록 (데이터셋 15085750).
데이터셋마다 OpenAPI 엔드포인트/필드명이 다르므로 ENDPOINT 는 env 로 주입한다.
필드 매핑은 흔한 키 후보를 순서대로 탐색하는 방식으로 방어적으로 처리한다.
"""
from __future__ import annotations

import os

import requests

from config import DATA_GO_KR_KEY
from normalize import build_record

# 데이터셋의 OpenAPI 엔드포인트(.../getList 형태). 미설정 시 건너뜀.
ENDPOINT = os.getenv("DATA_GO_KR_ENDPOINT", "")
NUM_ROWS = int(os.getenv("DATA_GO_KR_ROWS", "100"))

# 응답 항목에서 값을 찾을 때 시도할 키 후보들.
_TITLE_KEYS = ["title", "ttl", "rptTtl", "bsnsTripTtl", "subject", "ttl_nm"]
_DATE_KEYS = ["rptDt", "regDt", "trip_de", "tripBgnDe", "wrtDt", "date"]
_URL_KEYS = ["url", "link", "rptUrl", "detailUrl", "fileUrl"]
_AGENCY_KEYS = ["instNm", "agency", "deptNm", "orgNm", "institution"]
_SUMMARY_KEYS = ["cn", "smmr", "summary", "contents", "purpose", "rptCn"]


def _first(item: dict, keys: list[str]) -> str:
    for key in keys:
        val = item.get(key)
        if val:
            return str(val)
    return ""


def fetch() -> list[dict]:
    if not DATA_GO_KR_KEY:
        print("[data_go_kr] 키 없음 — 건너뜀")
        return []
    if not ENDPOINT:
        print("[data_go_kr] DATA_GO_KR_ENDPOINT 미설정 — 건너뜀")
        return []

    params = {
        "serviceKey": DATA_GO_KR_KEY,
        "numOfRows": NUM_ROWS,
        "pageNo": 1,
        "type": "json",
        "returnType": "json",
    }
    try:
        resp = requests.get(ENDPOINT, params=params, timeout=20)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        print(f"[data_go_kr] 요청/파싱 실패: {exc}")
        return []

    items = _extract_items(payload)
    records: list[dict] = []
    for item in items:
        rec = build_record(
            source_type="gov_report",
            source_name="data.go.kr",
            title=_first(item, _TITLE_KEYS),
            summary=_first(item, _SUMMARY_KEYS),
            url=_first(item, _URL_KEYS) or ENDPOINT,
            published_at=_first(item, _DATE_KEYS) or None,
            agency=_first(item, _AGENCY_KEYS),
            raw=item,
        )
        if rec:
            records.append(rec)
    print(f"[data_go_kr] {len(records)}건")
    return records


def _extract_items(payload) -> list[dict]:
    """data.go.kr 응답의 다양한 중첩 구조에서 item 리스트를 찾아낸다."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        # response.body.items.item 형태가 가장 흔함
        body = payload.get("response", {}).get("body", payload.get("body", payload))
        items = body.get("items", body.get("data", [])) if isinstance(body, dict) else []
        if isinstance(items, dict):
            items = items.get("item", [])
        if isinstance(items, dict):
            items = [items]
        return items if isinstance(items, list) else []
    return []


if __name__ == "__main__":
    for r in fetch()[:3]:
        print(r["published_at"], r["title"])
