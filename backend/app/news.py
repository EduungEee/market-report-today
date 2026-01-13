"""
뉴스 수집 모듈
여러 뉴스 API(현재는 newsdata.io)를 사용하여 최신 뉴스를 수집할 수 있도록
확장 가능한 아키텍처로 구성합니다.
"""
import os
import requests
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import sys
import os as os_module
import json
from abc import ABC, abstractmethod

# models 경로 추가
backend_path = os_module.path.dirname(os_module.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from models.models import NewsArticle

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")
NEWSDATA_API_URL = "https://newsdata.io/api/1/latest"
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_API_URL = "https://openapi.naver.com/v1/search/news.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


class BaseNewsProvider(ABC):
    """
    뉴스 제공자 공통 인터페이스.
    여러 뉴스 API를 동일한 형태의 결과로 반환하도록 추상화합니다.

    새 뉴스 API를 추가할 때는 이 클래스를 상속받아 구현하고,
    get_default_providers()에 등록하면 됩니다.
    """

    name: str = "base"

    @abstractmethod
    def fetch(self, query: str, size: int) -> List[dict]:
        """
        뉴스를 수집해 표준화된 딕셔너리 리스트로 반환합니다.
        각 아이템은 다음 키를 포함해야 합니다:
        - title: str
        - content: str
        - source: str
        - url: str
        - published_at: Optional[datetime]
        """
        raise NotImplementedError


def fetch_news_from_api(query: str = "주식", size: int = 10) -> List[dict]:
    """
    newsdata.io API에서 최신 뉴스를 가져옵니다.
    
    Args:
        query: 검색 쿼리 (기본값: "주식")
        size: 가져올 뉴스 개수 (1-10, 기본값: 10개, 무료 티어 제한)
    
    Returns:
        뉴스 기사 리스트
    """
    if not NEWSDATA_API_KEY:
        raise ValueError("NEWSDATA_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    # size 범위 검증 (newsdata.io API 무료 티어: 1-10)
    if size < 1 or size > 10:
        raise ValueError(f"size는 1-10 사이의 값이어야 합니다. (무료 티어 제한) 현재 값: {size}")
    
    # newsdata.io API 파라미터 설정 (한국 관련 뉴스)
    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": query,
        "country": "kr",  # 한국
        "language": "ko",  # 한국어
        "timezone": "asia/seoul",  # 한국 시간대 (소문자)
        "image": 0,  # 이미지 제외
        "video": 0,  # 비디오 제외
        "removeduplicate": 1,  # 중복 제거
        "size": size,  # 가져올 뉴스 개수
        # full_content는 무료 티어에서 지원하지 않으므로 제거
    }
    
    try:
        print(f"newsdata.io API 호출: query={query}, size={size}")
        print(f"요청 파라미터: {params}")
        response = requests.get(NEWSDATA_API_URL, params=params, timeout=10)
        
        # 응답 상태 확인
        print(f"응답 상태 코드: {response.status_code}")
        print(f"요청 URL: {response.url}")
        
        # 422 에러인 경우 상세 응답 로깅
        if response.status_code == 422:
            try:
                error_data = response.json()
                print(f"422 에러 상세 응답: {error_data}")
                error_message = error_data.get("message", "파라미터 오류")
                raise ValueError(f"newsdata.io API 파라미터 오류: {error_message}")
            except:
                print(f"422 에러 응답 텍스트: {response.text}")
                raise ValueError(f"newsdata.io API 파라미터 오류: {response.text}")
        
        response.raise_for_status()
        data = response.json()
        
        # newsdata.io API 응답 형식 확인
        if data.get("status") != "success":
            error_message = data.get("message", "알 수 없는 오류")
            raise ValueError(f"newsdata.io API 오류: {error_message}")
        
        total_results = data.get("totalResults", 0)
        results = data.get("results", [])
        
        print(f"API 응답 성공: 총 {total_results}개 결과, {len(results)}개 반환")
        
        articles = []
        for item in results:
            title = item.get("title", "")
            description = item.get("description", "")
            url = item.get("link", "")
            source_id = item.get("source_id", "")
            
            # pubDate 파싱 (ISO 8601 형식 또는 다른 형식)
            published_at = None
            pub_date_str = item.get("pubDate", "")
            if pub_date_str:
                try:
                    # ISO 8601 형식 파싱 시도
                    # 예: "2024-01-15T10:30:00Z" 또는 "2024-01-15T10:30:00+09:00"
                    published_at = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        # RFC 2822 형식 시도
                        published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except ValueError:
                        try:
                            # 다른 형식 시도
                            published_at = datetime.strptime(pub_date_str, "%Y-%m-%d %H:%M:%S")
                        except:
                            print(f"날짜 파싱 실패: {pub_date_str}")
                            pass
            
            articles.append({
                "title": title,
                "content": description,  # description을 content로 사용
                "source": source_id,  # source_id를 source로 사용
                "url": url,
                "published_at": published_at
            })
        
        print(f"파싱된 뉴스 기사: {len(articles)}개")
        return articles
    except requests.exceptions.HTTPError as e:
        import traceback
        print(f"newsdata.io API HTTP 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 헤더: {dict(e.response.headers)}")
            try:
                error_data = e.response.json()
                print(f"응답 내용: {error_data}")
                error_message = error_data.get("message", "알 수 없는 오류")
                raise ValueError(f"newsdata.io API 오류 ({e.response.status_code}): {error_message}")
            except:
                print(f"응답 내용: {e.response.text}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"newsdata.io API 요청 실패: {str(e)}")
    except requests.exceptions.RequestException as e:
        import traceback
        print(f"newsdata.io API 요청 실패: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"newsdata.io API 요청 실패: {str(e)}")


class NewsdataProvider(BaseNewsProvider):
    """
    newsdata.io 기반 뉴스 제공자.
    기존 구현(fetch_news_from_api)을 Provider 인터페이스로 감싼 클래스입니다.
    """

    name = "newsdata.io"

    def fetch(self, query: str = "주식", size: int = 10) -> List[dict]:
        return fetch_news_from_api(query=query, size=size)


def fetch_news_from_naver(query: str = "주식", size: int = 10) -> List[dict]:
    """
    Naver 뉴스 검색 API에서 최신 뉴스를 가져옵니다.
    
    Args:
        query: 검색 쿼리 (기본값: "주식")
        size: 가져올 뉴스 개수 (1-100, 기본값: 10개)
    
    Returns:
        뉴스 기사 리스트
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET 환경 변수가 설정되지 않았습니다.")
    
    # size 범위 검증 (Naver API: 1-100)
    if size < 1 or size > 100:
        raise ValueError(f"size는 1-100 사이의 값이어야 합니다. 현재 값: {size}")
    
    # Naver API 헤더 설정
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    # Naver API 파라미터 설정
    params = {
        "query": query,
        "display": min(size, 100),  # 최대 100개
        "sort": "date",  # 날짜순 정렬
        "start": 1  # 시작 위치
    }
    
    try:
        print(f"Naver API 호출: query={query}, size={size}")
        response = requests.get(NAVER_API_URL, headers=headers, params=params, timeout=10)
        
        # 응답 상태 확인
        print(f"응답 상태 코드: {response.status_code}")
        print(f"요청 URL: {response.url}")
        
        response.raise_for_status()
        data = response.json()
        
        # Naver API 응답 형식 확인
        total_results = data.get("total", 0)
        items = data.get("items", [])
        
        print(f"API 응답 성공: 총 {total_results}개 결과, {len(items)}개 반환")
        
        articles = []
        for item in items:
            # HTML 태그 제거 (Naver API는 HTML 태그가 포함된 제목/내용을 반환)
            title = item.get("title", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            description = item.get("description", "").replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            originallink = item.get("originallink", "")
            link = item.get("link", "")
            # originallink가 있으면 우선 사용, 없으면 link 사용
            url = originallink if originallink else link
            
            # pubDate 파싱 (Naver API 형식: "Mon, 15 Jan 2024 10:30:00 +0900")
            published_at = None
            pub_date_str = item.get("pubDate", "")
            if pub_date_str:
                try:
                    # RFC 2822 형식 파싱 시도
                    published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                except ValueError:
                    try:
                        # 다른 형식 시도 (타임존 없이)
                        published_at = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S")
                    except ValueError:
                        try:
                            # ISO 형식 시도
                            published_at = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                        except:
                            print(f"날짜 파싱 실패: {pub_date_str}")
                            pass
            
            articles.append({
                "title": title,
                "content": description,  # description을 content로 사용
                "source": "Naver",  # Naver 뉴스는 출처가 Naver
                "url": url,
                "published_at": published_at
            })
        
        print(f"파싱된 뉴스 기사: {len(articles)}개")
        return articles
    except requests.exceptions.HTTPError as e:
        import traceback
        print(f"Naver API HTTP 오류: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"응답 상태 코드: {e.response.status_code}")
            print(f"응답 헤더: {dict(e.response.headers)}")
            try:
                error_data = e.response.json()
                print(f"응답 내용: {error_data}")
                error_message = error_data.get("errorMessage", "알 수 없는 오류")
                raise ValueError(f"Naver API 오류 ({e.response.status_code}): {error_message}")
            except:
                print(f"응답 내용: {e.response.text}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Naver API 요청 실패: {str(e)}")
    except requests.exceptions.RequestException as e:
        import traceback
        print(f"Naver API 요청 실패: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"Naver API 요청 실패: {str(e)}")


class NaverProvider(BaseNewsProvider):
    """
    Naver 뉴스 검색 API 기반 뉴스 제공자.
    """

    name = "Naver"

    def fetch(self, query: str = "주식", size: int = 10) -> List[dict]:
        return fetch_news_from_naver(query=query, size=size)


def get_default_providers() -> List[BaseNewsProvider]:
    """
    활성화된 기본 뉴스 제공자 목록을 반환합니다.
    - NEWSDATA_API_KEY가 설정되어 있으면 newsdata.io Provider를 사용합니다.
    - NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되어 있으면 Naver Provider를 사용합니다.
    - 향후 다른 뉴스 API를 추가할 때는 이 함수에 Provider를 추가하면 됩니다.
    """
    providers: List[BaseNewsProvider] = []

    if NEWSDATA_API_KEY:
        providers.append(NewsdataProvider())

    if NAVER_CLIENT_ID and NAVER_CLIENT_SECRET:
        providers.append(NaverProvider())

    return providers


def create_embedding(text_content: str) -> Optional[List[float]]:
    """
    OpenAI Embedding API를 사용하여 텍스트의 벡터 임베딩을 생성합니다.
    
    Args:
        text_content: 임베딩을 생성할 텍스트 (meta description)
    
    Returns:
        벡터 임베딩 리스트 (1536 차원) 또는 None (실패 시)
    """
    if not OPENAI_API_KEY:
        print("⚠️  OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. 임베딩을 생성할 수 없습니다.")
        return None
    
    if not text_content or not text_content.strip():
        print("⚠️  빈 텍스트로는 임베딩을 생성할 수 없습니다.")
        return None
    
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # text-embedding-3-small 모델 사용 (1536 차원, 비용 효율적)
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text_content.strip()
        )
        
        embedding = response.data[0].embedding
        print(f"✅ 임베딩 생성 완료: {len(embedding)} 차원")
        return embedding
    except Exception as e:
        import traceback
        print(f"⚠️  임베딩 생성 실패: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return None


def create_metadata(title: str, url: str, published_at: Optional[datetime], collected_at: Optional[datetime]) -> dict:
    """
    벡터 DB에 저장할 메타데이터를 생성합니다.
    LLM이 나중에 어떤 기사를 참조했는지 알 수 있도록 title과 url을 반드시 포함합니다.
    
    Args:
        title: 뉴스 기사 제목
        url: 뉴스 기사 URL
        published_at: 발행 날짜
        collected_at: 수집 날짜
    
    Returns:
        메타데이터 딕셔너리
    """
    metadata = {
        "title": title,
        "url": url,
    }
    
    if published_at:
        # ISO 8601 형식으로 저장
        metadata["published_date"] = published_at.isoformat()
    
    if collected_at:
        metadata["collected_at"] = collected_at.isoformat()
    else:
        metadata["collected_at"] = datetime.now().isoformat()
    
    return metadata


def save_embedding_to_db(db: Session, article_id: int, embedding: List[float], metadata: dict, commit: bool = False):
    """
    pgvector에 벡터 임베딩을 저장합니다.
    
    Args:
        db: 데이터베이스 세션
        article_id: 뉴스 기사 ID
        embedding: 벡터 임베딩 리스트
        metadata: 메타데이터 딕셔너리
        commit: 커밋 여부 (기본값: False, 트랜잭션을 외부에서 관리할 때 사용)
    """
    try:
        # 벡터를 PostgreSQL 배열 형식으로 변환
        # pgvector 형식: '[1,2,3]'::vector(1536)
        embedding_str = "[" + ",".join(map(str, embedding)) + "]"
        
        # 메타데이터를 JSON 문자열로 변환
        metadata_json = json.dumps(metadata, ensure_ascii=False)
        
        # pgvector에 벡터 저장 (connection을 직접 사용하여 raw SQL 실행)
        # embedding 컬럼은 vector(1536) 타입이므로 SQL로 직접 업데이트
        # SQLAlchemy의 connection에서 실제 psycopg2 connection 얻기
        sqlalchemy_conn = db.connection()
        # SQLAlchemy 버전에 따라 다른 방법으로 raw connection 얻기
        if hasattr(sqlalchemy_conn, 'connection'):
            raw_conn = sqlalchemy_conn.connection
            # driver_connection이 있으면 사용 (SQLAlchemy 2.0+)
            if hasattr(raw_conn, 'driver_connection'):
                raw_conn = raw_conn.driver_connection
        else:
            raw_conn = sqlalchemy_conn
        cursor = raw_conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE news_articles 
                SET embedding = %s::vector(1536),
                    metadata = %s::jsonb
                WHERE id = %s
            """, (embedding_str, metadata_json, article_id))
            # commit 파라미터가 True일 때만 커밋 (트랜잭션을 외부에서 관리할 때는 False)
            if commit:
                raw_conn.commit()
            print(f"✅ 벡터 임베딩 저장 완료: article_id={article_id}")
        finally:
            cursor.close()
    except Exception as e:
        # 벡터 값이 너무 길어서 에러 로그에 출력하지 않음
        error_msg = str(e)
        # SQL 쿼리 내용을 제거하고 에러 메시지만 출력
        if "SQL:" in error_msg:
            error_msg = error_msg.split("SQL:")[0].strip()
        print(f"⚠️  벡터 임베딩 저장 실패 (article_id={article_id}): {error_msg}")
        # traceback은 출력하되, embedding_str이 포함된 부분은 제외
        import traceback
        tb_lines = traceback.format_exc().split('\n')
        filtered_tb = []
        skip_next = False
        for line in tb_lines:
            if 'embedding_str' in line or 'UPDATE news_articles' in line or 'SET embedding' in line:
                skip_next = True
                continue
            if skip_next and ('metadata =' in line or 'WHERE id' in line):
                continue
            skip_next = False
            filtered_tb.append(line)
        print("Traceback (벡터 값 제외):")
        print('\n'.join(filtered_tb))
        # rollback은 호출하지 않음 (상위 함수에서 트랜잭션 관리)
        raise


def save_news_to_db(db: Session, articles: List[dict]) -> List[NewsArticle]:
    """
    뉴스 기사를 데이터베이스에 저장합니다.
    중복 체크 (URL 기반)를 수행하고, 벡터 임베딩을 생성하여 pgvector에 저장합니다.
    벡터 저장이 실패하면 뉴스 기사 저장도 함께 롤백됩니다.
    
    Args:
        db: 데이터베이스 세션
        articles: 저장할 뉴스 기사 리스트
    
    Returns:
        저장된 NewsArticle 객체 리스트
    
    Raises:
        Exception: 벡터 저장 실패 시 뉴스 기사 저장도 롤백됨
    """
    saved_articles = []
    collected_at = datetime.now()
    
    try:
        # 1단계: 뉴스 기사 저장 (아직 commit하지 않음)
        for article_data in articles:
            # URL 기반 중복 체크
            existing = db.query(NewsArticle).filter(
                NewsArticle.url == article_data.get("url")
            ).first()
            
            if existing:
                continue
            
            title = article_data.get("title", "")
            content = article_data.get("content", "")  # description을 content로 사용
            url = article_data.get("url", "")
            published_at = article_data.get("published_at")
            
            # NewsArticle 생성 (임베딩과 메타데이터는 나중에 추가)
            news_article = NewsArticle(
                title=title,
                content=content,
                source=article_data.get("source", ""),
                url=url,
                published_at=published_at
            )
            
            db.add(news_article)
            saved_articles.append(news_article)
        
        # flush하여 ID를 얻기 (아직 commit하지 않음)
        db.flush()
        
        # 저장된 객체에 ID 부여를 위해 refresh
        for article in saved_articles:
            db.refresh(article)
        
        # 2단계: 벡터 임베딩 생성 및 저장
        for article in saved_articles:
            # 해당 article의 원본 데이터 찾기
            article_data = next(
                (a for a in articles if a.get("url") == article.url),
                None
            )
            
            if not article_data:
                continue
            
            title = article_data.get("title", "")
            content = article_data.get("content", "")  # meta description 기반
            url = article_data.get("url", "")
            published_at = article_data.get("published_at")
            
            # 메타데이터 생성 (title, url 필수 포함)
            metadata = create_metadata(
                title=title,
                url=url,
                published_at=published_at,
                collected_at=collected_at
            )
            
            # 임베딩 생성 (meta description 기반)
            embedding = create_embedding(content)
            
            if embedding:
                # pgvector에 벡터 저장 (commit=False로 트랜잭션 유지)
                save_embedding_to_db(
                    db=db,
                    article_id=article.id,
                    embedding=embedding,
                    metadata=metadata,
                    commit=False  # 트랜잭션을 외부에서 관리
                )
            else:
                # 임베딩 생성 실패 시에도 메타데이터는 저장
                metadata_json = json.dumps(metadata, ensure_ascii=False)
                # SQLAlchemy의 connection에서 실제 psycopg2 connection 얻기
                sqlalchemy_conn = db.connection()
                # SQLAlchemy 버전에 따라 다른 방법으로 raw connection 얻기
                if hasattr(sqlalchemy_conn, 'connection'):
                    raw_conn = sqlalchemy_conn.connection
                    # driver_connection이 있으면 사용 (SQLAlchemy 2.0+)
                    if hasattr(raw_conn, 'driver_connection'):
                        raw_conn = raw_conn.driver_connection
                else:
                    raw_conn = sqlalchemy_conn
                cursor = raw_conn.cursor()
                
                try:
                    cursor.execute("""
                        UPDATE news_articles 
                        SET metadata = %s::jsonb
                        WHERE id = %s
                    """, (metadata_json, article.id))
                    # commit하지 않음 (트랜잭션을 외부에서 관리)
                finally:
                    cursor.close()
                print(f"✅ 메타데이터 저장 완료 (임베딩 없음): article_id={article.id}")
        
        # 3단계: 모든 작업이 성공하면 commit
        db.commit()
        print(f"✅ 뉴스 수집 및 벡터 저장 완료: {len(saved_articles)}개 저장됨")
        return saved_articles
        
    except Exception as e:
        # 벡터 저장 실패 시 전체 롤백
        db.rollback()
        error_msg = str(e)
        if "SQL:" in error_msg:
            error_msg = error_msg.split("SQL:")[0].strip()
        print(f"⚠️  뉴스 저장 실패 (전체 롤백): {error_msg}")
        raise


def collect_news(db: Session, query: str = "주식", size: int = 10) -> List[NewsArticle]:
    """
    (멀티 Provider 아키텍처) 뉴스를 수집하고 데이터베이스에 저장합니다.

    여러 뉴스 API Provider를 통해 뉴스를 수집한 뒤,
    URL 기준 중복 제거는 DB 저장 함수(save_news_to_db)에서 처리합니다.

    Args:
        db: 데이터베이스 세션
        query: 검색 쿼리
        size: 전체적으로 가져올 목표 뉴스 개수 (기본값: 10개)

    Returns:
        저장된 NewsArticle 객체 리스트

    Raises:
        ValueError: API 호출 실패 또는 뉴스 수집 실패 시
    """
    try:
        providers = get_default_providers()
        if not providers:
            raise ValueError("사용 가능한 뉴스 제공자가 없습니다. API 키 설정을 확인해주세요.")

        # 여러 Provider에 분산할 개수 계산 (소수점 버림, 최소 1개)
        per_provider_size = max(1, size // len(providers))

        collected_articles: List[dict] = []

        for provider in providers:
            try:
                print(f"▶ 뉴스 수집: provider={provider.name}, query={query}, size={per_provider_size}")
                provider_articles = provider.fetch(query=query, size=per_provider_size)

                # Provider 이름을 source가 비어 있을 때 기본값으로 사용
                for article in provider_articles:
                    if not article.get("source"):
                        article["source"] = provider.name
                collected_articles.extend(provider_articles)
            except Exception as e:
                # 개별 Provider 실패는 로그만 남기고 계속 진행
                print(f"⚠️  뉴스 제공자 '{provider.name}' 수집 실패: {e}")

        if not collected_articles:
            raise ValueError(
                f"'{query}' 검색어로 뉴스를 찾을 수 없습니다. "
                f"다른 검색어를 시도하거나 Provider 구성을 확인해주세요."
            )

        # 데이터베이스에 저장 (URL 기반 중복 제거 포함)
        saved_articles = save_news_to_db(db, collected_articles)

        print(f"뉴스 수집 완료 (멀티 Provider): {len(saved_articles)}개 저장됨")
        return saved_articles
    except ValueError:
        # ValueError는 그대로 전달
        raise
    except Exception as e:
        import traceback
        print(f"뉴스 수집 중 예상치 못한 오류: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise ValueError(f"뉴스 수집 실패: {str(e)}")
