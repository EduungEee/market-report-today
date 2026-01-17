"""
LangGraph State 정의
보고서 생성 프로세스의 상태를 관리합니다.
"""
from typing import TypedDict, List, Dict, Optional
from datetime import date, datetime
import sys
import os

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import NewsArticle


class ReportGenerationState(TypedDict, total=False):
    """보고서 생성 프로세스의 상태"""
    # 입력
    analysis_date: date
    current_time: datetime
    
    # 중간 결과
    filtered_news: List[NewsArticle]
    selected_news: List[NewsArticle]
    news_scores: Dict[int, float]
    selection_reasons: Dict[int, str]
    predicted_industries: List[Dict]
    companies_by_industry: Dict[str, List[Dict]]
    financial_data: Dict[str, Dict]
    health_factors: Dict[str, Dict]
    
    # 최종 결과
    report_data: Dict
    report_id: Optional[int]
    
    # 에러 처리
    errors: List[str]
