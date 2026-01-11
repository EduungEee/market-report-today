# Backend 실행 가이드

## 방법 1: Docker Compose 사용 (권장)

프로젝트 루트에서 실행:

```bash
# 1. 환경 변수 설정
cd /Users/woolim/jtj
cp .env.example .env
# .env 파일에 API 키 등 설정

# 2. 전체 서비스 실행 (PostgreSQL + Backend)
docker-compose up -d

# 3. 로그 확인
docker-compose logs -f backend

# 4. 서비스 중지
docker-compose down
```

**접속 주소:**

- API: http://localhost:8000
- API 문서: http://localhost:8000/docs
- 헬스 체크: http://localhost:8000/api/health
- 데이터베이스 관리 (Adminer): http://localhost:8080

---

## 방법 2: 로컬에서 직접 실행

### 사전 요구사항

- Python 3.11+
- PostgreSQL 15 (또는 Docker로 실행)

### 실행 단계

```bash
# 1. 가상환경 생성 및 활성화
cd /Users/woolim/jtj/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
# 프로젝트 루트의 .env 파일 설정 또는
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/stock_analysis"

# 4. PostgreSQL 실행 (Docker 사용 시)
docker run --name postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=stock_analysis -p 5432:5432 -d postgres:15

# 5. 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**접속 주소:**

- API: http://localhost:8000
- API 문서: http://localhost:8000/docs

---

## 문제 해결

### 포트가 이미 사용 중인 경우

```bash
# 포트 확인
lsof -i :8000

# 다른 포트로 실행
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 데이터베이스 연결 실패

- PostgreSQL이 실행 중인지 확인
- `DATABASE_URL` 환경 변수 확인
- Docker Compose 사용 시: `docker-compose ps`로 postgres 서비스 확인

### 데이터베이스 데이터 확인

**Adminer 사용 (웹 인터페이스):**

1. http://localhost:8080 접속
2. 로그인 정보 입력:
   - 시스템: PostgreSQL
   - 서버: postgres
   - 사용자명: postgres
   - 비밀번호: postgres
   - 데이터베이스: stock_analysis
3. "로그인" 버튼 클릭

**또는 psql CLI 사용:**

```bash
docker-compose exec postgres psql -U postgres -d stock_analysis
```

### 모듈을 찾을 수 없는 경우

```bash
# backend 디렉토리에서 실행
cd /Users/woolim/jtj/backend
python -m uvicorn app.main:app --reload
```
