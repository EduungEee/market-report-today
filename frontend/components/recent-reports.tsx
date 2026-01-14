import { Suspense } from "react";
import { getAllReports } from "@/lib/api/reports";
import { ReportCard } from "./report-card";

/**
 * 로딩 스켈레톤 컴포넌트
 */
function ReportListSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="p-6 border rounded-lg animate-pulse bg-white">
          <div className="h-6 bg-slate-200 rounded mb-2" />
          <div className="h-4 bg-slate-200 rounded mb-4 w-3/4" />
          <div className="flex gap-4">
            <div className="h-3 bg-slate-200 rounded w-16" />
            <div className="h-3 bg-slate-200 rounded w-16" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * 보고서 목록 컴포넌트 (Server Component)
 */
async function ReportList() {
  try {
    const reports = await getAllReports(10);

    if (reports.length === 0) {
      return (
        <div className="text-center py-12">
          <p className="text-slate-600">작성된 보고서가 없습니다.</p>
        </div>
      );
    }

    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {reports.map((report) => (
          <ReportCard key={report.id} report={report} />
        ))}
      </div>
    );
  } catch (error) {
    // 백엔드 연결 실패 시 에러 메시지 표시
    // 페이지는 정상적으로 렌더링됨
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-4">
          <svg
            className="w-8 h-8 text-slate-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
        </div>
        <p className="text-slate-600 text-lg font-medium mb-2">리포트를 가져올 수 없습니다</p>
        <p className="text-slate-500 text-sm">서버에 연결할 수 없습니다. 잠시 후 다시 시도해주세요.</p>
      </div>
    );
  }
}

/**
 * 최신 보고서 목록 컴포넌트
 * Suspense로 감싸서 로딩 상태를 처리합니다.
 */
export function RecentReports() {
  return (
    <Suspense fallback={<ReportListSkeleton />}>
      <ReportList />
    </Suspense>
  );
}
