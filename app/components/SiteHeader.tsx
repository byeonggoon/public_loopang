import Link from "next/link";
import NavTabs from "./NavTabs";

// 모든 페이지 상단에 고정되는 공통 헤더 (로고·제목·태그라인·고지·탭).
export default function SiteHeader() {
  return (
    <>
      <header className="mb-6">
        <Link href="/" className="flex items-center gap-3">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/monkey.png"
            alt="월급루팡 원숭이 로고"
            width={56}
            height={56}
            className="monkey-logo pixelated h-14 w-14 shrink-0 cursor-pointer select-none drop-shadow-sm"
          />
          <h1 className="text-2xl font-bold leading-tight sm:text-3xl">
            해외출장 월급루팡 모니터링
          </h1>
        </Link>
        <p className="mt-2 text-sm text-gray-500">
          해외 나가서 일은 제대로 했을까? 공무원·지방의원 국외출장·연수 기록을 한곳에서 검색·열람합니다.
        </p>
      </header>

      <div className="mb-6 rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200">
        본 사이트는 공개된 정부 보고서와 언론 보도를 사실 그대로 모아 보여주는 아카이브입니다.
        특정인에 대한 가치판단을 담지 않으며, 모든 항목은 원문 링크로 출처를 확인할 수 있습니다.
      </div>

      <NavTabs />
    </>
  );
}
