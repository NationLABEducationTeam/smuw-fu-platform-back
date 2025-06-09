# app/database.py
"""
Couchbase 데이터베이스 클라이언트 모듈

Couchbase 연결 및 데이터 액세스 기능 제공
"""
import os
from typing import Any, Dict, Optional
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig:
    """Couchbase 데이터베이스 설정"""
    USERNAME = os.getenv("COUCHBASE_USER", "smwu-admin")
    PASSWORD = os.getenv("COUCHBASE_PASSWORD", "631218")
    HOST = os.getenv("COUCHBASE_HOST", "localhost")
    BUCKET = os.getenv("COUCHBASE_BUCKET", "smwu-sales-data")
    CLUSTER_URI = f'couchbase://{HOST}/smwu-hang-sales'


class CouchbaseClient:
    """
    Couchbase 데이터베이스 클라이언트
    
    싱글톤 패턴을 적용하여 클라이언트 인스턴스를 재사용
    """
    _instance = None
    
    def __new__(cls):
        """싱글톤 인스턴스 생성"""
        if cls._instance is None:
            cls._instance = super(CouchbaseClient, cls).__new__(cls)
            cls._instance._initialize_connection()
        return cls._instance
    
    def _initialize_connection(self):
        """Couchbase 서버 연결 초기화"""
        try:
            auth = PasswordAuthenticator(
                DatabaseConfig.USERNAME, 
                DatabaseConfig.PASSWORD
            )
            cluster = Cluster(
                DatabaseConfig.CLUSTER_URI,
                ClusterOptions(auth)
            )
            self.collection = cluster.bucket(
                DatabaseConfig.BUCKET
            ).default_collection()
        except Exception as e:
            raise ConnectionError(
                f"Couchbase 연결 실패: {str(e)}"
            )
    
    def get_by_key(
        self, 
        district_code: str, 
        quarter: str, 
        industry_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        키를 사용하여 데이터 조회
        
        Args:
            district_code: 행정동 코드
            quarter: 분기 정보 (YYYYQ 형식)
            industry_code: 업종 코드
        
        Returns:
            Optional[Dict[str, Any]]: 조회된 문서 데이터 또는 None
        """
        try:
            doc_id = f"sales::{district_code}::{quarter}::{industry_code}"
            result = self.collection.get(doc_id)
            return result.value
        except Exception:
            return None

    def upsert_document(
        self, 
        key: str, 
        data: Dict[str, Any]
    ) -> bool:
        """
        문서 생성 또는 업데이트
        
        Args:
            key: 문서 식별 키
            data: 저장할 데이터 
            
        Returns:
            bool: 성공 여부
        """
        try:
            self.collection.upsert(key, data)
            return True
        except Exception:
            return False
    
    def query(self, statement: str, *args, **kwargs) -> list:
        """
        N1QL 쿼리 실행
        
        Args:
            statement: N1QL 쿼리 문자열
            *args, **kwargs: 쿼리 파라미터
            
        Returns:
            list: 쿼리 결과 목록
        """
        try:
            cluster = Cluster(
                DatabaseConfig.CLUSTER_URI,
                ClusterOptions(PasswordAuthenticator(
                    DatabaseConfig.USERNAME, 
                    DatabaseConfig.PASSWORD
                ))
            )
            result = cluster.query(statement, *args, **kwargs)
            return [row for row in result]
        except Exception as e:
            print(f"쿼리 실행 오류: {str(e)}")
            return []

    