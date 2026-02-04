from fastapi import APIRouter, HTTPException
from database.mongodb_connection import mongo_db # 이전에 만든 연결 파일
from review_analysis.preprocessing.imdb_processor import ImdbDataProcessor
from review_analysis.preprocessing.letterboxd_processor import LetterboxdProcessor
from review_analysis.preprocessing.rotten_processor import RottenProcessor

import pandas as pd

router = APIRouter()

PROCESSORS = {
    "imdb": ImdbDataProcessor,
    "letterboxd": LetterboxdProcessor,
    "rotten": RottenProcessor
}

# 명세서 요구사항: POST /review/preprocess/{site_name}
@router.post("/review/preprocess/{site_name}")
async def preprocess_reviews(site_name: str):
    # processor 선택
    processor_class = PROCESSORS.get(site_name.lower())
    if not processor_class:
        raise HTTPException(status_code=400, detail="Invalid site name")

    # 1. 몽고DB에서 원본 데이터 컬렉션 선택
    raw_data = list(mongo_db[site_name].find())
    df_from_mongo = pd.DataFrame(raw_data)
    processor = processor_class.__new__(processor_class)
    
    processor.input_path = f"database/reviews_{site_name}.csv"
    processor.output_dir = "data/processed"
    
    # 2.'데이터프레임'으로 변환
    processor.df = df_from_mongo
    if site_name.lower() == "letterboxd":
        processor.stopwords = []

    # 3. 기존의 preprocess 함수 실행
    if site_name.lower() == "letterboxd":
        processor.df_processed = processor.df 
        processor.stopwords = [] # stopwords 에러 방지

    processor.preprocess() 
    # 4. FE 실행
    try:
        processor.feature_engineering()
        print(f"--- {site_name} Feature Engineering 완료 ---")
    except Exception as e:
        # 만약 FE 함수가 없는 프로세서가 있다면 무시하고 넘어갑니다.
        print(f"--- {site_name} FE 건너뜀 또는 에러: {e} ---")
    
    # 5. 로컬 저장
    try:
        processor.save_to_database()
        print(f"--- {site_name} 로컬 파일 저장 성공 ---")
    except Exception as e:
        print(f"--- {site_name} 로컬 저장 실패: {e} ---")
    
    # 6. 전처리가 완료된 데이터를 딕셔너리 형태로 변환
    if site_name.lower() == "letterboxd":
        # Letterboxd는 FE 결과가 담긴 df_processed를 사용
        final_df = processor.df_processed
    elif site_name.lower() == "imdb":
        # IMDb는 sentence_count를 self.df에 직접 추가
        final_df = processor.df
    else:
        # Rotten은 self.df를 갱신
        final_df = processor.df

    # 몽고DB 저장 시 _id 충돌 방지를 위해 변환
    processed_docs = final_df.to_dict("records")
    for doc in processed_docs:
        if '_id' in doc:
            doc['original_id'] = str(doc.pop('_id'))
    
    # [확인용]
    print(f"--- {site_name} 최종 저장 컬럼: {final_df.columns.tolist()} ---")

    return {"status": "success", "message": "기존 로직으로 자동 전처리 완료", "count": len(processed_docs)}