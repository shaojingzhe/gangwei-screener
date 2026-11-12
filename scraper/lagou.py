"""拉勾 lagou.com 互联网社招爬虫"""

import logging
from typing import List

from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper

logger = logging.getLogger("scraper.lagou")

BASE_URL = "https://www.lagou.com"


class LaGouScraper(PlaywrightScraper):
    name = "lagou"

    def scrape(self) -> List[dict]:
        jobs = []
        keywords = [
            "运营",
            "市场",
            "项目管理",
            "数据分析",
            "新媒体",
            "品牌",
            "产品",
        ]

        for kw in keywords:
            self._delay(4, 8)
            url = f"https://www.lagou.com/wn/jobs?kd={kw}&px=default&city=全国"
            html = self.fetch_rendered_html(url, wait_selector=".job-list, .s_position_list, .item-list")
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".job-item, .s_position_item, .list-item, li")
            for card in cards[:15]:
                try:
                    title_el = card.select_one(".position-name, .p_top a, .job-name, h3 a")
                    if not title_el:
                        title_el = card.find("a", class_=lambda c: c and "position" in c if c else False)
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href:
                        continue
                    if not href.startswith("http"):
                        href = BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"

                    company_el = card.select_one(".company-name, .company, .corp-name")
                    city_el = card.select_one(".add, .city, .location")
                    salary_el = card.select_one(".money, .salary, .pay")
                    exp_el = card.select_one(".li_b_l, .experience, .require")
                    date_el = card.select_one(".format-time, .time, .date")

                    requirements = ""
                    if exp_el:
                        requirements = exp_el.get_text(strip=True)

                    jobs.append({
                        "url_hash": self.make_hash(href),
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "company_type": "民企",
                        "city": city_el.get_text(strip=True) if city_el else "",
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "description": "",
                        "requirements": requirements,
                        "apply_url": href,
                        "source": "lagou.com",
                        "publish_date": date_el.get_text(strip=True) if date_el else self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[lagou] 解析异常: {e}")

        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
