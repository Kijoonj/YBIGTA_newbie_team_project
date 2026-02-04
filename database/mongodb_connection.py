from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

# .env 파일에 작성한 주소
mongo_url = os.getenv("MONGO_URL")

# MongoDB에 연결
mongo_client = MongoClient(mongo_url)

# 사용할 데이터베이스 이름
mongo_db = mongo_client.get_database("movie_project")
