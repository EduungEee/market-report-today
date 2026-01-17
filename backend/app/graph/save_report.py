"""
보고서 저장 함수
LangGraph 결과를 데이터베이스에 저장합니다.
"""
from typing import Dict, List
from sqlalchemy.orm import Session
from datetime import date
import sys
import os

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import Report, ReportIndustry, ReportStock, NewsArticle


def save_report_to_db(
    db: Session,
    report_data: Dict,
    selected_news: List[NewsArticle],
    analysis_date: date
) -> Report:
    """
    LangGraph로 생성된 보고서 데이터를 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        report_data: 보고서 데이터 (report_data 필드)
        selected_news: 선별된 뉴스 기사 리스트
        analysis_date: 분석 날짜
    
    Returns:
        생성된 Report 객체
    """
    # Report 생성
    report = Report(
        title=f"{analysis_date.strftime('%Y-%m-%d')} 주식 동향 분석",
        summary=report_data.get("summary", ""),
        analysis_date=analysis_date,
        report_metadata=report_data  # report_data 전체를 metadata에 저장
    )
    db.add(report)
    db.flush()  # ID를 얻기 위해 flush
    
    # 뉴스 연결
    for news in selected_news:
        report.news_articles.append(news)
    
    # 산업 및 주식 저장
    for industry_data in report_data.get("industries", []):
        industry = ReportIndustry(
            report_id=report.id,
            industry_name=industry_data.get("industry_name", ""),
            impact_level=industry_data.get("impact_level", "medium"),
            impact_description=industry_data.get("impact_description", ""),
            trend_direction=industry_data.get("trend_direction", "neutral"),
            selection_reason=industry_data.get("selection_reason", "")
        )
        db.add(industry)
        db.flush()
        
        # 주식 저장
        for company_data in industry_data.get("companies", []):
            stock = ReportStock(
                report_id=report.id,
                industry_id=industry.id,
                stock_code=company_data.get("stock_code", ""),
                stock_name=company_data.get("stock_name", ""),
                expected_trend="neutral",  # 기본값
                confidence_score=0.5,  # 기본값
                reasoning=company_data.get("reasoning", ""),
                health_factor=float(company_data.get("health_factor", 0.5)),
                dart_code=company_data.get("dart_code", "")
            )
            db.add(stock)
    
    db.commit()
    db.refresh(report)
    
    return report
