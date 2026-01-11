# 🚀 MVP 구현 계획서

해커톤을 위한 최소 기능 구현 계획서입니다.

## 📋 목표

3-5일 내에 동작하는 MVP를 완성합니다.

## 🎯 핵심 기능 (MVP)

1. ✅ 뉴스 수집 (수동/API)
2. ✅ AI 분석 (OpenAI)
3. ✅ 보고서 생성 및 저장
4. ✅ 웹에서 보고서 조회
5. ⚠️ 이메일 전송 (선택사항 - 외부 이메일 API 사용: SendGrid/Resend)

## 📅 일정 (5일 기준)

### Day 1: Backend 기본 구조 + DB

**목표**: FastAPI 서버 실행, DB 연결

- [x] 프로젝트 구조 생성
- [x] Docker Compose 설정
- [x] PostgreSQL 연결
- [x] SQLAlchemy 모델 정의
  - [x] `news_articles` 테이블
  - [x] `reports` 테이블
  - [x] `report_industries` 테이블
  - [x] `report_stocks` 테이블
- [x] FastAPI 기본 구조 (`main.py`)
- [x] 헬스 체크 API (`GET /api/health`)

**체크포인트**: `http://localhost:8000/docs` 접속 가능

---

### Day 2: 뉴스 수집 + AI 분석

**목표**: 뉴스 수집 및 AI 분석 파이프라인

- [x] 뉴스 API 연동 (`app/news.py`)
  - [x] 네이버 뉴스 API (최신 뉴스 10개)
  - [x] 뉴스 저장 함수
- [x] OpenAI API 연동 (`app/analysis.py`)
  - [x] 프롬프트 작성
  - [x] 뉴스 분석 함수
  - [x] 산업/주식 분석 함수
- [x] 분석 결과 저장
- [x] 분석 API (`POST /api/analyze`)

**체크포인트**: 뉴스 수집 → AI 분석 → DB 저장 플로우 동작

---

### Day 3: 보고서 API + Frontend 기본

**목표**: 보고서 조회 API 및 Frontend 기본 구조

**Backend:**

- [x] 보고서 조회 API (`GET /api/report/{report_id}`)
- [x] 오늘의 보고서 API (`GET /api/reports/today`)

**Frontend:**

- [x] Next.js 15 프로젝트 초기화
- [x] Tailwind 4 CSS 설정
- [x] shadcn/ui 설정
- [x] 레이아웃 구조 (`app/layout.tsx`)
- [x] API 클라이언트 함수 (`lib/api/reports.ts`)
- [x] 홈페이지 기본 구조 (`app/page.tsx`)

**체크포인트**: Frontend에서 Backend API 호출 성공

---

### Day 4: Frontend 페이지 구현

**목표**: 홈페이지 및 보고서 상세 페이지

- [x] 홈페이지 구현
  - [x] Hero 섹션
  - [x] 오늘의 보고서 목록 (`components/TodayReports.tsx`)
  - [x] 보고서 카드 컴포넌트
- [x] 보고서 상세 페이지 (`app/report/[id]/page.tsx`)
  - [x] 보고서 헤더
  - [x] 뉴스 기사 리스트
  - [x] 산업별 분석 섹션
  - [x] 주식 카드 컴포넌트

**체크포인트**: 전체 플로우 동작 (홈 → 보고서 상세)

---

### Day 5: 통합 테스트 + 버그 수정

**목표**: 전체 기능 테스트 및 최종 수정

- [ ] 전체 플로우 테스트
  - [ ] 뉴스 수집 → 분석 → 보고서 생성
  - [ ] Frontend에서 보고서 조회
- [ ] 버그 수정
- [ ] UI/UX 개선
- [ ] 이메일 기능 (시간 여유 시)
  - [ ] 외부 이메일 API 연동 (SendGrid/Resend)
  - [ ] 이메일 구독 API (`POST /api/subscribe`)
  - [ ] 이메일 전송 기능 (`app/email.py`)

**체크포인트**: 데모 가능한 상태

---

## 🗂 프로젝트 구조

```
jtj/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 앱
│   │   ├── news.py          # 뉴스 수집
│   │   ├── analysis.py      # AI 분석
│   │   ├── report.py        # 보고서 생성
│   │   └── email.py         # 이메일 전송 (외부 API)
│   ├── models/
│   │   └── models.py        # SQLAlchemy 모델
│   ├── routers/
│   │   ├── reports.py       # 보고서 API
│   │   └── analyze.py       # 분석 API
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx         # 홈페이지
│   │   └── report/
│   │       └── [id]/
│   │           └── page.tsx # 보고서 상세
│   ├── components/
│   │   ├── TodayReports.tsx
│   │   └── StockCard.tsx
│   ├── lib/
│   │   └── api/
│   │       └── reports.ts    # API 클라이언트
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── .env.example
```

