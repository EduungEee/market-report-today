import { Industry } from "@/lib/api/reports";
import { CompanyCard } from "./company-card";
import { FiExternalLink } from "react-icons/fi";

interface IndustrySectionProps {
  industry: Industry;
}

/**
 * 산업별 분석 섹션 컴포넌트
 */
export function IndustrySection({ industry }: IndustrySectionProps) {
  const getImpactBadgeColor = (level: string | null) => {
    switch (level) {
      case "high":
        return "bg-red-100 text-red-700";
      case "medium":
        return "bg-yellow-100 text-yellow-700";
      case "low":
        return "bg-green-100 text-green-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getImpactText = (level: string | null) => {
    switch (level) {
      case "high":
        return "높은 영향";
      case "medium":
        return "중간 영향";
      case "low":
        return "낮은 영향";
      default:
        return "영향";
    }
  };

  const getTrendBadgeColor = (trend: string | null) => {
    switch (trend) {
      case "positive":
        return "bg-green-100 text-green-700";
      case "negative":
        return "bg-red-100 text-red-700";
      case "neutral":
        return "bg-gray-100 text-gray-700";
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  const getTrendText = (trend: string | null) => {
    switch (trend) {
      case "positive":
        return "긍정적";
      case "negative":
        return "부정적";
      case "neutral":
        return "중립적";
      default:
        return "중립적";
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg border shadow-sm mb-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-foreground">{industry.industry_name}</h3>
        <div className="flex items-center gap-2">
          {industry.trend_direction && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${getTrendBadgeColor(industry.trend_direction)}`}
            >
              {getTrendText(industry.trend_direction)}
            </span>
          )}
          {industry.impact_level && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${getImpactBadgeColor(industry.impact_level)}`}
            >
              {getImpactText(industry.impact_level)}
            </span>
          )}
        </div>
      </div>

      {/* 영향 설명 */}
      {industry.impact_description && (
        <p className="text-muted-foreground leading-relaxed mb-4">{industry.impact_description}</p>
      )}

      {/* 산업 선정 이유 */}
      {industry.selection_reason && (
        <div className="mb-4 p-3 bg-blue-50 rounded-lg border border-blue-200">
          <h4 className="text-sm font-semibold text-blue-900 mb-1">선정 이유</h4>
          <p className="text-sm text-blue-800 leading-relaxed">{industry.selection_reason}</p>
        </div>
      )}

      {/* 관련 뉴스 기사들 */}
      {industry.related_news && industry.related_news.length > 0 && (
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-foreground mb-2">관련 뉴스 기사</h4>
          <div className="space-y-2">
            {industry.related_news.map((news) => (
              <div key={news.news_id} className="p-3 bg-gray-50 rounded-lg border">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    {news.url ? (
                      <a
                        href={news.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm font-medium text-primary hover:text-primary/80 hover:underline inline-flex items-center gap-1"
                      >
                        <span className="truncate">{news.title}</span>
                        <FiExternalLink className="w-3 h-3 shrink-0" />
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-foreground">{news.title}</p>
                    )}
                    {news.published_at && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(news.published_at).toLocaleDateString("ko-KR")}
                      </p>
                    )}
                    {news.impact_on_industry && (
                      <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                        {news.impact_on_industry}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 해당 산업군 회사 목록 */}
      {industry.stocks && industry.stocks.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-3">
            추천 회사 ({industry.stocks.length}개)
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {industry.stocks.map((stock) => (
              <CompanyCard key={stock.id} company={stock} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

