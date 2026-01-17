#!/bin/bash

# 로컬 데이터베이스 초기화 스크립트
# 뉴스 데이터(news_articles)를 제외한 모든 테이블의 데이터를 삭제합니다.
#
# 사용법:
#   ./reset_db.sh
#   또는
#   ./reset_db.sh --yes

set -e

# 로컬 DB 설정 (docker-compose 사용)
LOCAL_DB="stock_analysis"
LOCAL_USER="postgres"
LOCAL_PASSWORD="postgres"
DOCKER_COMPOSE_FILE="docker-compose.yml"

# 옵션 파싱
SKIP_CONFIRM=false
if [ "$1" == "--yes" ] || [ "$1" == "-y" ]; then
    SKIP_CONFIRM=true
fi

# docker-compose가 실행 중인지 확인
if ! docker-compose -f "${DOCKER_COMPOSE_FILE}" ps postgres | grep -q "Up"; then
    echo "❌ docker-compose의 postgres 컨테이너가 실행 중이 아닙니다."
    echo "   docker-compose up -d를 실행하세요."
    exit 1
fi

# 확인 요청
if [ "${SKIP_CONFIRM}" = false ]; then
    echo "============================================================"
    echo "⚠️  경고: 이 작업은 다음 테이블의 모든 데이터를 삭제합니다:"
    echo "   - reports"
    echo "   - report_industries"
    echo "   - report_stocks"
    echo "   - report_news (관계 테이블)"
    echo "   - email_subscriptions"
    echo ""
    echo "   다음 테이블은 유지됩니다:"
    echo "   - news_articles (뉴스 데이터)"
    echo "============================================================"
    echo ""
    read -p "정말로 진행하시겠습니까? (yes/no): " response
    
    if [ "${response}" != "yes" ] && [ "${response}" != "y" ]; then
        echo "❌ 작업이 취소되었습니다."
        exit 0
    fi
fi

echo "============================================================"
echo "🗑️  데이터베이스 초기화 시작..."
echo "============================================================"

# PostgreSQL 명령 실행 헬퍼 함수
run_psql() {
    docker-compose -f "${DOCKER_COMPOSE_FILE}" exec -T postgres \
        env PGPASSWORD="${LOCAL_PASSWORD}" \
        psql -U "${LOCAL_USER}" -d "${LOCAL_DB}" -c "$1"
}

# 1. 관계 테이블 삭제 (report_news)
echo "📋 report_news 관계 테이블 삭제 중..."
run_psql "DELETE FROM report_news;" > /dev/null
echo "   ✅ report_news 삭제 완료"

# 2. report_stocks 삭제
echo "📋 report_stocks 삭제 중..."
STOCKS_COUNT=$(run_psql "SELECT COUNT(*) FROM report_stocks;" -t | tr -d ' ')
run_psql "DELETE FROM report_stocks;" > /dev/null
echo "   ✅ report_stocks ${STOCKS_COUNT}개 삭제 완료"

# 3. report_industries 삭제
echo "📋 report_industries 삭제 중..."
INDUSTRIES_COUNT=$(run_psql "SELECT COUNT(*) FROM report_industries;" -t | tr -d ' ')
run_psql "DELETE FROM report_industries;" > /dev/null
echo "   ✅ report_industries ${INDUSTRIES_COUNT}개 삭제 완료"

# 4. reports 삭제
echo "📋 reports 삭제 중..."
REPORTS_COUNT=$(run_psql "SELECT COUNT(*) FROM reports;" -t | tr -d ' ')
run_psql "DELETE FROM reports;" > /dev/null
echo "   ✅ reports ${REPORTS_COUNT}개 삭제 완료"

# 5. email_subscriptions 삭제
echo "📋 email_subscriptions 삭제 중..."
SUBSCRIPTIONS_COUNT=$(run_psql "SELECT COUNT(*) FROM email_subscriptions;" -t | tr -d ' ')
run_psql "DELETE FROM email_subscriptions;" > /dev/null
echo "   ✅ email_subscriptions ${SUBSCRIPTIONS_COUNT}개 삭제 완료"

# 뉴스 데이터 확인
NEWS_COUNT=$(run_psql "SELECT COUNT(*) FROM news_articles;" -t | tr -d ' ')

echo "============================================================"
echo "✅ 데이터베이스 초기화 완료!"
echo "   📰 news_articles: ${NEWS_COUNT}개 (유지됨)"
echo "============================================================"
