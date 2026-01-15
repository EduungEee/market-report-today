import os
import requests
import json
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

load_dotenv()

# DART API 설정
DART_API_KEY = os.getenv("DART_API_KEY")

def get_financial_statements(corp_codes: List[str], bsns_year: str = "2023", reprt_code: str = "11011") -> Dict[str, Any]:
    """
    DART API(fnlttMultiAcnt)를 사용하여 여러 기업의 주요 재무지표를 가져옵니다.
    
    Args:
        corp_codes (List[str]): DART 고유번호(8자리) 리스트. 최대 100개까지 가능.
        bsns_year (str): 사업연도 (예: '2023')
        reprt_code (str): 보고서 코드
            11013: 1분기보고서
            11012: 반기보고서
            11014: 3분기보고서
            11011: 사업보고서 (결산)
            
    Returns:
        Dict[str, Any]: DART API 응답 데이터
    """
    if not DART_API_KEY:
        return {"success": False, "error": "DART_API_KEY is missing in .env file."}
    
    if not corp_codes:
        return {"success": False, "error": "corp_codes list is empty."}

    # 기업 코드를 콤마로 연결
    corp_code_param = ",".join(corp_codes)
    
    url = "https://opendart.fss.or.kr/api/fnlttMultiAcnt.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code_param,
        "bsns_year": bsns_year,
        "reprt_code": reprt_code
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("status") != "000":
            return {
                "success": False,
                "error": data.get("message", "Unknown DART API error"),
                "status": data.get("status")
            }
            
        return {
            "success": True,
            "data": data.get("list", [])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Request Error: {str(e)}"
        }

if __name__ == "__main__":
    # 테스트용 (삼성전자: 00126380, 카카오: 00334624)
    test_codes = ["00126380", "00334624"]
    year = "2023"
    
    print(f"DART API 호출 중: {test_codes}, 연도: {year}...")
    result = get_financial_statements(test_codes, year)
    
    if result.get("success"):
        financial_list = result["data"]
        print(f"성공: {len(financial_list)}개의 데이터 항목을 가져왔습니다.")
        
        # 기업별로 주요 지표 출력 (일부만)
        for item in financial_list[:10]:
            print(f"[{item.get('corp_code')}] {item.get('account_nm')}: {item.get('thstrm_amount')} {item.get('currency')}")
    else:
        print(f"실패: {result.get('error')}")
