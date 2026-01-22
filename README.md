</br>

# [4회차] EDA & FE 및 시각화 

## 0. 개요 및 실행방법

## 1. 개별 사이트 EDA

### 1.1 Rotten Tomato

* 점수 분포



* 리뷰 수 추이



* 리뷰 길이


### 1.2 IDMB

* 점수 분포



* 리뷰 수 추이



* 리뷰 길이

### 1.3 LetterBox

* 점수 분포



* 리뷰 수 추이



* 리뷰 길이


## 2. 전처리 / FE

* 결측치 처리

    * 별점, 리뷰, 날짜 정보가 없는 행을 dropna()로 제거하였습니다.


* 이상치 처리

    * 별점 0점 데이터 및 텍스트 길이가 극단적으로 짧거나 긴 리뷰를 제거하였습니다.

* 텍스트 데이터 전처리



* 파생 변수 생성

  * ```sentence_count``` : 리뷰 text 에서 문장의 수를 추출.

* 텍스트 벡터화

  * TF-IDF를 사용해 단어를 벡터화
 
  * ```max_features``` = 2000 으로 설정



## 3. 비교분석
![alt text](image.png)
연도별 리뷰 개수를 확인한 결과, Rotten Tomatoes의 경우 최근의 리뷰 위주로 크롤링되어 전체 시계열 분석 시 왜곡이 발생할 가능성이 파악되었습니다.
이를 해결하기 위해 전체 기간(2014-2026)을 다루는 'Broad Range' 분석과 더불어, 데이터가 밀집된 최근 시간 범위(2024-2026)에 대해 별도의 'Tight Range' 시계열 분석을 병행하여 분석의 정확도를 높였습니다.
Tight Range에서 2024년 12월, 전 플랫폼에서 리뷰 수가 동시 다발적으로 급증하는 구간이 관찰됩니다. 이는 개봉 10주년 기념 재상영이 대중의 관심을 다시 집중시키는 강력한 기폭제였음을 시사합니다. 특히 최근 데이터 위주인 Rotten Tomatoes에서도 이 시기를 기점으로 지속적인 리뷰 유입이 확인됩니다.

![alt text](image-1.png)
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
![review and merged](https://github.com/Kijoonj/YBIGTA_newbie_team_project/blob/main/github/review_and_merged.png)


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
|소속|
|1지망 팀|
|MBTI|
|취미|


</br>
