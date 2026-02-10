import asyncio
import logging
import random
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import aiohttp
from parsel import Selector

from src.crud import create_car
from src.config import BASE_URL
from src.utils import clean_price, clean_odometer



logger = logging.getLogger(__name__)

CONCURRENT_WORKERS = 3
MAX_PAGES = 5

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}


# def get_phone_number(driver: webdriver.Chrome) -> int:
#     """Знаходить кнопку телефону в сайдбарі (#side) і клікає через JS."""
#     try:
#         wait = WebDriverWait(driver, 5)
#
#         phone_btn = wait.until(EC.presence_of_element_located((
#             By.CSS_SELECTOR,
#             "#side button.size-large.conversion"
#         )))
#         driver.execute_script("arguments[0].click();", phone_btn)
#         time.sleep(2.0)
#         phone_elements = driver.find_elements(By.CSS_SELECTOR,
#              "a[href^='tel:'], #side a[href^='tel:'], #side button span, .popup-show-phone a")
#
#         for elem in phone_elements:
#             text = elem.text.strip()
#             clean_digits = ''.join(filter(str.isdigit, text))
#
#             if len(clean_digits) >= 10:
#                 return int(clean_digits)
#
#         return 0
#
#     except Exception as e:
#         logger.error(f"Phone error: {e}")
#         return 0



async def fetch_html(session: aiohttp.ClientSession, url: str) -> Optional[str]:
    """
        Fetches the raw HTML content of a URL asynchronously.

        Includes a random delay to simulate human behavior and avoid rate limiting.

        Args:
            session (aiohttp.ClientSession): The active HTTP session.
            url (str): The target URL to fetch.

        Returns:
            Optional[str]: The HTML content as a string, or None if the request fails.
        """
    try:
        await asyncio.sleep(random.uniform(0.5, 1.5))
        async with session.get(url, headers=HEADERS) as response:
            if response.status == 200:
                return await response.text()
            else:
                logger.error(f"Failed to fetch {url}: Status {response.status}")
                return None
    except Exception as e:
        logger.error(f"Error fetching {url}: {e}")
        return None


def parse_car_data(html: str, url: str) -> Optional[Dict[str, Any]]:
    """
        Parses the raw HTML of a single car page to extract structured data.

        Uses `parsel` with CSS selectors, XPath, and Regex to handle
        various layout versions of Auto.ria.

        Args:
            html (str): The raw HTML content of the page.
            url (str): The URL of the page (for reference).

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing car details,
            or None if critical errors occur during parsing.
        """
    try:
        sel = Selector(text=html)

        # 1. title
        title = sel.css("h1.head::text").get() or sel.css("h1.titleL::text").get()
        title = title.strip() if title else "No Title"

        # 2. price
        price_text = sel.css("div.price_value strong::text, #basicInfoPrice strong::text").get()
        price_usd = clean_price(price_text)

        # 3. odometer
        odometer_text = sel.re_first(r"\d{1,3}[\s\xa0]?\d{3}\s*тис\.\s*км") or \
                        sel.re_first(r"\d+\s*тис\.\s*км")

        if not odometer_text:
            odometer_text = sel.xpath("//*[contains(text(), 'тис. км')]/text()").get()

        odometer = clean_odometer(odometer_text)

        # 4. username
        username = sel.css("#sellerInfoUserName span::text").get() or \
                   sel.css(".seller_info .seller_name::text").get()
        username = username.strip() if username else "Unknown"

        # 5. VIN
        car_vin = sel.css(
            "#badgesVin span::text, " 
            "#badgesVin::text, "
            ".label-vin::text, "
            ".vin-code::text, "
            "span[class*='vin-code']::text"
        ).get()
        car_vin = car_vin.strip() if car_vin else None

        # 6. car_number
        car_number = sel.css(
            ".state-num::text, " 
            ".car-number span::text, " 
            ".car-number::text"
        ).get()
        car_number = car_number.strip() if car_number else None

        # 7. image_url
        image_url = sel.css("meta[property='og:image']::attr(content)").get()

        if not image_url:
            image_url = sel.css(
                "#photoSlider picture img::attr(src), .photo-620x465 img::attr(src)"
            ).get()

        # 8. images_count
        images_count = len(sel.css("#photoSlider .carousel__slide"))

        # phone
        # NOTE: Phone numbers are hidden behind a dynamic AJAX request (POST /popUp/).
        # Getting them requires browser automation (Playwright), which slows down scraping
        # significantly. For this version, we set it to 0.
        phone_number = 0

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
        logger.error(f"Parsing error on {url}: {e}")
        return None


