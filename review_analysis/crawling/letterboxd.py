import os
import re
import pandas as pd
from time import sleep, time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from review_analysis.crawling.base_crawler import BaseCrawler
from utils.logger import setup_logger


class letterboxdCrawler(BaseCrawler):
    """
    Letterboxd 사이트에서 영화 리뷰 데이터를 수집하는 크롤러 클래스입니다.
    BaseCrawler 추상 클래스를 상속받아 구현되었습니다.
    
    [최적화 버전]
    - sleep 시간 최소화
    - JavaScript 기반 일괄 추출로 DOM 접근 횟수 감소
    - 불필요한 리소스 로딩 차단
    - 페이지당 2분 → 10-15초로 단축
    """

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.driver = None
        self.reviews_data = []
        self.logger = setup_logger()
        self.target_url = "https://letterboxd.com/film/interstellar/reviews/by/activity/"
        self.max_retries = 3
        # 중복 체크용 set
        self.seen_contents = set()

    def start_browser(self):
        """최적화된 브라우저 설정"""
        options = Options()
        
        # 기본 설정
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--window-size=1920,1080")
        
        # User Agent
        options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # 자동화 탐지 우회
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # ★ 성능 최적화: 불필요한 리소스 차단
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            # 이미지 로딩 비활성화 (캡챠에 영향 줄 수 있으니 필요시 제거)
            # "profile.managed_default_content_settings.images": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # ★ 페이지 로드 전략: eager (DOM 준비되면 바로 진행)
        options.page_load_strategy = 'eager'
        
        self.driver = webdriver.Chrome(options=options)
        
        # WebDriver 속성 숨기기
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            '''
        })
        
        # ★ implicit wait 줄이기 (명시적 wait 사용할 것)
        self.driver.implicitly_wait(2)
        self.logger.info("브라우저 시작 완료 (최적화 모드)")

    def _extract_all_reviews_js(self):
        """
        ★ 핵심 최적화: JavaScript로 모든 리뷰를 한 번에 추출
        DOM 접근을 최소화하여 속도 대폭 향상
        """
        js_script = """
        const reviews = [];
        const items = document.querySelectorAll('div.listitem');
        
        items.forEach(item => {
            try {
                // 별점 추출
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
                
                // 날짜 추출
                let date = '날짜 정보 없음';
                const timeElem = item.querySelector('time.timestamp');
                if (timeElem) {
                    const datetime = timeElem.getAttribute('datetime');
                    if (datetime) {
                        date = datetime;  // YYYY-MM-DD 형식
                    }
                }
                
                // 내용 추출
                let content = '';
                const bodyText = item.querySelector('div.body-text');
                if (bodyText) {
                    content = bodyText.innerText.trim();
                }
                
                if (content) {
                    reviews.push({
                        rating: rating,
                        date: date,
                        content: content
                    });
                }
            } catch (e) {
                // 개별 리뷰 오류 무시
            }
        });
        
        return reviews;
        """
        
        try:
            return self.driver.execute_script(js_script)
        except Exception as e:
            self.logger.error(f"JS 추출 오류: {e}")
            return []

    def _format_date(self, date_str):
        """날짜 형식 변환 → YYYY.MM.DD"""
        if not date_str or date_str == '날짜 정보 없음':
            return '날짜 정보 없음'
        try:
            # ISO 형식: 2026-01-21T21:10:02.282Z
            if 'T' in date_str:
                date_part = date_str.split('T')[0]  # 2026-01-21
                return date_part.replace('-', '.')
            
            # YYYY-MM-DD 형식
            if '-' in date_str and len(date_str) == 10:
                return date_str.replace('-', '.')
            
            return date_str
        except:
            return date_str

    def _wait_for_reviews(self, timeout=8):
        """리뷰 로딩 대기 (최적화)"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.listitem"))
            )
            return True
        except TimeoutException:
            return False

    def scrape_reviews(self):
        """
        최적화된 리뷰 수집 - 페이지당 10-15초 목표
        """
        if not self.driver:
            self.start_browser()

        self.logger.info(f"데이터 수집 시작: {self.target_url}")
        start_time = time()
        
        self.driver.get(self.target_url)
        
        # ★ 캡챠 체크: 첫 페이지에서만 충분히 대기
        self.logger.info("첫 페이지 로딩 중... (캡챠 확인)")
        sleep(2)
        
        # 캡챠가 있으면 사용자가 수동으로 해결할 시간
        if not self._wait_for_reviews(timeout=10):
            self.logger.warning("리뷰가 로드되지 않음. 캡챠를 수동으로 해결해주세요.")
            self.logger.info("30초 대기 중...")
            sleep(30)
            if not self._wait_for_reviews(timeout=10):
                self.logger.error("리뷰 로딩 실패")
                return

        page_count = 0
        consecutive_failures = 0
        
        while len(self.reviews_data) < 500:
            page_count += 1
            page_start = time()
            self.logger.info(f"페이지 {page_count} 크롤링 중... (현재: {len(self.reviews_data)}/500)")
            
            try:
                # ★ JavaScript로 한 번에 모든 리뷰 추출
                reviews = self._extract_all_reviews_js()
                
                if not reviews:
                    self.logger.warning("리뷰를 찾지 못함")
                    consecutive_failures += 1
                    if consecutive_failures >= 3:
                        break
                    sleep(1)
                    continue
                
                consecutive_failures = 0
                new_count = 0
                
                for review in reviews:
                    if len(self.reviews_data) >= 500:
                        break
                    
                    content = review['content'].replace('\n', ' ').strip()
                    
                    # ★ 중복 체크 (content 해시)
                    content_hash = hash(content[:100])  # 앞 100자로 중복 체크
                    if content_hash in self.seen_contents:
                        continue
                    self.seen_contents.add(content_hash)
                    
                    self.reviews_data.append({
                        "rating": review['rating'],
                        "date": self._format_date(review['date']),
                        "content": content
                    })
                    new_count += 1
                
                page_time = time() - page_start
                self.logger.info(f"페이지 {page_count}: {new_count}개 추가 ({page_time:.1f}초)")
                
                # 중간 저장 (100개 단위)
                if len(self.reviews_data) % 100 < new_count and len(self.reviews_data) >= 100:
                    self._intermediate_save()
                
                if len(self.reviews_data) >= 500:
                    break
                
                # ★ 다음 페이지 이동 (클릭 방식 - 캡챠 우회)
                if not self._click_next_page():
                    self.logger.info("마지막 페이지 도달")
                    break
                
                # ★ 리뷰 로딩 대기 (동적 대기)
                if not self._wait_for_reviews(timeout=10):
                    self.logger.warning("다음 페이지 로딩 지연")
                    sleep(3)
                
            except Exception as e:
                self.logger.error(f"페이지 {page_count} 오류: {str(e)}")
                consecutive_failures += 1
                if consecutive_failures >= 3:
                    break
                sleep(2)
                continue

        total_time = time() - start_time
        self.logger.info(f"수집 완료: {len(self.reviews_data)}개 / {total_time:.1f}초")
        self.logger.info(f"평균 페이지당: {total_time/max(page_count,1):.1f}초")

    def _click_next_page(self):
        """
        다음 페이지로 클릭 이동 (driver.get 대신 - 캡챠 우회)
        """
        try:
            # 다음 버튼 찾기
            next_btn = self.driver.find_element(By.CSS_SELECTOR, "div.paginate-nextprev a.next")
            
            # 스크롤해서 버튼 보이게
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
            sleep(0.3)
            
            # JavaScript 클릭 (더 안정적)
            self.driver.execute_script("arguments[0].click();", next_btn)
            
            # 페이지 전환 대기
            sleep(1.5)
            return True
            
        except NoSuchElementException:
            return False
        except Exception as e:
            self.logger.error(f"다음 페이지 클릭 오류: {e}")
            return False

    def _intermediate_save(self):
        """중간 저장"""
        if not self.reviews_data:
            return
        
        os.makedirs(self.output_dir, exist_ok=True)
        temp_path = os.path.join(self.output_dir, "reviews_letterboxd_temp.csv")
        df = pd.DataFrame(self.reviews_data)
        df.to_csv(temp_path, index=False, encoding="utf-8-sig")
        self.logger.info(f"중간 저장: {len(self.reviews_data)}개")

    def save_to_database(self):
        """최종 저장"""
        if not self.reviews_data:
            self.logger.error("저장할 데이터 없음")
            return

        os.makedirs(self.output_dir, exist_ok=True)
        
        df = pd.DataFrame(self.reviews_data)
        save_path = os.path.join(self.output_dir, "reviews_letterboxd.csv")
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        
        self.logger.info(f"저장 완료: {save_path} ({len(self.reviews_data)}개)")
        
        # 임시 파일 삭제
        temp_path = os.path.join(self.output_dir, "reviews_letterboxd_temp.csv")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if self.driver:
            self.driver.quit()
            self.logger.info("브라우저 종료")