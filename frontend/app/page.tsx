import { Navbar } from "@/components/navbar";
import { HeroSection } from "@/components/hero-section";
import { TodayReports } from "@/components/today-reports";

/**
 * 홈페이지 메인 컴포넌트
 */
export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <Navbar />

      {/* 메인 컨텐츠 */}
      <main className="pt-16">
        {/* Hero 섹션 - 서비스 소개 */}
        <section id="service-intro" className="container mx-auto px-4 py-16">
          <HeroSection />
        </section>

        {/* 오늘의 보고서 섹션 */}
        <section id="today-reports" className="container mx-auto px-4 py-16">
          <h2 className="text-3xl font-bold mb-8 text-foreground">오늘의 보고서</h2>
          <TodayReports />
        </section>

        {/* 기능란 섹션 */}
        <section id="features" className="container mx-auto px-4 py-16">
          <h2 className="text-3xl font-bold mb-8 text-foreground">기능란</h2>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="p-6 border rounded-lg bg-card hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-lg mb-2 text-card-foreground">📰 뉴스 수집</h3>
              <p className="text-muted-foreground">최신 뉴스를 자동으로 수집하여 분석합니다</p>
            </div>
            <div className="p-6 border rounded-lg bg-card hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-lg mb-2 text-card-foreground">🤖 AI 분석</h3>
              <p className="text-muted-foreground">AI가 뉴스의 파급효과와 영향을 분석합니다</p>
            </div>
            <div className="p-6 border rounded-lg bg-card hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-lg mb-2 text-card-foreground">📊 보고서 생성</h3>
              <p className="text-muted-foreground">분석 결과를 보고서로 정리하여 제공합니다</p>
            </div>
          </div>
        </section>
      </main>

      {/* 푸터 */}
      <footer className="border-t mt-12 bg-background">
        <div className="container mx-auto px-4 py-6 text-center text-muted-foreground">
          <p>© 2024 주식 동향 분석 서비스. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
