import Link from "next/link";

/**
 * 보고서를 찾을 수 없을 때 표시되는 페이지
 */
export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4 text-slate-900 dark:text-slate-50">보고서를 찾을 수 없습니다</h1>
        <p className="text-slate-600 dark:text-slate-400 mb-8">요청하신 보고서가 존재하지 않거나 삭제되었습니다.</p>
        <Link
          href="/"
          className="px-6 py-3 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors dark:bg-slate-50 dark:text-slate-900 dark:hover:bg-slate-200"
        >
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  );
}
