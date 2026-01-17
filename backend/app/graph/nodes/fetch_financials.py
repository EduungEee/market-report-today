"""
재무제표 조회 노드
DART API를 통해 각 회사의 재무제표를 조회합니다.
"""
from typing import Dict, Any
import sys
import os
import time

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.graph.state import ReportGenerationState
from app.services.dart_api import get_company_financials


def fetch_financial_data(state: ReportGenerationState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    DART API를 통해 각 회사의 재무제표를 조회합니다.
    
    Args:
        state: 현재 상태
        
    Returns:
        업데이트된 상태
    """
    companies_by_industry = state.get("companies_by_industry", {})
    
    if not companies_by_industry:
        print("⚠️  회사 목록이 없습니다.")
        return {
            "financial_data": {},
            "errors": state.get("errors", []) + ["회사 목록이 없습니다."]
        }
    
    financial_data = {}
    errors = state.get("errors", [])
    
    # 모든 회사 수집
    all_companies = []
    for industry_name, companies in companies_by_industry.items():
        for company in companies:
            all_companies.append({
                "industry": industry_name,
                "stock_code": company.get("stock_code"),
                "stock_name": company.get("stock_name"),
                "dart_code": company.get("dart_code")
            })
    
    print(f"📊 재무제표 조회 시작: {len(all_companies)}개 회사")
    
    # 각 회사의 재무제표 조회
    for idx, company in enumerate(all_companies, 1):
        stock_code = company.get("stock_code")
        dart_code = company.get("dart_code")
        stock_name = company.get("stock_name", "알 수 없음")
        
        if not dart_code:
            print(f"⚠️  [{idx}/{len(all_companies)}] {stock_name} ({stock_code}): DART 코드 없음, 스킵")
            continue
        
        try:
            # DART API 호출 (rate limiting 고려)
            if idx > 1:
                time.sleep(0.2)  # API 호출 간격 (초당 5회 제한 고려)
            
            financials = get_company_financials(dart_code, stock_code)
            
            if financials:
                financial_data[stock_code] = financials
                print(f"✅ [{idx}/{len(all_companies)}] {stock_name} ({stock_code}): 재무제표 조회 성공")
            else:
                print(f"⚠️  [{idx}/{len(all_companies)}] {stock_name} ({stock_code}): 재무제표 조회 실패")
                # 실패해도 계속 진행
                
        except Exception as e:
            error_msg = f"{stock_name} ({stock_code}) 재무제표 조회 중 오류: {str(e)}"
            print(f"⚠️  [{idx}/{len(all_companies)}] {error_msg}")
            errors.append(error_msg)
    
    success_count = len(financial_data)
    print(f"✅ 재무제표 조회 완료: {success_count}/{len(all_companies)}개 성공")
    
    return {
        "financial_data": financial_data,
        "errors": errors
    }
