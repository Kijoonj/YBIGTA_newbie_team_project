from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, cast

import pandas as pd
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from review_analysis.crawling.base_crawler import BaseCrawler


class ImdbCrawler(BaseCrawler):
    """
    imdb 영화리뷰 사이트 크롤링
    BaseCrawler 상속받아 브라우저 제어 및 데이터 저장
    """

    base_url: str
    reviews: List[Dict[str, str]]
    driver: Optional[WebDriver]

    def __init__(self, output_dir: str) -> None:
        """imdbcrawler 클래스 초기화"""
        super().__init__(output_dir)
        self.base_url = "https://www.imdb.com/title/tt0816692/reviews/?ref_=tt_ururv_genai_sm"
        self.reviews = []
        self.driver = None

    def start_browser(self) -> None:
        """Selenium WebDriver 설정하고 대상 브라우저 실행"""
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options,
        )
        self.driver.get(self.base_url)
        time.sleep(3)

    def format_date(self, date_str: str) -> str:
        """영문날짜 형식 -> 숫자 형식 변환"""
        try:
            clean_date = date_str.strip().replace('"', "").replace("'", "")
            date_obj = datetime.strptime(clean_date, "%b %d, %Y")
            return date_obj.strftime("%Y.%m.%d")
        except ValueError:
            return date_str.strip().replace('"', "").replace("'", "")

    def load_all_reviews(self, target_count: int) -> None:
        """목표 수집 개수만큼 리뷰 목록 확장"""
        if self.driver is None:
            raise RuntimeError("Browser not started. Call start_browser() first.")

        print(f"리뷰 목록 확장 시작 (목표: {target_count}개)")

        while True:
            current_links = self.driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper")
            count = len(current_links)
            print(f"현재 로드된 리뷰: {count} / {target_count}")

            if count >= target_count:
                print("목표 목록 확보 완료!")
                break

            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3.5)

                see_all_xpath = "//span[text()='See all'] | //button[.//span[text()='See all']]"
                wait: WebDriverWait[Any] = WebDriverWait(self.driver, 15)
                see_all_btn = wait.until(EC.element_to_be_clickable((By.XPATH, see_all_xpath)))

                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    see_all_btn,
                )
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", see_all_btn)
                time.sleep(4)

            except Exception:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 700);")
                time.sleep(2)

                new_count = len(self.driver.find_elements(By.CSS_SELECTOR, "a.ipc-title-link-wrapper"))
                if new_count == count:
                    #self.logger.info(f"추가 로드 버튼이 없어 종료합니다. (최종: {count}개)")
                    break

    def scrape_reviews(self, n: int = 600) -> None:
        """전체 리뷰 목록에서 상세 페이지 URL 추출 후 개별 페이지 순회하며 데이터 수집"""
        self.start_browser()
        if self.driver is None:
            raise RuntimeError("Driver initialization failed.")

        self.load_all_reviews(target_count=n)

        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        links = soup.select("a.ipc-title-link-wrapper")

        review_urls: List[str] = []
        for link in links[:n]:
            # mypy: BeautifulSoup select()는 Tag/str 섞일 수 있어서 Tag로 캐스팅
            tag = cast(Tag, link)
            href = tag.get("href")
            if isinstance(href, str):
                review_urls.append("https://www.imdb.com" + href)

        for i, url in enumerate(review_urls):
            try:
                self.driver.get(url)
                time.sleep(1.5)

                # Spoiler 버튼 클릭
                try:
                    spoiler_btn = self.driver.find_element(
                        By.XPATH,
                        "//button[contains(@class, 'ipc-btn') and .//span[contains(text(), 'Spoiler')]]",
                    )
                    self.driver.execute_script("arguments[0].click();", spoiler_btn)
                    time.sleep(0.5)
                except Exception:
                    pass

                detail_soup = BeautifulSoup(self.driver.page_source, "html.parser")

                rating_tag = detail_soup.select_one("span.ipc-rating-star--rating")
                rating_raw = rating_tag.get_text() if rating_tag else "0"
                rating = rating_raw.split("/")[0]

                date_tag = detail_soup.select_one("li.review-date")
                date_raw = date_tag.get_text() if date_tag else ""
                date = self.format_date(date_raw)

                content_tag = detail_soup.select_one("div.ipc-html-content-inner-div")
                raw_content = content_tag.get_text(separator=" ").strip() if content_tag else ""
                content = raw_content.replace("\n", " ").replace("\r", " ").strip()
                content = content.replace('"', "'")

                if content:
                    self.reviews.append(
                        {
                            "date": date,
                            "rating": rating,
                            "content": content,
                        }
                    )
                    if (i + 1) % 10 == 0:
                        print(f"진행 상황: [{i+1}/{len(review_urls)}]")

            except Exception:
                continue

        print(f"전체 데이터 수집 완료 (총 {len(self.reviews)}건)")
        self.driver.quit()
        self.driver = None

    def save_to_database(self) -> None:
        """수집된 리뷰 데이터를 csv 형식으로 저장"""
        if not self.reviews:
            print("저장할 데이터가 존재하지 않습니다.")
            return

        df = pd.DataFrame(self.reviews)
        save_path = os.path.join(self.output_dir, "reviews_imdb.csv")
        os.makedirs(self.output_dir, exist_ok=True)
        df.to_csv(save_path, index=False, encoding="utf-8-sig")
        print(f"CSV 파일 저장 완료: {save_path}")
