import os
import re
import pandas as pd  # type: ignore
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns  # type: ignore
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
from review_analysis.preprocessing.base_processor import BaseDataProcessor

# 한글 폰트 설정 (Mac)
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


class LetterboxdProcessor(BaseDataProcessor):
    """
    Letterboxd 리뷰 데이터 전처리 프로세서
    
    기능:
    - 결측치 처리 (null값 제거/대체)
    - 이상치 처리 (별점 범위, 텍스트 길이)
    - 텍스트 전처리 (특수문자, 불용어 제거)
    - 파생변수 생성 (문장 수)
    - TF-IDF 벡터화 (max_features=2000)
    """
    
    def __init__(self, input_path: str, output_dir: str):
        super().__init__(input_path, output_dir)
        self.df = None
        self.df_processed = None
        self.tfidf_matrix = None
        self.tfidf_vectorizer = None
        
        # 영어 불용어 (Letterboxd는 영어 리뷰)
        self.stopwords = {
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 
            'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself',
            'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them',
            'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this',
            'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
            'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
            'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to',
            'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
            'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can',
            'will', 'just', 'don', 'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y'
        }
    
    def preprocess(self):
        """
        데이터 전처리 수행
        - 데이터 로드
        - 결측치 처리
        - 이상치 처리
        - 텍스트 정제
        """
        print("=" * 50)
        print("1. 데이터 전처리 시작")
        print("=" * 50)
        
        # 데이터 로드
        self.df = pd.read_csv(self.input_path)
        print(f"원본 데이터: {len(self.df)}개 리뷰")
        print(f"컬럼: {list(self.df.columns)}")
        
        self.df_processed = self.df.copy()
        
        # 1. 결측치 처리
        self._handle_missing_values()
        
        # 2. 이상치 처리
        self._handle_outliers()
        
        # 3. 텍스트 전처리
        self._preprocess_text()
        
        print(f"\n전처리 후 데이터: {len(self.df_processed)}개 리뷰")
    
    def _handle_missing_values(self):
        """결측치 처리"""
        print("\n[결측치 처리]")
        
        # 결측치 현황
        print(f"결측치 현황:\n{self.df_processed.isnull().sum()}")
        
        # content가 없는 행 제거
        before = len(self.df_processed)
        self.df_processed = self.df_processed.dropna(subset=['content'])
        self.df_processed = self.df_processed[self.df_processed['content'].str.strip() != '']
        print(f"- content 결측치 제거: {before - len(self.df_processed)}개")
        
        # rating 결측치: '평점 없음' 또는 NaN → 제거
        before = len(self.df_processed)
        self.df_processed = self.df_processed[self.df_processed['rating'] != '평점 없음']
        self.df_processed = self.df_processed.dropna(subset=['rating'])
        print(f"- rating 결측치 제거: {before - len(self.df_processed)}개")
        
        # date 결측치: '날짜 정보 없음' 유지
        self.df_processed['date'] = self.df_processed['date'].fillna('날짜 정보 없음')
    
    def _handle_outliers(self):
        """이상치 처리"""
        print("\n[이상치 처리]")
        
        # 1. 별점 범위 체크 (Letterboxd: 1-10, 0.5점 단위)
        # rating을 숫자로 변환
        self.df_processed['rating_numeric'] = pd.to_numeric(
            self.df_processed['rating'], errors='coerce'
        )
        
        # 유효 별점 범위: 1-10
        before = len(self.df_processed)
        self.df_processed = self.df_processed[
            (self.df_processed['rating_numeric'] >= 1) & 
            (self.df_processed['rating_numeric'] <= 10)
        ]
        print(f"- 유효하지 않은 별점 제거: {before - len(self.df_processed)}개")
        
        # 2. 텍스트 길이 이상치 처리
        self.df_processed['content_length'] = self.df_processed['content'].str.len()
        
        # 너무 짧은 리뷰 (10자 미만) 제거
        before = len(self.df_processed)
        self.df_processed = self.df_processed[self.df_processed['content_length'] >= 10]
        print(f"- 너무 짧은 리뷰(10자 미만) 제거: {before - len(self.df_processed)}개")
        
        # 너무 긴 리뷰 (10000자 초과) 잘라내기
        long_reviews = len(self.df_processed[self.df_processed['content_length'] > 10000])
        self.df_processed['content'] = self.df_processed['content'].str[:10000]
        print(f"- 너무 긴 리뷰(10000자 초과) 잘라냄: {long_reviews}개")
        
        # 3. 날짜 이상치 처리
        def validate_date(date_str):
            if date_str == '날짜 정보 없음':
                return date_str
            try:
                # YYYY.MM.DD 형식
                parsed = datetime.strptime(date_str, '%Y.%m.%d')
                # 너무 오래된(2010년 이전) 또는 미래 날짜 체크
                if parsed.year < 2010 or parsed > datetime.now():
                    return '날짜 정보 없음'
                return date_str
            except:
                return '날짜 정보 없음'
        
        self.df_processed['date'] = self.df_processed['date'].apply(validate_date)
    
    def _preprocess_text(self):
        """텍스트 전처리"""
        print("\n[텍스트 전처리]")
        
        def clean_text(text):
            if not isinstance(text, str):
                return ""
            
            # 소문자 변환
            text = text.lower()
            
            # URL 제거
            text = re.sub(r'http\S+|www\.\S+', '', text)
            
            # 이메일 제거
            text = re.sub(r'\S+@\S+', '', text)
            
            # 특수문자 제거 (알파벳, 숫자, 공백만 유지)
            text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
            
            # 연속 공백 제거
            text = re.sub(r'\s+', ' ', text)
            
            # 불용어 제거
            words = text.split()
            words = [w for w in words if w not in self.stopwords and len(w) > 1]
            
            return ' '.join(words).strip()
        
        self.df_processed['content_cleaned'] = self.df_processed['content'].apply(clean_text)
        
        # 정제 후 빈 텍스트 제거
        before = len(self.df_processed)
        self.df_processed = self.df_processed[self.df_processed['content_cleaned'].str.len() > 0]
        print(f"- 정제 후 빈 텍스트 제거: {before - len(self.df_processed)}개")
        
        print(f"- 텍스트 정제 완료")
    
    def feature_engineering(self):
        """
        피처 엔지니어링
        - 파생변수 생성 (문장 수)
        - TF-IDF 벡터화
        """
        print("\n" + "=" * 50)
        print("2. 피처 엔지니어링 시작")
        print("=" * 50)
        
        # 1. 파생변수: 문장 수
        self._create_sentence_count()
        
        # 2. TF-IDF 벡터화
        self._tfidf_vectorize()
    
    def _create_sentence_count(self):
        """파생변수: 문장 수 생성"""
        print("\n[파생변수 생성: 문장 수]")
        
        def count_sentences(text):
            if not isinstance(text, str):
                return 0
            # 문장 종결 부호로 분리 (., !, ?)
            sentences = re.split(r'[.!?]+', text)
            # 빈 문장 제외
            sentences = [s.strip() for s in sentences if s.strip()]
            return len(sentences)
        
        self.df_processed['sentence_count'] = self.df_processed['content'].apply(count_sentences)
        
        print(f"- 문장 수 통계:")
        print(f"  평균: {self.df_processed['sentence_count'].mean():.2f}")
        print(f"  최소: {self.df_processed['sentence_count'].min()}")
        print(f"  최대: {self.df_processed['sentence_count'].max()}")
    
    def _tfidf_vectorize(self):
        """TF-IDF 벡터화 (max_features=2000)"""
        print("\n[TF-IDF 벡터화]")
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=2000,
            min_df=2,           # 최소 2개 문서에 등장
            max_df=0.95,        # 95% 이상 문서에 등장하면 제외
            ngram_range=(1, 2)  # unigram + bigram
        )
        
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(
            self.df_processed['content_cleaned']
        )
        
        print(f"- TF-IDF 매트릭스 shape: {self.tfidf_matrix.shape}")
        print(f"- 피처 수: {len(self.tfidf_vectorizer.get_feature_names_out())}")
        
        # 상위 20개 피처 출력
        feature_names = self.tfidf_vectorizer.get_feature_names_out()
        tfidf_sum = np.array(self.tfidf_matrix.sum(axis=0)).flatten()
        top_indices = tfidf_sum.argsort()[-20:][::-1]
        
        print(f"- 상위 20개 피처:")
        for idx in top_indices:
            print(f"  {feature_names[idx]}: {tfidf_sum[idx]:.4f}")
    
    def save_to_database(self):
        """전처리 결과 저장"""
        print("\n" + "=" * 50)
        print("3. 결과 저장")
        print("=" * 50)
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 1. 전처리된 데이터 저장
        output_columns = ['rating', 'rating_numeric', 'date', 'content', 
                         'content_cleaned', 'content_length', 'sentence_count']
        
        output_path = os.path.join(self.output_dir, "preprocessed_reviews_letterboxd.csv")
        self.df_processed[output_columns].to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"- 전처리 데이터 저장: {output_path}")
        
        # 2. TF-IDF 매트릭스 저장 (sparse matrix → DataFrame)
        tfidf_df = pd.DataFrame(
            self.tfidf_matrix.toarray(),
            columns=self.tfidf_vectorizer.get_feature_names_out()
        )
        tfidf_path = os.path.join(self.output_dir, "tfidf_reviews_letterboxd.csv")
        tfidf_df.to_csv(tfidf_path, index=False, encoding='utf-8-sig')
        print(f"- TF-IDF 매트릭스 저장: {tfidf_path}")
        
        # 3. 통계 요약 저장
        stats = {
            '총 리뷰 수': len(self.df_processed),
            '평균 별점': self.df_processed['rating_numeric'].mean(),
            '평균 리뷰 길이': self.df_processed['content_length'].mean(),
            '평균 문장 수': self.df_processed['sentence_count'].mean(),
            'TF-IDF 피처 수': self.tfidf_matrix.shape[1]
        }
        
        stats_df = pd.DataFrame([stats])
        stats_path = os.path.join(self.output_dir, "stats_reviews_letterboxd.csv")
        stats_df.to_csv(stats_path, index=False, encoding='utf-8-sig')
        print(f"- 통계 요약 저장: {stats_path}")
        
        # 4. EDA 시각화
        self._visualize_eda()
        
        print("\n" + "=" * 50)
        print("전처리 완료!")
        print("=" * 50)
    
    def _visualize_eda(self):
        """EDA 시각화 - 개별 파일로 저장 (영어)"""
        print("\n[EDA 시각화]")
        
        # 저장 폴더
        plots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plots")
        os.makedirs(plots_dir, exist_ok=True)
        
        # 1. 별점 분포 (Histogram)
        plt.figure(figsize=(10, 6))
        plt.hist(self.df_processed['rating_numeric'], bins=10, range=(1, 11), edgecolor='black', color='#3498db', alpha=0.7)
        plt.xlabel('Rating')
        plt.ylabel('Number of Reviews')
        plt.title('Rating Distribution (Histogram)')
        plt.xticks(range(1, 11))
        mean_rating = self.df_processed['rating_numeric'].mean()
        plt.axvline(mean_rating, color='red', linestyle='--', label=f'Mean: {mean_rating:.1f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "rating_histogram.png"), dpi=150)
        plt.close()
        print("- rating_histogram.png 저장")
        
        # 2. 리뷰 길이 분포 (Boxplot)
        plt.figure(figsize=(10, 6))
        sns.boxplot(x=self.df_processed['content_length'], color='#2ecc71')
        plt.xlabel('Review Length (characters)')
        plt.title('Review Length Distribution (Boxplot)')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "length_boxplot.png"), dpi=150)
        plt.close()
        print("- length_boxplot.png 저장")
        
        # 3. 별점 분포 (Pie Chart)
        plt.figure(figsize=(8, 8))
        high = len(self.df_processed[self.df_processed['rating_numeric'] >= 8])
        mid = len(self.df_processed[(self.df_processed['rating_numeric'] >= 5) & (self.df_processed['rating_numeric'] < 8)])
        low = len(self.df_processed[self.df_processed['rating_numeric'] < 5])
        rating_counts = [high, mid, low]
        labels = ['High (8-10)', 'Medium (5-7)', 'Low (1-4)']
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        plt.pie(rating_counts, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Rating Distribution (Pie Chart)')
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "rating_piechart.png"), dpi=150)
        plt.close()
        print("- rating_piechart.png 저장")
        
        # 4. 문장 수 분포 (Histogram)
        plt.figure(figsize=(10, 6))
        plt.hist(self.df_processed['sentence_count'], bins=20, edgecolor='black', color='#9b59b6', alpha=0.7)
        plt.xlabel('Sentence Count')
        plt.ylabel('Number of Reviews')
        plt.title('Sentence Count Distribution (Histogram)')
        mean_sentences = self.df_processed['sentence_count'].mean()
        plt.axvline(mean_sentences, color='red', linestyle='--', label=f'Mean: {mean_sentences:.1f}')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "sentence_histogram.png"), dpi=150)
        plt.close()
        print("- sentence_histogram.png 저장")
        
        print(f"\n총 4개 그래프 저장 완료: {plots_dir}")
        
        # 5. 시계열 그래프 (날짜별 리뷰 수)
        plt.figure(figsize=(12, 6))
        date_counts = self.df_processed[self.df_processed['date'] != '날짜 정보 없음']['date'].value_counts().sort_index()
        plt.plot(range(len(date_counts)), date_counts.values, marker='o', color='#3498db', linewidth=2, markersize=4)
        plt.xlabel('Date')
        plt.ylabel('Number of Reviews')
        plt.title('Reviews Over Time (Time Series)')
        
        if len(date_counts) > 10:
            step = len(date_counts) // 10
            plt.xticks(range(0, len(date_counts), step), [date_counts.index[i] for i in range(0, len(date_counts), step)], rotation=45)
        else:
            plt.xticks(range(len(date_counts)), date_counts.index, rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "reviews_timeseries.png"), dpi=150)
        plt.close()
        print("- reviews_timeseries.png 저장")
        
        # 6. 날짜별 평균 별점 (시계열)
        plt.figure(figsize=(12, 6))
        valid_dates = self.df_processed[self.df_processed['date'] != '날짜 정보 없음']
        date_rating = valid_dates.groupby('date')['rating_numeric'].mean().sort_index()
        plt.plot(range(len(date_rating)), date_rating.values, marker='s', color='#e74c3c', linewidth=2, markersize=4)
        plt.xlabel('Date')
        plt.ylabel('Average Rating')
        plt.title('Average Rating Over Time (Time Series)')
        plt.ylim(0, 10)
        
        if len(date_rating) > 10:
            step = len(date_rating) // 10
            plt.xticks(range(0, len(date_rating), step), [date_rating.index[i] for i in range(0, len(date_rating), step)], rotation=45)
        else:
            plt.xticks(range(len(date_rating)), date_rating.index, rotation=45)
        
        plt.tight_layout()
        plt.savefig(os.path.join(plots_dir, "rating_timeseries.png"), dpi=150)
        plt.close()
        print("- rating_timeseries.png 저장")
        
        print(f"\n총 6개 그래프 저장 완료: {plots_dir}")