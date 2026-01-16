import os
import requests
import json
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class CorpCodeItem:
    corp_code: str         # 고유번호
    corp_name: str         # 종목명
    corp_eng_name: str     # 종목영문명
    stock_code: str        # 종목코드

@dataclass
class FinancialStatementItem:
    rcept_no: str         # 접수번호
    reprt_code: str       # 보고서 코드
    bsns_year: str        # 사업연도
    corp_code: str        # 고유번호
    stock_code: str       # 종목코드
    fs_div: str           # 재무제표 구분 (CFS: 연결재무제표, OFS: 재무제표)
    fs_nm: str            # 재무제표 명칭
    sj_div: str           # 계정구분 (BS: 재무상태표, IS: 손익계산서)
    sj_nm: str            # 계정명칭
    account_nm: str       # 항목명
    thstrm_nm: str        # 당기 명칭
    thstrm_dt: str        # 당기 일자
    thstrm_amount: str    # 당기 금액
    frmtrm_nm: str        # 전기 명칭
    frmtrm_dt: str        # 전기 일자
    frmtrm_amount: str    # 전기 금액
    bfefrmtrm_nm: str     # 전전기 명칭
    bfefrmtrm_dt: str     # 전전기 일자
    bfefrmtrm_amount: str # 전전기 금액
    ord: str              # 계정과목 정렬순서
    currency: str         # 통화 단위

load_dotenv()

# DART API 설정
DART_API_KEY = os.getenv("DART_API_KEY")

# 현재 파일의 디렉토리 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORPCODE_PATH = os.path.join(BASE_DIR, "CORPCODE_filtered.xml")

def get_corp_code_by_stock_code(stock_code: str) -> Optional[CorpCodeItem]:
    """
    상장 주식 코드(6자리)를 사용하여 DART 고유번호(8자리) 및 기업 정보를 찾습니다.
    
    Args:
        stock_code (str): 상장 주식 코드 (예: '005930')
        
    Returns:
        Optional[CorpCodeItem]: 기업 정보 객체, 찾지 못한 경우 None
    """
    if not os.path.exists(CORPCODE_PATH):
        print(f"Error: {CORPCODE_PATH} not found.")
        return None
        
    try:
        tree = ET.parse(CORPCODE_PATH)
        root = tree.getroot()
        
        for list_node in root.findall('list'):
            sc_node = list_node.find('stock_code')
            if sc_node is not None and sc_node.text == stock_code:
                return CorpCodeItem(
                    corp_code=list_node.findtext('corp_code', ''),
                    corp_name=list_node.findtext('corp_name', ''),
                    corp_eng_name=list_node.findtext('corp_eng_name', ''),
                    stock_code=sc_node.text
                )
                    
        return None
    except Exception as e:
        print(f"Error parsing {CORPCODE_PATH}: {e}")
        return None

def get_financial_statements(corp_codes: List[str], bsns_year: str = "2023", reprt_code: str = "11011") -> List[FinancialStatementItem]:
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
        List[FinancialStatementItem]: DART API 응답 데이터 (기업별 재무지표 리스트)
        
    Raises:
        ValueError: API 키 누락, 빈 corp_codes 리스트 또는 DART API 상태 오류 시 발생
        RuntimeError: 네트워크 요청 오류 시 발생
    """
    if not DART_API_KEY:
        raise ValueError("DART_API_KEY is missing in .env file.")
    
    if not corp_codes:
        raise ValueError("corp_codes list is empty.")

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
            raise ValueError(f"DART API Error ({data.get('status')}): {data.get('message', 'Unknown error')}")
            
        return [FinancialStatementItem(**item) for item in data.get("list", [])]
        
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Request Error: {str(e)}")
    except Exception as e:
        raise e

if __name__ == "__main__":
    # 1. stock_code -> CorpCodeItem 변환 테스트
    test_stock_code = "005930" # 삼성전자
    print(f"Stock Code '{test_stock_code}'의 기업 정보 찾는 중...")
    corp_info = get_corp_code_by_stock_code(test_stock_code)
    
    if corp_info:
        print(f"찾음! 기업명: {corp_info.corp_name}, Corp Code: {corp_info.corp_code}")
        
        # 2. 재무제표 조회 테스트
        test_codes = [corp_info.corp_code, "00334624"] # 삼성전자(검색), 카카오(고정)
        year = "2023"
        
        print(f"\nDART API 호출 중: {test_codes}, 연도: {year}...")
        try:
            financial_list = get_financial_statements(test_codes, year)
            print(f"성공: {len(financial_list)}개의 데이터 항목을 가져왔습니다.")
            
            # 기업별로 주요 지표 출력 (일부만)
            for item in financial_list[:10]:
                print(f"[{item.corp_code}] {item.account_nm}: {item.thstrm_amount} {item.currency}")
        except Exception as e:
            print(f"실패: {e}")
    else:
        print("기업 정보를 찾지 못했습니다.")
