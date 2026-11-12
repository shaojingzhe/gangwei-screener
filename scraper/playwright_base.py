"""基于 Playwright 的爬虫基类（用于JS渲染页面）"""

import hashlib
import logging
import random
import time
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger("scraper.playwright")


class PlaywrightScraper(ABC):
    name: str = "playwright_base"

    def _delay(self, min_s: float = 2, max_s: float = 6):
        t = random.uniform(min_s, max_s)
        logger.debug(f"[{self.name}] 延迟 {t:.1f}s")
        time.sleep(t)

    @staticmethod
    def make_hash(url: str) -> str:
        return hashlib.md5(url.strip().encode()).hexdigest()

    @staticmethod
    def today_str() -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

    def _launch_browser(self):
        """启动 Playwright 浏览器（每次爬取后关闭）"""
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=True)
        self._page = self._browser.new_page()
        self._page.set_default_timeout(30000)

    def _close_browser(self):
        if hasattr(self, "_browser") and self._browser:
            self._browser.close()
        if hasattr(self, "_pw") and self._pw:
            self._pw.stop()

    def fetch_rendered_html(self, url: str, wait_selector: str = "body", retries: int = 2) -> str:
        """使用 Playwright 获取 JS 渲染后的 HTML"""
        for attempt in range(retries):
            try:
                self._page.goto(url, wait_until="networkidle")
                self._page.wait_for_selector(wait_selector, timeout=15000)
                self._delay(1, 3)
                return self._page.content()
            except Exception as e:
                logger.warning(f"[{self.name}] Playwright 获取失败 (第{attempt+1}次): {url[:80]} — {e}")
                if attempt < retries - 1:
                    self._delay(3, 5)
        return ""

    @abstractmethod
    def scrape(self) -> List[dict]:
        ...

    def run(self) -> List[dict]:
        logger.info(f"[{self.name}] 开始爬取(Playwright)...")
        try:
            self._launch_browser()
            jobs = self.scrape()
            logger.info(f"[{self.name}] 获取到 {len(jobs)} 个岗位")
            return jobs
        except Exception as e:
            logger.error(f"[{self.name}] 爬取异常: {e}", exc_info=True)
            return []
        finally:
            self._close_browser()
