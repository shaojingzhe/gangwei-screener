"""爬虫调度管理器：汇总所有数据源的爬取结果并入库"""

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from .base import logger as base_logger
from .iguopin import IguoPinScraper
from .job_24365 import Job24365Scraper
from .yingjiesheng import YingJieShengScraper
from .nowcoder import NowCoderScraper
from .liepin import LiePinScraper
from .lagou import LaGouScraper
from storage.database import insert_job, job_exists

logger = logging.getLogger("scraper.manager")


class ScraperManager:
    def __init__(self):
        # 轻量爬虫（requests，先跑）
        self.light_scrapers = [
            IguoPinScraper(),
            Job24365Scraper(),
        ]
        # 重量爬虫（Playwright，按需启用）
        self.heavy_scrapers = [
            YingJieShengScraper(),
            NowCoderScraper(),
            LiePinScraper(),
            LaGouScraper(),
        ]

    @property
    def scrapers(self):
        return self.light_scrapers + self.heavy_scrapers

    def run_all(self):
        """运行所有爬虫，去重后入库"""
        total_new = 0
        total_skipped = 0

        for scraper in self.scrapers:
            try:
                jobs = scraper.run()
                new = 0
                for job in jobs:
                    if not job.get("url_hash") or not job.get("title"):
                        continue
                    # 补全空字段
                    job.setdefault("company_type", "其他")
                    job.setdefault("city", "")
                    job.setdefault("salary", "")
                    job.setdefault("description", "")
                    job.setdefault("requirements", "")
                    job.setdefault("apply_url", "")
                    job.setdefault("publish_date", scraper.today_str())

                    if job_exists(job["url_hash"]):
                        total_skipped += 1
                        continue

                    job_id = insert_job(job)
                    if job_id is not None:
                        new += 1
                logger.info(f"[{scraper.name}] 新增 {new}, 跳过 {len(jobs) - new}")
                total_new += new
            except Exception as e:
                logger.error(f"[{scraper.name}] 爬取异常: {e}", exc_info=True)

        # 对新入库岗位进行打分和建议生成
        if total_new > 0:
            self._score_new_jobs()

        logger.info(f"总计: 新增 {total_new} 个岗位, 跳过 {total_skipped} 个重复")
        return total_new, total_skipped

    def _score_new_jobs(self):
        """对新入库的未评分岗位进行匹配打分"""
        try:
            from analyzer.resume_parser import build_profile
            from analyzer.prioritizer import batch_score_and_advise
            from storage.database import get_jobs, update_job_score, update_job_status

            profile = build_profile()
            unscored = get_jobs(filters={"status": "新岗位"}, order_by="created_at DESC", limit=200)
            # 过滤掉已评分的（advice非空表示已评分）
            unscored = [j for j in unscored if not j.get("advice", "")]
            if not unscored:
                return

            batch_score_and_advise(profile, unscored)
            for job in unscored:
                update_job_score(job["id"], job["score"], job["priority_level"])
                import sqlite3
                import os
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs.db")
                conn = sqlite3.connect(db_path)
                conn.execute(
                    "UPDATE jobs SET advice = ?, company_type = ?, difficulty = ?, difficulty_label = ? WHERE id = ?",
                    (job.get("advice", ""), job.get("company_type", "其他"),
                     job.get("difficulty", 50), job.get("difficulty_label", "适中"), job["id"]))
                conn.commit()
                conn.close()
            logger.info(f"已为 {len(unscored)} 个岗位打分并生成建议")
        except Exception as e:
            logger.error(f"打分失败: {e}", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    manager = ScraperManager()
    manager.run_all()
