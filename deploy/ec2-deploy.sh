#!/bin/bash

# EC2 배포 스크립트
# 사용법: ./deploy/ec2-deploy.sh

set -e  # 에러 발생 시 스크립트 중단

echo "🚀 EC2 배포 스크립트 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. Docker 설치 확인
echo -e "${YELLOW}1. Docker 설치 확인 중...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker가 설치되어 있지 않습니다.${NC}"
    echo "Docker 설치 중..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo -e "${GREEN}Docker 설치 완료. 로그아웃 후 다시 로그인하세요.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker 설치 확인됨${NC}"

# 2. Docker Compose 설치 확인
echo -e "${YELLOW}2. Docker Compose 설치 확인 중...${NC}"
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Docker Compose가 설치되어 있지 않습니다.${NC}"
    echo "Docker Compose 설치 중..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
echo -e "${GREEN}✓ Docker Compose 설치 확인됨${NC}"

# 3. .env 파일 확인
echo -e "${YELLOW}3. 환경 변수 파일 확인 중...${NC}"
if [ ! -f .env ]; then
    echo -e "${RED}.env 파일이 없습니다.${NC}"
    if [ -f .env.example ]; then
        echo ".env.example 파일을 복사하여 .env 파일을 생성합니다."
        cp .env.example .env
        echo -e "${YELLOW}⚠️  .env 파일을 수정하여 필요한 환경 변수를 설정하세요.${NC}"
        echo "설정 후 다시 스크립트를 실행하세요."
        exit 1
    else
        echo -e "${RED}.env.example 파일도 없습니다.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✓ .env 파일 확인됨${NC}"

# 4. Docker 이미지 빌드
echo -e "${YELLOW}4. Docker 이미지 빌드 중...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache
echo -e "${GREEN}✓ Docker 이미지 빌드 완료${NC}"

# 5. 기존 컨테이너 중지 및 제거
echo -e "${YELLOW}5. 기존 컨테이너 정리 중...${NC}"
docker-compose -f docker-compose.prod.yml down
echo -e "${GREEN}✓ 기존 컨테이너 정리 완료${NC}"

# 6. 컨테이너 시작
echo -e "${YELLOW}6. 컨테이너 시작 중...${NC}"
docker-compose -f docker-compose.prod.yml up -d
echo -e "${GREEN}✓ 컨테이너 시작 완료${NC}"

# 7. 서비스 상태 확인
echo -e "${YELLOW}7. 서비스 상태 확인 중...${NC}"
sleep 5
docker-compose -f docker-compose.prod.yml ps

# 8. 로그 확인
echo -e "${YELLOW}8. 최근 로그 확인 중...${NC}"
docker-compose -f docker-compose.prod.yml logs --tail=50 backend

# 9. nginx 설치 확인
echo -e "${YELLOW}9. nginx 설치 확인 중...${NC}"
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}nginx가 설치되어 있지 않습니다. 설치 중...${NC}"
    sudo apt update
    sudo apt install nginx -y
    sudo systemctl enable nginx
    echo -e "${GREEN}✓ nginx 설치 완료${NC}"
else
    echo -e "${GREEN}✓ nginx 설치 확인됨${NC}"
fi

# 10. nginx 설정 파일 적용
echo -e "${YELLOW}10. nginx 설정 파일 적용 중...${NC}"
if [ ! -f nginx/nginx.conf ]; then
    echo -e "${RED}nginx/nginx.conf 파일을 찾을 수 없습니다.${NC}"
    echo -e "${YELLOW}⚠️  nginx 설정을 수동으로 적용하세요.${NC}"
else
    # nginx 설정 파일 복사
    sudo cp nginx/nginx.conf /etc/nginx/sites-available/jtj
    
    # 심볼릭 링크 생성 (이미 존재하면 제거 후 생성)
    if [ -L /etc/nginx/sites-enabled/jtj ]; then
        sudo rm /etc/nginx/sites-enabled/jtj
    fi
    sudo ln -s /etc/nginx/sites-available/jtj /etc/nginx/sites-enabled/
    
    # 기본 설정 비활성화 (선택사항 - 사용자가 원하면 주석 해제)
    # if [ -L /etc/nginx/sites-enabled/default ]; then
    #     sudo rm /etc/nginx/sites-enabled/default
    # fi
    
    # nginx 설정 테스트
    if sudo nginx -t; then
        echo -e "${GREEN}✓ nginx 설정 파일 검증 성공${NC}"
        
        # nginx 재시작
        echo -e "${YELLOW}nginx 재시작 중...${NC}"
        sudo systemctl restart nginx
        echo -e "${GREEN}✓ nginx 재시작 완료${NC}"
    else
        echo -e "${RED}nginx 설정 파일에 오류가 있습니다.${NC}"
        echo -e "${YELLOW}⚠️  nginx 설정을 수동으로 확인하세요.${NC}"
        echo "  sudo nginx -t"
    fi
fi

echo ""
echo -e "${GREEN}✅ 배포 완료!${NC}"
echo ""
echo "다음 명령어로 서비스 상태를 확인할 수 있습니다:"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  docker-compose -f docker-compose.prod.yml logs -f backend"
echo "  sudo systemctl status nginx"
echo ""
echo "nginx 로그 확인:"
echo "  sudo tail -f /var/log/nginx/access.log"
echo "  sudo tail -f /var/log/nginx/error.log"
