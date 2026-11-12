#!/usr/bin/env python3
"""手动运行爬虫脚本"""

import logging
import os
import sys

# 确保项目根目录在 path 中
PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)

# 配置日志
os.makedirs(os.path.join(PROJECT_ROOT, "data"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(PROJECT_ROOT, "data", "scraper.log"), encoding="utf-8"
        ),
    ],
)


def main():
    from storage.database import init_db, get_stats
    from scraper.manager import ScraperManager

    print("=" * 50)
    print("  PasteFlow 岗位爬虫")
    print("=" * 50)

    # 初始化数据库
    init_db()
    before = get_stats()
    print(f"\n爬取前有效岗位数: {before['total']}")

    # 运行所有爬虫
    manager = ScraperManager()
    new, skipped = manager.run_all()

    # 统计结果
    after = get_stats()
    print(f"\n{'=' * 50}")
    print(f"  新增: {new}  跳过(重复): {skipped}")
    print(f"  爬取后有效岗位总数: {after['total']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
