import os
import time
import re
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from review_analysis.crawling.base_crawler import BaseCrawler


class RottenCrawler(BaseCrawler):
    
    def __init__(self, output_dir: str):
        super().__init__(output_dir)
        self.base_url = 'https://www.rottentomatoes.com/m/interstellar_2014/reviews/all-audience'
        self.driver = None
        self.reviews = []
        os.makedirs(output_dir, exist_ok=True)
        
    def start_browser(self):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)
            self.driver.maximize_window()
            
        except Exception as e:
            raise
    
    def scrape_reviews(self):
        if self.driver is None:
            self.start_browser()
        
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
            
            target_count = 600
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
            
            if self.driver:
                self.driver.quit()
                
        except Exception as e:
            if self.driver:
                self.driver.quit()
            raise
    
    def _extract_reviews_from_page(self):
        try:
            review_elements = self.driver.find_elements(By.TAG_NAME, 'review-card')
            
            for element in review_elements:
                try:
                    rating_elements = element.find_elements(By.TAG_NAME, 'rating-stars-group')
                    if rating_elements:
                        rating = rating_elements[0].get_attribute('score')
                        rating = float(rating) * 2 if rating else 0.0
                    else:
                        rating = 0.0
                    
                    date_elements = element.find_elements(By.CSS_SELECTOR, '[slot="timestamp"]')
                    date = date_elements[0].text.strip() if date_elements else 'Unknown'
                    date = self._format_date(date)
                    
                    drawer_elements = element.find_elements(By.TAG_NAME, 'drawer-more')
                    if drawer_elements:
                        content_elements = drawer_elements[0].find_elements(By.CSS_SELECTOR, '[slot="content"]')
                        content = content_elements[0].text.strip() if content_elements else ''
                    else:
                        content = ''
                    
                    if not content or len(content) < 3:
                        continue
                    
                    review_data = {
                        'date': date,
                        'rating': rating,
                        'content': content
                    }
                    
                    if review_data not in self.reviews:
                        self.reviews.append(review_data)
                        
                except (NoSuchElementException, Exception):
                    continue
                    
        except Exception:
            pass
    
    def _format_date(self, date_str: str) -> str:
        try:
            date_str = date_str.strip()
            
            if '-' in date_str and len(date_str.split('-')) == 3:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date_obj = datetime.strptime(date_str, '%b %d, %Y')
            
            return date_obj.strftime('%Y.%m.%d')
            
        except Exception:
            return date_str
    
    def _click_load_more(self) -> bool:
        try:
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
            
        except Exception:
            return False
    
    def save_to_database(self):
        try:
            if not self.reviews:
                return
            
            df = pd.DataFrame(self.reviews)
            os.makedirs(self.output_dir, exist_ok=True)
            
            output_path = os.path.join(self.output_dir, 'reviews_rotten.csv')
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            print(f"Successfully saved {len(self.reviews)} reviews to {output_path}")
            
        except Exception as e:
            raise