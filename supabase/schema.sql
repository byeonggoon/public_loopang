-- 공무 국외출장/연수 모니터링 - Supabase 스키마
-- Supabase SQL Editor 에 그대로 붙여 실행하세요.

create extension if not exists pg_trgm;

create table if not exists public.records (
  id           uuid primary key default gen_random_uuid(),
  source_type  text not null check (source_type in ('news', 'gov_report')),
  source_name  text not null,                 -- '네이버뉴스' | 'BTIS' | 'data.go.kr'
  title        text not null,
  summary      text default '',
  url          text not null unique,          -- 원문 링크 (본문 전문 저장 안 함)
  published_at timestamptz,
  agency       text default '',               -- 기관 (시도/의회/부처)
  region       text default '',               -- 광역 시·도 (필터용)
  tags         text[] default '{}',
  -- 출장 상세 (BTIS 보고서 전용, 그 외 소스는 null)
  people_count   int,                 -- 출장 인원수
  countries      text default '',     -- 방문국가
  trip_start     date,                -- 출장 시작일
  trip_end       date,                -- 출장 종료일
  cost_total     bigint,              -- 총여비 (원)
  cost_breakdown jsonb default '{}'::jsonb, -- 운임/체재비/준비금 등
  raw          jsonb default '{}'::jsonb,
  collected_at timestamptz not null default now()
);

-- 기존 테이블에도 컬럼 추가 (재실행 안전)
alter table public.records add column if not exists people_count   int;
alter table public.records add column if not exists countries      text default '';
alter table public.records add column if not exists trip_start     date;
alter table public.records add column if not exists trip_end       date;
alter table public.records add column if not exists cost_total     bigint;
alter table public.records add column if not exists cost_breakdown jsonb default '{}'::jsonb;

-- 인덱스
create index if not exists records_published_at_idx on public.records (published_at desc nulls last);
create index if not exists records_region_idx       on public.records (region);
create index if not exists records_source_type_idx  on public.records (source_type);
create index if not exists records_cost_total_idx    on public.records (cost_total desc nulls last);
create index if not exists records_tags_idx         on public.records using gin (tags);
create index if not exists records_title_trgm_idx   on public.records using gin (title gin_trgm_ops);
create index if not exists records_summary_trgm_idx on public.records using gin (summary gin_trgm_ops);

-- RLS: 공개 읽기, 쓰기는 service_role 키(수집기)만
alter table public.records enable row level security;

drop policy if exists "public read records" on public.records;
create policy "public read records"
  on public.records for select
  to anon, authenticated
  using (true);

-- anon/authenticated 에는 insert/update/delete 정책을 만들지 않음 → 차단됨.
-- service_role 키는 RLS 를 우회하므로 수집기에서 upsert 가능.
