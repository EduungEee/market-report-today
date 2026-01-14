"""
LangGraph 기반 고급 주식 분석 모듈 v2
순환 구조와 다단계 추론을 활용한 정교한 분석 파이프라인
"""
import os
from typing import List, Dict, Optional, TypedDict, Annotated
from datetime import datetime, date
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
import sys

# 기존 모델 import
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import NewsArticle, Report, ReportIndustry, ReportStock

# ==================== 환경 변수 ====================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ==================== LLM 설정 ====================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.3,
    api_key=OPENAI_API_KEY
)

print(f"✅ LLM 초기화 완료: OpenAI GPT-4o-mini")

# ==================== DuckDuckGo 검색 및 BeautifulSoup 스크래핑 ====================

def search_with_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    DuckDuckGo로 검색 결과 가져오기
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 개수
    
    Returns:
        검색 결과 리스트 [{"title": "...", "url": "...", "snippet": "..."}]
    """
    try:
        from duckduckgo_search import DDGS
        
        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
        
        print(f"  ✅ DuckDuckGo 검색 완료: {len(results)}개 결과")
        return results
    except ImportError:
        print("⚠️ duckduckgo-search 패키지가 설치되지 않았습니다. pip install duckduckgo-search")
        return []
    except Exception as e:
        print(f"⚠️ DuckDuckGo 검색 오류: {e}")
        return []


def scrape_with_beautifulsoup(url: str, max_length: int = 2000) -> str:
    """
    BeautifulSoup으로 웹페이지 내용 스크래핑
    
    Args:
        url: 스크래핑할 URL
        max_length: 최대 텍스트 길이
    
    Returns:
        스크래핑된 텍스트 내용
    """
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # 스크립트와 스타일 태그 제거
        for script in soup(["script", "style"]):
            script.decompose()
        
        # 텍스트 추출
        text = soup.get_text(separator=" ", strip=True)
        
        # 길이 제한
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        return text
    except ImportError:
        print("⚠️ beautifulsoup4 또는 requests 패키지가 설치되지 않았습니다.")
        return ""
    except Exception as e:
        print(f"⚠️ 웹 스크래핑 오류 ({url}): {e}")
        return ""

# ==================== Pydantic Models ====================

class NewsAnalysisResult(BaseModel):
    """뉴스 분석 결과"""
    summary: str = Field(description="뉴스 요약 및 핵심 이슈")
    key_industries: List[str] = Field(description="주도 산업 리스트")
    sentiment: str = Field(description="시장 감성 (positive/negative/neutral)")

class StockCandidate(BaseModel):
    """추천 종목 후보"""
    code: str = Field(description="종목코드 6자리", pattern=r"^\d{6}$")
    name: str = Field(description="종목명")
    reason: str = Field(description="추천 이유")
    industry: str = Field(description="소속 산업")

class FinancialData(BaseModel):
    """재무 데이터"""
    roe: Optional[float] = Field(None, description="ROE (자기자본이익률)")
    cash_flow: Optional[float] = Field(None, description="잉여현금흐름 (억원)")
    current_price: Optional[float] = Field(None, description="현재가 (원)")
    previous_close: Optional[float] = Field(None, description="전일 종가 (원)")
    source: Optional[str] = Field(None, description="데이터 출처")

class RelevanceCheck(BaseModel):
    """연관성 검증 결과"""
    is_relevant: bool = Field(description="뉴스와 연관성이 있는지")
    reasoning: str = Field(description="검증 근거")

class FinancialCheck(BaseModel):
    """재무 건전성 검증 결과"""
    is_sound: bool = Field(description="재무 건전성이 양호한지")
    reasoning: str = Field(description="검증 근거")

class IndirectStock(BaseModel):
    """간접 수혜주"""
    code: str = Field(description="종목코드 6자리", pattern=r"^\d{6}$")
    name: str = Field(description="종목명")
    category: str = Field(description="카테고리 (direct/indirect/secondary)")
    reason: str = Field(description="수혜 이유")
    connection_chain: str = Field(description="연결 고리 설명")

class FinalRecommendation(BaseModel):
    """최종 추천 리포트"""
    direct_stocks: List[StockCandidate] = Field(description="직접 수혜주")
    indirect_stocks: List[IndirectStock] = Field(description="간접 수혜주")
    analysis_summary: str = Field(description="전체 분석 요약")

# ==================== GraphState 정의 ====================

class GraphState(TypedDict):
    """그래프 상태 - 모든 노드 간 공유 데이터"""
    # 입력
    news_articles: List[NewsArticle]
    
    # [1노드] 뉴스 분석 결과
    news_analysis: Optional[NewsAnalysisResult]
    
    # [2노드] 추천 종목 후보
    candidate_stocks: List[Dict]
    
    # 제외된 종목 리스트 (재추천 방지)
    excluded_stocks: List[str]  # 종목코드 리스트
    
    # 현재 검증 중인 종목
    current_stock: Optional[Dict]
    
    # [4노드] 재무 데이터
    financial_data: Optional[FinancialData]
    
    # [6노드] 최종 추천 리포트
    final_recommendations: Optional[FinalRecommendation]
    
    # 메타데이터
    iteration_count: int  # 반복 횟수 추적
    max_iterations: int  # 최대 반복 횟수
    start_time: datetime

# ==================== [1노드] 뉴스 크롤링 및 분석 ====================

def crawl_and_analyze_node(state: GraphState) -> GraphState:
    """[1노드] 뉴스 크롤링 및 분석"""
    print("--- [1노드] 뉴스 크롤링 및 분석 시작 ---")
    
    news_articles = state["news_articles"]
    
    # 뉴스 요약 (최대 10개)
    news_summary = "\n\n".join([
        f"[{i+1}] 제목: {article.title}\n출처: {article.source}\n내용: {article.content[:300] if article.content else '내용 없음'}"
        for i, article in enumerate(news_articles[:10])
    ])
    
    prompt = f"""당신은 한국 주식시장 전문 애널리스트입니다.

