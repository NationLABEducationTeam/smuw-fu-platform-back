from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
from couchbase.cluster import Cluster
from couchbase.options import ClusterOptions
from couchbase.auth import PasswordAuthenticator

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
    now = datetime.now()
    year = now.year
    quarter = (now.month - 1) // 3 + 1
    return f"{year}{quarter}"

def find_max_value_key(data: Dict[str, int]) -> str:
    return max(data.items(), key=lambda x: x[1])[0]

@router.get("/district/{district_code}")
async def get_district_sales(district_code: str):
    try:
        # Couchbase 연결
        auth = PasswordAuthenticator("smwu-admin", "631218")
        cluster = Cluster('couchbase://localhost/smwu-hang-sales', ClusterOptions(auth))
        collection = cluster.bucket('smwu-sales-data').default_collection()
        
        quarter = "20242"  # 직접 지정
        print(f"Searching for district: {district_code}, quarter: {quarter}")
        
        # 각 업종별로 데이터 조회
        results = []
        for industry_code in FOOD_INDUSTRY_CODES.keys():
            doc_id = f"sales::{district_code}::{quarter}::{industry_code}"
            try:
                result = collection.get(doc_id)
                results.append(result.value)
            except Exception as e:
                print(f"Not found: {doc_id} - {str(e)}")  # 디버그용
                continue

        if not results:
            raise HTTPException(status_code=404, detail="Data not found")

        # 업종별 데이터 분류
        industry_data = {}
        for r in results:
            industry_code = r.get('svc_induty_cd')
            if industry_code in FOOD_INDUSTRY_CODES:
                industry_data[industry_code] = {
                    "industry_name": FOOD_INDUSTRY_CODES[industry_code],
                    "sales_analysis": {
                        "daily_sales": {
                            "data": {
                                "월요일": r.get('mon_selng_amt', 0),
                                "화요일": r.get('tues_selng_amt', 0),
                                "수요일": r.get('wed_selng_amt', 0),
                                "목요일": r.get('thur_selng_amt', 0),
                                "금요일": r.get('fri_selng_amt', 0),
                                "토요일": r.get('sat_selng_amt', 0),
                                "일요일": r.get('sun_selng_amt', 0)
                            }
                        },
                        "time_based_sales": {
                            "data": {
                                "심야 (00-06)": r.get('tmzon_00_06_selng_amt', 0),
                                "아침 (06-11)": r.get('tmzon_06_11_selng_amt', 0),
                                "점심 (11-14)": r.get('tmzon_11_14_selng_amt', 0),
                                "오후 (14-17)": r.get('tmzon_14_17_selng_amt', 0),
                                "저녁 (17-21)": r.get('tmzon_17_21_selng_amt', 0),
                                "야간 (21-24)": r.get('tmzon_21_24_selng_amt', 0)
                            }
                        },
                        "demographics": {
                            "gender": {
                                "male": r.get('ml_selng_amt', 0),
                                "female": r.get('fml_selng_amt', 0)
                            },
                            "age": {
                                "10대": r.get('agrde_10_selng_amt', 0),
                                "20대": r.get('agrde_20_selng_amt', 0),
                                "30대": r.get('agrde_30_selng_amt', 0),
                                "40대": r.get('agrde_40_selng_amt', 0),
                                "50대": r.get('agrde_50_selng_amt', 0),
                                "60대 이상": r.get('agrde_60_above_selng_amt', 0)
                            }
                        },
                        "weekday_weekend": {
                            "weekday": r.get('mdwk_selng_co', 0),
                            "weekend": r.get('wkend_selng_co', 0)
                        }
                    }
                }

        return {
            "district_name": results[0].get('adstrd_cd_nm') if results else None,
            "quarter": quarter,
            "industries": industry_data
        }

    except Exception as e:
        print(f"Error in API: {str(e)}")  # 디버그용
        raise HTTPException(status_code=500, detail=str(e))