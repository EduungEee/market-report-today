"""
Health Factor 계산 노드
재무 데이터를 기반으로 각 회사의 health_factor를 계산합니다.
"""
from typing import Dict, Any
import sys
import os

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.graph.state import ReportGenerationState


def calculate_health_factor(state: ReportGenerationState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    재무 데이터를 기반으로 각 회사의 health_factor를 계산합니다.
    
    계산 요소:
    - 수익성 (영업이익률, 가중치: 0.3)
    - 부채비율 = 부채총계 / 자본총계 (가중치: 0.3)
    - 유동비율 = 유동자산 / 유동부채 (가중치: 0.2)
    - 자기자본비율 = 자본총계 / 자산총계 (가중치: 0.2)
    
    Args:
        state: 현재 상태
        
    Returns:
        업데이트된 상태
    """
    financial_data = state.get("financial_data", {})
    companies_by_industry = state.get("companies_by_industry", {})
    
    if not financial_data:
        print("⚠️  재무 데이터가 없습니다.")
        return {
            "health_factors": {},
            "errors": state.get("errors", []) + ["재무 데이터가 없습니다."]
        }
    
    health_factors = {}
    
    # 모든 회사 수집
    all_companies = []
    for industry_name, companies in companies_by_industry.items():
        for company in companies:
            stock_code = company.get("stock_code")
            if stock_code:
                all_companies.append({
                    "stock_code": stock_code,
                    "stock_name": company.get("stock_name", "알 수 없음"),
                    "industry": industry_name
                })
    
    print(f"💊 Health Factor 계산 시작: {len(all_companies)}개 회사")
    
    for company in all_companies:
        stock_code = company.get("stock_code")
        stock_name = company.get("stock_name")
        financials = financial_data.get(stock_code, {})
        
        if not financials:
            # 재무 데이터가 없으면 기본값
            health_factors[stock_code] = {
                "health_factor": 0.5,
                "calculation_details": {
                    "profitability_score": 0.5,
                    "debt_ratio_score": 0.5,
                    "current_ratio_score": 0.5,
                    "equity_ratio_score": 0.5
                },
                "note": "재무 데이터 없음"
            }
            continue
        
        # 1. 수익성 (영업이익률, 높을수록 좋음, 가중치: 0.3)
        operating_margin = financials.get("operating_margin", 0)
        # 음수면 0.0, 15% 이상이면 1.0, 그 사이는 선형 보간
        profitability_score = max(0.0, min(1.0, operating_margin / 15.0))
        
        # 2. 부채비율 = 부채총계 / 자본총계 (낮을수록 좋음, 가중치: 0.3)
        total_debt = financials.get("total_debt", 0)
        equity = financials.get("equity", 0)
        if equity > 0:
            debt_ratio = (total_debt / equity) * 100  # 백분율로 변환
        else:
            debt_ratio = 100.0  # 자본이 0이면 최악으로 설정
        
        # 부채비율 점수: 0% ~ 100% 범위를 1.0 ~ 0.0으로 선형 변환
        # 0% 이하면 1.0, 100% 이상이면 0.0
        debt_ratio_score = max(0.0, min(1.0, (100 - debt_ratio) / 100.0))
        
        # 3. 유동비율 = 유동자산 / 유동부채 (높을수록 좋음, 가중치: 0.2)
        current_assets = financials.get("current_assets", 0)
        current_liabilities = financials.get("current_liabilities", 0)
        if current_liabilities > 0:
            current_ratio = current_assets / current_liabilities
        else:
            current_ratio = 0.0
        
        # 유동비율 점수: 0 ~ 2.0 범위를 0.0 ~ 1.0으로 선형 변환
        # 2.0 이상이면 1.0, 그 사이는 선형 보간
        current_ratio_score = max(0.0, min(1.0, current_ratio / 2.0))
        
        # 4. 자기자본비율 = 자본총계 / 자산총계 (높을수록 좋음, 가중치: 0.2)
        total_assets = financials.get("total_assets", 0)
        if total_assets > 0:
            equity_ratio = (equity / total_assets) * 100  # 백분율로 변환
        else:
            equity_ratio = 0.0
        
        # 자기자본비율 점수: 0% ~ 100% 범위를 0.0 ~ 1.0으로 선형 변환
        # 100%면 1.0, 0%면 0.0
        equity_ratio_score = max(0.0, min(1.0, equity_ratio / 100.0))
        
        # 최종 health_factor 계산 (가중 평균)
        health_factor = (
            profitability_score * 0.3 +
            debt_ratio_score * 0.3 +
            current_ratio_score * 0.2 +
            equity_ratio_score * 0.2
        )
        
        # 0-1 범위로 제한
        health_factor = max(0.0, min(1.0, health_factor))
        
        health_factors[stock_code] = {
            "health_factor": health_factor,
            "calculation_details": {
                "profitability_score": profitability_score,
                "debt_ratio_score": debt_ratio_score,
                "current_ratio_score": current_ratio_score,
                "equity_ratio_score": equity_ratio_score
            }
        }
        
        print(f"✅ {stock_name} ({stock_code}): Health Factor = {health_factor:.2f}")
    
    print(f"✅ Health Factor 계산 완료: {len(health_factors)}개 회사")
    
    return {
        "health_factors": health_factors,
        "errors": state.get("errors", [])
    }