[뉴스 기사들]
{news_summary}

[분석 요구사항]
1. 전체 뉴스의 핵심 이슈를 300자 이내로 요약
2. 주도 산업 3-5개 추출 (예: 반도체, 전기차, 금융 등)
3. 시장 감성 판단 (positive/negative/neutral)

JSON 형식으로 응답:
{{
    "summary": "요약",
    "key_industries": ["산업1", "산업2", "산업3"],
    "sentiment": "positive"
}}
"""
    
    structured_llm = llm.with_structured_output(NewsAnalysisResult)
    result = structured_llm.invoke(prompt)
    
    print(f"✅ 분석 완료: {len(result.key_industries)}개 산업, 감성={result.sentiment}")
    
    return {
        "news_analysis": result.dict(),
        "iteration_count": 0,
        "start_time": datetime.now()
    }

# ==================== [2노드] 1차 대장주/핫종목 도출 ====================

def primary_selection_node(state: GraphState) -> GraphState:
    """[2노드] 1차 대장주/핫종목 도출"""
    print(f"--- [2노드] 1차 대장주 도출 시작 (반복 {state.get('iteration_count', 0)}회) ---")
    
    news_analysis = state["news_analysis"]
    excluded_stocks = state.get("excluded_stocks", [])
    
    if not news_analysis:
        print("⚠️ 뉴스 분석 결과가 없습니다.")
        return {"candidate_stocks": []}
    
    # 제외된 종목 리스트를 프롬프트에 포함
    excluded_text = ""
    if excluded_stocks:
        excluded_text = f"\n\n[제외할 종목코드] (이미 검증 실패): {', '.join(excluded_stocks)}\n위 종목들은 제외하고 새로운 종목을 추천하세요."
    
    prompt = f"""당신은 한국 주식시장 전문가입니다.

[뉴스 분석 결과]
요약: {news_analysis['summary']}
주도 산업: {', '.join(news_analysis['key_industries'])}
시장 감성: {news_analysis['sentiment']}

[미션]
위 분석 결과를 바탕으로 각 산업의 대장주를 1개씩 추천하세요.
총 {len(news_analysis['key_industries'])}개 종목을 추천합니다.

