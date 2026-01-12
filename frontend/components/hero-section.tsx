/**
 * Hero 섹션 컴포넌트
 * 홈페이지 상단의 주요 가입 유도 섹션
 * Magic UI 효과 포함
 */
export function HeroSection() {
  return (
    <section className="relative mb-16 text-center py-20 px-4 bg-gradient-to-b from-background via-background/95 to-background rounded-lg overflow-hidden">
      {/* Magic UI: Background particles effect */}
      <div className="absolute inset-0 opacity-30 pointer-events-none">
        <div className="absolute top-10 left-10 w-2 h-2 rounded-full bg-primary/40 animate-pulse" style={{ animationDelay: '0s' }} />
        <div className="absolute top-20 right-20 w-1.5 h-1.5 rounded-full bg-primary/30 animate-pulse" style={{ animationDelay: '0.5s' }} />
        <div className="absolute bottom-20 left-1/4 w-2.5 h-2.5 rounded-full bg-primary/20 animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute bottom-10 right-1/3 w-1 h-1 rounded-full bg-primary/40 animate-pulse" style={{ animationDelay: '1.5s' }} />
      </div>

      {/* Content */}
      <div className="relative z-10">
        <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 text-foreground bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
          매일 업데이트되는 주식 분석 보고서
        </h2>
        <p className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto">
          최신 뉴스를 AI로 분석하여 유망 산업과 주식을 파악하세요
        </p>
        <button className="relative px-8 py-4 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-all duration-300 text-lg font-semibold shadow-lg hover:shadow-xl hover:scale-105 active:scale-95">
          <span className="relative z-10">무료로 시작하기</span>
          {/* Shimmer effect */}
          <span className="absolute inset-0 rounded-lg bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-shimmer-slide" />
        </button>
      </div>
    </section>
  );
}
