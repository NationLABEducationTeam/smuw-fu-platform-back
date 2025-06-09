"""
Google Trends API 라우터 모듈

Google Trends API를 활용한 키워드 트렌드 분석 기능 제공
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime
import os
import json
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 라우터 정의
router = APIRouter(
    prefix="/api/trends",
    tags=["trends"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal Server Error"}
    }
)

# 요청 모델
class TrendRequest(BaseModel):
    """Google Trends 분석 요청 모델"""
    keywords: List[str] = Field(..., description="검색할 키워드 목록 (최대 5개)")
    timeframe: str = Field("today 3-m", description="검색 기간 (예: 'today 3-m', '2023-01-01 2023-12-31')")
    geo: str = Field("KR", description="지역 코드 (기본값: 한국)")
    category: int = Field(0, description="카테고리 ID (기본값: 전체)")

class KeywordSuggestionRequest(BaseModel):
    """키워드 추천 요청 모델"""
    keyword: str = Field(..., description="검색어 추천을 받을 키워드")

# 응답 모델
class TimelineTrendResponse(BaseModel):
    """시간별 트렌드 응답 모델"""
    status: str = Field(..., description="요청 처리 상태")
    data: Dict[str, Any] = Field(..., description="시간별 트렌드 데이터")
    message: str = Field(..., description="응답 메시지")

class RegionTrendResponse(BaseModel):
    """지역별 트렌드 응답 모델"""
    status: str = Field(..., description="요청 처리 상태")
    data: Dict[str, Any] = Field(..., description="지역별 트렌드 데이터")
    message: str = Field(..., description="응답 메시지")

class RelatedTopicsResponse(BaseModel):
    """연관 주제 응답 모델"""
    status: str = Field(..., description="요청 처리 상태")
    data: Dict[str, Any] = Field(..., description="연관 주제 데이터")
    message: str = Field(..., description="응답 메시지")

class RelatedQueriesResponse(BaseModel):
    """연관 검색어 응답 모델"""
    status: str = Field(..., description="요청 처리 상태")
    data: Dict[str, Any] = Field(..., description="연관 검색어 데이터")
    message: str = Field(..., description="응답 메시지")

class KeywordSuggestionsResponse(BaseModel):
    """키워드 추천 응답 모델"""
    status: str = Field(..., description="요청 처리 상태")
    data: List[Dict[str, Any]] = Field(..., description="키워드 추천 데이터")
    message: str = Field(..., description="응답 메시지")

# 유틸리티 함수
def get_pytrends_client():
    """PyTrends 클라이언트를 초기화하고 반환합니다."""
    return TrendReq(
        hl='ko-KR',
        tz=540,  # UTC+9 (한국 시간)
        retries=2,
        backoff_factor=0.5,
        timeout=(5, 20)
    )

def format_trend_data(df, drop_partial=True):
    """
    트렌드 데이터를 API 응답 형식으로 변환합니다.
    
    Args:
        df: 원본 DataFrame
        drop_partial: isPartial 컬럼 제거 여부
    """
    if df is None or df.empty:
        return {}
    
    # isPartial 컬럼 제거
    if drop_partial and 'isPartial' in df.columns:
        df = df.drop('isPartial', axis=1)
    
    # DatetimeIndex 처리
    if isinstance(df.index, pd.DatetimeIndex):
        result = {
            "dates": [d.strftime('%Y-%m-%d %H:%M:%S') for d in df.index],
            "values": {}
        }
        
        # 각 키워드별 값 추출
        for column in df.columns:
            result["values"][column] = df[column].tolist()
    else:
        # 일반적인 인덱스의 경우
        result = {
            "regions": df.index.tolist(),
            "values": {}
        }
        
        # 각 키워드별 값 추출
        for column in df.columns:
            result["values"][column] = df[column].tolist()
    
    return result

def process_related_data(data_dict):
    """
    연관 데이터(주제/쿼리)를 API 응답 형식으로 변환합니다.
    
    Args:
        data_dict: pytrends에서 반환된 딕셔너리 (related_topics 또는 related_queries)
    """
    if not data_dict:
        return {}
    
    result = {}
    
    try:
        for keyword, data in data_dict.items():
            # 키워드에 대한 데이터가 None인 경우 처리
            if data is None:
                result[keyword] = {"rising": [], "top": []}
                continue
                
            result[keyword] = {}
            
            # rising 데이터 처리
            if 'rising' in data and data['rising'] is not None and not data['rising'].empty:
                result[keyword]['rising'] = data['rising'].to_dict(orient='records')
            else:
                result[keyword]['rising'] = []
            
            # top 데이터 처리
            if 'top' in data and data['top'] is not None and not data['top'].empty:
                result[keyword]['top'] = data['top'].to_dict(orient='records')
            else:
                result[keyword]['top'] = []
    except (IndexError, KeyError, TypeError, Exception) as e:
        logger.error(f"연관 데이터 처리 중 오류 발생: {str(e)}")
        # 오류 발생 시 빈 결과 반환
        return {k: {"rising": [], "top": []} for k in data_dict.keys()} if data_dict else {}
    
    return result

# 엔드포인트
@router.post("/timeline", response_model=TimelineTrendResponse)
async def get_interest_over_time(request: TrendRequest):
    """
    시간에 따른 관심도 데이터를 조회합니다.
    
    - 여러 키워드의 시간별 검색 트렌드 데이터 제공
    - 기간 설정 가능 (기본값: 최근 3개월)
    - 지역 설정 가능 (기본값: 한국)
    """
    try:
        # 키워드 개수 검증
        if len(request.keywords) > 5:
            raise HTTPException(
                status_code=400,
                detail="키워드는 최대 5개까지만 지원됩니다."
            )
        
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 페이로드 설정
        pytrends.build_payload(
            request.keywords,
            cat=request.category,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=''
        )
        
        # 시간별 관심도 데이터 조회
        interest_over_time = pytrends.interest_over_time()
        
        # 데이터가 없는 경우
        if interest_over_time.empty:
            return {
                "status": "success",
                "data": {},
                "message": "검색 조건에 맞는 데이터가 없습니다."
            }
        
        # 응답 데이터 구성
        formatted_data = format_trend_data(interest_over_time)
        
        return {
            "status": "success",
            "data": formatted_data,
            "message": "시간별 트렌드 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"시간별 트렌드 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"트렌드 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/regions", response_model=RegionTrendResponse)
async def get_interest_by_region(
    request: TrendRequest,
    resolution: str = Query("COUNTRY", description="지역 단위 (COUNTRY, REGION, CITY, DMA)")
):
    """
    지역별 관심도 데이터를 조회합니다.
    
    - 여러 키워드의 지역별 검색 트렌드 데이터 제공
    - 지역 단위 설정 가능 (국가, 지역, 도시)
    - 기간 설정 가능 (기본값: 최근 3개월)
    """
    try:
        # 키워드 개수 검증
        if len(request.keywords) > 5:
            raise HTTPException(
                status_code=400,
                detail="키워드는 최대 5개까지만 지원됩니다."
            )
        
        # 유효한 resolution 값 검증
        valid_resolutions = ["COUNTRY", "REGION", "CITY", "DMA"]
        if resolution not in valid_resolutions:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 지역 단위입니다. 사용 가능한 값: {valid_resolutions}"
            )
        
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 페이로드 설정
        pytrends.build_payload(
            request.keywords,
            cat=request.category,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=''
        )
        
        # 지역별 관심도 데이터 조회
        interest_by_region = pytrends.interest_by_region(
            resolution=resolution,
            inc_low_vol=True,
            inc_geo_code=False
        )
        
        # 데이터가 없는 경우
        if interest_by_region.empty:
            return {
                "status": "success",
                "data": {},
                "message": f"{resolution} 단위의 데이터가 없습니다."
            }
        
        # 응답 데이터 구성
        formatted_data = format_trend_data(interest_by_region, drop_partial=False)
        
        return {
            "status": "success",
            "data": formatted_data,
            "message": f"{resolution} 단위의 지역별 트렌드 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"지역별 트렌드 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"지역별 트렌드 분석 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/related-topics", response_model=RelatedTopicsResponse)
async def get_related_topics(request: TrendRequest):
    """
    연관 주제 데이터를 조회합니다.
    
    - 키워드와 연관된 주제 제공
    - 상승 중인 주제 및 인기 주제 포함
    """
    try:
        # 키워드 개수 검증
        if len(request.keywords) > 5:
            raise HTTPException(
                status_code=400,
                detail="키워드는 최대 5개까지만 지원됩니다."
            )
        
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 페이로드 설정
        pytrends.build_payload(
            request.keywords,
            cat=request.category,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=''
        )
        
        # 연관 주제 데이터 조회
        related_topics = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                related_topics = pytrends.related_topics()
                # 반환된 데이터가 빈 딕셔너리인지 확인
                if related_topics and any(related_topics.get(keyword) is not None for keyword in request.keywords):
                    break
                
                logger.warning(f"연관 주제 데이터가 비어있습니다. 재시도 중... ({retry_count+1}/{max_retries})")
                retry_count += 1
                import time
                time.sleep(1)  # 요청 간격 두기
            except (IndexError, KeyError, Exception) as e:
                logger.error(f"연관 주제 조회 중 오류 발생: {str(e)}. 재시도 중... ({retry_count+1}/{max_retries})")
                retry_count += 1
                import time
                time.sleep(2)  # 오류 발생 시 더 긴 대기 시간
        
        # 데이터가 없는 경우 빈 결과 반환
        if not related_topics:
            related_topics = {keyword: None for keyword in request.keywords}
        
        # 응답 데이터 구성
        processed_data = process_related_data(related_topics)
        
        return {
            "status": "success",
            "data": processed_data,
            "message": "연관 주제 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"연관 주제 조회 중 오류 발생: {str(e)}")
        return {
            "status": "partial",
            "data": {keyword: {"rising": [], "top": []} for keyword in request.keywords},
            "message": f"연관 주제 분석 중 오류가 발생했습니다: {str(e)}"
        }

@router.post("/related-queries", response_model=RelatedQueriesResponse)
async def get_related_queries(request: TrendRequest):
    """
    연관 검색어 데이터를 조회합니다.
    
    - 키워드와 연관된 검색어 제공
    - 상승 중인 검색어 및 인기 검색어 포함
    """
    try:
        # 키워드 개수 검증
        if len(request.keywords) > 5:
            raise HTTPException(
                status_code=400,
                detail="키워드는 최대 5개까지만 지원됩니다."
            )
        
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 페이로드 설정
        pytrends.build_payload(
            request.keywords,
            cat=request.category,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=''
        )
        
        # 연관 검색어 데이터 조회
        related_queries = None
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                related_queries = pytrends.related_queries()
                # 반환된 데이터가 빈 딕셔너리인지 확인
                if related_queries and any(related_queries.get(keyword) is not None for keyword in request.keywords):
                    break
                
                logger.warning(f"연관 검색어 데이터가 비어있습니다. 재시도 중... ({retry_count+1}/{max_retries})")
                retry_count += 1
                import time
                time.sleep(1)  # 요청 간격 두기
            except (IndexError, KeyError, Exception) as e:
                logger.error(f"연관 검색어 조회 중 오류 발생: {str(e)}. 재시도 중... ({retry_count+1}/{max_retries})")
                retry_count += 1
                import time
                time.sleep(2)  # 오류 발생 시 더 긴 대기 시간
        
        # 데이터가 없는 경우 빈 결과 반환
        if not related_queries:
            related_queries = {keyword: None for keyword in request.keywords}
        
        # 응답 데이터 구성
        processed_data = process_related_data(related_queries)
        
        return {
            "status": "success",
            "data": processed_data,
            "message": "연관 검색어 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"연관 검색어 조회 중 오류 발생: {str(e)}")
        return {
            "status": "partial",
            "data": {keyword: {"rising": [], "top": []} for keyword in request.keywords},
            "message": f"연관 검색어 분석 중 오류가 발생했습니다: {str(e)}"
        }

@router.post("/keyword-suggestions", response_model=KeywordSuggestionsResponse)
async def get_keyword_suggestions(request: KeywordSuggestionRequest):
    """
    키워드 검색어 자동 완성 제안을 조회합니다.
    
    - 입력한 키워드에 대한 Google의 자동 완성 추천 제공
    """
    try:
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 키워드 제안 조회
        suggestions = pytrends.suggestions(request.keyword)
        
        # 데이터가 없는 경우
        if not suggestions:
            return {
                "status": "success",
                "data": [],
                "message": f"키워드 '{request.keyword}'에 대한 추천이 없습니다."
            }
        
        return {
            "status": "success",
            "data": suggestions,
            "message": "키워드 추천 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"키워드 추천 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"키워드 추천 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/interest-by-property")
async def get_interest_by_property(
    request: TrendRequest,
    property_type: str = Query("", description="검색 속성 (빈 문자열: 웹 검색, images: 이미지, news: 뉴스, youtube: 유튜브)")
):
    """
    검색 속성별 관심도 데이터를 조회합니다.
    
    - 웹 검색, 이미지, 뉴스, 유튜브 등 속성별 트렌드 제공
    """
    try:
        # 키워드 개수 검증
        if len(request.keywords) > 5:
            raise HTTPException(
                status_code=400,
                detail="키워드는 최대 5개까지만 지원됩니다."
            )
        
        # 유효한 property_type 값 검증
        valid_properties = ["", "images", "news", "youtube", "froogle"]
        if property_type not in valid_properties:
            raise HTTPException(
                status_code=400,
                detail=f"유효하지 않은 검색 속성입니다. 사용 가능한 값: {valid_properties}"
            )
        
        # PyTrends 클라이언트 초기화
        pytrends = get_pytrends_client()
        
        # 페이로드 설정
        pytrends.build_payload(
            request.keywords,
            cat=request.category,
            timeframe=request.timeframe,
            geo=request.geo,
            gprop=property_type
        )
        
        # 시간별 관심도 데이터 조회
        interest_over_time = pytrends.interest_over_time()
        
        # 데이터가 없는 경우
        if interest_over_time.empty:
            property_name = property_type if property_type else "웹 검색"
            return {
                "status": "success",
                "data": {},
                "message": f"{property_name} 속성에 대한 데이터가 없습니다."
            }
        
        # 응답 데이터 구성
        formatted_data = format_trend_data(interest_over_time)
        
        property_name = property_type if property_type else "웹 검색"
        return {
            "status": "success",
            "data": formatted_data,
            "message": f"{property_name} 속성의 트렌드 데이터를 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"검색 속성별 트렌드 조회 중 오류 발생: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"검색 속성별 트렌드 분석 중 오류가 발생했습니다: {str(e)}"
        ) 