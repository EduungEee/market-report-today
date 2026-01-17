"""
뉴스 선별 및 점수화 노드
Semantic Search와 LLM을 사용하여 주식 영향도가 높은 뉴스를 선별합니다.
"""
from typing import Dict, Any, List
import sys
import os
import json

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.graph.state import ReportGenerationState
from app.analysis import create_query_embedding, search_similar_news_by_embedding, get_openai_client
from datetime import datetime, timedelta
import pytz


def select_relevant_news(state: ReportGenerationState, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Semantic Search와 LLM을 사용하여 주식 영향도가 높은 뉴스를 선별합니다.
    
    Args:
        state: 현재 상태
        config: 설정 (db 포함)
        
    Returns:
        업데이트된 상태
    """
    db = config.get("db") if config else None
    filtered_news = state.get("filtered_news", [])
    target_count = 20
    
    if not db:
        return {
            "errors": state.get("errors", []) + ["데이터베이스 세션이 없습니다."],
            "selected_news": [],
            "news_scores": {},
            "selection_reasons": {}
        }
    
    if not filtered_news:
        print("⚠️  필터링된 뉴스가 없습니다.")
        return {
            "selected_news": [],
            "news_scores": {},
            "selection_reasons": {},
            "errors": state.get("errors", []) + ["필터링된 뉴스가 없습니다."]
        }
    
    try:
        # 1단계: Semantic Search로 주식 영향도 높은 뉴스 후보 추출
        query_text = """주식 시장에 직접적인 영향을 미치는 뉴스:
- 기업 실적 발표 및 재무제표
- 정부 정책 및 규제 변화
- 산업 동향 및 시장 전망
- M&A 및 투자 소식
- 주가 변동에 영향을 주는 경제 지표"""
        
        query_embedding = create_query_embedding(query_text)
        
        if not query_embedding:
            print("⚠️  쿼리 임베딩 생성 실패, 모든 뉴스를 후보로 사용")
            candidate_news = filtered_news[:100]  # 최대 100개
        else:
            # 한국 시간대 설정
            seoul_tz = pytz.timezone('Asia/Seoul')
            now = datetime.now(seoul_tz)
            analysis_date = state.get("analysis_date")
            
            target_date = datetime.combine(analysis_date, datetime.min.time())
            target_date_kst = seoul_tz.localize(target_date)
            yesterday_6am = (target_date_kst - timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
            end_datetime = target_date_kst.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Semantic Search로 후보 추출 (50-100개)
            candidate_news = search_similar_news_by_embedding(
                db=db,
                query_embedding=query_embedding,
                start_datetime=yesterday_6am,
                end_datetime=end_datetime,
                limit=100  # 후보는 더 많이 추출
            )
            print(f"✅ Semantic Search로 {len(candidate_news)}개 후보 추출")
        
        if not candidate_news:
            print("⚠️  후보 뉴스가 없습니다.")
            return {
                "selected_news": [],
                "news_scores": {},
                "selection_reasons": {},
                "errors": state.get("errors", []) + ["후보 뉴스가 없습니다."]
            }
        
        # 2단계: LLM으로 각 뉴스의 주식 영향도 점수화
        client = get_openai_client()
        if not client:
            print("⚠️  OpenAI 클라이언트를 사용할 수 없습니다. 후보 중 상위 N개 선택")
            selected_news = candidate_news[:target_count]
            news_scores = {news.id: 0.5 for news in selected_news}
            selection_reasons = {news.id: "OpenAI API를 사용할 수 없어 자동 선택" for news in selected_news}
        else:
            # 배치로 처리하여 API 호출 최소화
            news_scores = {}
            selection_reasons = {}
            
            # 뉴스를 배치로 나누어 처리 (한 번에 10개씩)
            batch_size = 10
            for i in range(0, len(candidate_news), batch_size):
                batch = candidate_news[i:i + batch_size]
                
                # 배치 프롬프트 생성
                news_items = []
                for news in batch:
                    content_preview = news.content[:500] if news.content else "내용 없음"
                    news_items.append(f"ID: {news.id}\n제목: {news.title}\n내용: {content_preview}")
                
                prompt = f"""다음 뉴스 기사들이 주식 시장에 미치는 영향도를 평가해주세요.

뉴스 기사:
{chr(10).join(news_items)}

각 뉴스에 대해 다음 JSON 형식으로 응답해주세요:
{{
  "scores": [
    {{
      "news_id": int,
      "score": float,  // 0.0-1.0 (1.0에 가까울수록 주식 시장에 큰 영향)
      "reason": str  // 선별 이유 (간단히)
    }}
  ]
}}

점수 기준:
- 0.9 이상: 매우 높은 영향 (기업 실적 발표, 정책 변화 등)
- 0.7-0.9: 높은 영향 (산업 동향, M&A 등)
- 0.5-0.7: 중간 영향 (일반적인 경제 뉴스)
- 0.5 미만: 낮은 영향 (주식 시장과 직접적 관련 없음)"""
                
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "당신은 주식 시장 분석 전문가입니다. 뉴스가 주식 시장에 미치는 영향을 정확하게 평가합니다."},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.3
                    )
                    
                    result_text = response.choices[0].message.content
                    result = json.loads(result_text)
                    
                    for item in result.get("scores", []):
                        news_id = item.get("news_id")
                        score = float(item.get("score", 0.5))
                        reason = item.get("reason", "평가 완료")
                        news_scores[news_id] = score
                        selection_reasons[news_id] = reason
                    
                    print(f"✅ 배치 {i//batch_size + 1} 처리 완료: {len(batch)}개 뉴스 평가")
                except Exception as e:
                    print(f"⚠️  배치 {i//batch_size + 1} 처리 실패: {e}")
                    # 실패한 뉴스는 기본 점수 부여
                    for news in batch:
                        if news.id not in news_scores:
                            news_scores[news.id] = 0.5
                            selection_reasons[news.id] = "평가 실패로 기본 점수 부여"
        
        # 3단계: 점수 순으로 정렬하여 상위 N개 선택
        scored_news = [(news, news_scores.get(news.id, 0.0)) for news in candidate_news if news.id in news_scores]
        scored_news.sort(key=lambda x: x[1], reverse=True)
        selected_news = [news for news, score in scored_news[:target_count]]
        
        # 선택된 뉴스의 점수와 이유만 유지
        final_scores = {news.id: news_scores[news.id] for news in selected_news}
        final_reasons = {news.id: selection_reasons[news.id] for news in selected_news}
        
        print(f"✅ 뉴스 선별 완료: {len(selected_news)}개 선택 (최고 점수: {max(final_scores.values()) if final_scores else 0:.2f})")
        
        return {
            "selected_news": selected_news,
            "news_scores": final_scores,
            "selection_reasons": final_reasons,
            "errors": state.get("errors", [])
        }
        
    except Exception as e:
        import traceback
        error_msg = f"뉴스 선별 실패: {str(e)}"
        print(f"⚠️  {error_msg}")
        print(traceback.format_exc())
        return {
            "selected_news": [],
            "news_scores": {},
            "selection_reasons": {},
            "errors": state.get("errors", []) + [error_msg]
        }
