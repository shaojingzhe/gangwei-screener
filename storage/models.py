"""数据模型定义"""

JOBS_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url_hash TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    company_type TEXT DEFAULT '其他',
    city TEXT DEFAULT '',
    salary TEXT DEFAULT '',
    description TEXT DEFAULT '',
    requirements TEXT DEFAULT '',
    apply_url TEXT DEFAULT '',
    source TEXT DEFAULT '',
    publish_date TEXT DEFAULT '',
    score INTEGER DEFAULT 0,
    priority_level TEXT DEFAULT '仅供参考',
    status TEXT DEFAULT '新岗位',
    advice TEXT DEFAULT '',
    difficulty INTEGER DEFAULT 50,
    difficulty_label TEXT DEFAULT '适中',
    created_at TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at TEXT DEFAULT (datetime('now', 'localtime'))
);
"""

CONFIG_TABLE_SCHEMA = """
CREATE TABLE IF NOT EXISTS config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_jobs_score ON jobs(score DESC);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_company_type ON jobs(company_type);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_publish_date ON jobs(publish_date);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);",
]
