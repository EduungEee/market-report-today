import Link from "next/link";
import { ReportListItem } from "@/lib/api/reports";

interface ReportCardProps {
  report: ReportListItem;
}

/**
 * 보고서 카드 컴포넌트
 */
export function ReportCard({ report }: ReportCardProps) {
  return (
    <Link
      href={`/report/${report.id}`}
      className="block p-6 border rounded-lg hover:shadow-md transition-shadow bg-white dark:bg-slate-900"
    >
      <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-slate-50">{report.title}</h3>
      {report.summary && (
        <p className="text-sm text-slate-600 dark:text-slate-400 line-clamp-2 mb-4">{report.summary}</p>
      )}
      <div className="flex gap-4 text-xs">
        <span className="text-slate-600 dark:text-slate-400">뉴스 {report.news_count}개</span>
        <span className="text-slate-600 dark:text-slate-400">산업 {report.industry_count}개</span>
      </div>
    </Link>
  );
}
