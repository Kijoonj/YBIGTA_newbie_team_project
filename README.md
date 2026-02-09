</br>

# [9회차] RAG AGENT
- stramlit cloud 주소: https://ybigtanewbieteamproject-gru6cyngzutmghveufdka5.streamlit.app/

  
- 작동 화면


![ragDemo](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/rag%20agent%20demo.png?raw=true)

- Pipeline


![pipeline](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/pipline.drawio.png?raw=true)


# [8회차] DB DOCKER AWS
- Dockerhub 주소: https://hub.docker.com/repository/docker/jkijoon/ybigta_team_assignment

- API ENDPOINTS
1. preprocess
![preprocess](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/preprocess.png?raw=true) 

2. register
![register](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/register.png?raw=true)

3. login
![login](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/login.png?raw=true)

4. update-password
![update-password](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/update-password.png?raw=true) 

5. delete
![delete](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/delete.png?raw=true) 


- Github Action
![github_action](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/aws/github_action.png?raw=true) 

# [4회차] Crawling & EDA & FE 및 시각화 

## 0. 개요 및 실행방법

- 인터스텔라(2014)에 대한 ```rating```, ```review_counts```, ```review_length``` 를 다음 세 사이트를 활용하여 크롤링했습니다.
  
  - Rotten Tomatoes: https://www.rottentomatoes.com/
  - IMDb: https: https://www.imdb.com/
  - LetterBoxd: https://letterboxd.com/
 
- 데이터 형식: 수집된 데이터는 'date, rating, content' 항목에 대하여 csv 형식으로 저장되어 있습니다.
- 데이터 개수: 각 사이트마다 약 500 ~ 600개의 데이터를 수집하였으며 총 1700개 이상의 리뷰 데이터를 수집하였습니다.
  - Rotten Tomatoes: 610
  - IMDb: 600개
  - LetterBoxd: 500개
    

- 실행 방법
  1) 환경 설정 및 가상환경 활성화:
     ```bash
      # 가상환경 생성 및 활성화
      python -m venv venv
      source venv/bin/activate  # Mac/Linux
      .\venv\Scripts\activate   # Windows
      
      # 의존성 라이브러리 설치
      pip install -r requirements.txt

  2) 프로젝트 루트로 이동
     ```bash
       cd YBIGTA_newbie_team_project

  3) 크롤러 실행
    ```bash
       cd review_analysis/crawling
       python main.py -o ../../database --all

  4) 전처리 실행
    ```bash
      cd ../preprocessing
      python main.py --output_dir ../../database --all


## 1. 개별 사이트 EDA

### 1.1 Rotten Tomato

#### 점수 분포

![rating rotten](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/rating(Rotten%20Tomato).png)

- 특성
  - 긍정적 리뷰 (8~10점)에 대부분이 분포하며 그 중 10점이 가장 많습니다.

- 이상치
  - 모든 데이터는 1~10 범위 안에 있었고 이를 벗어나는 데이터는 없었습니다.

#### 리뷰 수 추이

![review counts rotten](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_counts(Rotten%20Tomato).png)

- 특성
  - 개봉 10주년이 되는 24년 말을 제외하고 비슷하게 적은 리뷰수가 유지되는 모습을 확인할 수 있습니다.

- 이상치
  - 2024년 12월에 리뷰수가 급격하게 증가하는 모습을 보입니다. 이에 대한 조사 결과, 10주년 IMAX 재개봉이 그 원인으로 보이며 비슷한 흐름을 구글 트렌드에서도 확인할 수 있었습니다.

#### 리뷰 길이

![review length](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_length(Rotten%20Tomato).png)

- 특성
  - 대부분의 리뷰는 500자(char기준) 이내에 분포합니다.

- 이상치
  - 3000, 4000자를 넘는 리뷰가 각각 1개씩 확인됩니다.

### 1.2 IMDB

#### 점수 분포
IMDb 리뷰 데이터의 전반적인 특성과 이상치를 파악하기 위해 다양한 시각화를 수행하였습니다.

![rating imdb](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/rating(IMDb).png)

- 특성  
  - 별점이 9~10점 구간에 집중된 분포를 보입니다.  
  - 전반적으로 영화에 대한 만족도가 높은 경향을 확인할 수 있습니다.
- 이상치  
  - 별점이 없는 경우를 0으로 처리한 데이터가 존재합니다.
  - 정상 범위(1~10점)를 벗어나는 이상치 데이터는 총 35개로 확인되었습니다.

#### 리뷰 수 추이

![review counts imdb](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_counts(IMDb).png)

- 특성  
  - 영화 개봉 시점은 2014년 11월입니다.  
  - 2015년 이전 시점에 리뷰가 일시적으로 급증하는 구간이 관찰됩니다.  
  - 이후에는 2026년까지 낮은 빈도로 꾸준히 리뷰가 생성됩니다.

- 이상치  
  - 개봉 이전(2014년 이전) 또는 미래 시점(2026년 이후)의 데이터는 발견되지 않았습니다.  
  - 시계열 분석에 활용 가능한 데이터임을 확인하였습니다.


#### 리뷰 길이

![review length imdb](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_length(IMDb).png)

- 특성  
  - 대부분의 리뷰가 1,000자 미만에 집중된 Long-tail 분포를 보입니다.  
  - 짧은 감상 위주의 리뷰가 다수를 차지합니다.

- 이상치  
  - 수천 자 이상의 긴 리뷰가 일부 존재합니다.  
  - 5자 미만의 비정상적으로 짧은 리뷰는 존재하지 않았습니다.


