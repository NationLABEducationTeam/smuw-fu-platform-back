"""
매출 데이터 라우터 모듈

행정동별, 업종별 매출 데이터 조회 API
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Path, Query
from datetime import datetime
from dotenv import load_dotenv

from app.database import CouchbaseClient
from app.models import SalesResponse

load_dotenv()


router = APIRouter(prefix="/api/sales", tags=["sales"])


# 음식 관련 업종 코드 리스트
FOOD_INDUSTRY_CODES = {
    "CS100001": "한식음식점",
    "CS100002": "중식음식점",
    "CS100003": "일식음식점",
    "CS100004": "양식음식점",
    "CS100005": "제과점",
    "CS100006": "패스트푸드점",
    "CS100007": "치킨전문점",
    "CS100008": "분식전문점",
    "CS100009": "호프-간이주점",
    "CS100010": "커피-음료",
    "CS200001": "편의점",
}


def get_current_quarter() -> str:
    """
    현재 날짜 기준 분기 정보 반환 (YYYYQ 형식)
    
    Returns:
        str: 현재 연도와 분기 (예: 20231 = 2023년 1분기)
    """
    now = datetime.now()
    year = now.year
    quarter = (now.month - 1) // 3 + 1
    return f"{year}{quarter}"


def find_max_value_key(data: Dict[str, int]) -> str:
    """
    딕셔너리에서 최대값을 가진 키 반환
    
    Args:
        data: 키-값 쌍으로 이루어진 딕셔너리
        
    Returns:
        str: 최대값을 가진 키
    """
    return max(data.items(), key=lambda x: x[1])[0]


def format_industry_data(raw_data: dict, industry_code: str) -> dict:
    """
    업종별 원시 데이터를 클라이언트 응답 형식으로 변환
    
    Args:
        raw_data: 원시 매출 데이터
        industry_code: 업종 코드
        
    Returns:
        dict: 형식화된 업종 데이터
    """
    return {
        "industry_name": FOOD_INDUSTRY_CODES[industry_code],
        "sales_analysis": {
            "daily_sales": {
                "data": {
                    "월요일": raw_data.get('mon_selng_amt', 0),
                    "화요일": raw_data.get('tues_selng_amt', 0),
                    "수요일": raw_data.get('wed_selng_amt', 0),
                    "목요일": raw_data.get('thur_selng_amt', 0),
                    "금요일": raw_data.get('fri_selng_amt', 0),
                    "토요일": raw_data.get('sat_selng_amt', 0),
                    "일요일": raw_data.get('sun_selng_amt', 0)
                }
            },
            "time_based_sales": {
                "data": {
                    "심야": raw_data.get('tmzon_00_06_selng_amt', 0),
                    "아침": raw_data.get('tmzon_06_11_selng_amt', 0),
                    "점심": raw_data.get('tmzon_11_14_selng_amt', 0),
                    "오후": raw_data.get('tmzon_14_17_selng_amt', 0),
                    "저녁": raw_data.get('tmzon_17_21_selng_amt', 0),
                    "야간": raw_data.get('tmzon_21_24_selng_amt', 0)
                }
            },
            "demographics": {
                "gender": {
                    "male": raw_data.get('ml_selng_amt', 0),
                    "female": raw_data.get('fml_selng_amt', 0)
                },
                "age": {
                    "10대": raw_data.get('agrde_10_selng_amt', 0),
                    "20대": raw_data.get('agrde_20_selng_amt', 0),
                    "30대": raw_data.get('agrde_30_selng_amt', 0),
                    "40대": raw_data.get('agrde_40_selng_amt', 0),
                    "50대": raw_data.get('agrde_50_selng_amt', 0),
                    "60대 이상": raw_data.get('agrde_60_above_selng_amt', 0)
                }
            },
            "weekday_weekend": {
                "weekday": raw_data.get('mdwk_selng_co', 0),
                "weekend": raw_data.get('wkend_selng_co', 0)
            }
        }
    }


@router.get(
    "/district/{district_code}", 
    response_model=SalesResponse,
    summary="행정동별 매출 데이터 조회",
    description="행정동 코드를 기준으로 분기별 매출 데이터를 조회합니다."
)
async def get_district_sales(
    district_code: str = Path(..., description="행정동 코드"),
    quarter: Optional[str] = Query(
        None, 
        description="조회할 분기 (YYYYQ 형식, 미입력시 최근 분기)"
    )
):
    """
    행정동별 매출 데이터 조회 API
    """
    try:
        # 분기 정보 설정
        if not quarter:
            quarter = "20242"  # 직접 지정 또는 get_current_quarter() 사용
        
        print(f"Searching for district: {district_code}, quarter: {quarter}")
        
        # Couchbase 클라이언트 초기화
        db_client = CouchbaseClient()
        
        # 각 업종별로 데이터 조회
        results = []
        for industry_code in FOOD_INDUSTRY_CODES.keys():
            try:
                result = db_client.get_by_key(
                    district_code, quarter, industry_code
                )
                if result:
                    results.append(result)
            except Exception as e:
                print(
                    f"Not found: sales::{district_code}::{quarter}::"
                    f"{industry_code} - {str(e)}"
                )
                continue

        if not results:
            raise HTTPException(status_code=404, detail="Data not found")

        # 업종별 데이터 분류
        industry_data = {}
        for r in results:
            industry_code = r.get('svc_induty_cd')
            if industry_code in FOOD_INDUSTRY_CODES:
                industry_data[industry_code] = format_industry_data(
                    r, industry_code
                )

        return {
            "status": "success",
            "message": "데이터 조회 성공",
            "data": {
                "district_name": (
                    results[0].get('adstrd_cd_nm') if results else None
                ),
                "quarter": quarter,
                "industries": industry_data
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in API: {str(e)}")  # 디버그용
        raise HTTPException(
            status_code=500, 
            detail=f"서버 오류가 발생했습니다: {str(e)}"
        )