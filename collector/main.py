"""수집 오케스트레이션: 세 소스 수집 → 정규화/중복제거 → Supabase 업로드.

로컬 실행:  python collector/main.py
JSON 미리보기(업로드 없이):  python collector/main.py --dry-run
"""
import json
import sys

import btis
import data_go_kr
import kcc
import nabo
import naver_news
import nec
from normalize import dedupe, dedupe_news_by_title
from upload import upload


def collect() -> list[dict]:
    records: list[dict] = []
    for name, source in (
        ("naver_news", naver_news),
        ("data_go_kr", data_go_kr),
        ("btis", btis),
        ("nabo", nabo),
        ("nec", nec),
        ("kcc", kcc),
    ):
        try:
            records.extend(source.fetch())
        except Exception as exc:  # noqa: BLE001 - 한 소스 실패가 전체를 막지 않도록
            print(f"[main] {name} 실패: {exc}")
    by_url = dedupe(records)
    deduped = dedupe_news_by_title(by_url)
    print(
        f"[main] 수집 {len(records)}건 → url중복제거 {len(by_url)}건 "
        f"→ 뉴스제목중복제거 {len(deduped)}건"
    )
    return deduped


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    records = collect()
    if dry_run:
        print(json.dumps(records[:10], ensure_ascii=False, indent=2))
        print(f"[main] --dry-run: 총 {len(records)}건 (업로드 안 함)")
        return
    upload(records)


if __name__ == "__main__":
    main()
