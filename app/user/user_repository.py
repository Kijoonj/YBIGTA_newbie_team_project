from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text  # SQL 문장을 직접 쓰기 위한 도구
from app.user.user_schema import User as UserSchema

class UserRepository:
    # 1. 초기화 시 DB 세션을 외부에서 주입받음.
    def __init__(self, db:Session) -> None:
        self.db = db

    # 2. 이메일로 유저 찾기(SELECT * FROM users WHERE email = ...)
    def get_user_by_email(self, email: str) -> Optional[UserSchema]:
        # SQL 문으로 직접 물어보기
        query = text("SELECT email, password, username FROM users WHERE email = :email")
        result = self.db.execute(query, {"email": email}).fetchone()
        
        if result:
            # 결과가 있으면 스키마 형식에 맞춰 반환
            return UserSchema(
                email=result[0], 
                password=result[1], 
                username=result[2]
            )
        return None

    # 3. 유저 저장하기(INSERT / UPDATE)
    def save_user(self, user: UserSchema) -> UserSchema:
        # 1. 먼저 이 유저가 이미 DB에 있는지 확인
        existing_user = self.get_user_by_email(user.email)

        if existing_user:
            # 2. 이미 있다면 정보 수정(UPDATE).
            query = text("""
                UPDATE users 
                SET password = :password, username = :username 
                WHERE email = :email
            """)
        else:
            # 3. 없다면 새로 저장(INSERT).
            query = text("""
                INSERT INTO users (email, password, username) 
                VALUES (:email, :password, :username)
            """)

        self.db.execute(query, {
            "email": user.email, 
            "password": user.password, 
            "username": user.username
        })
        self.db.commit() 
        return user
    

    # 4. 유저 삭제하기(DELETE)
    # 수정 후
    def delete_user(self, user: UserSchema) -> None:
        # 1. SQL 문으로 직접 삭제하기
        query = text("DELETE FROM users WHERE email = :email")
        
        # 2. 실행
        self.db.execute(query, {"email": user.email})
        
        # 3. 커밋 (중요: 커밋을 해야 실제 반영됩니다)
        self.db.commit()