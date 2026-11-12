"""国家24365大学生就业服务平台 爬虫"""

import json
import logging
from typing import List, Optional

from .base import BaseScraper

logger = logging.getLogger("scraper.24365")

# 24365 平台的API接口
API_URL = "https://job.ncss.cn/api/job/search"
BASE_URL = "https://job.ncss.cn"


class Job24365Scraper(BaseScraper):
    name = "24365"

    def _try_api(self, page: int = 1, keyword: str = "") -> List[dict]:
        """通过API获取岗位"""
        jobs = []
        try:
            self._rotate_ua()
            resp = self.session.get(
                API_URL,
                params={
                    "keyword": keyword,
                    "page_index": page,
                    "page_size": 20,
                    "order_by": "publish_time",
                },
                timeout=20,
                headers={"Referer": "https://job.ncss.cn/student/jobs/index.html"},
            )
            if resp.status_code != 200:
                logger.warning(f"[24365] API 返回 {resp.status_code}")
                return jobs

            data = resp.json()
            items = (
                data.get("data", {}).get("list", [])
                or data.get("data", {}).get("records", [])
                or data.get("data", [])
            )

            for item in items:
                job = self._parse_item(item)
                if job:
                    jobs.append(job)
        except Exception as e:
            logger.warning(f"[24365] API 请求异常: {e}")
        return jobs

    def _parse_item(self, item: dict) -> Optional[dict]:
        title = (
            item.get("jobName")
            or item.get("job_title")
            or item.get("name")
            or item.get("title", "")
        )
        company = item.get("companyName") or item.get("company_name") or item.get("company", "")
        if not title or not company:
            return None

        job_id = item.get("id") or item.get("jobId") or item.get("job_id", "")
        apply_url = item.get("url") or f"{BASE_URL}/student/jobs/detail/{job_id}"

        return {
            "url_hash": self.make_hash(apply_url),
            "title": title.strip(),
            "company": company.strip(),
            "company_type": self._classify_company_type(company),
            "city": item.get("cityName") or item.get("city", "") or item.get("workPlace", ""),
            "salary": item.get("salaryDesc") or item.get("salary", "") or item.get("salaryDesc", ""),
            "description": item.get("jobDesc") or item.get("description", ""),
            "requirements": item.get("jobRequire") or item.get("qualification", ""),
            "apply_url": apply_url,
            "source": "24365.smartedu.cn",
            "publish_date": item.get("publishTime") or item.get("publishDate", self.today_str()),
        }

    def _classify_company_type(self, company: str) -> str:
        """根据公司名称判断企业类型"""
        state_keywords = ["集团", "中国", "国家", "央企", "国资", "中建", "中铁", "中交", "中航", "中核", "电网", "石油", "石化", "烟草", "华能", "华电", "大唐", "国电", "中粮", "中化", "中国移动", "中国联通", "中国电信"]
        foreign_keywords = ["外资", "外商", "有限公司", "中国区"]
        # 简单的字符串匹配
        for kw in state_keywords:
            if kw in company:
                return "央国企"
        return "其他"

    def _try_html_fallback(self) -> List[dict]:
        """HTML 兜底"""
        jobs = []
        for keyword in ["运营", "市场营销", "项目管理", "数据分析"]:
            self._delay()
            html = self.fetch_html(
                f"https://job.ncss.cn/student/jobs/index.html?keyword={keyword}"
            )
            if not html:
                continue
            soup = self.parse_html(html)

            cards = soup.select(".job-item, .job-card, .list-item")
            for card in cards[:10]:
                try:
                    title_el = card.select_one("a.job-name, .title a, h4 a")
                    company_el = card.select_one(".company, .company-name")
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
                        "company_type": self._classify_company_type(company_el.get_text(strip=True) if company_el else ""),
                        "city": "",
                        "salary": "",
                        "apply_url": href,
                        "source": "24365.smartedu.cn",
                        "publish_date": self.today_str(),
                    })
                except Exception as e:
                    logger.debug(f"[24365] 卡片解析失败: {e}")
            if jobs:
                break
        return jobs

    def scrape(self) -> List[dict]:
        jobs = []
        keywords = ["运营", "市场营销", "项目管理", "数据分析", "产品", "品牌", "新媒体", "校招", "管培"]
        for kw in keywords:
            for page in range(1, 3):
                self._delay()
                page_jobs = self._try_api(page=page, keyword=kw)
                if not page_jobs:
                    break
                jobs.extend(page_jobs)

        if not jobs:
            logger.info("[24365] API 无结果，尝试HTML解析...")
            jobs = self._try_html_fallback()

        seen = set()
        unique = []
        for j in jobs:
            if j["url_hash"] not in seen:
                seen.add(j["url_hash"])
                unique.append(j)
        return unique
