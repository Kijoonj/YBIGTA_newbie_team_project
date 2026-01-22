from review_analysis.crawling.base_crawler import BaseCrawler
import time
import pandas as pd
import os
from datetime import datetime # [핵심] 영문 날짜를 숫자로 바꾸기 위해 필요
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class ImdbCrawler(BaseCrawler):
    '''
    imdb 영화리뷰 사이트 크롤링
    BaseCrawler 상속받아 브라우저 제어 및 데이터 저장
    '''
    def __init__(self, output_dir: str):
        '''imdbcrawler 클래스 초기화'''
        super().__init__(output_dir)
        self.base_url = 'https://www.imdb.com/title/tt0816692/reviews/?ref_=tt_ururv_genai_sm'
        self.reviews = []
        
    def start_browser(self):
        '''Selenium WebDriver 설정하고 대상 브라우저 실행'''
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.driver.get(self.base_url)
        time.sleep(3)

    def format_date(self, date_str: str) -> str:
        '''영문날짜 형식 -> 숫자 형식 변환'''
        try:
            # strip()으로 앞뒤 공백과 따옴표 영향을 제거한 뒤 파싱
            clean_date = date_str.strip().replace('"', '').replace("'", "")
            date_obj = datetime.strptime(clean_date, '%b %d, %Y')
            return date_obj.strftime('%Y.%m.%d')
        except Exception:
            # 변환 실패 시 원본에서 불필요한 문자만 제거하여 반환
            return date_str.strip().replace('"', '').replace("'", "")

    def load_all_reviews(self, target_count):
        '''목표 수집 개수만큼 리뷰 목록 확장'''
        print(f"리뷰 목록 확장 시작 (목표: {target_count}개)")
        
        while True:
            # 상세 페이지 링크 요소를 기준으로 로드된 리뷰 개수 파악
            current_links = self.driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
            count = len(current_links)
            print(f"현재 로드된 리뷰: {count} / {target_count}")

            if count >= target_count:
                print("목표 목록 확보 완료!")
                break
                
            try:
                # 페이지 하단으로 스크롤하여 더보기 버튼 노출
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3.5)

                # 'See all' 버튼을 정확히 찾아 클릭
                see_all_xpath = "//span[text()='See all'] | //button[.//span[text()='See all']]"
                wait = WebDriverWait(self.driver, 15)
                see_all_btn = wait.until(EC.element_to_be_clickable((By.XPATH, see_all_xpath)))
                
                # 버튼 위치로 스크롤 이동 (버튼이 화면에 가려져 클릭 안되는 문제 방지)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", see_all_btn)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", see_all_btn)
                time.sleep(4)

            except Exception:
                # 버튼 찾기 재시도 로직 추가
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 700);")
                time.sleep(2)
                
                # 재시도 후에도 개수가 늘지 않으면 그때 진짜로 종료
                new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper"))
                if new_count == count:
                    self.logger.info(f"추가 로드 버튼이 없어 종료합니다. (최종: {count}개)")
                    break

    def scrape_reviews(self, n=600):
        '''전체 리뷰 목록에서 상세 페이지 URL 추출 후 개별 페이지 순회하며 데이터 수집'''
        self.start_browser()
        
        # 1. 목록 확장 (입력받은 n만큼)
        self.load_all_reviews(target_count=n)
        
        # 2. 인덱스 에러 방지를 위해 모든 상세 URL을 리스트에 미리 담기
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        links = soup.select('a.ipc-title-link-wrapper')
        review_urls = ["https://www.imdb.com" + link['href'] for link in links][:n]
        
        # 3. 개별 페이지 진입 및 데이터 추출
        for i, url in enumerate(review_urls):
            try:
                # 주소 직접 이동
                self.driver.get(url)
                time.sleep(1.5)

                # 스포일러 버튼 클릭 (내용 펼치기)
                try:
                    spoiler_btn = self.driver.find_element(By.XPATH, "//button[contains(@class, 'ipc-btn') and .//span[contains(text(), 'Spoiler')]]")
                    self.driver.execute_script("arguments[0].click();", spoiler_btn)
                    time.sleep(0.5)
                except: pass

                detail_soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # 별점 추출
                rating_raw = detail_soup.select_one('span.ipc-rating-star--rating').get_text() if detail_soup.select_one('span.ipc-rating-star--rating') else "0"
                rating = rating_raw.split('/')[0]
                
                # 날짜 추출 및 변환
                date_raw = detail_soup.select_one('li.review-date').get_text() if detail_soup.select_one('li.review-date') else ""
                date = self.format_date(date_raw)
                
                # 본문 정제: 줄바꿈 제거 및 따옴표 통일
                raw_content = detail_soup.select_one('div.ipc-html-content-inner-div').get_text(separator=" ").strip()
                content = raw_content.replace('\n', ' ').replace('\r', ' ').strip()
                content = content.replace('"', "'")

                if content:
                    # 컬럼명: date, rating, content 통일
                    self.reviews.append({
                        "date": date,
                        "rating": rating,
                        "content": content
                    })
                    if (i + 1) % 10 == 0:
                        print(f"진행 상황: [{i+1}/{len(review_urls)}]")

            except Exception:
                continue
                
        print(f"전체 데이터 수집 완료 (총 {len(self.reviews)}건)")
        self.driver.quit()

    def save_to_database(self):
        '''수집된 리뷰 데이터를 csv 형식으로 저장'''
        if not self.reviews:
            print("저장할 데이터가 존재하지 않습니다.")
            return
        
        df = pd.DataFrame(self.reviews)
        save_path = os.path.join(self.output_dir, "reviews_imdb.csv")
        os.makedirs(self.output_dir, exist_ok=True)
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"CSV 파일 저장 완료: {save_path}")