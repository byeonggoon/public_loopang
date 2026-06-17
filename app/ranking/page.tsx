import { costPerPerson, fetchGovRecords, tripDays } from "@/lib/stats";
import { RecordRow } from "@/lib/types";

export const dynamic = "force-dynamic";

interface RankItem {
  url: string;
  title: string;
  sub: string;
  value: string;
}

function RankSection({
  emoji,
  title,
  desc,
  items,
}: {
  emoji: string;
  title: string;
  desc: string;
  items: RankItem[];
}) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white/60 p-4 dark:border-gray-800 dark:bg-gray-900/40">
      <h2 className="text-base font-bold">
        {emoji} {title}
      </h2>
      <p className="mb-3 text-xs text-gray-400">{desc}</p>
      <ol className="space-y-1">
        {items.map((it, i) => (
          <li key={it.url} className="flex items-center gap-3 rounded-lg px-2 py-1.5 hover:bg-gray-50 dark:hover:bg-gray-800/60">
            <span className={`w-5 shrink-0 text-center text-sm font-bold ${i < 3 ? "text-blue-600 dark:text-blue-400" : "text-gray-400"}`}>
              {i + 1}
            </span>
            <div className="min-w-0 flex-1">
              <a href={it.url} target="_blank" rel="noopener noreferrer" className="line-clamp-2 text-sm font-medium hover:underline">
                {it.title}
              </a>
              <span className="block truncate text-xs text-gray-400">{it.sub}</span>
            </div>
            <span className="shrink-0 text-sm font-semibold text-rose-600 dark:text-rose-400">{it.value}</span>
          </li>
        ))}
      </ol>
    </section>
  );
}

const won = (n: number) => `₩${n.toLocaleString()}`;
const sub = (r: RecordRow) => [r.agency, r.countries].filter(Boolean).join(" · ");

export default async function RankingPage() {
  const rows = await fetchGovRecords();

  const byCost: RankItem[] = rows
    .filter((r) => r.cost_total && r.cost_total > 0)
    .sort((a, b) => (b.cost_total ?? 0) - (a.cost_total ?? 0))
    .slice(0, 10)
    .map((r) => ({ url: r.url, title: r.title, sub: sub(r), value: won(r.cost_total!) }));

  const byPeople: RankItem[] = rows
    .filter((r) => r.people_count)
    .sort((a, b) => (b.people_count ?? 0) - (a.people_count ?? 0))
    .slice(0, 10)
    .map((r) => ({ url: r.url, title: r.title, sub: sub(r), value: `${r.people_count}명` }));

  const byDays: RankItem[] = rows
    .map((r) => ({ r, d: tripDays(r) }))
    .filter((x) => x.d)
    .sort((a, b) => (b.d ?? 0) - (a.d ?? 0))
    .slice(0, 10)
    .map(({ r, d }) => ({ url: r.url, title: r.title, sub: sub(r), value: `${d}일` }));

  const byPerPerson: RankItem[] = rows
    .map((r) => ({ r, v: costPerPerson(r) }))
    .filter((x) => x.v)
    .sort((a, b) => (b.v ?? 0) - (a.v ?? 0))
    .slice(0, 10)
    .map(({ r, v }) => ({ url: r.url, title: r.title, sub: sub(r), value: won(v!) }));

  return (
    <>
      <h2 className="text-lg font-bold">🏆 월급루팡 랭킹</h2>
      <p className="mb-4 mt-1 text-xs text-gray-400">
        공개된 정부 출장보고서(BTIS·NABO·선관위·방통위) 기준. 비용·인원·기간이 공개된 건만 집계됩니다.
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <RankSection emoji="💰" title="최고 비용 출장" desc="총여비가 가장 큰 출장" items={byCost} />
        <RankSection emoji="🧮" title="1인당 비용" desc="총여비 ÷ 인원" items={byPerPerson} />
        <RankSection emoji="👥" title="최다 인원 단체출장" desc="출장 인원이 가장 많은 건" items={byPeople} />
        <RankSection emoji="📅" title="최장기간 출장" desc="출장 일수가 가장 긴 건" items={byDays} />
      </div>
    </>
  );
}
