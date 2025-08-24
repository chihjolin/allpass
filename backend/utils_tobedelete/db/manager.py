from utils.db.postgres import PostgresDB

class DatabaseManager:
    def __init__(self):
        self.pg_main = PostgresDB(env_prefix="DB")
        #self.pg_analytics = PostgresDB(env_prefix="DB_ANALYTICS")
        #self.redis = RedisClient()
        #self.milvus = MilvusClient()

    def init_all(self):
        self.pg_main.connect()
        #self.pg_analytics.connect()
        #self.redis.connect()
        #self.milvus.connect()