import { Industry } from "@/lib/api/reports";
import { StockCard } from "./stock-card";

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
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200";
      case "low":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200";
    }
  };

  const getTrendBadgeColor = (trend: string | null) => {
    switch (trend) {
      case "positive":
        return "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200";
      case "negative":
        return "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200";
      default:
        return "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-200";
    }
  };

  return (
    <div className="p-6 border rounded-lg bg-white dark:bg-slate-900">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-50 mb-2">{industry.industry_name}</h3>
          <div className="flex gap-2 flex-wrap">
            {industry.impact_level && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${getImpactBadgeColor(industry.impact_level)}`}
              >
                영향도:{" "}
                {industry.impact_level === "high" ? "높음" : industry.impact_level === "medium" ? "보통" : "낮음"}
              </span>
            )}
            {industry.trend_direction && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-medium ${getTrendBadgeColor(industry.trend_direction)}`}
              >
                {industry.trend_direction === "positive"
                  ? "긍정적"
                  : industry.trend_direction === "negative"
                  ? "부정적"
                  : "중립"}
              </span>
            )}
          </div>
        </div>
      </div>
      {industry.impact_description && (
        <p className="text-slate-600 dark:text-slate-400 mb-4">{industry.impact_description}</p>
      )}
      {industry.stocks.length > 0 && (
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-slate-50 mb-3">
            관련 주식 ({industry.stocks.length}개)
          </h4>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {industry.stocks.map((stock) => (
              <StockCard key={stock.id} stock={stock} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
