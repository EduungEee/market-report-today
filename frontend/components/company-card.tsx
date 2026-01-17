import { Stock } from "@/lib/api/reports";
import { FiExternalLink } from "react-icons/fi";

interface CompanyCardProps {
  company: Stock;
}

/**
 * 회사 카드 컴포넌트
 * 회사 이름과 health_factor를 표시
 */
export function CompanyCard({ company }: CompanyCardProps) {
  const healthFactor = company.health_factor ?? 0.5;
  const healthPercentage = Math.round(healthFactor * 100);

  // health_factor에 따른 색상 결정
  const getHealthColor = (factor: number) => {
    if (factor >= 0.7) return "bg-green-500";
    if (factor >= 0.4) return "bg-yellow-500";
    return "bg-red-500";
  };

  // health_factor에 따른 텍스트 색상
  const getHealthTextColor = (factor: number) => {
    if (factor >= 0.7) return "text-green-700";
    if (factor >= 0.4) return "text-yellow-700";
    return "text-red-700";
  };

  return (
    <div className="p-4 border rounded-lg bg-white hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-2">
        <div className="flex-1 min-w-0">
          <h4 className="font-bold text-foreground truncate">{company.stock_name || "알 수 없음"}</h4>
          {company.stock_code && (
            <p className="text-xs text-muted-foreground mt-1">종목코드: {company.stock_code}</p>
          )}
        </div>
        <span className={`text-sm font-semibold ${getHealthTextColor(healthFactor)} ml-2 shrink-0`}>
          {healthPercentage}%
        </span>
      </div>

      {/* Health Factor 진행 표시줄 */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div
          className={`h-2 rounded-full transition-all ${getHealthColor(healthFactor)}`}
          style={{ width: `${healthPercentage}%` }}
        />
      </div>

      {/* 회사 선정 이유 */}
      {company.reasoning && (
        <p className="text-xs text-muted-foreground mt-2 line-clamp-2">{company.reasoning}</p>
      )}

      {/* DART 코드 (작은 글씨) */}
      {company.dart_code && (
        <p className="text-xs text-muted-foreground mt-1">DART: {company.dart_code}</p>
      )}
    </div>
  );
}
