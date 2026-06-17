export type SourceType = "news" | "gov_report";

export interface RecordRow {
  id: string;
  source_type: SourceType;
  source_name: string;
  title: string;
  summary: string;
  url: string;
  published_at: string | null;
  agency: string;
  region: string;
  tags: string[];
  people_count: number | null;
  countries: string;
  trip_start: string | null;
  trip_end: string | null;
  cost_total: number | null;
  collected_at: string;
}

// 광역 시·도 (필터 옵션) — collector/config.py 의 REGIONS 와 일치.
export const REGIONS = [
  "서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종",
  "경기", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
];

export const SOURCE_TYPES: { value: SourceType; label: string }[] = [
  { value: "news", label: "뉴스" },
  { value: "gov_report", label: "정부보고서" },
];

export const PAGE_SIZE = 20;
