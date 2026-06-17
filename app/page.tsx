import Pagination from "./components/Pagination";
import RecordCard from "./components/RecordCard";
import Toolbar from "./components/Toolbar";
import { queryRecords, RecordQuery } from "@/lib/records";

export const dynamic = "force-dynamic";

type SearchParams = { [key: string]: string | string[] | undefined };

function pick(sp: SearchParams, key: string): string | undefined {
  const v = sp[key];
  return Array.isArray(v) ? v[0] : v;
}

export default async function Home({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const params: RecordQuery = {
    q: pick(searchParams, "q"),
    type: pick(searchParams, "type") ?? "gov_report", // 기본은 정부보고서(1차자료), 뉴스는 보조
    region: pick(searchParams, "region"),
    from: pick(searchParams, "from"),
    to: pick(searchParams, "to"),
    sort: pick(searchParams, "sort") ?? "latest",
    page: Number(pick(searchParams, "page") ?? "1") || 1,
  };

  const result = await queryRecords(params);
  const totalPages = Math.max(1, Math.ceil(result.total / result.pageSize));

  return (
    <>
      <Toolbar params={params} />

      {result.error && (
        <div className="rounded border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          데이터를 불러오지 못했습니다: {result.error}
        </div>
      )}

      {!result.error && (
        <>
          <p className="mb-3 text-sm text-gray-500">총 {result.total.toLocaleString()}건</p>
          {result.rows.length === 0 ? (
            <p className="py-12 text-center text-gray-400">검색 결과가 없습니다.</p>
          ) : (
            <div className="grid gap-3">
              {result.rows.map((row) => (
                <RecordCard key={row.id} row={row} />
              ))}
            </div>
          )}
          <Pagination params={params} page={result.page} totalPages={totalPages} />
        </>
      )}
    </>
  );
}