# --- Main logic (PRODUCER - CONSUMER) ---

async def producer(queue: asyncio.Queue, session: aiohttp.ClientSession):
    """
        Producer function: Iterates through pagination pages and collects car URLs.

        It fetches the list page, extracts links to individual car pages,
        and puts them into the asyncio Queue for consumers to process.

        Args:
            queue (asyncio.Queue): The shared work queue.
            session (aiohttp.ClientSession): The HTTP session.
        """
    logger.info("--- Producer started ---")

    for page in range(1, MAX_PAGES + 1):
        list_url = f"{BASE_URL}?page={page}"
        logger.info(f"[Producer] Reading Page {page}...")

        html = await fetch_html(session, list_url)

        if not html:
            logger.warning(f"[Producer] Page {page} is empty or failed.")
            continue

        sel = Selector(text=html)
        links = sel.css(".ticket-item .m-link-ticket::attr(href)").getall()

        if not links:
            logger.info("[Producer] No more cars found. Stopping.")
            break

        count = 0
        for link in links:
            if "javascript" not in link and "/newauto/" not in link:
                full_url = urljoin(BASE_URL, link)
                await queue.put(full_url)
                count += 1

        logger.info(f"[Producer] +{count} cars added to queue.")

    logger.info("--- Producer finished. No more pages. ---")


async def consumer(worker_id: int, queue: asyncio.Queue, session: aiohttp.ClientSession):
    """
        Consumer (Worker) function: Processes URLs from the queue.

        1. Gets a URL from the queue.
        2. Fetches the HTML.
        3. Parses the data.
        4. Saves it to the database.

        Args:
            worker_id (int): ID of the worker for logging purposes.
            queue (asyncio.Queue): The shared work queue.
            session (aiohttp.ClientSession): The HTTP session.
        """
    logger.info(f"Worker {worker_id} ready.")

    while True:
        url = await queue.get()

        if url is None:
            queue.task_done()
            break

        try:
            html = await fetch_html(session, url)

            if html:
                car_data = parse_car_data(html, url)
                if car_data:
                    await create_car(car_data)
                    logger.info(f"[Worker {worker_id}] Saved: {car_data['title']}")

        except Exception as e:
            logger.error(f"[Worker {worker_id}] Error: {e}")

        finally:
            queue.task_done()

    logger.info(f"Worker {worker_id} going home.")


async def run_scraper():
    """
        Main orchestrator function.

        1. Initializes the Queue and HTTP Session.
        2. Spawns Consumer workers (background tasks).
        3. Runs the Producer to fill the queue.
        4. Waits for the queue to be empty.
        5. Sends stop signals to workers.
        """
    queue = asyncio.Queue()

    async with aiohttp.ClientSession() as session:
        consumers = [asyncio.create_task(consumer(i, queue, session)) for i in range(CONCURRENT_WORKERS)]

        await producer(queue, session)

        await queue.join()

        for _ in range(CONCURRENT_WORKERS):
            await queue.put(None)

        logger.info("Waiting for workers to finish...")

        done, pending = await asyncio.wait(consumers, return_when=asyncio.ALL_COMPLETED)

        for task in done:
            if task.exception():
                logger.error(f"One worker failed with error: {task.exception()}")



    logger.info("All scraping finished successfully.")


# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     asyncio.run(run_scraper())
