import { createClient } from "@supabase/supabase-js";

// 읽기 전용 공개 클라이언트 (anon 키). 쓰기는 수집기(service_role)만 수행.
const url = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

export const supabaseConfigured = Boolean(url && anonKey);

// Next.js 의 fetch 캐시를 끈다 — 수집기가 데이터를 갱신해도 항상 최신 결과를 조회.
export const supabase = createClient(url || "http://localhost", anonKey || "anon", {
  auth: { persistSession: false },
  global: {
    fetch: (input: RequestInfo | URL, init?: RequestInit) =>
      fetch(input, { ...init, cache: "no-store" }),
  },
});