[필수 조건]
1. 실제 존재하는 한국 종목 (코스피/코스닥)
2. 종목코드 6자리 필수 (예: 005930=삼성전자, 000660=SK하이닉스)
3. 각 산업의 대장주 (시가총액 1위 또는 2위)
4. 구체적인 추천 이유
{excluded_text}

JSON 형식으로 응답:
{{
    "stocks": [
        {{
            "code": "005930",
            "name": "삼성전자",
            "reason": "추천 이유",
            "industry": "반도체"
        }}
    ]
}}
"""
    
    class StockListOutput(BaseModel):
        stocks: List[StockCandidate]
    
    structured_llm = llm.with_structured_output(StockListOutput)
    result = structured_llm.invoke(prompt)
    
    print(f"✅ 추천 완료: {len(result.stocks)}개 종목")
    for stock in result.stocks:
        print(f"   - {stock.name}({stock.code}): {stock.industry}")
    
    return {
        "candidate_stocks": [s.dict() for s in result.stocks],
        "iteration_count": state.get("iteration_count", 0) + 1
    }

# ==================== [3노드] 뉴스 연관성 검증 ====================

def relevance_checker_node(state: GraphState) -> GraphState:
    """[3노드] 뉴스 연관성 검증"""
    print("--- [3노드] 뉴스 연관성 검증 시작 ---")
    
    candidate_stocks = state.get("candidate_stocks", [])
    news_analysis = state.get("news_analysis")
    
    if not candidate_stocks:
        print("⚠️ 검증할 종목이 없습니다.")
        return {}
    
    # 첫 번째 종목 검증 (한 번에 하나씩)
    current_stock = candidate_stocks[0]
    
    prompt = f"""당신은 매우 엄격한 주식 분석 검증관입니다.

[뉴스 분석 결과]
{news_analysis['summary'] if news_analysis else 'N/A'}

[추천된 종목]
종목코드: {current_stock['code']}
종목명: {current_stock['name']}
추천 이유: {current_stock['reason']}
소속 산업: {current_stock['industry']}

[검증 질문]
이 종목이 실제로 위 뉴스 이슈의 수혜를 받을 수 있는가?
- 뉴스 내용과 종목의 연결고리가 명확한가?
- 논리적으로 타당한가?
- 억지스러운 연결은 아닌가?

JSON 형식으로 응답:
{{
    "is_relevant": true,
    "reasoning": "검증 근거"
}}
"""
    
    structured_llm = llm.with_structured_output(RelevanceCheck)
    result = structured_llm.invoke(prompt)
    
    status = "✅ 통과" if result.is_relevant else "❌ 실패"
    print(f"{status}: {current_stock['name']}({current_stock['code']}) - {result.reasoning[:100]}...")
    
    if result.is_relevant:
        # 통과: 현재 종목을 저장하고 다음 단계로
        return {
            "current_stock": current_stock,
            "candidate_stocks": candidate_stocks[1:]  # 나머지 종목들
        }
    else:
        # 실패: excluded_stocks에 추가하고 2노드로 복귀
        excluded = state.get("excluded_stocks", [])
        excluded.append(current_stock['code'])
        print(f"   → 제외 목록에 추가: {current_stock['code']}")
        return {
            "excluded_stocks": excluded,
            "candidate_stocks": candidate_stocks[1:]  # 다음 종목으로
        }

# ==================== [4노드] 재무 데이터 검색 (Tavily Search) ====================

def financial_search_node(state: GraphState) -> GraphState:
    """[4노드] 재무 데이터 검색 (DuckDuckGo + BeautifulSoup 사용)"""
    print("--- [4노드] 재무 데이터 검색 시작 (DuckDuckGo + BeautifulSoup) ---")
    
    current_stock = state.get("current_stock")
    
    if not current_stock:
        print("⚠️ 검색할 종목이 없습니다.")
        return {"financial_data": None}
    
    stock_name = current_stock['name']
    stock_code = current_stock['code']
    
    # 기본값
    financial_info = {
        "roe": None,
        "cash_flow": None,
        "current_price": None,
        "previous_close": None,
        "source": None
    }
    
    try:
        # DuckDuckGo로 재무 데이터 검색
        query = f"{stock_name} {stock_code} 재무제표 ROE 현금흐름 최신 분기"
        
        print(f"  검색 쿼리: {query}")
        search_results = search_with_duckduckgo(query, max_results=5)
        
        if not search_results:
            print("⚠️ 검색 결과가 없습니다.")
            return {"financial_data": financial_info}
        
        # 검색 결과에서 관련성이 높은 페이지 스크래핑
        scraped_contents = []
        for i, result in enumerate(search_results[:3]):  # 상위 3개만 스크래핑
            url = result.get("url", "")
            snippet = result.get("snippet", "")
            
            print(f"  스크래핑 중: {result.get('title', '')[:50]}...")
            
            # BeautifulSoup으로 페이지 내용 스크래핑
            page_content = scrape_with_beautifulsoup(url, max_length=2000)
            
            if page_content:
                scraped_contents.append({
                    "title": result.get("title", ""),
                    "url": url,
                    "snippet": snippet,
                    "content": page_content
                })
        
        # 스크래핑된 내용을 LLM에 전달하여 구조화된 데이터 추출
        if scraped_contents:
            results_text = "\n\n".join([
                f"[{i+1}] {r['title']}\nURL: {r['url']}\n스니펫: {r['snippet']}\n내용: {r['content'][:1000]}"
                for i, r in enumerate(scraped_contents)
            ])
            
            extraction_prompt = f"""다음 검색 및 스크래핑 결과에서 {stock_name}({stock_code})의 재무 데이터를 추출하세요.

