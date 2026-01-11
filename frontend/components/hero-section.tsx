/**
 * Hero 섹션 컴포넌트
 * 홈페이지 상단의 주요 가입 유도 섹션
 */
export function HeroSection() {
  return (
    <section className="mb-16 text-center py-16 px-4 bg-gradient-to-b from-slate-50 to-white dark:from-slate-900 dark:to-slate-800 rounded-lg">
      <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 dark:text-slate-50">
        매일 업데이트되는 주식 분석 보고서
      </h2>
      <p className="text-lg md:text-xl text-slate-600 dark:text-slate-400 mb-8 max-w-2xl mx-auto">
        최신 뉴스를 AI로 분석하여 유망 산업과 주식을 파악하세요
      </p>
      <button className="px-8 py-4 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition-colors dark:bg-slate-50 dark:text-slate-900 dark:hover:bg-slate-200 text-lg font-semibold">
        무료로 시작하기
      </button>
    </section>
  );
}
