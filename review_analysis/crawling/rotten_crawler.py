from __future__ import annotations

import os
import re
import time
from datetime import datetime, timedelta
from typing import Optional, TypedDict, List

import pandas as pd
from selenium import webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from review_analysis.crawling.base_crawler import BaseCrawler


class Review(TypedDict):
    date: str
    rating: float
    content: str


class RottenCrawler(BaseCrawler):

    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://www.rottentomatoes.com/m/interstellar_2014/reviews/all-audience'
        self.driver: Optional[WebDriver] = None
        self.reviews: List[Review] = []
        os.makedirs(output_dir, exist_ok=True)

    def start_browser(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        options.add_experimental_option('excludeSwitches', ['enable-logging'])

        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
        self.driver.maximize_window()

    def scrape_reviews(self) -> None:
        if self.driver is None:
            self.start_browser()

        assert self.driver is not None  
        try:
            self.driver.get(self.base_url)
            time.sleep(5)

            try:
                cookie_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
                )
                cookie_button.click()
                time.sleep(3)
            except TimeoutException:
                pass

            target_count = 500
            load_more_attempts = 0
            max_attempts = 100

            while len(self.reviews) < target_count and load_more_attempts < max_attempts:
                self._extract_reviews_from_page()

                if len(self.reviews) >= target_count:
                    break

                if not self._click_load_more():
                    break

                load_more_attempts += 1
                time.sleep(2)

        finally:
            self.driver.quit()
            self.driver = None

    def _extract_reviews_from_page(self) -> None:
        assert self.driver is not None

        review_elements = self.driver.find_elements(By.TAG_NAME, 'review-card')
        for element in review_elements:
            try:
                rating_elements = element.find_elements(By.TAG_NAME, "rating-stars-group")

                rating: float = 0.0
                if rating_elements:
                    rating_score_str = rating_elements[0].get_attribute("score")  # str | None
                    if rating_score_str is not None:
                        rating = float(rating_score_str) * 2

                date_elements = element.find_elements(By.CSS_SELECTOR, '[slot="timestamp"]')
                date = date_elements[0].text.strip() if date_elements else 'Unknown'

                drawer_elements = element.find_elements(By.TAG_NAME, 'drawer-more')
                if drawer_elements:
                    content_elements = drawer_elements[0].find_elements(By.CSS_SELECTOR, '[slot="content"]')
                    content = content_elements[0].text.strip() if content_elements else ''
                else:
                    content = ''

                if not content or len(content) < 3:
                    continue

                review_data: Review = {
                    'date': date,
                    'rating': rating,
                    'content': content
                }

                if review_data not in self.reviews:
                    self.reviews.append(review_data)

            except (NoSuchElementException, Exception):
                continue

    def _click_load_more(self) -> bool:
        assert self.driver is not None

        selectors = [
            'rt-button[data-pagemediareviewsmanager="loadMoreBtn:click"]',
            'button[data-pagemediareviewsmanager="loadMoreBtn:click"]',
            '.button-wrap rt-button',
            '//button[contains(text(), "Load More")]'
        ]

        for selector in selectors:
            try:
                if selector.startswith('//'):
                    load_more_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    load_more_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )

                self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", load_more_button)
                return True

            except (TimeoutException, NoSuchElementException):
                continue

        return False