[검색 및 스크래핑 결과]
{results_text}

[추출할 데이터]
1. ROE (자기자본이익률) - 숫자만 (예: 15.5)
2. 잉여현금흐름 - 억원 단위 (예: 5000)
3. 현재가 - 원 단위 (예: 75000)
4. 전일 종가 - 원 단위 (예: 74500)

데이터를 찾을 수 없으면 null로 표시하세요.
가장 신뢰할 수 있는 출처의 URL을 source에 기록하세요.

JSON 형식으로 응답:
{{
    "roe": 15.5,
    "cash_flow": 5000,
    "current_price": 75000,
    "previous_close": 74500,
    "source": "데이터 출처 URL"
}}
"""
            
            structured_llm = llm.with_structured_output(FinancialData)
            extracted_data = structured_llm.invoke(extraction_prompt)
            
            financial_info = extracted_data.dict()
            print(f"✅ 재무 데이터 추출 완료: ROE={financial_info.get('roe')}, 현금흐름={financial_info.get('cash_flow')}억원")
        else:
            print("⚠️ 스크래핑된 내용이 없습니다.")
            
    except Exception as e:
        import traceback
        print(f"⚠️ 재무 데이터 검색 오류: {e}")
        print(traceback.format_exc())
    
    return {
        "financial_data": financial_info
    }

# ==================== [5노드] 재무 건전성 판단 ====================

def financial_evaluator_node(state: GraphState) -> GraphState:
    """[5노드] 재무 건전성 판단"""
    print("--- [5노드] 재무 건전성 판단 시작 ---")
    
    current_stock = state.get("current_stock")
    financial_data = state.get("financial_data")
    
    if not current_stock or not financial_data:
        print("⚠️ 평가할 데이터가 없습니다.")
        return {}
    
    prompt = f"""당신은 재무 분석 전문가입니다.

[종목 정보]
종목명: {current_stock['name']}
종목코드: {current_stock['code']}

[재무 데이터]
ROE: {financial_data.get('roe', 'N/A')}
잉여현금흐름: {financial_data.get('cash_flow', 'N/A')}억원
현재가: {financial_data.get('current_price', 'N/A')}원
전일 종가: {financial_data.get('previous_close', 'N/A')}원

[평가 기준]
1. ROE가 10% 이상인가? (양호한 수익성)
2. 잉여현금흐름이 양수인가? (현금 창출 능력)
3. 재무 건전성이 투자하기에 적합한가?

