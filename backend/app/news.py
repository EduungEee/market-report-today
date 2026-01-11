"""
뉴스 수집 모듈
네이버 뉴스 API를 사용하여 최신 뉴스를 수집합니다.
"""
import os
import requests
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
import sys
import os as os_module
import html
from urllib.parse import quote

# models 경로 추가
backend_path = os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import NewsArticle

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"


def fetch_news_from_api(query: str = "주식", count: int = 10) -> List[dict]:
    """
    네이버 뉴스 API에서 최신 뉴스를 가져옵니다.
    
    Args:
        query: 검색 쿼리 (UTF-8 인코딩됨)
        count: 가져올 뉴스 개수 (1-100, 기본값: 10개)
    
    Returns:
        뉴스 기사 리스트
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")
    
    # count 범위 검증 (네이버 API: 1-100)
    if count < 1 or count > 100:
        raise ValueError(f"count는 1-100 사이의 값이어야 합니다. 현재 값: {count}")
    
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    # 네이버 API 파라미터 설정
    # query는 requests가 자동으로 URL 인코딩하지만, UTF-8 문자열이어야 함
    params = {
        "query": query,  # UTF-8 문자열 (requests가 자동 인코딩)
        "display": count,  # 1-100 범위
        "sort": "date",  # "sim" (정확도순) 또는 "date" (날짜순, 최신순)
        "start": 1  # 검색 시작 위치 (1-1000, 기본값: 1)
    }
    
    try:
        print(f"네이버 뉴스 API 호출: query={query}, display={count}, sort=date")
        response = requests.get(NAVER_NEWS_API_URL, headers=headers, params=params, timeout=10)
        
        # 응답 상태 확인
        print(f"응답 상태 코드: {response.status_code}")
        
        # 오류 응답 처리
        if response.status_code == 400:
            error_text = response.text
            print(f"❌ 네이버 API 400 오류")
            print(f"요청 URL: {response.url}")
            print(f"요청 파라미터: {params}")
            print(f"응답 내용: {error_text}")
            
            # XML 형식 오류 파싱 시도
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(error_text)
                error_code = root.find('.//errorCode')
                error_message = root.find('.//errorMessage')
                if error_code is not None and error_message is not None:
                    print(f"오류 코드: {error_code.text}")
                    print(f"오류 메시지: {error_message.text}")
                    raise ValueError(f"네이버 API 오류 ({error_code.text}): {error_message.text}")
            except ET.ParseError:
                # JSON 형식일 수도 있음
                try:
                    error_json = response.json()
                    print(f"오류 상세 (JSON): {error_json}")
                except:
                    pass
            
            raise ValueError(f"네이버 API 400 오류: {error_text}")
        
        if response.status_code == 403:
            error_text = response.text
            print(f"❌ 네이버 API 403 오류 (권한 없음)")
            print(f"응답 내용: {error_text}")
            raise ValueError(
                "네이버 API 권한이 없습니다.\n"
                "1. 네이버 개발자 센터(https://developers.naver.com) 접속\n"
                "2. 내 애플리케이션 > API 설정 탭\n"
                "3. '검색' API가 체크되어 있는지 확인"
            )
        
        response.raise_for_status()
        data = response.json()
        
        print(f"API 응답 성공: 총 {data.get('total', 0)}개 결과, {len(data.get('items', []))}개 반환")
        
        articles = []
        if "items" in data:
            for item in data.get("items", []):
                # HTML 태그 제거 및 디코딩
                title = html.unescape(item.get("title", "").replace("<b>", "").replace("</b>", ""))
                description = html.unescape(item.get("description", "").replace("<b>", "").replace("</b>", ""))
                
                # pubDate 파싱 (RFC 2822 형식: "Mon, 26 Sep 2016 07:50:00 +0900")
                published_at = None
                pub_date_str = item.get("pubDate", "")
                if pub_date_str:
                    try:
                        # RFC 2822 형식 파싱 (네이버 API 표준 형식)
                        # 예: "Mon, 26 Sep 2016 07:50:00 +0900"
                        published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        try:
                            # 다른 형식 시도 (타임존 없음)
                            published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S")
                        except ValueError:
                            try:
                                # YYYY-MM-DD 형식
                                published_at = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
                            except:
                                print(f"날짜 파싱 실패: {pub_date_str}")
                                pass
                
                # originallink가 있으면 사용, 없으면 link 사용
                url = item.get("originallink") or item.get("link", "")
                
                # source 추출 (originallink의 도메인)
                source = ""
                if item.get("originallink"):
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(item.get("originallink"))
                        source = parsed.netloc.replace("www.", "")
                    except:
                        source = ""
                
                articles.append({
                    "title": title,
                    "content": description,  # 네이버 API는 본문이 아닌 요약만 제공
                    "source": source,
                    "url": url,
                    "published_at": published_at
                })
        
        print(f"파싱된 뉴스 기사: {len(articles)}개")
        return articles
    except requests.exceptions.HTTPError as e:
        import traceback
        print(f"네이버 뉴스 API HTTP 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 헤더: {dict(e.response.headers)}")
            print(f"응답 내용: {e.response.text}")
            
            # 네이버 API 오류 코드 파싱 시도
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(e.response.text)
                error_code = root.find('.//errorCode')
                error_message = root.find('.//errorMessage')
                if error_code is not None and error_message is not None:
                    print(f"네이버 오류 코드: {error_code.text}")
                    print(f"네이버 오류 메시지: {error_message.text}")
            except:
                pass
        print(f"Traceback: {traceback.format_exc()}")
        raise  # ValueError로 변환하여 상위로 전달
    except requests.exceptions.RequestException as e:
        import traceback
        print(f"네이버 뉴스 API 요청 실패: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"네이버 뉴스 API 요청 실패: {str(e)}")


def save_news_to_db(db: Session, articles: List[dict]) -> List[NewsArticle]:
    """
    뉴스 기사를 데이터베이스에 저장합니다.
    중복 체크 (URL 기반)를 수행합니다.
    
    Args:
        db: 데이터베이스 세션
        articles: 저장할 뉴스 기사 리스트
    
    Returns:
        저장된 NewsArticle 객체 리스트
    """
    saved_articles = []
    
    for article_data in articles:
        # URL 기반 중복 체크
        existing = db.query(NewsArticle).filter(
            NewsArticle.url == article_data.get("url")
        ).first()
        
        if existing:
            continue
        
        # NewsArticle 생성
        news_article = NewsArticle(
            title=article_data.get("title", ""),
            content=article_data.get("content", ""),
            source=article_data.get("source", ""),
            url=article_data.get("url", ""),
            published_at=article_data.get("published_at")
        )
        
        db.add(news_article)
        saved_articles.append(news_article)
    
    db.commit()
    
    # 저장된 객체에 ID 부여를 위해 refresh
    for article in saved_articles:
        db.refresh(article)
    
    return saved_articles


def collect_news(db: Session, query: str = "주식", count: int = 10) -> List[NewsArticle]:
    """
    뉴스를 수집하고 데이터베이스에 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        query: 검색 쿼리
        count: 가져올 뉴스 개수 (기본값: 10개)
    
    Returns:
        저장된 NewsArticle 객체 리스트
    
    Raises:
        ValueError: API 호출 실패 또는 뉴스 수집 실패 시
    """
    try:
        # API에서 뉴스 가져오기
        articles = fetch_news_from_api(query=query, count=count)
        
        if not articles:
            raise ValueError(f"'{query}' 검색어로 뉴스를 찾을 수 없습니다. 다른 검색어를 시도해주세요.")
        
        # 데이터베이스에 저장
        saved_articles = save_news_to_db(db, articles)
        
        print(f"뉴스 수집 완료: {len(saved_articles)}개 저장됨")
        return saved_articles
    except ValueError as e:
        # ValueError는 그대로 전달
        raise
    except Exception as e:
        import traceback
        print(f"뉴스 수집 중 예상치 못한 오류: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"뉴스 수집 실패: {str(e)}")
