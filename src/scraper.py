import time
import random
import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

from src.crud import create_car
from src.config import BASE_URL
from src.utils import clean_price, clean_odometer


logger = logging.getLogger(__name__)


# Driver settings
def get_driver() -> webdriver.Chrome:
    """Creates a driver with settings so that the site does not see that it is a bot."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    driver.maximize_window()
    return driver


def get_phone_number(driver: webdriver.Chrome) -> int:
    """Знаходить кнопку телефону в сайдбарі (#side) і клікає через JS."""
    try:
        wait = WebDriverWait(driver, 5)

        phone_btn = wait.until(EC.presence_of_element_located((
            By.CSS_SELECTOR,
            "#side button.size-large.conversion"
        )))
        driver.execute_script("arguments[0].click();", phone_btn)
        time.sleep(2.0)
        phone_elements = driver.find_elements(By.CSS_SELECTOR,
             "a[href^='tel:'], #side a[href^='tel:'], #side button span, .popup-show-phone a")

        for elem in phone_elements:
            text = elem.text.strip()
            clean_digits = ''.join(filter(str.isdigit, text))

            if len(clean_digits) >= 10:
                return int(clean_digits)

        return 0

    except Exception as e:
        logger.error(f"Phone error: {e}")
        return 0


def parse_single_car(driver: webdriver.Chrome, url: str) -> Optional[Dict[str, Any]]:
    """Goes to the car page and collects all the details."""
    try:
        driver.get(url)
        time.sleep(random.uniform(1, 2))  # User delay

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # TITLE
        title_tag = soup.select_one("h1.head, h1.titleL, #heading-cars .head")
        title = title_tag.text.strip() if title_tag else "No Title"

        # PRICE
        price_tag = soup.select_one("div.price_value strong, #basicInfoPrice strong")
        price_usd = clean_price(price_tag.text) if price_tag else 0

        # ODOMETER
        odometer_tag = soup.find(
            lambda tag: tag.name in ["span", "div"] and tag.text and "тис. км" in tag.text and len(tag.text) < 50)
        odometer = clean_odometer(odometer_tag.text) if odometer_tag else 0

        # USERNAME
        username_tag = soup.select_one("#sellerInfoUserName span, .seller_info .seller_name, .seller_info_name")
        username = username_tag.text.strip() if username_tag else "Unknown"

        # VIN CODE
        vin_tag = soup.select_one("#badgesVin, .label-vin, .vin-code, span[class*='vin-code']")
        car_vin = vin_tag.text.strip() if vin_tag else None

        # CAR NUMBER
        number_tag = soup.select_one(".state-num, .car-number span, .car-number")
        car_number = number_tag.text.strip() if number_tag else None

        # IMAGE URL
        image_tag = soup.select_one(
            "#photoSlider picture img, "  # Новий дизайн (Nissan, Audi)
            "#photoSlider img, "  # Звичайний дизайн
            "img.outline, "  # Старий дизайн
            ".gallery-order-carousel img, "
            ".photo-620x465 img"
        )
        image_url = image_tag.get('src') if image_tag else None

        # IMAGES COUNT
        images_count = 0

        # 1.
        count_badge = soup.select_one("span.common-badge.alpha.medium")
        if count_badge:
            text = count_badge.get_text(strip=True)
            if "з" in text:
                try:
                    parts = text.split("з")
                    images_count = int(''.join(filter(str.isdigit, parts[-1])))
                except ValueError:
                    pass

        # 2.
        if images_count == 0:
            link_tag = soup.select_one("a.show-all, a.link-look-all")
            if link_tag:
                images_count = int(''.join(filter(str.isdigit, link_tag.text)))

        # 3.
        if images_count == 0:
            previews = soup.select(".gallery-order-carousel .m-hide, #photoSlider .carousel__slide")
            images_count = len(previews) if previews else 0

        phone_number = get_phone_number(driver)

        return {
            "url": url,
            "title": title,
            "price_usd": price_usd,
            "odometer": odometer,
            "username": username,
            "phone_number": phone_number,
            "image_url": image_url,
            "images_count": images_count,
            "car_number": car_number,
            "car_vin": car_vin,
        }

    except Exception as e:
        logger.error(f"Error parsing car {url}: {e}")
        return None


def run_scraper():
    driver = get_driver()
    page = 1

    try:
        while True:
            logger.info(f"--- Processing Page {page} ---")

            list_url = f"{BASE_URL}?page={page}"
            try:
                driver.get(list_url)
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error loading page {page}: {e}")
                break

            soup = BeautifulSoup(driver.page_source, "html.parser")
            links = soup.select(".ticket-item .m-link-ticket")

            if not links:
                logger.info("No more cars found. Finishing.")
                break

            logger.info(f"Found {len(links)} cars on page {page}")

            for link_tag in links:
                raw_url = link_tag.get('href')

                if not raw_url or "javascript" in raw_url:
                    continue

                if "/newauto/" in raw_url:
                    continue

                car_url = urljoin(BASE_URL, raw_url)

                car_data = parse_single_car(driver, car_url)

                if car_data:
                    create_car(car_data)

            page += 1

    except Exception as e:
        logger.error(f"Global error: {e}")
    finally:
        try:
            driver.quit()
            logger.info("Driver closed successfully.")
        except:
            pass
