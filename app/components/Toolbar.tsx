import { REGIONS } from "@/lib/types";
import { RecordQuery } from "@/lib/records";
import FancySelect from "./FancySelect";
import FancyDate from "./FancyDate";

const TYPE_OPTIONS = [
  { value: "gov_report", label: "정부보고서" },
  { value: "news", label: "뉴스" },
  { value: "all", label: "전체" },
];
const REGION_OPTIONS = [
  { value: "", label: "전체" },
  ...REGIONS.map((r) => ({ value: r, label: r })),
];
const SORT_OPTIONS = [
  { value: "latest", label: "최신순" },
  { value: "oldest", label: "오래된순" },
  { value: "cost", label: "비용 높은순" },
];

// 네이티브 GET 폼 — 제출 시 URL 쿼리스트링이 갱신되고 서버에서 재조회된다.
function Labeled({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="mb-1 block text-[11px] font-medium uppercase tracking-wide text-gray-400">
        {label}
      </label>
      {children}
    </div>
  );
}

export default function Toolbar({ params }: { params: RecordQuery }) {
  return (
    <form
      method="get"
      className="mb-6 rounded-2xl border border-gray-200/80 bg-white/70 p-4 shadow-sm ring-1 ring-black/5 backdrop-blur dark:border-gray-800 dark:bg-gray-900/50 dark:ring-white/5 sm:p-5"
    >
      {/* 검색 라인 */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m21 21-4.3-4.3" strokeLinecap="round" />
          </svg>
          <input
            type="text"
            name="q"
            defaultValue={params.q ?? ""}
            placeholder="제목·요약·기관으로 검색  (예: 외유, 몰디브, 시의회)"
            className="h-12 w-full rounded-xl border border-gray-300 bg-white pl-11 pr-4 text-base text-gray-900 shadow-sm transition placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:border-gray-700 dark:bg-gray-950 dark:text-gray-100"
          />
        </div>
        <div className="flex gap-2">
          <button
            type="submit"
            className="inline-flex h-12 flex-1 items-center justify-center gap-1.5 rounded-xl bg-blue-600 px-6 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/40 active:scale-[0.98] sm:flex-none"
          >
            검색
          </button>
          <a
            href="/"
            className="inline-flex h-12 items-center justify-center rounded-xl border border-gray-300 px-4 text-sm text-gray-600 transition hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
          >
            초기화
          </a>
        </div>
      </div>

      {/* 필터 라인 */}
      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-gray-100 pt-4 dark:border-gray-800 sm:grid-cols-5">
        <Labeled label="소스">
          <FancySelect name="type" defaultValue={params.type ?? ""} options={TYPE_OPTIONS} />
        </Labeled>
        <Labeled label="지역">
          <FancySelect name="region" defaultValue={params.region ?? ""} options={REGION_OPTIONS} />
        </Labeled>
        <Labeled label="시작일">
          <FancyDate name="from" defaultValue={params.from ?? ""} />
        </Labeled>
        <Labeled label="종료일">
          <FancyDate name="to" defaultValue={params.to ?? ""} />
        </Labeled>
        <Labeled label="정렬">
          <FancySelect name="sort" defaultValue={params.sort ?? "latest"} options={SORT_OPTIONS} />
        </Labeled>
      </div>
    </form>
  );
}
