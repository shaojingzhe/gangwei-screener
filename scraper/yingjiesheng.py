"""应届生求职网 yingjiesheng.com 爬虫"""

import logging
from typing import List

from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper

logger = logging.getLogger("scraper.yingjiesheng")

BASE_URL = "https://www.yingjiesheng.com"


class YingJieShengScraper(PlaywrightScraper):
    name = "yingjiesheng"

    def scrape(self) -> List[dict]:
        jobs = []
        keywords = ["运营", "市场", "项目管理", "数据分析", "产品", "品牌"]

        for kw in keywords:
            self._delay(3, 8)
            url = f"https://www.yingjiesheng.com/commsearch?keyword={kw}&jobtype=0&city=0"
            html = self.fetch_rendered_html(url, wait_selector=".job-list, .result-list, .comm-list")
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".job-item, .result-item, .comm-item, .list-item, tr")
            for card in cards[:15]:
                try:
                    title_el = (
                        card.select_one("a.title, .job-title a, .name a, td a")
                        or card.find("a")
                    )
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href or "job" not in href.lower():
                        continue
                    if not href.startswith("http"):
                        href = BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"

                    company_el = card.select_one(".company, .corp, .cname, td:nth-child(2)")
                    city_el = card.select_one(".city, .location, .workplace, td:nth-child(3)")
                    date_el = card.select_one(".date, .time, .pub-date, td:nth-child(4)")

                    jobs.append({
                        "url_hash": self.make_hash(href),
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "company_type": "其他",
                        "city": city_el.get_text(strip=True) if city_el else "",
                        "salary": "",
                        "apply_url": href,
                        "source": "yingjiesheng.com",
                        "publish_date": date_el.get_text(strip=True) if date_el else self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[yingjiesheng] 解析异常: {e}")

        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
