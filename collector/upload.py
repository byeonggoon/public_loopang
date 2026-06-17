"""Supabase 업로드 (url 기준 upsert)."""
from __future__ import annotations

from config import SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None


def detailed_urls(source_name: str) -> set[str]:
    """이미 상세보강된(people_count 있는) 레코드 url 집합 — 증분 처리용.

    Supabase 미설정/오류면 빈 집합(→ 전체 보강)."""
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY) or create_client is None:
        return set()
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        urls: set[str] = set()
        start = 0
        while True:
            rows = (
                client.table("records")
                .select("url,people_count,trip_start,countries")
                .eq("source_name", source_name)
                .range(start, start + 999)
                .execute()
                .data
            )
            # 기간/국가/인원 중 하나라도 있으면 '보강됨'으로 보고 재다운로드 생략
            for r in rows:
                if r.get("people_count") or r.get("trip_start") or r.get("countries"):
                    urls.add(r["url"])
            if len(rows) < 1000:
                break
            start += 1000
        return urls
    except Exception as exc:  # noqa: BLE001
        print(f"[upload] detailed_urls 조회 실패: {exc}")
        return set()


def upload(records: list[dict]) -> int:
    """records 를 Supabase 에 upsert. 저장된 건수 반환."""
    if not records:
        print("[upload] 업로드할 레코드 없음")
        return 0
    if not (SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY):
        print("[upload] Supabase 키 없음 — 건너뜀")
        return 0
    if create_client is None:
        print("[upload] supabase 패키지 미설치 — 건너뜀")
        return 0

    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    # url 중복 제거(나중 값 우선) — 한 upsert 명령에 같은 url 두 번 들어가면 Postgres 오류.
    by_url = {r["url"]: r for r in records if r.get("url")}
    records = list(by_url.values())
    saved = 0
    # 배치로 나눠서 upsert (url unique 충돌 시 갱신).
    for i in range(0, len(records), 100):
        batch = records[i : i + 100]
        try:
            client.table("records").upsert(batch, on_conflict="url").execute()
            saved += len(batch)
        except Exception as exc:  # noqa: BLE001 - 네트워크/스키마 오류 로깅
            print(f"[upload] 배치 {i // 100} 실패: {exc}")
    print(f"[upload] {saved}건 저장")
    return saved
