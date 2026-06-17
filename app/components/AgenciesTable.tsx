"use client";

import { useState } from "react";
import { AgencyStat } from "@/lib/stats";

type SortKey = "agency" | "count" | "totalCost" | "avgPerPerson" | "undisclosedRate";
type Dir = "asc" | "desc";

const COLUMNS: { key: SortKey; label: string; align: "left" | "right" }[] = [
  { key: "agency", label: "기관", align: "left" },
  { key: "count", label: "건수", align: "right" },
  { key: "totalCost", label: "공개 비용 합계", align: "right" },
  { key: "avgPerPerson", label: "1인당 평균", align: "right" },
  { key: "undisclosedRate", label: "비용 미공개", align: "right" },
];

const won = (n: number) => `₩${n.toLocaleString()}`;

function sortStats(stats: AgencyStat[], key: SortKey, dir: Dir): AgencyStat[] {
  const sign = dir === "asc" ? 1 : -1;
  return [...stats].sort((a, b) => {
    if (key === "agency") return sign * a.agency.localeCompare(b.agency, "ko");
    const av = key === "avgPerPerson" ? a.avgPerPerson ?? -1 : a[key];
    const bv = key === "avgPerPerson" ? b.avgPerPerson ?? -1 : b[key];
    return sign * ((av as number) - (bv as number));
  });
}

export default function AgenciesTable({ stats }: { stats: AgencyStat[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("totalCost");
  const [dir, setDir] = useState<Dir>("desc");

  function onSort(key: SortKey) {
    if (key === sortKey) {
      setDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setDir(key === "agency" ? "asc" : "desc");
    }
  }

  const rows = sortStats(stats, sortKey, dir);

  return (
    <div className="overflow-x-auto rounded-2xl border border-gray-200 dark:border-gray-800">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-xs text-gray-500 dark:bg-gray-900">
          <tr>
            {COLUMNS.map((c) => (
              <th key={c.key} className={`px-3 py-2 font-medium ${c.align === "right" ? "text-right" : "text-left"}`}>
                <button
                  type="button"
                  onClick={() => onSort(c.key)}
                  className={`inline-flex items-center gap-1 transition-colors hover:text-gray-900 dark:hover:text-gray-100 ${
                    sortKey === c.key ? "text-gray-900 dark:text-gray-100" : ""
                  } ${c.align === "right" ? "flex-row-reverse" : ""}`}
                >
                  {c.label}
                  <span className="text-[10px]">
                    {sortKey === c.key ? (dir === "asc" ? "▲" : "▼") : "↕"}
                  </span>
                </button>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
          {rows.map((s, i) => (
            <tr key={s.agency} className="hover:bg-gray-50 dark:hover:bg-gray-800/50">
              <td className="px-3 py-2">
                <span className="mr-2 text-xs font-bold text-gray-400">{i + 1}</span>
                {s.agency}
              </td>
              <td className="px-3 py-2 text-right text-gray-500">{s.count}건</td>
              <td className="px-3 py-2 text-right font-semibold text-rose-600 dark:text-rose-400">
                {s.totalCost > 0 ? won(s.totalCost) : "—"}
              </td>
              <td className="px-3 py-2 text-right text-gray-600 dark:text-gray-300">
                {s.avgPerPerson ? won(s.avgPerPerson) : "—"}
              </td>
              <td className="px-3 py-2 text-right">
                <span className={s.undisclosedRate >= 50 ? "font-semibold text-amber-600 dark:text-amber-400" : "text-gray-400"}>
                  {s.undisclosed}건 ({s.undisclosedRate}%)
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
