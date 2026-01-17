"""
LangGraph 기반 보고서 생성 그래프
"""
from langgraph.graph import StateGraph, END
from typing import Dict, Any
import sys
import os

# models 경로 추가
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.graph.state import ReportGenerationState
from app.graph.nodes import (
    filter_news_by_date,
    select_relevant_news,
    predict_industries,
    extract_companies,
    fetch_financial_data,
    calculate_health_factor,
    generate_report
)


def create_report_graph(db=None):
    """
    보고서 생성 그래프를 생성하고 컴파일합니다.
    
    Args:
        db: 데이터베이스 세션 (노드에 전달하기 위해 사용)
    
    Returns:
        컴파일된 LangGraph 그래프
    """
    # db를 바인딩한 노드 래퍼 생성
    def make_node_wrapper(node_func):
        def wrapper(state):
            return node_func(state, config={"db": db})
        return wrapper
    
    workflow = StateGraph(ReportGenerationState)
    
    # 노드 추가 (db 바인딩)
    workflow.add_node("filter_news", make_node_wrapper(filter_news_by_date))
    workflow.add_node("select_news", make_node_wrapper(select_relevant_news))
    workflow.add_node("predict_industries", make_node_wrapper(predict_industries))
    workflow.add_node("extract_companies", make_node_wrapper(extract_companies))
    workflow.add_node("fetch_financials", make_node_wrapper(fetch_financial_data))
    workflow.add_node("calculate_health", make_node_wrapper(calculate_health_factor))
    workflow.add_node("generate_report", make_node_wrapper(generate_report))
    
    # 엣지 정의
    workflow.set_entry_point("filter_news")
    workflow.add_edge("filter_news", "select_news")
    workflow.add_edge("select_news", "predict_industries")
    workflow.add_edge("predict_industries", "extract_companies")
    workflow.add_edge("extract_companies", "fetch_financials")
    workflow.add_edge("fetch_financials", "calculate_health")
    workflow.add_edge("calculate_health", "generate_report")
    workflow.add_edge("generate_report", END)
    
    return workflow.compile()
