from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from serpapi import GoogleSearch
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(
    prefix="/api/v1/keyword-insights",
    tags=["keyword insights"]
)

class KeywordRequest(BaseModel):
    keyword: str

async def get_search_insights(keyword: str) -> Dict[str, Any]:
    params = {
        "engine": "google",
        "google_domain": "google.co.kr",
        "q": keyword,
        "api_key": os.getenv("SERPAPI_API_KEY"),
        "location": "Seoul",
        "hl": "ko",
        "gl": "kr",
        "num": 5
    }
    
    search = GoogleSearch(params)
    return search.get_dict()

@router.post("/analyze")
async def analyze_keyword(request: KeywordRequest):
    """
    키워드 종합 분석 API
    
    - Google 검색 결과 분석
    - 상위 검색 결과 및 관련 데이터 제공
    """
    try:
        # SerpAPI를 사용하여 데이터 수집
        return await get_search_insights(request.keyword)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"키워드 분석 중 오류가 발생했습니다: {str(e)}"
        )