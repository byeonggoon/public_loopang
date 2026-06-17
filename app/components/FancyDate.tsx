"use client";

import { useEffect, useRef, useState } from "react";

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

function pad(n: number): string {
  return String(n).padStart(2, "0");
}
function toISO(y: number, m: number, d: number): string {
  return `${y}-${pad(m + 1)}-${pad(d)}`;
}

// 네이티브 date input 대신 직접 그리는 달력 — 선택값은 hidden input 으로 폼(GET) 제출.
export default function FancyDate({
  name,
  defaultValue,
}: {
  name: string;
  defaultValue: string;
}) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(defaultValue); // "YYYY-MM-DD" | ""
  const [view, setView] = useState(() => {
    const base = defaultValue ? new Date(defaultValue + "T00:00:00") : new Date();
    return { y: base.getFullYear(), m: base.getMonth() };
  });
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, []);

  const startDow = new Date(view.y, view.m, 1).getDay();
  const daysInMonth = new Date(view.y, view.m + 1, 0).getDate();
  const cells: (number | null)[] = [
    ...Array<null>(startDow).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  const todayISO = toISO(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());

  function shiftMonth(delta: number) {
    setView((v) => {
      const d = new Date(v.y, v.m + delta, 1);
      return { y: d.getFullYear(), m: d.getMonth() };
    });
  }

  return (
    <div className="relative" ref={ref}>
      <input type="hidden" name={name} value={value} />
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex h-10 w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-3 text-sm shadow-sm transition hover:border-gray-400 hover:bg-gray-50 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/30 dark:border-gray-700 dark:bg-gray-950 dark:hover:border-gray-600 dark:hover:bg-gray-900"
      >
        <span className={value ? "text-gray-900 dark:text-gray-100" : "text-gray-400"}>
          {value || "날짜 선택"}
        </span>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4 text-gray-400">
          <rect x="3" y="4" width="18" height="18" rx="2" />
          <path d="M16 2v4M8 2v4M3 10h18" strokeLinecap="round" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-30 mt-1.5 w-64 rounded-xl border border-gray-200 bg-white p-3 shadow-xl ring-1 ring-black/5 dark:border-gray-700 dark:bg-gray-900 dark:ring-white/10">
          {/* 월 이동 헤더 */}
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              onClick={() => shiftMonth(-1)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="이전 달"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4">
                <path d="m15 18-6-6 6-6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
            <span className="text-sm font-semibold">{view.y}년 {view.m + 1}월</span>
            <button
              type="button"
              onClick={() => shiftMonth(1)}
              className="flex h-7 w-7 items-center justify-center rounded-md text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
              aria-label="다음 달"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} className="h-4 w-4">
                <path d="m9 18 6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </button>
          </div>

          {/* 요일 */}
          <div className="grid grid-cols-7 gap-0.5 text-center text-xs">
            {WEEKDAYS.map((w, i) => (
              <div key={w} className={`py-1 font-medium ${i === 0 ? "text-rose-500" : i === 6 ? "text-blue-500" : "text-gray-400"}`}>
                {w}
              </div>
            ))}
            {/* 날짜 */}
            {cells.map((day, idx) => {
              if (day === null) return <div key={`b${idx}`} />;
              const iso = toISO(view.y, view.m, day);
              const selected = iso === value;
              const isToday = iso === todayISO;
              return (
                <button
                  key={iso}
                  type="button"
                  onClick={() => {
                    setValue(iso);
                    setOpen(false);
                  }}
                  className={`flex h-8 items-center justify-center rounded-md text-sm transition-colors ${
                    selected
                      ? "bg-blue-600 font-semibold text-white"
                      : isToday
                        ? "font-semibold text-blue-600 ring-1 ring-inset ring-blue-300 dark:text-blue-400"
                        : "text-gray-700 hover:bg-gray-100 dark:text-gray-200 dark:hover:bg-gray-800"
                  }`}
                >
                  {day}
                </button>
              );
            })}
          </div>

          {/* 지우기 */}
          <div className="mt-2 flex justify-end border-t border-gray-100 pt-2 dark:border-gray-800">
            <button
              type="button"
              onClick={() => {
                setValue("");
                setOpen(false);
              }}
              className="rounded-md px-2 py-1 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200"
            >
              지우기
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
