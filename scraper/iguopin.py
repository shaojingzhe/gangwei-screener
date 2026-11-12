"""国资央企招聘平台 iguopin.com 爬虫"""

import json
import re
import logging
from typing import List, Optional

import requests

from .base import BaseScraper

logger = logging.getLogger("scraper.iguopin")

BASE_URL = "https://iguopin.com"
SEARCH_URL = "https://iguopin.com/api/job/list"


class IguoPinScraper(BaseScraper):
    name = "iguopin"

    def _try_api(self, page: int = 1, keyword: str = "") -> List[dict]:
        """尝试通过API接口获取岗位列表"""
        jobs = []
        try:
            self._rotate_ua()
            resp = self.session.post(
                SEARCH_URL,
                json={
                    "page": page,
                    "size": 20,
                    "keyword": keyword or "",
                    "jobType": "",
                    "cityCode": "",
                    "companyNature": "",
                },
                timeout=20,
                headers={
                    "Content-Type": "application/json",
                    "Referer": "https://iguopin.com/job",
                },
            )
            if resp.status_code != 200:
                logger.warning(f"[iguopin] API 返回 {resp.status_code}")
                return jobs

            data = resp.json()
            items = data.get("data", {}).get("list", []) or data.get("data", {}).get("records", []) or data.get("data", [])

            if isinstance(items, list):
                for item in items:
                    job = self._parse_api_item(item)
                    if job:
                        jobs.append(job)
        except (requests.RequestException, json.JSONDecodeError, ValueError) as e:
            logger.warning(f"[iguopin] API 请求异常: {e}")
        return jobs

    def _parse_api_item(self, item: dict) -> Optional[dict]:
        title = item.get("jobName") or item.get("name") or item.get("title", "")
        company = item.get("companyName") or item.get("company", "")
        if not title or not company:
            return None

        job_id = item.get("id") or item.get("jobId", "")
        detail_url = item.get("jobDetailUrl") or f"https://iguopin.com/job/detail?id={job_id}"

        return {
            "url_hash": self.make_hash(detail_url),
            "title": title.strip(),
            "company": company.strip(),
            "company_type": "央国企",
            "city": item.get("cityName") or item.get("city", ""),
            "salary": item.get("salaryDesc") or item.get("salary", ""),
            "description": item.get("jobDescription") or item.get("description", ""),
            "requirements": item.get("jobRequire") or item.get("qualification", ""),
            "apply_url": detail_url,
            "source": "iguopin.com",
            "publish_date": item.get("publishDate") or item.get("createTime", self.today_str()),
        }

    def _try_html_fallback(self) -> List[dict]:
        """API不可用时的HTML兜底方案"""
        jobs = []
        for keyword in ["校招", "应届", "管培", "运营", "市场", "项目"]:
            self._delay()
            html = self.fetch_html(f"https://iguopin.com/job?keyword={keyword}")
            if not html:
                continue
            soup = self.parse_html(html)

            cards = soup.select(".job-card, .job-item, .position-item, li.job")
            for card in cards[:10]:
                try:
                    title_el = card.select_one("a.title, h3 a, .job-name a, .name a")
                    company_el = card.select_one(".company, .company-name, .corp-name")
                    city_el = card.select_one(".city, .location, .workplace")
                    salary_el = card.select_one(".salary, .pay, .money")

                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    if href and not href.startswith("http"):
                        href = BASE_URL + href

                    jobs.append({
                        "url_hash": self.make_hash(href),
                        "title": title,
                        "company": company_el.get_text(strip=True) if company_el else "",
                        "company_type": "央国企",
                        "city": city_el.get_text(strip=True) if city_el else "",
                        "salary": salary_el.get_text(strip=True) if salary_el else "",
                        "apply_url": href,
                        "source": "iguopin.com",
                        "publish_date": self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[iguopin] 卡片解析失败: {e}")
                    continue

            if jobs:
                break
        return jobs

    def scrape(self) -> List[dict]:
        jobs = []
        # 多关键词、多页爬取
        keywords = ["校招", "应届", "管培", "运营", "市场", "项目管理"]
        for kw in keywords:
            for page in range(1, 4):
                self._delay()
                page_jobs = self._try_api(page=page, keyword=kw)
                if not page_jobs:
                    break
                jobs.extend(page_jobs)
                if len(page_jobs) < 20:
                    break

        if not jobs:
            logger.info("[iguopin] API 无结果，尝试HTML解析...")
            jobs = self._try_html_fallback()

        # 去重
        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
