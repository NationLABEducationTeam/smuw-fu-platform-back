"""
SMWU Sales Data API - 주요 애플리케이션 모듈
메인 FastAPI 애플리케이션과 라우터 설정을 담당
"""
import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


# 경로 설정 (필요한 경우)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_application() -> FastAPI:
    """
    FastAPI 애플리케이션을 생성하고 설정합니다.
    
    Returns:
        FastAPI: 설정된 FastAPI 애플리케이션 인스턴스
    """
    # 라우터 모듈을 여기서 임포트
    from app.routers import sales, keyword_insights, trends
    
    application = FastAPI(
        title="SMWU Sales Data API",
        description="행정동별 매출 데이터 및 트렌드 분석 API",
        version="1.0.0",
        docs_url=None,  # 커스텀 독스 URL 사용
        redoc_url="/redoc"
    )

    # CORS 설정
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 추가
    application.include_router(sales.router)
    application.include_router(keyword_insights.router)
    application.include_router(trends.router)

    # 커스텀 문서 URL 추가
    @application.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=application.openapi_url,
            title=f"{application.title} - API 문서",
            swagger_js_url=(
                "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
                "swagger-ui-bundle.js"
            ),
            swagger_css_url=(
                "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/"
                "swagger-ui.css"
            ),
        )

    @application.get("/openapi.json", include_in_schema=False)
    async def get_open_api_endpoint():
        return get_openapi(
            title=application.title,
            version=application.version,
            description=application.description,
            routes=application.routes,
        )

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)