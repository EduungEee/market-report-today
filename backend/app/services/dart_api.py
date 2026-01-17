"""
DART API 서비스
전자공시시스템(DART) OpenAPI를 사용하여 재무제표 데이터를 조회합니다.
"""
import os
import requests
from typing import Dict, Optional, List
from datetime import datetime
import time


DART_API_KEY = os.getenv("DART_API_KEY")
DART_API_BASE_URL = "https://opendart.fss.or.kr/api"


def get_financial_statements(
    corp_code: str,
    bsns_year: Optional[str] = None,
    reprt_code: str = "11011"  # 11011: 사업보고서, 11012: 반기보고서, 11013: 분기보고서
) -> Optional[Dict]:
    """
    DART API를 통해 재무제표 데이터를 조회합니다.
    
    Args:
        corp_code: DART 기업코드 (8자리)
        bsns_year: 사업연도 (YYYY 형식, 기본값: 최근 연도)
        reprt_code: 보고서 코드 (기본값: 11011 - 사업보고서)
    
    Returns:
        재무제표 데이터 딕셔너리 또는 None (실패 시)
    """
    if not DART_API_KEY:
        print("⚠️  DART_API_KEY 환경 변수가 설정되지 않았습니다.")
        return None
    
    if not corp_code or len(corp_code) != 8:
        print(f"⚠️  잘못된 DART 코드: {corp_code}")
        return None
    
    # 기본값: 최근 연도
    if not bsns_year:
        bsns_year = str(datetime.now().year - 1)
    
    url = f"{DART_API_BASE_URL}/fnlttSinglAcnt.json"
    
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code,
        "fs_div": "CFS"  # CFS: 연결재무제표, OFS: 별도재무제표
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("status") == "000":  # 정상
            return data
        else:
            error_msg = data.get("message", "알 수 없는 오류")
            print(f"⚠️  DART API 오류: {error_msg} (corp_code: {corp_code})")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️  DART API 요청 실패: {e} (corp_code: {corp_code})")
        return None
    except Exception as e:
        print(f"⚠️  DART API 처리 실패: {e} (corp_code: {corp_code})")
        return None


def parse_financial_data(dart_data: Dict) -> Dict:
    """
    DART API 응답 데이터를 파싱하여 필요한 재무 지표를 추출합니다.
    
    Args:
        dart_data: DART API 응답 데이터
    
    Returns:
        파싱된 재무 데이터 딕셔너리
    """
    if not dart_data or not dart_data.get("list"):
        return {}
    
    financial_items = {}
    
    # 필요한 계정과목 매핑
    account_mapping = {
        "매출액": "revenue",
        "영업이익": "operating_profit",
        "당기순이익": "net_income",
        "자산총계": "total_assets",
        "부채총계": "total_debt",
        "자본총계": "equity",
        "유동자산": "current_assets",
        "유동부채": "current_liabilities"
    }
    
    for item in dart_data.get("list", []):
        account_nm = item.get("account_nm", "")
        thstrm_amount = item.get("thstrm_amount", "0")  # 당기금액
        frmtrm_amount = item.get("frmtrm_amount", "0")  # 전기금액
        
        # 계정과목이 매핑에 있는 경우
        for korean_name, english_name in account_mapping.items():
            if korean_name in account_nm:
                try:
                    amount = int(thstrm_amount.replace(",", "")) if thstrm_amount else 0
                    prev_amount = int(frmtrm_amount.replace(",", "")) if frmtrm_amount else 0
                    
                    financial_items[english_name] = amount
                    
                    # 성장률 계산 (매출액, 영업이익, 당기순이익)
                    if english_name in ["revenue", "operating_profit", "net_income"] and prev_amount > 0:
                        growth_key = f"{english_name}_growth"
                        financial_items[growth_key] = ((amount - prev_amount) / prev_amount) * 100
                    
                except (ValueError, AttributeError):
                    pass
                break
    
    return financial_items


def get_company_financials(
    dart_code: str,
    stock_code: Optional[str] = None
) -> Optional[Dict]:
    """
    회사의 재무제표 데이터를 조회하고 파싱합니다.
    
    Args:
        dart_code: DART 기업코드 (8자리)
        stock_code: 종목코드 (6자리, 선택사항)
    
    Returns:
        파싱된 재무 데이터 딕셔너리 또는 None
    """
    if not dart_code:
        return None
    
    # API 호출 제한을 고려하여 짧은 대기
    time.sleep(0.1)
    
    dart_data = get_financial_statements(dart_code)
    
    if not dart_data:
        return None
    
    financial_data = parse_financial_data(dart_data)
    
    # 추가 계산 지표
    if financial_data.get("revenue") and financial_data.get("operating_profit"):
        financial_data["operating_margin"] = (financial_data["operating_profit"] / financial_data["revenue"]) * 100
    
    if financial_data.get("total_assets") and financial_data.get("total_debt"):
        financial_data["debt_ratio"] = (financial_data["total_debt"] / financial_data["total_assets"]) * 100
    
    if financial_data.get("current_assets") and financial_data.get("current_liabilities"):
        financial_data["current_ratio"] = financial_data["current_assets"] / financial_data["current_liabilities"] if financial_data["current_liabilities"] > 0 else 0
    
    if financial_data.get("equity") and financial_data.get("total_assets"):
        financial_data["equity_ratio"] = (financial_data["equity"] / financial_data["total_assets"]) * 100
    
    return financial_data
