# app/database.py
from couchbase.cluster import Cluster, ClusterOptions
from couchbase.auth import PasswordAuthenticator

class CouchbaseClient:
    def __init__(self):
        auth = PasswordAuthenticator("smwu-admin", "631218")
        cluster = Cluster(
            'couchbase://localhost/smwu-hang-sales',
            ClusterOptions(auth)
        )
        self.collection = cluster.bucket('smwu-sales-data').default_collection()

    def get_by_key(self, district_code: str, quarter: str, industry_code: str):
        try:
            doc_id = f"sales::{district_code}::{quarter}::{industry_code}"
            result = self.collection.get(doc_id)
            return result.value
        except Exception as e:
            return None
        

    