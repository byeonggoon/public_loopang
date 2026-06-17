import AgenciesTable from "../components/AgenciesTable";
import { aggregateAgencies, fetchGovRecords } from "@/lib/stats";

export const dynamic = "force-dynamic";

export default async function AgenciesPage() {
  const rows = await fetchGovRecords();
  const stats = aggregateAgencies(rows);

  return (
    <>
      <h2 className="text-lg font-bold">🏛️ 기관별 해외출장 집계</h2>
      <p className="mb-4 mt-1 text-xs text-gray-400">
        어느 기관이 해외출장에 가장 많이 썼나? 공개된 정부 출장보고서를 기관 단위로 합산했습니다.
      </p>

      <AgenciesTable stats={stats} />
      <p className="mt-3 text-xs text-gray-400">
        ※ 헤더를 클릭하면 정렬됩니다(다시 클릭 시 오름/내림 전환). 기관명은 상위 조직 기준으로 합산
        (예: &ldquo;교육부 [○○대학교]&rdquo; → 교육부). 비용 미공개 건은 합계에서 제외됩니다.
      </p>
    </>
  );
}
