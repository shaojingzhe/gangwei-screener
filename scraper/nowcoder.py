"""牛客网 nowcoder.com 校招爬虫"""

import logging
from typing import List

from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper

logger = logging.getLogger("scraper.nowcoder")

BASE_URL = "https://www.nowcoder.com"


class NowCoderScraper(PlaywrightScraper):
    name = "nowcoder"

    def scrape(self) -> List[dict]:
        jobs = []
        # 牛客网校招+社招板块
        urls = [
            "https://www.nowcoder.com/jobs/school",
            "https://www.nowcoder.com/jobs/social",
        ]

        for url in urls:
            self._delay(3, 8)
            html = self.fetch_rendered_html(url, wait_selector=".job-list, .job-item, .recruit-list")
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".job-item, .recruit-item, .list-item, li")
            for card in cards[:20]:
                try:
                    title_el = card.select_one("a.job-title, .title a, .name a, h4 a")
                    if not title_el:
                        title_el = card.find("a")
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"

                    company_el = card.select_one(".company, .corp-name, .company-name")
                    city_el = card.select_one(".city, .location, .work-addr")
                    salary_el = card.select_one(".salary, .pay, .money-tag")
                    date_el = card.select_one(".date, .time, .update-time")

                    jobs.append({
                        "url_hash": self.make_hash(href),
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "company_type": "其他",
                        "city": city_el.get_text(strip=True) if city_el else "",
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "apply_url": href,
                        "source": "nowcoder.com",
                        "publish_date": date_el.get_text(strip=True) if date_el else self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[nowcoder] 解析异常: {e}")

        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