## 🔧 기술 스택 상세

### Backend

- **Framework**: FastAPI
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy
- **AI**: OpenAI API
- **Email**: SendGrid 또는 Resend API (외부 이메일 서비스)

### Frontend

- **Framework**: Next.js 15 (App Router)
- **Styling**: Tailwind CSS

### Infrastructure

- **Containerization**: Docker & Docker Compose

## 🗄 데이터베이스 스키마 (최소)

```sql
-- 뉴스 기사
CREATE TABLE news_articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    source VARCHAR(255),
    url VARCHAR(1000),
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 보고서
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_date DATE NOT NULL
);

-- 보고서-뉴스 연결
CREATE TABLE report_news (
    report_id INTEGER REFERENCES reports(id),
    news_id INTEGER REFERENCES news_articles(id),
    PRIMARY KEY (report_id, news_id)
);

-- 산업 분석
CREATE TABLE report_industries (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    industry_name VARCHAR(255) NOT NULL,
    impact_level VARCHAR(50),
    trend_direction VARCHAR(50)
);

-- 주식 분석
CREATE TABLE report_stocks (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES reports(id),
    industry_id INTEGER REFERENCES report_industries(id),
    stock_code VARCHAR(50),
    stock_name VARCHAR(255),
    expected_trend VARCHAR(50),
    confidence_score DECIMAL(3,2),
    reasoning TEXT
);
```

## 🔌 API 엔드포인트 (MVP)

### 필수

- `GET /api/health` - 헬스 체크
- `GET /api/reports/today` - 오늘의 보고서 목록
- `GET /api/report/{report_id}` - 보고서 상세
- `POST /api/analyze` - 뉴스 분석 요청

### 선택 (시간 여유 시)

- `POST /api/subscribe` - 이메일 구독
- `POST /api/send-email` - 이메일 전송 (외부 이메일 API 사용)

## 🎨 Frontend 페이지 (MVP)

### 필수

- `/` - 홈페이지 (오늘의 보고서 목록)
- `/report/[id]` - 보고서 상세 페이지

### 선택

- 이메일 구독 폼 (홈페이지에 추가)

## ⚡ 빠른 시작 체크리스트

### 초기 설정

- [ ] Git 저장소 생성
- [ ] `.env.example` 파일 생성
- [ ] `docker-compose.yml` 작성
- [ ] Backend `Dockerfile` 작성
- [ ] Frontend `Dockerfile` 작성

### Backend

- [ ] `requirements.txt` 작성
- [ ] FastAPI 앱 초기화
- [ ] DB 모델 정의
- [ ] 기본 API 라우터

### Frontend

- [ ] Next.js 15 프로젝트 생성
- [ ] Tailwind CSS 설정
- [ ] 기본 레이아웃

## 🐛 문제 해결 가이드

### DB 연결 실패

- Docker Compose에서 postgres 서비스 확인
- `DATABASE_URL` 환경 변수 확인

### OpenAI API 에러

- API 키 확인
- Rate limit 확인
- 프롬프트 최적화 (토큰 수 줄이기)

### 이메일 API 에러

- SendGrid/Resend API 키 확인
- Rate limit 확인 (무료 티어 제한 확인)
- 이메일 템플릿 형식 확인
- 발신자 이메일 도메인 인증 확인 (SendGrid/Resend)

### Frontend-Backend 연결 실패

- CORS 설정 확인
- `NEXT_PUBLIC_API_URL` 환경 변수 확인
- 네트워크 요청 확인 (브라우저 DevTools)
- 네트워크 요청 확인 (브라우저 DevTools)

## 📝 개발 팁

1. **우선순위**: 핵심 기능부터 구현
2. **테스트**: 각 단계마다 동작 확인
3. **에러 처리**: 기본적인 에러 처리만 (MVP)
4. **UI**: 최소한의 스타일링 (Tailwind 기본 클래스)
5. **데이터**: Mock 데이터로 먼저 테스트
6. **이메일**: 외부 API 사용 (SendGrid 무료 티어 또는 Resend 무료 티어 활용)

## 🎯 MVP 완성 기준

- [ ] 뉴스 수집 가능
- [ ] AI 분석 결과 생성
- [ ] 보고서 DB 저장
- [ ] Frontend에서 보고서 조회 가능
- [ ] 전체 플로우 동작 확인

---

**해커톤 MVP** - 빠르게 동작하는 프로토타입 완성!
