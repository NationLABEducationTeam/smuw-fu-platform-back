"""
API 응답 모델 정의 모듈

API 요청 및 응답을 위한 Pydantic 모델 정의
"""
from typing import Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field


class DataType(str, Enum):
    """데이터 유형 열거형"""
    TOTAL = "total"
    DAILY = "daily"
    TIME = "time"
    GENDER = "gender"
    AGE = "age"


class BaseResponse(BaseModel):
    """기본 API 응답 모델"""
    status: str = Field(..., description="처리 상태 (success/error)")
    message: str = Field(..., description="상태 메시지")


class SalesData(BaseModel):
    """매출 데이터 모델"""
    district_name: Optional[str] = Field(None, description="행정동 이름")
    quarter: str = Field(..., description="분기 (YYYYQ 형식)")
    industries: Dict[str, Dict[str, Any]] = Field(
        ..., description="업종별 매출 데이터"
    )


class SalesResponse(BaseResponse):
    """매출 데이터 응답 모델"""
    data: SalesData = Field(..., description="매출 데이터")


class DailySales(BaseModel):
    """요일별 매출 데이터"""
    data: Dict[str, int] = Field(..., description="요일별 매출 금액")


class TimeSales(BaseModel):
    """시간대별 매출 데이터"""
    data: Dict[str, int] = Field(..., description="시간대별 매출 금액")


class GenderSales(BaseModel):
    """성별 매출 데이터"""
    male: int = Field(..., description="남성 매출 금액")
    female: int = Field(..., description="여성 매출 금액")


class AgeSales(BaseModel):
    """연령대별 매출 데이터"""
    age_10: int = Field(..., alias="10대", description="10대 매출 금액")
    age_20: int = Field(..., alias="20대", description="20대 매출 금액")
    age_30: int = Field(..., alias="30대", description="30대 매출 금액")
    age_40: int = Field(..., alias="40대", description="40대 매출 금액")
    age_50: int = Field(..., alias="50대", description="50대 매출 금액")
    age_60_plus: int = Field(..., alias="60대 이상", description="60대 이상 매출 금액")


class KeywordSearchRequest(BaseModel):
    """키워드 검색 요청 모델"""
    keyword: str = Field(..., description="검색 키워드")
    location: Optional[str] = Field(None, description="지역 코드")


class KeywordSearchResponse(BaseResponse):
    """키워드 검색 응답 모델"""
    data: Dict[str, Any] = Field(..., description="검색 결과 데이터")


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    status: str = Field("error", description="에러 상태")
    detail: str = Field(..., description="상세 에러 메시지")
    code: Optional[int] = Field(None, description="에러 코드")