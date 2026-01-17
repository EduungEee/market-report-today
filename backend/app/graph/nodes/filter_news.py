"""
날짜 범위 필터링 노드
전날 6시부터 현재 시간까지의 뉴스를 조회합니다.
"""
from typing import Dict, Any
import sys
import os

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.graph.state import ReportGenerationState
from app.analysis import get_news_by_date_range
from datetime import datetime, timedelta
import pytz


def filter_news_by_date(state: ReportGenerationState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    날짜 범위로 뉴스를 필터링합니다.
    
    Args:
        state: 현재 상태
        config: 설정 (db 포함)
        
    Returns:
        업데이트된 상태
    """
    # config에서 db 가져오기
    db = config.get("db") if config else None
    if db is None:
        return {
            "errors": state.get("errors", []) + ["데이터베이스 세션이 없습니다."],
            "filtered_news": []
        }
    
    analysis_date = state.get("analysis_date")
    current_time = state.get("current_time")
    
    # 한국 시간대 설정
    seoul_tz = pytz.timezone('Asia/Seoul')
    
    # 분석 대상 날짜의 전날 06:00:00 계산
    if current_time.tzinfo is None:
        current_time = seoul_tz.localize(current_time)
    
    target_date = datetime.combine(analysis_date, datetime.min.time())
    target_date_kst = seoul_tz.localize(target_date)
    yesterday_6am = (target_date_kst - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
    
    # 분석 대상 날짜의 23:59:59를 종료 시간으로 설정
    end_datetime = target_date_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    print(f"📅 날짜 범위 필터링: {yesterday_6am.strftime('%Y-%m-%d %H:%M:%S')} ~ {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 날짜 범위로 뉴스 조회
        filtered_news = get_news_by_date_range(
            db=db,
            start_datetime=yesterday_6am,
            end_datetime=end_datetime,
            limit=None  # 모든 뉴스 조회
        )
        
        print(f"✅ 날짜 범위 필터링 완료: {len(filtered_news)}개 뉴스 조회")
        
        return {
            "filtered_news": filtered_news,
            "errors": state.get("errors", [])
        }
    except Exception as e:
        error_msg = f"날짜 범위 필터링 실패: {str(e)}"
        print(f"⚠️  {error_msg}")
        return {
            "filtered_news": [],
            "errors": state.get("errors", []) + [error_msg]
        }