### 1.3 LetterBox

#### 점수 분포

![rating letterbox](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/rating(letterbox).png)

- 특성
  - 평점이 10점에 강하게 몰려 있음 (가장 높은 막대가 10점 구간)
  - 전체적으로 고평점 편향(왼쪽 꼬리 분포) 형태를 보임

#### 리뷰 수 추이

![review counts imdb](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_counts(letterbox).png)

- 특성
  - 대부분 날짜에서 리뷰 수가 1개 수준으로 평소엔 리뷰가 꾸준히 적게 발생
  - 리뷰 발생이 연속적이지 않고 간헐적으로 긴 기간 동안 띄엄띄엄 있음
- 이상치
  - 2024년 초 10주년 기념 재개봉이라는 특수 이벤트로 큰 스파이크를 보임

#### 리뷰 길이

![review length](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/review_length(letterbox).png)

- 특성
  - 중앙값은 270자 전후로 짧은 리뷰가 대부분임
  - IQR구간이 80 ~ 450 으로 일반적인 리뷰 길이가 꽤 넓게 퍼져있음
- 이상치
  - 10자 이내의 매우 짧은 리뷰, 600자 이상의 리뷰가 관찰됨



## 2. 전처리 / FE

* 결측치 처리

    * 별점, 리뷰, 날짜 정보가 없는 행을 dropna()로 제거하였습니다.


* 이상치 처리

    * 별점 범위 1~10 범위 밖의 데이터를 제거하였습니다.

* 텍스트 데이터 전처리

    * 극단적으로 짧거나 (-5 char)  긴 리뷰(3000- char)를 제거하였습니다.


* 파생 변수 생성

  * ```sentence_count``` : 리뷰 text 에서 문장의 수를 추출.

* 텍스트 벡터화

  * TF-IDF를 사용해 단어를 벡터화
 
  * ```max_features``` = 2000 으로 설정



## 3. 비교분석
![비교분석1](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/%EB%B9%84%EA%B5%90%EB%B6%84%EC%84%9D_1.png))
연도별 리뷰 개수를 확인한 결과, Rotten Tomatoes의 경우 최근의 리뷰 위주로 크롤링되어 전체 시계열 분석 시 왜곡이 발생할 가능성이 파악되었습니다.
이를 해결하기 위해 전체 기간(2014-2026)을 다루는 'Broad Range' 분석과 더불어, 데이터가 밀집된 최근 시간 범위(2024-2026)에 대해 별도의 'Tight Range' 시계열 분석을 병행하여 분석의 정확도를 높였습니다.
Tight Range에서 2024년 12월, 전 플랫폼에서 리뷰 수가 동시 다발적으로 급증하는 구간이 관찰됩니다. 이는 개봉 10주년 기념 재상영이 대중의 관심을 다시 집중시키는 강력한 기폭제였음을 시사합니다. 특히 최근 데이터 위주인 Rotten Tomatoes에서도 이 시기를 기점으로 지속적인 리뷰 유입이 확인됩니다.

![비교분석2](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/review_analysis/plots/%EB%B9%84%EA%B5%90%EB%B6%84%EC%84%9D_2.png)
감성 지수 분포 분석 결과입니다.
Rotten Tomatoes: 최근 유입된 팬층의 영향으로 감성 분포가 긍정적인 영역에 매우 좁게 밀집되어 있습니다. 비판보다는 '명작에 대한 확인' 위주의 리뷰가 주를 이룹니다.
Letterboxd: 감정 단어 노출 빈도는 낮으나 이는 비평가적 어조를 사용하는 사용자 특성에 기인하며, 전반적으로 중립 이상의 긍정적 기조를 유지합니다.
IMDb: 감성 지수의 스펙트럼이 가장 넓습니다. 이는 장문의 분석글이 많아 긍정과 부정이 혼재된 복합적인 평가가 이루어지고 있음을 나타냅니다.


--------------------

# [4회차] Github 협업 및 자기소개

## 1. Github 협업 

* Branch Protection

![branch protection](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/branch_protection.png)

* Push Rejected

![push rejected](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/push_rejected.png)

* Review and Merged

* 오상호
  
![review and merged](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/review_and_merged.png)

* 황소현
    
![review and merged 황소현](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/review_and_merged_%ED%99%A9%EC%86%8C%ED%98%84.png)

* 정기준
    
![review and merged 정기준](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/review_and_merged_%EC%A0%95%EA%B8%B0%EC%A4%80.png)


## 2. 팀 소개
28기 8조는 정기준(팀장), 오상호, 황소현으로 구성되어있습니다.

* 정기준
  
|항목|내용|
|---|---|
|소속| QRM 20 
|1지망 팀| DE
|MBTI| INTJ
|취미| 기타, 사진

* 오상호
  
|항목|내용|
|---|---|
|소속| 응용통계학과 23
|1지망 팀| DA
|MBTI| INTJ
|취미| 헬스, 사진, 맛집가기

* 황소현
  
|항목|내용|
|---|---|
|소속| 인공지능학과 24
|1지망 팀| DS
|MBTI| ISTP
|취미| 음악듣기, 노래방가기


------------------------------
# Web 과제 실행법

1. 디렉토리 이동: ```cd YBIGTA_newbie_team_project\app```
2. 서버 실행 : ```uvicorn main:app --reload```
3. 페이지 접속 : ```http://127.0.0.1:8000``` 을 통해 접속


</br>













