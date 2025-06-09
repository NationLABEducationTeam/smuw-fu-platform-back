# SMWU Sales Data API

## 프로젝트 개요
숙명여자대학교 매출 데이터 분석 및 트렌드 분석을 위한 FastAPI 기반 백엔드 API 서버입니다.
행정동별 매출 데이터 처리, 키워드 인사이트 분석, 트렌드 분석 기능을 제공합니다.

## 주요 기능
- **매출 데이터 분석**: 행정동별 매출 데이터 수집 및 분석
- **키워드 인사이트**: 매출 데이터 기반 키워드 분석 및 인사이트 제공
- **트렌드 분석**: 시계열 데이터 기반 트렌드 분석 및 예측

## 기술 스택
- **Framework**: FastAPI
- **Database**: Couchbase
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: Selenium, BeautifulSoup
- **Server**: Uvicorn
- **Language**: Python 3.x

## API 엔드포인트
- `/sales` - 매출 데이터 관련 API
- `/keyword-insights` - 키워드 인사이트 분석 API
- `/trends` - 트렌드 분석 API
- `/docs` - Swagger UI 문서
- `/redoc` - ReDoc 문서

## 설치 및 실행

### 1. 프로젝트 클론
```bash
git clone https://github.com/NationLABEducationTeam/smuw-fu-platform-back.git
cd smuw-fu-platform-back
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv smuw-fast-server
source smuw-fast-server/bin/activate  # macOS/Linux
# 또는
smuw-fast-server\Scripts\activate  # Windows
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경변수 설정
프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경변수를 설정하세요.

### 5. 애플리케이션 실행
```bash
# 개발 환경
python app/main.py

# 또는 uvicorn 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API 문서
서버 실행 후 다음 URL에서 API 문서를 확인할 수 있습니다:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조
```
smwu-python-backend/
├── app/
│   ├── main.py              # 메인 애플리케이션
│   ├── database.py          # 데이터베이스 설정
│   ├── models.py            # 데이터 모델
│   ├── routers/             # API 라우터
│   │   ├── sales.py         # 매출 데이터 API
│   │   ├── keyword_insights.py  # 키워드 인사이트 API
│   │   └── trends.py        # 트렌드 분석 API
│   └── __init__.py
├── tests/                   # 테스트 파일
├── smuw-fast-server/        # 가상환경
├── requirements.txt         # Python 의존성
├── .gitignore              # Git 제외 파일
└── README.md               # 프로젝트 문서
```

## 개발 환경 설정
1. Python 3.8 이상 필요
2. Couchbase 서버 설치 및 설정
3. Chrome 브라우저 (Selenium WebDriver용)

## 라이선스
이 프로젝트는 숙명여자대학교의 교육 목적으로 개발되었습니다.

## 문의사항
프로젝트 관련 문의사항이 있으시면 Issues 탭을 통해 문의해주세요. 