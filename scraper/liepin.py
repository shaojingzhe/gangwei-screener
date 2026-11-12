"""猎聘 liepin.com 社招爬虫"""

import logging
from typing import List

from bs4 import BeautifulSoup
from .playwright_base import PlaywrightScraper

logger = logging.getLogger("scraper.liepin")

BASE_URL = "https://www.liepin.com"


class LiePinScraper(PlaywrightScraper):
    name = "liepin"

    def scrape(self) -> List[dict]:
        jobs = []
        # 搜索初级岗位：经验不限/应届/1年以下 + 目标岗位
        keywords = [
            "运营 应届",
            "市场营销 应届",
            "项目管理 应届",
            "品牌 应届",
            "新媒体 应届",
            "产品运营 1年以下",
            "数据分析 应届",
        ]

        for kw in keywords:
            self._delay(5, 10)
            url = f"https://www.liepin.com/zhaopin/?key={kw}"
            html = self.fetch_rendered_html(url, wait_selector=".job-list-box, .job-list, .result-list")
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")
            cards = soup.select(".job-list-item, .job-card, .result-job-item, li")
            for card in cards[:15]:
                try:
                    title_el = card.select_one(".job-title, .title, .name, h3 a, .job-name")
                    if not title_el:
                        title_el = card.find("a")
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if not href or "job" not in href.lower():
                        continue
                    if not href.startswith("http"):
                        href = BASE_URL + href if href.startswith("/") else f"{BASE_URL}/{href}"

                    company_el = card.select_one(".company-name, .company, .corp-name")
                    city_el = card.select_one(".area, .city, .location, .workplace")
                    salary_el = card.select_one(".salary, .pay, .money")
                    exp_el = card.select_one(".experience, .exp, .require")
                    date_el = card.select_one(".time, .date, .publish-time")

                    requirements = ""
                    if exp_el:
                        requirements = exp_el.get_text(strip=True)

                    jobs.append({
                        "url_hash": self.make_hash(href),
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "company_type": "其他",
                        "city": city_el.get_text(strip=True) if city_el else "",
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "description": "",
                        "requirements": requirements,
                        "apply_url": href,
                        "source": "liepin.com",
                        "publish_date": date_el.get_text(strip=True) if date_el else self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[liepin] 解析异常: {e}")

        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
