import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, Optional

load_dotenv()

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

def get_yesterday_prices(stock_code: str) -> Dict[str, Any]:
    """
    한국투자증권 API를 사용하여 특정 종목의 전날 시가와 종가를 가져옵니다.
    '주식일별분봉조회' API를 사용합니다. (TR_ID: FHKST03010230)
    
    Args:
        stock_code (str): 종목코드 (6자리)
        
    Returns:
        Dict[str, Any]: 전날 시가, 종가 데이터를 포함하는 딕셔너리
    """
    token = get_access_token()
    if not token:
        return {"success": False, "error": "Failed to get access token"}

    # 어제 날짜 구하기 (YYYYMMDD)
    # 실제로는 '주식 영업일' 기준이어야 하지만, 
    # API가 날짜를 입력받으므로 단순히 어제 날짜를 우선 사용합니다.
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
        "FID_INPUT_HOUR_1": "160000", # 장 종료 후 시간
        "FID_INPUT_DATE_1": yesterday,
        "FID_PW_DATA_INCU_YN": "Y",
        "FID_FAKE_TICK_INCU_YN": "" # 공백 필수 입력 (CSV 참고)
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rt_cd") != "0":
            return {
                "success": False, 
                "error": data.get("msg1"), 
                "msg_cd": data.get("msg_cd")
            }
        
        output1 = data.get("output1", {})
        output2 = data.get("output2", [])
        
        if not output2:
            return {
                "success": False,
                "error": f"No data found for date {yesterday}"
            }

        # output1.stck_prdy_clpr 가 전일 종가 (FID_INPUT_DATE_1 기준 전일)
        # 하지만 사용자가 입력한 날짜(어제)의 시가와 종가를 원한다면 output2를 분석해야 함.
        # output2는 분봉 데이터 리스트이며, 시간 내림차순으로 정렬되어 있음 (최신순).
        
        # 입력한 날짜(yesterday)에 해당하는 데이터만 필터링
        target_day_data = [item for item in output2 if item.get("stck_bsop_date") == yesterday]
        
        # 만약 휴장일 등으로 어제 데이터가 없다면, 가장 최근 영업일 데이터를 찾음
        if not target_day_data and output2:
            last_date = output2[0].get("stck_bsop_date")
            target_day_data = [item for item in output2 if item.get("stck_bsop_date") == last_date]
            yesterday = last_date # 실제 조회된 날짜로 업데이트

        if not target_day_data:
            return {"success": False, "error": "No price data available"}
            
        # 종가: 가장 늦은 시간의 현재가 (리스트의 첫 번째 항목이 대개 가장 늦은 시간)
        close_price = target_day_data[0].get("stck_prpr")
        # 시가: 가장 이른 시간의 시가 (리스트의 마지막 항목이 대개 가장 이른 시간)
        open_price = target_day_data[-1].get("stck_oprc")
        
        return {
            "success": True,
            "stock_code": stock_code,
            "date": yesterday,
            "open_price": open_price,
            "close_price": close_price,
            "stock_name": output1.get("hts_kor_isnm")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Request Error: {str(e)}"
        }

if __name__ == "__main__":
    # 테스트용 (삼성전자: 005930)
    stock = "005930"
    print(f"한국투자증권 API 호출 중 (종목: {stock})...")
    result = get_yesterday_prices(stock)
    
    if result.get("success"):
        print(f"조회 날짜: {result['date']}")
        print(f"종목명: {result['stock_name']}")
        print(f"시가: {result['open_price']}")
        print(f"종가: {result['close_price']}")
    else:
        print(f"실패: {result.get('error')}")
