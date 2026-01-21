import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
import re

from sklearn.feature_extraction.text import TfidfVectorizer
from review_analysis.preprocessing.base_processor import BaseDataProcessor

class ImdbDataProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_path: str):
        super().__init__(input_path, output_path)
        self.df = pd.read_csv(input_path)

    def preprocess(self):
        '''
        1. 결측치 처리 (별점, 리뷰, 날짜)
        2. 이상치 처리 (별점 범위 외 제거)
        3. 텍스트 전처리 (특수문자 제거)
        '''
        # 결측치 제거
        self.df = self.df.dropna(subset=['rating', 'content', 'date'])

        # 이상치 처리
        self.df = self.df[self.df['rating'] >= 1]  # 별점
        self.df = self.df[self.df['content'].str.len() >= 5]  # 텍스트 길이
        
        # 텍스트 전처리
        self.df['content'] = self.df['content'].str.lower().str.replace(r'[^a-z0-9\s.?!]', '', regex=True)        
        print("✅ Preprocessing & EDA Plots 완료")


    def feature_engineering(self):
        '''
        1. 파생 변수 생성 (문장 수)
        2. 텍스트 벡터화 (TF-IDF)
        '''

        # 1. 파생변수 생성: 문장 수 
        self.df['sentence_count'] = self.df['content'].apply(
            lambda x: len([s for s in re.split(r'[.!?]+', str(x)) if s.strip()]) if pd.notnull(x) else 0
        )
        
        # 2. 텍스트 벡터화: TF-IDF
        tfidf = TfidfVectorizer(max_features=2000, stop_words='english')
        tfidf_matrix = tfidf.fit_transform(self.df['content'])
        
        # 벡터화 결과 확인용 (선택 사항: 데이터프레임에 결합하거나 별도 저장)
        print(f"✅ FE 완료 (TF-IDF 특징 수: {len(tfidf.get_feature_names_out())})")        


    def save_to_database(self):
        '''최종 전처리 결과를 지정된 경로에 CSV로 저장'''
        save_path = os.path.join(self.output_dir, "preprocessed_reviews_imdb.csv")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"데이터 저장 완료: {save_path}")
