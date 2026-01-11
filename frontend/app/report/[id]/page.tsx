import { notFound } from "next/navigation";
import { getReport } from "@/lib/api/reports";
import { NewsList } from "@/components/news-list";
import { IndustrySection } from "@/components/industry-section";

interface ReportPageProps {
  params: Promise<{ id: string }>;
}

/**
 * 보고서 상세 페이지
 */
export default async function ReportPage({ params }: ReportPageProps) {
  const { id } = await params;
  const reportId = parseInt(id, 10);

  if (isNaN(reportId)) {
    notFound();
  }

  let report;
  try {
    report = await getReport(reportId);
  } catch (error) {
    notFound();
  }

  return (
    <div className="min-h-screen">
      {/* 헤더 */}
      <header className="border-b bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4 py-6">
          <a
            href="/"
            className="text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-50 mb-2 inline-block"
          >
            ← 홈으로 돌아가기
          </a>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-50">{report.title}</h1>
          <div className="flex gap-4 mt-2 text-sm text-slate-600 dark:text-slate-400">
            <span>분석일: {new Date(report.analysis_date).toLocaleDateString("ko-KR")}</span>
            <span>생성일: {new Date(report.created_at).toLocaleDateString("ko-KR")}</span>
          </div>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="container mx-auto px-4 py-8">
        {/* 보고서 요약 */}
        {report.summary && (
          <section className="mb-12">
            <div className="p-6 bg-slate-50 dark:bg-slate-800 rounded-lg border">
              <h2 className="text-xl font-semibold mb-3 text-slate-900 dark:text-slate-50">요약</h2>
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed">{report.summary}</p>
            </div>
          </section>
        )}

        {/* 뉴스 기사 리스트 */}
        {report.news_articles.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-6 text-slate-900 dark:text-slate-50">
              관련 뉴스 ({report.news_articles.length}개)
            </h2>
            <NewsList articles={report.news_articles} />
          </section>
        )}

        {/* 산업별 분석 섹션 */}
        {report.industries.length > 0 && (
          <section className="mb-12">
            <h2 className="text-2xl font-semibold mb-6 text-slate-900 dark:text-slate-50">
              산업별 분석 ({report.industries.length}개)
            </h2>
            <div className="space-y-6">
              {report.industries.map((industry) => (
                <IndustrySection key={industry.id} industry={industry} />
              ))}
            </div>
          </section>
        )}
      </main>

      {/* 푸터 */}
      <footer className="border-t mt-12 bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4 py-6 text-center text-slate-600 dark:text-slate-400">
          <p>© 2024 주식 동향 분석 서비스. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
