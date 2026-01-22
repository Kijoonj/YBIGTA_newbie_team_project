import pandas as pd
import os
import re
from datetime import datetime, timedelta
from review_analysis.preprocessing.base_processor import BaseDataProcessor


class RottenProcessor(BaseDataProcessor):
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        self.df = None
        
    def preprocess(self):
        """데이터 전처리 수행"""
        # CSV 파일 읽기
        self.df = pd.read_csv(self.input_path)
        
       
        
        # 1. 결측치 처리
        self._handle_missing_values()
        
        # 2. 날짜 형식 통일 및 이상치 처리
        self._process_dates()
        
        # 3. 이상치 처리
        self._handle_outliers()
        
        # 4. 텍스트 데이터 전처리
        self._preprocess_text()
        
        
        
    def _handle_missing_values(self):
        """결측치 처리"""
        
        initial_len = len(self.df)
        self.df = self.df.dropna(subset=['date', 'rating', 'content'])
        removed = initial_len - len(self.df)
    
    
    def _process_dates(self):
        """날짜 형식 통일 및 정보 부족한 날짜 제거"""
        def convert_date(date_str):
            """다양한 날짜 형식을 yyyy.mm.dd로 통일"""
            if pd.isna(date_str):
                return None
            
            date_str = str(date_str).strip()
            
            reference_date = datetime(2025, 1, 21)
            
            if date_str.endswith('h'):
                return None
            
            if date_str.endswith('d'):
                try:
                    days = int(date_str[:-1])
                    target_date = reference_date - timedelta(days=days)
                    return target_date.strftime('%Y.%m.%d')
                except:
                    return None
            
            
            try:
                parsed_date = datetime.strptime(date_str, '%b %d')
               
                target_date = parsed_date.replace(year=2025)
                
                if target_date > reference_date:
                    target_date = parsed_date.replace(year=2024)
                return target_date.strftime('%Y.%m.%d')
            except:
                pass
            
            
            try:
                if '-' in date_str:
                    target_date = datetime.strptime(date_str, '%Y-%m-%d')
                elif '.' in date_str:
                    target_date = datetime.strptime(date_str, '%Y.%m.%d')
                else:
                    return None
                return target_date.strftime('%Y.%m.%d')
            except:
                return None
        
        
        self.df['date'] = self.df['date'].apply(convert_date)
        
        
        initial_len = len(self.df)
        self.df = self.df.dropna(subset=['date'])
        removed = initial_len - len(self.df)
        
    
    def _handle_outliers(self):
        """이상치 처리"""
        initial_len = len(self.df)
        
        
        self.df = self.df[(self.df['rating'] >= 0.0) & (self.df['rating'] <= 10.0)]
        
        # 비정상적으로 짧은 리뷰 제거 (5자 미만)
        self.df = self.df[self.df['content'].str.len() >= 5]
        
        # 비정상적으로 긴 리뷰 제거 (10000자 초과)
        self.df = self.df[self.df['content'].str.len() <= 10000]
        
        removed = initial_len - len(self.df)
        
    
    def _preprocess_text(self):
        """텍스트 데이터 전처리"""
        # 양쪽 공백 제거
        self.df['content'] = self.df['content'].str.strip()
        
        # 연속된 공백을 하나로 통일
        self.df['content'] = self.df['content'].apply(lambda x: re.sub(r'\s+', ' ', x))
    
    def feature_engineering(self):
        """파생 변수 생성 및 텍스트 벡터화"""
        # 1. 리뷰 문장 수 계산 (파생 변수)
        self.df['sentence_count'] = self.df['content'].apply(self._count_sentences)
        
        
        # 2. TF-IDF 벡터화
        self._vectorize_text()
    
    def _vectorize_text(self):
        """TF-IDF를 이용한 텍스트 벡터화"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        
        
        
        # TF-IDF 벡터라이저 생성 (feature 개수: 2000)
        tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            ngram_range=(1, 2),  # unigram과 bigram 사용
            min_df=2,  # 최소 2개 문서에서 등장해야 함
            max_df=0.8  # 전체 문서의 80% 이상에서 등장하는 단어 제외
        )
        
        # TF-IDF 변환
        tfidf_matrix = tfidf_vectorizer.fit_transform(self.df['content'])
        
        # TF-IDF 결과를 데이터프레임으로 변환
        tfidf_df = pd.DataFrame(
            tfidf_matrix.toarray(),
            columns=[f'tfidf_{i}' for i in range(tfidf_matrix.shape[1])]
        )
        
        # 원본 데이터프레임과 결합
        self.df = pd.concat([self.df.reset_index(drop=True), tfidf_df], axis=1)
        
    
    def _count_sentences(self, text):
        """문장 수를 세는 함수"""
        # 문장 종결 부호로 분리 (., !, ?)
        sentences = re.split(r'[.!?]+', text)
        # 빈 문자열 제거 후 개수 반환
        sentences = [s.strip() for s in sentences if s.strip()]
        return len(sentences)
    
    def save_to_database(self):
        """전처리된 데이터를 database 폴더에 저장"""
        # 출력 파일명 생성
        output_filename = "preprocessed_reviews_rotten.csv"
        output_path = os.path.join(self.output_dir, output_filename)
        
        # 기존 파일이 있다면 삭제 시도
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
            
                raise
        
        # CSV로 저장
        self.df.to_csv(output_path, index=False, encoding='utf-8-sig')