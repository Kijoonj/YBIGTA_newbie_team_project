from fastapi import Depends
from sqlalchemy.orm import Session
from database.mysql_connection import SessionLocal
from app.user.user_repository import UserRepository
from app.user.user_service import UserService

# 1. DB 세션을 생성하고 안전하게 닫아주는 함수를 정의합니다. 
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() # 작업이 끝나면 DB 연결을 자동으로 닫습니다.

# 2. UserRepository를 생성할 때 DB 세션을 주입하도록 수정합니다.
def get_user_repository(db: Session = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


# 3. UserService는 그대로 Repository를 주입받아 사용합니다.
def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)
