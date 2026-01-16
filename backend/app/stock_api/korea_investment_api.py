import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

load_dotenv()

@dataclass
class StockPriceSummary:
    prdy_vrss: str         # 전일 대비
    prdy_vrss_sign: str    # 전일 대비 부호
    prdy_ctrt: str         # 전일 대비율
    stck_prdy_clpr: str    # 전일대비 종가
    acml_vol: str          # 누적 거래량
    acml_tr_pbmn: str      # 누적 거래대금
    hts_kor_isnm: str      # 한글 종목명
    stck_prpr: str         # 주식 현재가

@dataclass
class StockPriceHistory:
    stck_bsop_date: str    # 주식 영업일자
    stck_cntg_hour: str    # 주식 체결시간
    stck_prpr: str         # 주식 현재가
    stck_oprc: str         # 주식 시가
    stck_hgpr: str         # 주식 최고가
    stck_lwpr: str         # 주식 최저가
    cntg_vol: str          # 체결 거래량
    acml_tr_pbmn: str      # 누적 거래대금

@dataclass
class KoreaInvestmentResponse:
    rt_cd: str                            # 성공 실패 여부
    msg_cd: str                           # 응답코드
    msg1: str                             # 응답 메세지
    output1: Optional[StockPriceSummary] = None  # 응답 상세 (요약)
    output2: List[StockPriceHistory] = field(default_factory=list) # 응답 상세 (내역)

# 한국투자증권 API 설정
APP_KEY = os.getenv("KOREA_INVESTMENT_API_KEY")
APP_SECRET = os.getenv("KOREA_INVESTMENT_API_SECRET")
BASE_URL = "https://openapi.koreainvestment.com:9443"
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), ".token_cache.json")

def get_access_token() -> Optional[str]:
    """
    한국투자증권 OAuth2 접근 토큰을 발급받거나 캐시된 토큰을 반환합니다.
    """
    # 1. 캐시된 토큰 확인
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cache = json.load(f)
                access_token = cache.get("access_token")
                expired_at_str = cache.get("expired_at")
                
                if access_token and expired_at_str:
                    expired_at = datetime.fromisoformat(expired_at_str)
                    # 여유 있게 1분 전에 만료된 것으로 간주
                    if expired_at > datetime.now() + timedelta(minutes=1):
                        return access_token
        except Exception as e:
            print(f"⚠️ Cache read error: {e}")

    # 2. 새로운 토큰 발급
    if not APP_KEY or not APP_SECRET:
        print("⚠️ KOREA_INVESTMENT_API_KEY or APP_SECRET is missing.")
        return None

    url = f"{BASE_URL}/oauth2/tokenP"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to get access token: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        data = response.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 86400) # 기본 24시간
        
        # 3. 새로운 토큰 캐시 저장
        if access_token:
            expired_at = datetime.now() + timedelta(seconds=int(expires_in))
            cache_data = {
                "access_token": access_token,
                "expired_at": expired_at.isoformat()
            }
            try:
                with open(TOKEN_CACHE_FILE, "w") as f:
                    json.dump(cache_data, f)
            except Exception as e:
                print(f"⚠️ Cache write error: {e}")
                
        return access_token
    except Exception as e:
        print(f"⚠️ API Exception: {e}")
        return None

def get_yesterday_prices(stock_code: str) -> KoreaInvestmentResponse:
    """
    한국투자증권 API를 사용하여 특정 종목의 전날 시가와 종가를 포함한 데이터를 가져옵니다.
    '주식일별분봉조회' API를 사용합니다. (TR_ID: FHKST03010230)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        
    Returns:
        KoreaInvestmentResponse: API 응답 데이터를 구조화한 객체
    """
    token = get_access_token()
    if not token:
        return KoreaInvestmentResponse(rt_cd="1", msg_cd="TOKEN_ERROR", msg1="Failed to get access token")

    # 어제 날짜 구하기 (YYYYMMDD)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    url = f"{BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-time-dailychartprice"
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": APP_KEY,
        "appsecret": APP_SECRET,
        "tr_id": "FHKST03010230",
        "custtype": "P" # 개인
    }
    
    params = {
        "FID_COND_MRKT_DIV_CODE": "J", # KRX
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_HOUR_1": "160000",
        "FID_INPUT_DATE_1": yesterday,
        "FID_PW_DATA_INCU_YN": "Y",
        "FID_FAKE_TICK_INCU_YN": ""
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rt_cd = data.get("rt_cd", "1")
        msg_cd = data.get("msg_cd", "")
        msg1 = data.get("msg1", "")
        
        if rt_cd != "0":
            return KoreaInvestmentResponse(rt_cd=rt_cd, msg_cd=msg_cd, msg1=msg1)
        
        raw_output1 = data.get("output1", {})
        raw_output2 = data.get("output2", [])
        
        output1 = StockPriceSummary(**raw_output1) if raw_output1 else None
        output2 = [StockPriceHistory(**item) for item in raw_output2]
        
        return KoreaInvestmentResponse(
            rt_cd=rt_cd,
            msg_cd=msg_cd,
            msg1=msg1,
            output1=output1,
            output2=output2
        )
        
    except Exception as e:
        return KoreaInvestmentResponse(rt_cd="1", msg_cd="NET_ERROR", msg1=str(e))

if __name__ == "__main__":
    # 테스트용 (삼성전자: 005930)
    stock = "005930"
    print(f"한국투자증권 API 호출 중 (종목: {stock})...")
    result = get_yesterday_prices(stock)
    
    if result.rt_cd == "0":
        if result.output1:
            print(f"종목명: {result.output1.hts_kor_isnm}")
            print(f"현재가: {result.output1.stck_prpr}")
            print(f"전일대비 종가: {result.output1.stck_prdy_clpr}")
        
        if result.output2:
            print(f"\n최근 영업일({result.output2[0].stck_bsop_date}) 가격 정보:")
            # 종가: 리스트의 첫 번째 항목
            print(f"종가: {result.output2[0].stck_prpr}")
            # 시가: 해당 일자의 마지막 항목 (영업일이 같은지 확인 필요하나 단순화)
            target_date = result.output2[0].stck_bsop_date
            day_data = [item for item in result.output2 if item.stck_bsop_date == target_date]
            if day_data:
                print(f"시가: {day_data[-1].stck_oprc}")
    else:
        print(f"실패: {result.msg1} (코드: {result.msg_cd})")
