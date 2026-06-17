import { supabase, supabaseConfigured } from "./supabase";
import { PAGE_SIZE, RecordRow } from "./types";

export interface RecordQuery {
  q?: string;
  type?: string;
  region?: string;
  from?: string;
  to?: string;
  sort?: string;
  page?: number;
}

export interface RecordResult {
  rows: RecordRow[];
  total: number;
  page: number;
  pageSize: number;
  configured: boolean;
  error?: string;
}

// .or() 필터는 쉼표/괄호를 구분자로 쓰므로 검색어에서 제거해 깨짐 방지.
function sanitize(term: string): string {
  return term.replace(/[,()%]/g, " ").trim();
}

export async function queryRecords(params: RecordQuery): Promise<RecordResult> {
  const page = Math.max(1, params.page ?? 1);
  const offset = (page - 1) * PAGE_SIZE;
  const empty: RecordResult = {
    rows: [], total: 0, page, pageSize: PAGE_SIZE, configured: supabaseConfigured,
  };

  if (!supabaseConfigured) {
    return { ...empty, error: "Supabase 환경변수가 설정되지 않았습니다." };
  }

  let query = supabase
    .from("records")
    .select("*", { count: "exact" })
    .range(offset, offset + PAGE_SIZE - 1);

  const q = params.q ? sanitize(params.q) : "";
  if (q) {
    query = query.or(`title.ilike.%${q}%,summary.ilike.%${q}%,agency.ilike.%${q}%`);
  }
  if (params.type && params.type !== "all") query = query.eq("source_type", params.type);
  if (params.region) query = query.eq("region", params.region);
  if (params.from) query = query.gte("published_at", params.from);
  if (params.to) query = query.lte("published_at", params.to);

  if (params.sort === "cost") {
    query = query.order("cost_total", { ascending: false, nullsFirst: false });
  } else {
    const ascending = params.sort === "oldest";
    query = query.order("published_at", { ascending, nullsFirst: false });
  }

  const { data, count, error } = await query;
  if (error) return { ...empty, error: error.message };

  return {
    rows: (data as RecordRow[]) ?? [],
    total: count ?? 0,
    page,
    pageSize: PAGE_SIZE,
    configured: true,
  };
}
