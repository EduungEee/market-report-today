import { HeroSection } from "@/components/hero-section";
import { TodayReports } from "@/components/today-reports";

/**
 * 홈페이지 메인 컴포넌트
 */
export default function Home() {
  return (
    <div className="min-h-screen">
      {/* 헤더 */}
      <header className="border-b bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50">📈 주식 동향 분석</h1>
          <p className="text-slate-600 dark:text-slate-400 mt-1">뉴스 기반 주식 시장 동향 분석 서비스</p>
        </div>
      </header>

      {/* 메인 컨텐츠 */}
      <main className="container mx-auto px-4 py-8">
        {/* Hero 섹션 */}
        <HeroSection />

        {/* 오늘의 보고서 섹션 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 text-slate-900 dark:text-slate-50">오늘의 보고서</h2>
          <TodayReports />
        </section>

        {/* 분석 방식 소개 섹션 */}
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-6 text-slate-900 dark:text-slate-50">분석 방식</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="p-6 border rounded-lg bg-white dark:bg-slate-900">
              <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-slate-50">📰 뉴스 수집</h3>
              <p className="text-slate-600 dark:text-slate-400">최신 뉴스를 자동으로 수집하여 분석합니다</p>
            </div>
            <div className="p-6 border rounded-lg bg-white dark:bg-slate-900">
              <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-slate-50">🤖 AI 분석</h3>
              <p className="text-slate-600 dark:text-slate-400">AI가 뉴스의 파급효과와 영향을 분석합니다</p>
            </div>
            <div className="p-6 border rounded-lg bg-white dark:bg-slate-900">
              <h3 className="font-semibold text-lg mb-2 text-slate-900 dark:text-slate-50">📊 보고서 생성</h3>
              <p className="text-slate-600 dark:text-slate-400">분석 결과를 보고서로 정리하여 제공합니다</p>
            </div>
          </div>
        </section>
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
