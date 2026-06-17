import { supabase, supabaseConfigured } from "./supabase";
import { RecordRow } from "./types";

// 정부보고서 전체를 한 번에 가져와 랭킹/집계에 재사용 (약 700여 건).
export async function fetchGovRecords(): Promise<RecordRow[]> {
  if (!supabaseConfigured) return [];
  const { data } = await supabase
    .from("records")
    .select("*")
    .eq("source_type", "gov_report")
    .range(0, 1999);
  return (data as RecordRow[]) ?? [];
}

// 출장 일수 (시작·종료 포함). 둘 다 있을 때만.
export function tripDays(r: RecordRow): number | null {
  if (!r.trip_start || !r.trip_end) return null;
  const d =
    Math.round(
      (new Date(r.trip_end).getTime() - new Date(r.trip_start).getTime()) / 86_400_000,
    ) + 1;
  return d > 0 ? d : null;
}

// 1인당 비용 (비용/인원).
export function costPerPerson(r: RecordRow): number | null {
  if (!r.cost_total || !r.people_count) return null;
  return Math.round(r.cost_total / r.people_count);
}

// 기관명 정규화: "교육부 [경북대학교]" → "교육부", "방송통신위원회 [국제협력담당관]" → "방송통신위원회"
export function normalizeAgency(agency: string): string {
  if (!agency) return "(미상)";
  const head = agency.split("[")[0].trim();
  return head || agency.trim();
}

export interface AgencyStat {
  agency: string;
  count: number; // 출장 건수
  totalCost: number; // 공개된 비용 합계(원)
  costCount: number; // 비용이 공개된 건수
  undisclosed: number; // 비용 미공개 건수
  peopleSum: number; // 인원 합계(인원 있는 건만)
  avgPerPerson: number | null; // 1인당 평균(총비용/인원합)
  undisclosedRate: number; // 미공개 비율(%)
}

export function aggregateAgencies(rows: RecordRow[]): AgencyStat[] {
  const map = new Map<string, AgencyStat>();
  for (const r of rows) {
    const key = normalizeAgency(r.agency);
    let s = map.get(key);
    if (!s) {
      s = {
        agency: key, count: 0, totalCost: 0, costCount: 0,
        undisclosed: 0, peopleSum: 0, avgPerPerson: null, undisclosedRate: 0,
      };
      map.set(key, s);
    }
    s.count += 1;
    if (r.cost_total != null) {
      s.totalCost += r.cost_total;
      s.costCount += 1;
    } else {
      s.undisclosed += 1;
    }
    if (r.cost_total && r.people_count) s.peopleSum += r.people_count;
  }
  const out = Array.from(map.values());
  for (const s of out) {
    s.avgPerPerson = s.peopleSum > 0 ? Math.round(s.totalCost / s.peopleSum) : null;
    s.undisclosedRate = s.count > 0 ? Math.round((s.undisclosed / s.count) * 100) : 0;
  }
  return out;
}
