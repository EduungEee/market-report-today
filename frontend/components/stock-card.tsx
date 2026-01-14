"use client";

import { Stock } from "@/lib/api/reports";
import { getStockFinancial, StockFinancial } from "@/lib/api/reports";
import { FiTrendingUp, FiTrendingDown } from "react-icons/fi";
import { useEffect, useState } from "react";

interface StockCardProps {
  stock: Stock;
}

/**
 * 주식 카드 컴포넌트
 * 이미지 디자인에 맞춘 레이아웃
 */
export function StockCard({ stock }: StockCardProps) {
  const [financialData, setFinancialData] = useState<StockFinancial | null>(null);
  const [loading, setLoading] = useState(true);

  // expected_trend에 따라 상승/하락 결정
  const isPositive = stock.expected_trend === "up";
  const trendText = isPositive ? "상승" : stock.expected_trend === "down" ? "하락" : "중립";

  useEffect(() => {
    // 재무 데이터 가져오기
    if (stock.stock_code && stock.stock_name) {
      getStockFinancial(stock.stock_code, stock.stock_name)
        .then((data) => {
          setFinancialData(data);
          setLoading(false);
        })
        .catch((error) => {
          console.error("재무 데이터 조회 실패:", error);
          setLoading(false);
        });
    } else {
      setLoading(false);
    }
  }, [stock.stock_code, stock.stock_name]);

  return (
    <div className="p-4 border rounded-lg bg-white hover:shadow-md transition-shadow mb-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h4 className="font-bold text-foreground mb-1">{stock.stock_name || "알 수 없음"}</h4>
          <div
            className={`flex items-center gap-1 text-sm font-semibold ${
              isPositive ? "text-green-600" : stock.expected_trend === "down" ? "text-red-600" : "text-gray-600"
            }`}
          >
            {isPositive ? (
              <FiTrendingUp className="w-4 h-4" />
            ) : stock.expected_trend === "down" ? (
              <FiTrendingDown className="w-4 h-4" />
            ) : null}
            <span>{trendText}</span>
          </div>
        </div>
      </div>

      {/* 재무 데이터 표시 */}
      {loading ? (
        <div className="text-sm text-muted-foreground mb-3">재무 데이터 조회 중...</div>
      ) : financialData ? (
        <div className="mb-3 space-y-1">
          {financialData.debt_ratio !== null && (
            <div className="text-sm text-muted-foreground">
              부채비율: <span className="font-medium text-foreground">{financialData.debt_ratio.toFixed(1)}%</span>
            </div>
          )}
          {financialData.operating_profit_margin !== null && (
            <div className="text-sm text-muted-foreground">
              영업이익률:{" "}
              <span className="font-medium text-foreground">
                {financialData.operating_profit_margin.toFixed(1)}%
              </span>
            </div>
          )}
          {financialData.debt_ratio === null && financialData.operating_profit_margin === null && (
            <div className="text-sm text-muted-foreground">재무 데이터를 찾을 수 없습니다.</div>
          )}
        </div>
      ) : null}

      {stock.reasoning && <p className="text-sm text-muted-foreground mb-3 leading-relaxed">{stock.reasoning}</p>}
    </div>
  );
}
