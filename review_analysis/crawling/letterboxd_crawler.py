import os
import re
import random
import pandas as pd  # type: ignore
from time import sleep, time
from datetime import datetime

# 핵심: undetected_chromedriver로 교체
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException

# 기존 프로젝트 구조 임포트
from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger

class letterboxdCrawler(BaseCrawler):
    """
    Letterboxd 사이트에서 영화 리뷰 데이터를 수집하는 크롤러 클래스입니다.
    [캡차 우회 및 성능 최적화 버전]
    """

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.driver: uc.Chrome | None = None  # 타입 힌트 변경
        self.reviews_data: list[dict[str, str]] = []
        self.logger = setup_logger()
        self.target_url = "https://letterboxd.com/film/interstellar/reviews/by/activity/"
        self.max_retries = 3
        self.seen_contents: set[int] = set()

    def start_browser(self):
        """undetected-chromedriver를 이용한 최적화된 브라우저 설정"""
        options = uc.ChromeOptions()
        
        # 시크릿 모드 및 기본 설정
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # ★ 주의: UC는 User-Agent를 자동으로 설정하므로 하드코딩된 UA는 가급적 피하는 것이 좋습니다.
        # 필요하다면 최신 버전 문자열을 사용하세요.
        
        # 불필요한 리소스 차단 및 성능 최적화
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        }
        options.add_experimental_option("prefs", prefs)
        
        # 페이지 로드 전략
        options.page_load_strategy = 'eager'
        
        # 브라우저 실행 (드라이버 패치 자동 수행)
        # version_main을 지정하지 않아도 설치된 크롬 버전을 자동으로 찾습니다.
        self.driver = uc.Chrome(options=options)
        
        # ★ UC는 아래와 같은 navigator.webdriver 우회 설정을 내부적으로 이미 수행합니다.
        # 따라서 별도의 execute_cdp_cmd 없이도 탐지 확률이 매우 낮습니다.
        
        self.driver.implicitly_wait(2)
        self.logger.info("undetected-chromedriver 시작 완료 (스텔스 모드)")

    def _extract_all_reviews_js(self):
        """JavaScript로 모든 리뷰를 한 번에 추출 (DOM 접근 최소화)"""
        js_script = """
        const reviews = [];
        const items = document.querySelectorAll('div.listitem');
        
        items.forEach(item => {
            try {
                let rating = '평점 없음';
                const ratingSpan = item.querySelector('span.rating');
                if (ratingSpan) {
                    const classes = ratingSpan.className.split(' ');
                    for (const cls of classes) {
                        if (cls.startsWith('rated-')) {
                            rating = cls.replace('rated-', '');
                            break;
                        }
                    }
                }
                
                let date = '날짜 정보 없음';
                const timeElem = item.querySelector('time.timestamp');
                if (timeElem) {
                    const datetime = timeElem.getAttribute('datetime');
                    if (datetime) date = datetime;
                }
                
                let content = '';
                const bodyText = item.querySelector('div.body-text');
                if (bodyText) content = bodyText.innerText.trim();
                
                if (content) {
                    reviews.push({
                        rating: rating,
                        date: date,
                        content: content
                    });
                }
            } catch (e) {}
        });
        return reviews;
        """
        try:
            return self.driver.execute_script(js_script)
        except Exception as e:
            self.logger.error(f"JS 추출 오류: {e}")
            return []

    def _format_date(self, date_str):
        if not date_str or date_str == '날짜 정보 없음':
            return '날짜 정보 없음'
        try:
            if 'T' in date_str:
                return date_str.split('T')[0].replace('-', '.')
            return date_str.replace('-', '.')
        except:
            return date_str

    def _wait_for_reviews(self, timeout=8):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.listitem"))
            )
            return True
        except TimeoutException:
            return False

    def scrape_reviews(self):
        if not self.driver:
            self.start_browser()

        self.logger.info(f"데이터 수집 시작: {self.target_url}")
        start_time = time()
        
        self.driver.get(self.target_url)
        
        # 첫 진입 시 Cloudflare 체크를 위한 여유 시간
        sleep(random.uniform(3, 5))
        
        if not self._wait_for_reviews(timeout=10):
            self.logger.warning("캡차가 감지되었거나 로딩이 지연됨. 수동 해결을 위해 40초간 대기합니다.")
            sleep(40) 
            if not self._wait_for_reviews(timeout=10):
                self.logger.error("데이터 로딩 실패")
                return

        page_count = 0
        while len(self.reviews_data) < 500:
            page_count += 1
            page_start = time()
            
            try:
                reviews = self._extract_all_reviews_js()
                
                if not reviews:
                    self.logger.warning("리뷰를 찾지 못함")
                    break
                
                new_count = 0
                for review in reviews:
                    if len(self.reviews_data) >= 500: break
                    
                    content = review['content'].replace('\n', ' ').strip()
                    content_hash = hash(content[:100])
                    
                    if content_hash in self.seen_contents: continue
                    self.seen_contents.add(content_hash)
                    
                    self.reviews_data.append({
                        "rating": review['rating'],
                        "date": self._format_date(review['date']),
                        "content": content
                    })
                    new_count += 1
                
                self.logger.info(f"페이지 {page_count}: {new_count}개 추가 (총 {len(self.reviews_data)}개)")
                
                if len(self.reviews_data) >= 500: break
                
                # 다음 페이지 이동
                if not self._click_next_page():
                    break
                
                # 로딩 대기 (동적 지연)
                self._wait_for_reviews(timeout=10)
                
            except Exception as e:
                self.logger.error(f"오류 발생: {e}")
                break

        self.logger.info(f"수집 종료. 총 소요시간: {time() - start_time:.1f}초")

    def _click_next_page(self):
        """인간다운 클릭 동작 모사"""
        try:
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "div.paginate-nextprev a.next")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            
            # 무작위 지연으로 패턴 파악 방지
            sleep(random.uniform(1.5, 3.0))
            
            self.driver.execute_script("arguments[0].click();", next_btn)
            return True
        except NoSuchElementException:
            return False

    def save_to_database(self):
        if not self.reviews_data: return
        os.makedirs(self.output_dir, exist_ok=True)
        df = pd.DataFrame(self.reviews_data)
        save_path = os.path.join(self.output_dir, "reviews_letterboxd.csv")
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"최종 저장 완료: {save_path}")
        if self.driver:
            self.driver.quit()