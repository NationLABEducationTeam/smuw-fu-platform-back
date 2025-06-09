"""
키워드 인사이트 라우터 모듈

키워드 분석 및 검색어 트렌드 조회 API
"""
import os
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from serpapi import GoogleSearch
from dotenv import load_dotenv

from app.models import KeywordSearchRequest, KeywordSearchResponse


load_dotenv()


# SerpAPI 키 초기화
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")


router = APIRouter(
    prefix="/api/v1/keyword-insights",
    tags=["keyword insights"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal Server Error"}
    }
)


def get_api_key() -> str:
    """
    API 키 검증 및 반환
    
    Returns:
        str: SerpAPI API 키
    
    Raises:
        HTTPException: API 키가 설정되지 않은 경우
    """
    if not SERPAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SerpAPI 키가 설정되지 않았습니다."
        )
    return SERPAPI_API_KEY


async def get_search_insights(
    keyword: str, 
    api_key: str, 
    location: str = "Seoul",
    num_results: int = 5
) -> Dict[str, Any]:
    """
    SerpAPI를 통한 검색 인사이트 데이터 수집
    
    Args:
        keyword: 검색 키워드
        api_key: SerpAPI API 키
        location: 검색 위치
        num_results: 결과 개수
        
    Returns:
        Dict[str, Any]: 검색 결과 데이터
    """
    params = {
        "engine": "google",
        "google_domain": "google.co.kr",
        "q": keyword,
        "api_key": api_key,
        "location": location,
        "hl": "ko",
        "gl": "kr",
        "num": num_results
    }
    
    search = GoogleSearch(params)
    return search.get_dict()


@router.post(
    "/analyze", 
    response_model=KeywordSearchResponse,
    summary="키워드 분석 API",
    description="검색 키워드에 대한 종합 분석 데이터를 제공합니다."
)
async def analyze_keyword(
    request: KeywordSearchRequest,
    api_key: str = Depends(get_api_key)
):
    """
    키워드 종합 분석 API
    
    - Google 검색 결과 분석
    - 상위 검색 결과 및 관련 데이터 제공
    """
    try:
        # 위치 정보 설정
        location = request.location or "Seoul"
        
        # SerpAPI를 사용하여 데이터 수집
        search_data = await get_search_insights(
            request.keyword, api_key, location
        )
        
        # 응답 데이터 구성
        response_data = {
            "keyword": request.keyword,
            "timestamp": search_data.get("search_metadata", {}).get(
                "created_at", ""
            ),
            "total_results": search_data.get("search_information", {}).get(
                "total_results", 0
            ),
            "search_results": search_data.get("organic_results", [])[:5],
            "related_searches": search_data.get("related_searches", []),
        }
        
        return {
            "status": "success",
            "message": "키워드 분석이 완료되었습니다.",
            "data": response_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"키워드 분석 중 오류가 발생했습니다: {str(e)}"
        )