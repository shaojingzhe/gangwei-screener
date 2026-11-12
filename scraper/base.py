"""爬虫基类：提供UA轮换、重试、延迟、日志等通用能力"""

import hashlib
import logging
import random
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("scraper")


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]


class BaseScraper(ABC):
    name: str = "base"

    def __init__(self):
        self.session = requests.Session()
        self._rotate_ua()

    def _rotate_ua(self):
        ua = random.choice(USER_AGENTS)
        self.session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
        })

    def _delay(self):
        t = random.uniform(2, 6)
        logger.debug(f"[{self.name}] 延迟 {t:.1f}s")
        time.sleep(t)

    def fetch_html(self, url: str, retries: int = 3) -> Optional[str]:
        """GET 请求获取 HTML，支持重试"""
        for attempt in range(retries):
            try:
                self._rotate_ua()
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                resp.encoding = resp.apparent_encoding or "utf-8"
                return resp.text
            except requests.RequestException as e:
                logger.warning(f"[{self.name}] 请求失败 (第{attempt+1}次): {url[:80]} — {e}")
                if attempt < retries - 1:
                    time.sleep(3 * (attempt + 1))
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def make_hash(url: str) -> str:
        return hashlib.md5(url.strip().encode()).hexdigest()

    @staticmethod
    def today_str() -> str:
        return datetime.now().strftime("%Y-%m-%d")

    @abstractmethod
    def scrape(self) -> List[dict]:
        """返回岗位列表 [{url_hash, title, company, ...}]"""
        ...

    def run(self):
        """完整流程：爬取 -> 返回结果（由 manager 负责入库）"""
        logger.info(f"[{self.name}] 开始爬取...")
        jobs = self.scrape()
        logger.info(f"[{self.name}] 获取到 {len(jobs)} 个岗位")
        return jobs
