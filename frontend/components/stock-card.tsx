import { Stock } from "@/lib/api/reports";

interface StockCardProps {
  stock: Stock;
}

/**
 * 주식 카드 컴포넌트
 */
export function StockCard({ stock }: StockCardProps) {
  const getTrendColor = (trend: string | null) => {
    switch (trend) {
      case "up":
        return "text-green-600 dark:text-green-400";
      case "down":
        return "text-red-600 dark:text-red-400";
      default:
        return "text-slate-600 dark:text-slate-400";
    }
  };

  const getTrendIcon = (trend: string | null) => {
    switch (trend) {
      case "up":
        return "📈";
      case "down":
        return "📉";
      default:
        return "➡️";
    }
  };

  const getTrendText = (trend: string | null) => {
    switch (trend) {
      case "up":
        return "상승 예상";
      case "down":
        return "하락 예상";
      default:
        return "중립";
    }
  };

  return (
    <div className="p-4 border rounded-lg bg-white dark:bg-slate-900 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="font-semibold text-slate-900 dark:text-slate-50">{stock.stock_name || "알 수 없음"}</h4>
          {stock.stock_code && <p className="text-sm text-slate-600 dark:text-slate-400">{stock.stock_code}</p>}
        </div>
        <div className={`text-right ${getTrendColor(stock.expected_trend)}`}>
          <span className="text-2xl">{getTrendIcon(stock.expected_trend)}</span>
          <p className="text-xs font-medium">{getTrendText(stock.expected_trend)}</p>
        </div>
      </div>
      {stock.confidence_score !== null && (
        <div className="mb-2">
          <div className="flex items-center justify-between text-xs text-slate-600 dark:text-slate-400 mb-1">
            <span>신뢰도</span>
            <span>{(stock.confidence_score * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
            <div
              className="bg-slate-600 dark:bg-slate-400 h-2 rounded-full transition-all"
              style={{ width: `${stock.confidence_score * 100}%` }}
            />
          </div>
        </div>
      )}
      {stock.reasoning && (
        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mt-2">{stock.reasoning}</p>
      )}
    </div>
  );
}
