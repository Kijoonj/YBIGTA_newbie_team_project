from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn
import os

from app.review.review_router import router as review_router  # MongoDB 기반 전처리 로직
from app.user.user_router import user  # MySQL 기반 유저 CRUD 로직
from app.config import PORT

app = FastAPI()
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.include_router(review_router)  # 전처리 자동화 API
app.include_router(user)  # 유저 관리 API

if __name__=="__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)