JSON 형식으로 응답:
{{
    "is_sound": true,
    "reasoning": "평가 근거"
}}
"""
    
    structured_llm = llm.with_structured_output(FinancialCheck)
    result = structured_llm.invoke(prompt)
    
    status = "✅ 통과" if result.is_sound else "❌ 실패"
    print(f"{status}: {current_stock['name']} - {result.reasoning[:100]}...")
    
    if result.is_sound:
        # 통과: 6노드로 진행
        return {}
    else:
        # 실패: excluded_stocks에 추가하고 2노드로 복귀
        excluded = state.get("excluded_stocks", [])
        excluded.append(current_stock['code'])
        print(f"   → 제외 목록에 추가: {current_stock['code']}")
        return {
            "excluded_stocks": excluded,
            "current_stock": None,
            "financial_data": None
        }

# ==================== [6노드] 간접 수혜주 및 다단계 추론 ====================

def indirect_inference_node(state: GraphState) -> GraphState:
    """[6노드] 간접 수혜주 및 다단계 추론"""
    print("--- [6노드] 간접 수혜주 추론 시작 ---")
    
    news_analysis = state.get("news_analysis")
    current_stock = state.get("current_stock")
    
    # 지금까지 통과한 직접 수혜주들을 수집 (간단화: 현재 종목만)
    # 실제로는 state에 통과한 종목 리스트를 유지해야 함
    
    if not news_analysis or not current_stock:
        print("⚠️ 추론할 데이터가 없습니다.")
        return {}
    
    prompt = f"""당신은 산업 연관관계 및 밸류체인 분석 전문가입니다.

[원본 뉴스 분석]
{news_analysis['summary']}

[직접 수혜주 (검증 완료)]
종목명: {current_stock['name']}
종목코드: {current_stock['code']}
산업: {current_stock['industry']}
이유: {current_stock['reason']}

[미션]
위 직접 수혜주를 바탕으로 간접 수혜주를 추론하세요.

[추론 단계]
1. 직접 수혜주: 뉴스 이슈와 직접 연결 (이미 검증 완료)
2. 간접 수혜주: 직접 수혜주의 공급망/밸류체인에 있는 종목
   예: 직접 수혜주가 반도체 → 반도체 소재, 장비 기업
3. 2차 간접 수혜주: 간접 수혜주의 활성화로 반사이익을 얻는 종목
   예: 소재 기업 활성화 → 정밀 부품, 화학 기업

각 카테고리별로 2-3개씩 추천하세요.

