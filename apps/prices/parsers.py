from __future__ import annotations

import importlib
import logging
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

DNS_BASE_URL = 'https://www.dns-shop.ru'

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15',
]


@dataclass
class ParsedProduct:
    name: str
    price: int
    url: str
    vendor_code: str = ''
    image_url: str = ''
    old_price: int | None = None


@dataclass
class DNSParser:
    headless: bool = True
    proxy: str | None = None
    max_retries: int = 3
    delay_min: float = 1.0
    delay_max: float = 3.0
    scroll_attempts: int = 8
    page_load_timeout: int = 30
    _driver: Any = field(default=None, init=False, repr=False)
    _uc: Any = field(default=None, init=False, repr=False)
    _by: Any = field(default=None, init=False, repr=False)
    _action_chains: Any = field(default=None, init=False, repr=False)
    _ec: Any = field(default=None, init=False, repr=False)
    _web_driver_wait: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.headless = getattr(settings, 'CHROME_HEADLESS', True)
        self.delay_min = getattr(settings, 'PARSE_DELAY_MIN', 1.0)
        self.delay_max = getattr(settings, 'PARSE_DELAY_MAX', 3.0)
        self.max_retries = getattr(settings, 'PARSE_MAX_RETRIES', 3)
        self._load_selenium_deps()

        proxy_list: list[str] = getattr(settings, 'PROXY_LIST', [])
        if proxy_list:
            self.proxy = random.choice(proxy_list)

    def _load_selenium_deps(self) -> None:
        try:
            self._uc = importlib.import_module('undetected_chromedriver')
            by_module = importlib.import_module('selenium.webdriver.common.by')
            action_module = importlib.import_module('selenium.webdriver.common.action_chains')
            self._ec = importlib.import_module('selenium.webdriver.support.expected_conditions')
            wait_module = importlib.import_module('selenium.webdriver.support.ui')
            self._by = by_module.By
            self._action_chains = action_module.ActionChains
            self._web_driver_wait = wait_module.WebDriverWait
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                'Missing parser dependency. Install selenium and undetected-chromedriver.'
            ) from exc

    def _build_driver(self) -> Any:
        options = self._uc.ChromeOptions()
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={random.choice(USER_AGENTS)}')

        if self.headless:
            options.add_argument('--headless=new')

        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy}')
            logger.info('Используется прокси: %s', self.proxy)

        driver = self._uc.Chrome(options=options)
        driver.set_page_load_timeout(self.page_load_timeout)
        return driver

    def _get_driver(self) -> Any:
        if self._driver is None:
            self._driver = self._build_driver()
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None

    def __enter__(self) -> DNSParser:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _random_delay(self) -> None:
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)

    def parse_category(self, dns_category_slug: str) -> list[ParsedProduct]:
        url = f'{DNS_BASE_URL}/catalog/{dns_category_slug}/'
        logger.info('Парсинг категории: %s', url)

        for attempt in range(1, self.max_retries + 1):
            try:
                return self._do_parse_category(url)
            except Exception:
                logger.exception(
                    'Ошибка парсинга категории (попытка %d/%d): %s',
                    attempt, self.max_retries, url,
                )
                self.close()
                if attempt < self.max_retries:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    logger.info('Повтор через %.1f сек.', backoff)
                    time.sleep(backoff)

        logger.error('Все попытки парсинга категории исчерпаны: %s', url)
        return []

    def _do_parse_category(self, url: str) -> list[ParsedProduct]:
        driver = self._get_driver()
        driver.get(url)

        self._web_driver_wait(driver, 20).until(
            self._ec.presence_of_element_located((self._by.CLASS_NAME, 'catalog-product'))
        )
        self._random_delay()

        self._scroll_to_load_all(driver)

        product_elements = driver.find_elements(self._by.CLASS_NAME, 'catalog-product')
        logger.info('Найдено элементов на странице: %d', len(product_elements))

        seen: dict[str, ParsedProduct] = {}

        for el in product_elements:
            try:
                self._action_chains(driver).move_to_element(el).perform()
                time.sleep(0.15)
                parsed = self._extract_product_from_element(el)
                if parsed and parsed.url not in seen:
                    seen[parsed.url] = parsed
            except Exception:
                logger.debug('Не удалось извлечь товар из элемента', exc_info=True)
                continue

        products = list(seen.values())
        logger.info('Уникальных товаров после парсинга: %d', len(products))
        return products

    def _scroll_to_load_all(self, driver: Any) -> None:
        last_height = driver.execute_script('return document.body.scrollHeight')
        for _ in range(self.scroll_attempts):
            driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
            time.sleep(random.uniform(1.5, 2.5))
            new_height = driver.execute_script('return document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

    def parse_product(self, product_url: str) -> ParsedProduct | None:
        logger.info('Парсинг товара: %s', product_url)

        for attempt in range(1, self.max_retries + 1):
            try:
                return self._do_parse_product(product_url)
            except Exception:
                logger.exception(
                    'Ошибка парсинга товара (попытка %d/%d): %s',
                    attempt, self.max_retries, product_url,
                )
                self.close()
                if attempt < self.max_retries:
                    backoff = 2 ** attempt + random.uniform(0, 1)
                    time.sleep(backoff)

        logger.error('Все попытки парсинга товара исчерпаны: %s', product_url)
        return None

    def _do_parse_product(self, product_url: str) -> ParsedProduct | None:
        driver = self._get_driver()
        driver.get(product_url)
        self._random_delay()

        self._web_driver_wait(driver, 20).until(
            self._ec.presence_of_element_located((self._by.CLASS_NAME, 'product-card-top'))
        )

        name = self._safe_text(driver, 'product-card-top__title')
        if not name:
            return None

        price = self._extract_price(driver, 'product-buy__price')
        if price is None:
            return None

        old_price = self._extract_price(driver, 'product-buy__prev')

        vendor_code = ''
        try:
            vc_el = driver.find_element(self._by.CLASS_NAME, 'product-card-top__code')
            vc_text = vc_el.text.strip()
            match = re.search(r'(\d+)', vc_text)
            if match:
                vendor_code = match.group(1)
        except Exception:
            pass

        image_url = ''
        try:
            img = driver.find_element(self._by.CSS_SELECTOR, '.product-images-slider__main-img img')
            image_url = img.get_attribute('src') or ''
        except Exception:
            pass

        return ParsedProduct(
            name=name,
            price=price,
            url=product_url,
            vendor_code=vendor_code,
            image_url=image_url,
            old_price=old_price,
        )

    def _extract_product_from_element(self, el: Any) -> ParsedProduct | None:
        try:
            name_el = el.find_element(self._by.CLASS_NAME, 'catalog-product__name')
            name = name_el.text.strip()
            link = name_el.get_attribute('href') or ''
        except Exception:
            return None

        if not name or not link:
            return None

        price = self._extract_price_from_element(el, 'product-buy__price')
        if price is None:
            return None

        old_price = self._extract_price_from_element(el, 'product-buy__prev')

        image_url = ''
        try:
            img = el.find_element(self._by.CSS_SELECTOR, '.catalog-product__image img')
            image_url = img.get_attribute('src') or img.get_attribute('data-src') or ''
        except Exception:
            pass

        vendor_code = ''
        try:
            code_el = el.find_element(self._by.CLASS_NAME, 'catalog-product__code')
            match = re.search(r'(\d+)', code_el.text)
            if match:
                vendor_code = match.group(1)
        except Exception:
            pass

        return ParsedProduct(
            name=name,
            price=price,
            url=link,
            vendor_code=vendor_code,
            image_url=image_url,
            old_price=old_price,
        )

    @staticmethod
    def _extract_price(driver: Any, class_name: str) -> int | None:
        try:
            by = importlib.import_module('selenium.webdriver.common.by').By
            el = driver.find_element(by.CLASS_NAME, class_name)
            return DNSParser._clean_price(el.get_attribute('textContent'))
        except Exception:
            return None

    @staticmethod
    def _extract_price_from_element(parent: Any, class_name: str) -> int | None:
        try:
            by = importlib.import_module('selenium.webdriver.common.by').By
            el = parent.find_element(by.CLASS_NAME, class_name)
            return DNSParser._clean_price(el.get_attribute('textContent'))
        except Exception:
            return None

    @staticmethod
    def _clean_price(raw: str) -> int | None:
        cleaned = raw.split('₽')[0].strip()
        cleaned = re.sub(r'\s+', '', cleaned)
        cleaned = re.sub(r'[^\d]', '', cleaned)
        if cleaned.isdigit():
            return int(cleaned)
        return None

    @staticmethod
    def _safe_text(driver: Any, class_name: str) -> str:
        try:
            by = importlib.import_module('selenium.webdriver.common.by').By
            el = driver.find_element(by.CLASS_NAME, class_name)
            return el.text.strip()
        except Exception:
            return ''
