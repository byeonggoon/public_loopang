import { RecordQuery } from "@/lib/records";

function buildHref(params: RecordQuery, page: number): string {
  const sp = new URLSearchParams();
  if (params.q) sp.set("q", params.q);
  if (params.type) sp.set("type", params.type);
  if (params.region) sp.set("region", params.region);
  if (params.from) sp.set("from", params.from);
  if (params.to) sp.set("to", params.to);
  if (params.sort) sp.set("sort", params.sort);
  sp.set("page", String(page));
  return `/?${sp.toString()}`;
}

export default function Pagination({
  params,
  page,
  totalPages,
}: {
  params: RecordQuery;
  page: number;
  totalPages: number;
}) {
  if (totalPages <= 1) return null;
  const linkCls =
    "rounded border border-gray-300 px-3 py-1.5 text-sm hover:bg-gray-50 dark:border-gray-700";
  const disabledCls = "pointer-events-none opacity-40";

  return (
    <nav className="mt-8 flex items-center justify-center gap-3">
      <a href={buildHref(params, page - 1)} className={`${linkCls} ${page <= 1 ? disabledCls : ""}`}>
        이전
      </a>
      <span className="text-sm text-gray-500">
        {page} / {totalPages}
      </span>
      <a
        href={buildHref(params, page + 1)}
        className={`${linkCls} ${page >= totalPages ? disabledCls : ""}`}
      >
        다음
      </a>
    </nav>
  );
}
