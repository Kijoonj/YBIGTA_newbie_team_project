import os
import time
import logging
from typing import Optional, List, TypedDict, cast

import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement

from review_analysis.crawling.base_crawler import BaseCrawler


class ReviewData(TypedDict):
    date: str
    rating: float
    content: str


class RottenCrawler(BaseCrawler):
    """
    Rotten Tomatoes에서 Interstellar 영화의 관객 리뷰를 크롤링하는 클래스.

    Attributes:
        output_dir (str): 크롤링한 데이터를 저장할 디렉토리 경로
        base_url (str): 크롤링할 Rotten Tomatoes 페이지 URL
        driver (Optional[WebDriver]): Selenium WebDriver 인스턴스
        reviews (List[ReviewData]): 수집한 리뷰 데이터를 저장하는 리스트
        logger (logging.Logger): 로깅을 위한 logger 인스턴스
    """

    base_url: str
    driver: Optional[WebDriver]
    reviews: List[ReviewData]
    logger: logging.Logger

    def __init__(self, output_dir: str) -> None:
        """
        RottenCrawler 초기화.

        Args:
            output_dir (str): 크롤링한 데이터를 저장할 디렉토리 경로
        """
        super().__init__(output_dir)
        self.base_url = "https://www.rottentomatoes.com/m/interstellar_2014/reviews/all-audience"
        self.driver = None
        self.reviews = []

        # 로거 설정
        self.logger = logging.getLogger("RottenCrawler")
        self.logger.setLevel(logging.INFO)

        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)

        # 파일 핸들러 추가
        log_file = os.path.join(output_dir, "rotten_crawler.log")
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 포맷터 설정
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 핸들러가 중복으로 추가되지 않도록 체크
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    # -----------------------------
    # Selenium Driver
    # -----------------------------
    def start_browser(self) -> None:
        """
        Selenium WebDriver를 시작하고 초기 설정을 수행.
        Chrome 브라우저를 일반 모드로 실행 (디버깅용).
        """
        try:
            options = webdriver.ChromeOptions()
            # options.add_argument('--headless')
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            options.add_experimental_option("excludeSwitches", ["enable-logging"])

            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            self.driver.maximize_window()
            self.logger.info("Browser started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start browser: {e}")
            raise

    def _get_driver(self) -> WebDriver:
        """
        mypy-safe하게 self.driver를 WebDriver로 반환.
        """
        if self.driver is None:
            raise RuntimeError("WebDriver is not initialized. Call start_browser() first.")
        return self.driver

    # -----------------------------
    # Main Scraping
    # -----------------------------
    def scrape_reviews(self) -> None:
        """
        Rotten Tomatoes에서 리뷰를 크롤링.
        'Load More' 버튼을 클릭하여 최소 600개의 리뷰를 수집.
        """
        if self.driver is None:
            self.start_browser()

        driver = self._get_driver()

        try:
            self.logger.info(f"Accessing URL: {self.base_url}")
            driver.get(self.base_url)
            time.sleep(5)  # 초기 페이지 로딩 대기

            # 쿠키 동의 팝업 처리
            try:
                cookie_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
                )
                cookie_button.click()
                self.logger.info("Clicked cookie consent button")
                time.sleep(3)
            except TimeoutException:
                self.logger.info("No cookie consent popup found")

            # 페이지 HTML 디버깅 저장
            page_source = driver.page_source
            debug_file = os.path.join(self.output_dir, "debug_page.html")
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(page_source)
            self.logger.info(f"Page HTML saved to {debug_file}")

            # 리뷰 카드 찾기 시도 (여러 선택자)
            selectors_to_try = [
                ".review-card",
                "review-card",
                '[class*="review"]',
                "drawer-more",
            ]

            for selector in selectors_to_try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                self.logger.info(f"Selector '{selector}': found {len(elements)} elements")

            target_count = 600
            load_more_attempts = 0
            max_attempts = 100  # 무한 루프 방지

            while len(self.reviews) < target_count and load_more_attempts < max_attempts:
                # 현재 페이지의 리뷰 수집
                self._extract_reviews_from_page()
                self.logger.info(f"Current reviews collected: {len(self.reviews)}")

                if len(self.reviews) >= target_count:
                    break

                # Load More 버튼 클릭
                if not self._click_load_more():
                    self.logger.warning("No more 'Load More' button found")
                    break

                load_more_attempts += 1
                time.sleep(2)  # 페이지 로딩 대기

            self.logger.info(f"Total reviews collected: {len(self.reviews)}")

            driver.quit()
            self.driver = None
            self.logger.info("Browser closed")

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            try:
                if self.driver is not None:
                    self.driver.quit()
            finally:
                self.driver = None
            raise

    def _extract_reviews_from_page(self) -> None:
        """
        현재 페이지에 로드된 모든 리뷰를 추출하여 self.reviews에 추가.
        """
        driver = self._get_driver()

        try:
            # 리뷰 카드 찾기 - 클래스 없이 태그명으로 찾기
            review_elements = driver.find_elements(By.TAG_NAME, "review-card")
            self.logger.info(f"Found {len(review_elements)} review cards")

            for element in review_elements:
                try:
                    # 별점 추출
                    rating_elements = element.find_elements(By.TAG_NAME, "rating-stars-group")
                    rating: float
                    if rating_elements:
                        rating_str = rating_elements[0].get_attribute("score")
                        rating = float(rating_str) if rating_str else 0.0
                    else:
                        rating = 0.0

                    # 날짜 추출 (timestamp slot)
                    date_elements = element.find_elements(By.CSS_SELECTOR, '[slot="timestamp"]')
                    date = date_elements[0].text.strip() if date_elements else "Unknown"

                    # 리뷰 내용 추출 - drawer-more 태그 내부
                    drawer_elements = element.find_elements(By.TAG_NAME, "drawer-more")
                    content: str
                    if drawer_elements:
                        content_elements = drawer_elements[0].find_elements(By.CSS_SELECTOR, '[slot="content"]')
                        content = content_elements[0].text.strip() if content_elements else ""
                    else:
                        content = ""


                    review_data: ReviewData = {
                        "date": date,
                        "rating": rating,
                        "content": content,
                    }

                    
                    if review_data not in self.reviews:
                        self.reviews.append(review_data)
                        self.logger.debug(f"Added review: {date}, {rating}, {content[:30]}...")

                except NoSuchElementException as e:
                    self.logger.warning(f"Missing element in review: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error extracting individual review: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in _extract_reviews_from_page: {e}")

    def _parse_rating(self, rating_text: str) -> float:
        """
        별점 텍스트를 숫자로 변환.

        Args:
            rating_text (str): 별점 텍스트 (예: "4.5/5", "★★★★☆")

        Returns:
            float: 변환된 별점 (0.0 ~ 5.0)
        """
        try:
            # "4.5/5" 형식 처리
            if "/" in rating_text:
                return float(rating_text.split("/")[0])

            # 별 개수 
            filled_stars = rating_text.count("★")
            half_stars = rating_text.count("½")
            rating = filled_stars + (half_stars * 0.5)
            return float(rating)

        except Exception as e:
            self.logger.warning(f"Failed to parse rating '{rating_text}': {e}")
            return 0.0

    def _click_load_more(self) -> bool:
        """
        'Load More' 버튼을 찾아 클릭.

        Returns:
            bool: 버튼을 찾아 클릭했으면 True, 그렇지 않으면 False
        """
        driver = self._get_driver()

        try:

            selectors = [
                'rt-button[data-pagemediareviewsmanager="loadMoreBtn:click"]',
                'button[data-pagemediareviewsmanager="loadMoreBtn:click"]',
                ".button-wrap rt-button",
                '//button[contains(text(), "Load More")]',
            ]

            for selector in selectors:
                try:
                    load_more_button: WebElement
                    if selector.startswith("//"):
                        # XPath
                        load_more_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        # CSS Selector
                        load_more_button = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )

                    driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                    time.sleep(1)

                    driver.execute_script("arguments[0].click();", load_more_button)
                    self.logger.info(f"Clicked 'Load More' button using selector: {selector}")
                    return True

                except (TimeoutException, NoSuchElementException):
                    continue

            self.logger.info("Load More button not found with any selector")
            return False

        except Exception as e:
            self.logger.warning(f"Error clicking Load More button: {e}")
            return False

    def save_to_database(self) -> None:
        """
        수집한 리뷰 데이터를 CSV 파일로 저장.
        파일명: reviews_rotten.csv
        """
        try:
            if not self.reviews:
                self.logger.warning("No reviews to save")
                return

            df = pd.DataFrame(self.reviews)

            os.makedirs(self.output_dir, exist_ok=True)

            output_path = os.path.join(self.output_dir, "reviews_rotten.csv")
            df.to_csv(output_path, index=False, encoding="utf-8-sig")

            self.logger.info(f"Saved {len(self.reviews)} reviews to {output_path}")
            print(f"Successfully saved {len(self.reviews)} reviews to {output_path}")

        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
            raise
