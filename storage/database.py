"""SQLite 数据库操作"""

import sqlite3
import os
from typing import Optional, List, Union
from .models import JOBS_TABLE_SCHEMA, CONFIG_TABLE_SCHEMA, CREATE_INDEXES

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "jobs.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.execute(JOBS_TABLE_SCHEMA)
    conn.execute(CONFIG_TABLE_SCHEMA)
    for idx_sql in CREATE_INDEXES:
        conn.execute(idx_sql)
    conn.commit()
    conn.close()


def insert_job(job: dict) -> Optional[int]:
    """插入新岗位，返回 id；如已存在（url_hash 重复）则返回 None"""
    conn = get_conn()
    try:
        cursor = conn.execute(
            """INSERT INTO jobs (url_hash, title, company, company_type, city, salary,
               description, requirements, apply_url, source, publish_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job["url_hash"],
                job.get("title", ""),
                job.get("company", ""),
                job.get("company_type", "其他"),
                job.get("city", ""),
                job.get("salary", ""),
                job.get("description", ""),
                job.get("requirements", ""),
                job.get("apply_url", ""),
                job.get("source", ""),
                job.get("publish_date", ""),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def job_exists(url_hash: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM jobs WHERE url_hash = ?", (url_hash,)).fetchone()
    conn.close()
    return row is not None


def get_jobs(filters: Optional[dict] = None, order_by: str = "score DESC", limit: int = 500) -> List[dict]:
    """查询岗位列表"""
    conn = get_conn()
    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if filters:
        if filters.get("status"):
            query += " AND status = ?"
            params.append(filters["status"])
        if filters.get("company_type"):
            query += " AND company_type = ?"
            params.append(filters["company_type"])
        if filters.get("city_keyword"):
            query += " AND city LIKE ?"
            params.append(f"%{filters['city_keyword']}%")
        if filters.get("title_keyword"):
            query += " AND title LIKE ?"
            params.append(f"%{filters['title_keyword']}%")
        if filters.get("min_score"):
            query += " AND score >= ?"
            params.append(filters["min_score"])
        if filters.get("priority_level"):
            query += " AND priority_level = ?"
            params.append(filters["priority_level"])
        if filters.get("difficulty"):
            query += " AND difficulty_label = ?"
            params.append(filters["difficulty"])

    query += f" ORDER BY {order_by} LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_job_by_id(job_id: int) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_job_status(job_id: int, status: str):
    conn = get_conn()
    conn.execute(
        "UPDATE jobs SET status = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (status, job_id),
    )
    conn.commit()
    conn.close()


def update_job_score(job_id: int, score: int, priority_level: str):
    conn = get_conn()
    conn.execute(
        "UPDATE jobs SET score = ?, priority_level = ?, updated_at = datetime('now', 'localtime') WHERE id = ?",
        (score, priority_level, job_id),
    )
    conn.commit()
    conn.close()


def mark_expired_jobs(days: int = 30):
    """将超过指定天数未更新的岗位标记为过期"""
    conn = get_conn()
    conn.execute(
        """UPDATE jobs SET status = '已过期', updated_at = datetime('now', 'localtime')
           WHERE status NOT IN ('已投递', '面试中')
           AND created_at < datetime('now', 'localtime', ?)""",
        (f"-{days} days",),
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM jobs WHERE status != '已过期'").fetchone()[0]
    by_type = {
        row["company_type"]: row["cnt"]
        for row in conn.execute("SELECT company_type, COUNT(*) as cnt FROM jobs WHERE status != '已过期' GROUP BY company_type").fetchall()
    }
    by_priority = {
        row["priority_level"]: row["cnt"]
        for row in conn.execute("SELECT priority_level, COUNT(*) as cnt FROM jobs WHERE status != '已过期' GROUP BY priority_level").fetchall()
    }
    by_status = {
        row["status"]: row["cnt"]
        for row in conn.execute("SELECT status, COUNT(*) as cnt FROM jobs GROUP BY status").fetchall()
    }
    conn.close()
    return {"total": total, "by_type": by_type, "by_priority": by_priority, "by_status": by_status}


def set_config(key: str, value: str):
    conn = get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
    conn.close()


def get_config(key: str) -> Optional[str]:
    conn = get_conn()
    row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else None
