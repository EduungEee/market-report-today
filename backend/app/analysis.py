"""
AI 분석 모듈
OpenAI API를 사용하여 뉴스를 분석하고 산업/주식 예측을 수행합니다.
"""
import os
import json
from typing import List, Dict, Optional
from openai import OpenAI
from sqlalchemy.orm import Session
from datetime import date
import sys
import os as os_module

# models 경로 추가
backend_path = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import NewsArticle, Report, ReportIndustry, ReportStock

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def get_openai_client():
    """OpenAI 클라이언트를 지연 초기화합니다."""
    if not OPENAI_API_KEY:
        return None
    return OpenAI(api_key=OPENAI_API_KEY)


def analyze_news_with_ai(news_articles: List[NewsArticle]) -> Dict:
    """
    뉴스 기사들을 AI로 분석하여 파급효과, 산업, 주식을 예측합니다.
    
    Args:
        news_articles: 분석할 뉴스 기사 리스트
    
    Returns:
        분석 결과 딕셔너리
    """
    client = get_openai_client()
    if not client:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    # 뉴스 요약
    news_summary = "\n\n".join([
        f"제목: {article.title}\n내용: {article.content[:500] if article.content else '내용 없음'}"
        for article in news_articles[:10]  # 최대 10개만 분석
    ])
    
    prompt = f"""다음 뉴스 기사들을 분석하여 주식 시장에 미치는 영향을 분석해주세요.

뉴스 기사:
{news_summary}

다음 JSON 형식으로 응답해주세요:
{{
    "summary": "전체 뉴스 요약 (200자 이내)",
    "industries": [
        {{
            "industry_name": "산업명",
            "impact_level": "high|medium|low",
            "impact_description": "영향 설명",
            "trend_direction": "positive|negative|neutral",
            "stocks": [
                {{
                    "stock_code": "종목코드 (6자리)",
                    "stock_name": "종목명",
                    "expected_trend": "up|down|neutral",
                    "confidence_score": 0.0-1.0,
                    "reasoning": "예측 근거"
                }}
            ]
        }}
    ]
}}

한국 주식 시장에 집중하여 분석해주세요. 실제 존재하는 종목 코드와 이름을 사용해주세요."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # 비용 절감을 위해 mini 모델 사용
            messages=[
                {"role": "system", "content": "당신은 주식 시장 분석 전문가입니다. 뉴스를 분석하여 주식 시장에 미치는 영향을 정확하게 예측합니다."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        return result
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"응답 텍스트: {result_text if 'result_text' in locals() else 'N/A'}")
        raise ValueError(f"AI 분석 결과를 파싱할 수 없습니다: {e}")
    except Exception as e:
        import traceback
        print(f"OpenAI API 호출 실패: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise


def save_analysis_to_db(
    db: Session,
    news_articles: List[NewsArticle],
    analysis_result: Dict,
    analysis_date: date
) -> Report:
    """
    분석 결과를 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        news_articles: 분석된 뉴스 기사 리스트
        analysis_result: AI 분석 결과
        analysis_date: 분석 날짜
    
    Returns:
        생성된 Report 객체
    """
    # Report 생성
    report = Report(
        title=f"{analysis_date.strftime('%Y-%m-%d')} 주식 동향 분석",
        summary=analysis_result.get("summary", ""),
        analysis_date=analysis_date
    )
    db.add(report)
    db.flush()  # ID를 얻기 위해 flush
    
    # 뉴스 연결
    for news in news_articles:
        report.news_articles.append(news)
    
    # 산업 및 주식 저장
    for industry_data in analysis_result.get("industries", []):
        industry = ReportIndustry(
            report_id=report.id,
            industry_name=industry_data.get("industry_name", ""),
            impact_level=industry_data.get("impact_level", "medium"),
            impact_description=industry_data.get("impact_description", ""),
            trend_direction=industry_data.get("trend_direction", "neutral")
        )
        db.add(industry)
        db.flush()
        
        # 주식 저장
        for stock_data in industry_data.get("stocks", []):
            stock = ReportStock(
                report_id=report.id,
                industry_id=industry.id,
                stock_code=stock_data.get("stock_code", ""),
                stock_name=stock_data.get("stock_name", ""),
                expected_trend=stock_data.get("expected_trend", "neutral"),
                confidence_score=float(stock_data.get("confidence_score", 0.5)),
                reasoning=stock_data.get("reasoning", "")
            )
            db.add(stock)
    
    db.commit()
    db.refresh(report)
    
    return report


def analyze_and_save(
    db: Session,
    news_articles: List[NewsArticle],
    analysis_date: Optional[date] = None
) -> Report:
    """
    뉴스를 분석하고 결과를 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        news_articles: 분석할 뉴스 기사 리스트
        analysis_date: 분석 날짜 (기본값: 오늘)
    
    Returns:
        생성된 Report 객체
    """
    if not news_articles:
        raise ValueError("분석할 뉴스 기사가 없습니다.")
    
    if analysis_date is None:
        analysis_date = date.today()
    
    # AI 분석
    analysis_result = analyze_news_with_ai(news_articles)
    
    # 결과 저장
    report = save_analysis_to_db(db, news_articles, analysis_result, analysis_date)
    
    return report
