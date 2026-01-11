#!/usr/bin/env python3
"""
Day 2 기능 테스트 스크립트
뉴스 수집 및 AI 분석 기능을 테스트합니다.
"""
import requests
import json
import sys

API_BASE_URL = "http://localhost:8000"


def test_health():
    """헬스 체크 테스트"""
    print("=" * 50)
    print("1. 헬스 체크 테스트")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✅ 상태: {data.get('status')}")
        print(f"✅ 데이터베이스: {data.get('database')}")
        return True
    except Exception as e:
        print(f"❌ 헬스 체크 실패: {e}")
        return False


def test_analyze(query="주식", count=10, force=False):
    """분석 API 테스트"""
    print("\n" + "=" * 50)
    print("2. 뉴스 수집 및 AI 분석 테스트")
    print("=" * 50)
    
    url = f"{API_BASE_URL}/api/analyze"
    payload = {
        "query": query,
        "count": count,
        "force": force
    }
    
    print(f"요청: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    print("\n분석 중... (잠시만 기다려주세요)")
    
    try:
        response = requests.post(url, json=payload, timeout=120)  # AI 분석은 시간이 걸릴 수 있음
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ 분석 완료!")
        print(f"   - 보고서 ID: {data.get('report_id')}")
        print(f"   - 상태: {data.get('status')}")
        print(f"   - 메시지: {data.get('message')}")
        print(f"   - 수집된 뉴스: {data.get('news_count')}개")
        
        return data.get('report_id')
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ API 호출 실패: {e}")
        if e.response:
            try:
                error_data = e.response.json()
                print(f"   오류 내용: {error_data.get('detail', '알 수 없는 오류')}")
            except:
                print(f"   응답: {e.response.text}")
        return None
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        return None


def main():
    """메인 테스트 함수"""
    print("\n" + "=" * 50)
    print("Day 2 기능 테스트 시작")
    print("=" * 50)
    
    # 1. 헬스 체크
    if not test_health():
        print("\n❌ 서버가 실행 중이지 않습니다.")
        print("   다음 명령어로 서버를 실행하세요:")
        print("   docker-compose up -d")
        sys.exit(1)
    
    # 2. 분석 테스트
    report_id = test_analyze(query="주식", count=10, force=False)
    
    if report_id:
        print("\n" + "=" * 50)
        print("✅ 테스트 성공!")
        print("=" * 50)
        print(f"\n생성된 보고서 확인:")
        print(f"  - 보고서 ID: {report_id}")
        print(f"  - API 문서: http://localhost:8000/docs")
        print(f"  - 다음 단계: Day 3 (보고서 조회 API 구현)")
    else:
        print("\n" + "=" * 50)
        print("❌ 테스트 실패")
        print("=" * 50)
        print("\n확인 사항:")
        print("  1. 환경 변수 설정 확인 (.env 파일)")
        print("  2. OpenAI API 키 확인")
        print("  3. 네이버 API 키 확인")
        print("  4. 서버 로그 확인: docker-compose logs -f backend")
        sys.exit(1)


if __name__ == "__main__":
    main()