JSON 형식으로 응답:
{{
    "direct_stocks": [
        {{
            "code": "{current_stock['code']}",
            "name": "{current_stock['name']}",
            "reason": "{current_stock['reason']}",
            "industry": "{current_stock['industry']}"
        }}
    ],
    "indirect_stocks": [
        {{
            "code": "000660",
            "name": "SK하이닉스",
            "category": "indirect",
            "reason": "간접 수혜 이유",
            "connection_chain": "A → B → C 연결 설명"
        }}
    ],
    "analysis_summary": "전체 분석 요약"
}}
"""
    
    structured_llm = llm.with_structured_output(FinalRecommendation)
    result = structured_llm.invoke(prompt)
    
    print(f"✅ 추론 완료: 직접 {len(result.direct_stocks)}개, 간접 {len(result.indirect_stocks)}개")
    
    return {
        "final_recommendations": result.dict()
    }

# ==================== 조건부 엣지 함수 ====================

def should_continue_relevance_check(state: GraphState) -> str:
    """[3노드] 연관성 검증 후 분기"""
    current_stock = state.get("current_stock")
    
    if current_stock:
        # 통과: 4노드로
        return "financial_search"
    else:
        # 실패: 2노드로 복귀 (더 이상 후보가 없으면 종료)
        candidate_stocks = state.get("candidate_stocks", [])
        if not candidate_stocks:
            return "end"
        return "primary_selection"

def should_continue_financial_check(state: GraphState) -> str:
    """[5노드] 재무 검증 후 분기"""
    current_stock = state.get("current_stock")
    
    if current_stock:
        # 통과: 6노드로
        return "indirect_inference"
    else:
        # 실패: 2노드로 복귀 (더 이상 후보가 없으면 종료)
        candidate_stocks = state.get("candidate_stocks", [])
        if not candidate_stocks:
            return "end"
        return "primary_selection"

def should_continue_primary(state: GraphState) -> str:
    """[2노드] 후보가 있는지 확인"""
    candidate_stocks = state.get("candidate_stocks", [])
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    
    if not candidate_stocks:
        return "end"
    
    if iteration_count >= max_iterations:
        print(f"⚠️ 최대 반복 횟수 도달 ({max_iterations}회)")
        return "end"
    
    return "relevance_checker"

# ==================== LangGraph 워크플로우 구성 ====================

def create_analysis_workflow():
    """분석 워크플로우 생성"""
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("crawl_and_analyze", crawl_and_analyze_node)
    workflow.add_node("primary_selection", primary_selection_node)
    workflow.add_node("relevance_checker", relevance_checker_node)
    workflow.add_node("financial_search", financial_search_node)
    workflow.add_node("financial_evaluator", financial_evaluator_node)
    workflow.add_node("indirect_inference", indirect_inference_node)
    
    # 엣지 연결
    workflow.set_entry_point("crawl_and_analyze")
    workflow.add_edge("crawl_and_analyze", "primary_selection")
    
    # 조건부 엣지: 2노드 → 3노드 (후보가 있으면)
    workflow.add_conditional_edges(
        "primary_selection",
        should_continue_primary,
        {
            "relevance_checker": "relevance_checker",
            "end": END
        }
    )
    
    # 조건부 엣지: 3노드 → 4노드 또는 2노드로 복귀
    workflow.add_conditional_edges(
        "relevance_checker",
        should_continue_relevance_check,
        {
            "financial_search": "financial_search",
            "primary_selection": "primary_selection",
            "end": END
        }
    )
    
    workflow.add_edge("financial_search", "financial_evaluator")
    
    # 조건부 엣지: 5노드 → 6노드 또는 2노드로 복귀
    workflow.add_conditional_edges(
        "financial_evaluator",
        should_continue_financial_check,
        {
            "indirect_inference": "indirect_inference",
            "primary_selection": "primary_selection",
            "end": END
        }
    )
    
    workflow.add_edge("indirect_inference", END)
    
    return workflow.compile()

# ==================== 메인 분석 함수 ====================

def analyze_news_with_graph(
    db: Session,
    news_articles: List[NewsArticle],
    max_iterations: int = 10,
    analysis_date: Optional[date] = None
) -> Report:
    """
    LangGraph를 사용한 고급 분석
    
    Args:
        db: 데이터베이스 세션
        news_articles: 분석할 뉴스 기사 리스트
        max_iterations: 최대 반복 횟수
        analysis_date: 분석 날짜
    
    Returns:
        생성된 Report 객체
    """
    if not news_articles:
        raise ValueError("분석할 뉴스 기사가 없습니다.")
    
    if analysis_date is None:
        analysis_date = date.today()
    
    print(f"==================== LangGraph 분석 시작 ====================")
    print(f"뉴스 개수: {len(news_articles)}")
    print(f"최대 반복 횟수: {max_iterations}")
    print(f"=" * 60)
    
    # 워크플로우 생성
    app = create_analysis_workflow()
    
    # 초기 상태
    initial_state: GraphState = {
        "news_articles": news_articles,
        "news_analysis": None,
        "candidate_stocks": [],
        "excluded_stocks": [],
        "current_stock": None,
        "financial_data": None,
        "final_recommendations": None,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "start_time": datetime.now()
    }
    
    try:
        # 워크플로우 실행
        result = app.invoke(initial_state)
        
        # 결과 출력
        end_time = datetime.now()
        processing_time = (end_time - result["start_time"]).total_seconds()
        
        print(f"\n{'=' * 60}")
        print(f"✅ 분석 완료")
        print(f"처리 시간: {processing_time:.2f}초")
        print(f"반복 횟수: {result['iteration_count']}회")
        print(f"제외된 종목: {len(result.get('excluded_stocks', []))}개")
        print(f"{'=' * 60}\n")
        
        # DB 저장 (기존 함수 활용)
        # TODO: final_recommendations를 DB에 저장하는 로직 구현 필요
        
        # 임시로 기존 방식 사용
        from app.analysis import analyze_and_save
        return analyze_and_save(db, news_articles, analysis_date)
        
    except Exception as e:
        import traceback
        print(f"\n❌ 분석 중 오류 발생: {e}")
        print(traceback.format_exc())
        raise
