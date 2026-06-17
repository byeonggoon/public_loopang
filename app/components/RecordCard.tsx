import { RecordRow } from "@/lib/types";

function formatDate(value: string | null): string {
  if (!value) return "";
  return value.slice(0, 10);
}

function TripFacts({ row }: { row: RecordRow }) {
  // 정부보고서에만 정보 줄 표시 (뉴스는 제외)
  if (row.source_type !== "gov_report") return null;

  let period = "";
  if (row.trip_start) {
    period = formatDate(row.trip_start);
    if (row.trip_end) {
      period += ` ~ ${formatDate(row.trip_end)}`;
      const days =
        Math.round(
          (new Date(row.trip_end).getTime() - new Date(row.trip_start).getTime()) / 86_400_000,
        ) + 1; // 시작·종료일 포함
      if (days > 0) period += ` (${days}일)`;
    }
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      {row.people_count != null && (
        <span className="text-gray-600 dark:text-gray-300">👥 {row.people_count}명</span>
      )}
      {row.countries && (
        <span className="text-gray-600 dark:text-gray-300">🌍 {row.countries}</span>
      )}
      {period && <span className="text-gray-500">📅 {period}</span>}
      {row.cost_total == null ? (
        <span className="rounded-md border border-dashed border-gray-300 px-2 py-0.5 text-gray-400 dark:border-gray-700 dark:text-gray-500">
          💰 비용 미공개
        </span>
      ) : row.cost_total === 0 ? (
        <span className="rounded-md bg-emerald-100 px-2 py-0.5 font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
          💰 ₩0 · 지출 없음
        </span>
      ) : (
        <span className="rounded-md bg-rose-100 px-2 py-0.5 font-semibold text-rose-700 dark:bg-rose-950 dark:text-rose-300">
          💰 ₩{row.cost_total.toLocaleString()}
        </span>
      )}
      {row.cost_total != null && row.cost_total > 0 && row.people_count ? (
        <span className="text-gray-400">
          1인당 ₩{Math.round(row.cost_total / row.people_count).toLocaleString()}
        </span>
      ) : null}
    </div>
  );
}

export default function RecordCard({ row }: { row: RecordRow }) {
  const isNews = row.source_type === "news";
  return (
    <article className="rounded-lg border border-gray-200 bg-white p-4 transition hover:shadow-md dark:border-gray-800 dark:bg-gray-900">
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
        <span
          className={`rounded px-2 py-0.5 font-medium ${
            isNews
              ? "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200"
              : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-200"
          }`}
        >
          {isNews ? "뉴스" : "정부보고서"}
        </span>
        <span className="text-gray-500">{row.source_name}</span>
        {row.published_at && (
          <span className="text-gray-400">· {formatDate(row.published_at)}</span>
        )}
        {row.region && <span className="text-gray-400">· {row.region}</span>}
      </div>

      <h2 className="mb-1 text-base font-semibold leading-snug">
        <a
          href={row.url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:underline"
        >
          {row.title}
        </a>
      </h2>

      {row.agency && (
        <p className="mb-1 text-sm text-gray-600 dark:text-gray-400">{row.agency}</p>
      )}
      {row.summary && (
        <p className="line-clamp-2 text-sm text-gray-500">{row.summary}</p>
      )}

      <TripFacts row={row} />

      {row.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {row.tags.map((tag) => (
            <span
              key={tag}
              className="rounded bg-amber-100 px-1.5 py-0.5 text-xs text-amber-800 dark:bg-amber-900 dark:text-amber-200"
            >
              #{tag}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}
