#!/usr/bin/env python3
"""配置 macOS launchd 定时任务，每12小时自动爬取"""

import os
import sys
import plistlib
import subprocess

PROJECT_ROOT = os.path.dirname(__file__)
LAUNCHD_NAME = "com.shaojingzhe.jobscraper"
LAUNCHD_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_NAME}.plist")
RUNNER_SCRIPT = os.path.join(PROJECT_ROOT, "scheduled_run.sh")
PYTHON_PATH = sys.executable


def create_runner_script():
    """创建爬虫执行脚本"""
    content = f"""#!/bin/bash
# PasteFlow 岗位爬虫 — 定时执行脚本
# 由 launchd 每12小时触发

export PATH="/usr/local/bin:/usr/bin:/bin:/Library/Developer/CommandLineTools/usr/bin:{os.path.dirname(PYTHON_PATH)}"

cd "{PROJECT_ROOT}"

# 运行爬虫
{PYTHON_PATH} run_scraper.py >> data/scraper.log 2>&1

# 标记过期岗位（30天）
{PYTHON_PATH} -c "
import sys
sys.path.insert(0, '{PROJECT_ROOT}')
from storage.database import init_db, mark_expired_jobs
init_db()
mark_expired_jobs(30)
print('过期岗位已标记')
" >> data/scraper.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 定时任务执行完毕" >> data/scraper.log
"""
    with open(RUNNER_SCRIPT, "w") as f:
        f.write(content)
    os.chmod(RUNNER_SCRIPT, 0o755)
    print(f"✓ 执行脚本已创建: {RUNNER_SCRIPT}")


def install():
    """安装 launchd 定时任务"""
    create_runner_script()

    plist = {
        "Label": LAUNCHD_NAME,
        "Program": RUNNER_SCRIPT,
        "StartInterval": 43200,  # 12小时 = 43200秒
        "RunAtLoad": True,  # 安装后立即执行一次
        "StandardOutPath": os.path.join(PROJECT_ROOT, "data", "launchd_stdout.log"),
        "StandardErrorPath": os.path.join(PROJECT_ROOT, "data", "launchd_stderr.log"),
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/usr/bin:/bin:/Library/Developer/CommandLineTools/usr/bin",
            "HOME": os.path.expanduser("~"),
        },
    }

    os.makedirs(os.path.dirname(LAUNCHD_PATH), exist_ok=True)
    with open(LAUNCHD_PATH, "wb") as f:
        plistlib.dump(plist, f)
    print(f"✓ launchd plist 已创建: {LAUNCHD_PATH}")

    # 加载到 launchd
    subprocess.run(["launchctl", "unload", LAUNCHD_PATH], capture_output=True)
    result = subprocess.run(["launchctl", "load", LAUNCHD_PATH], capture_output=True, text=True)
    if result.returncode == 0:
        print("✓ 定时任务已加载！每12小时自动爬取一次")
        print(f"  下次执行: 12小时后")
        print(f"  手动触发: launchctl start {LAUNCHD_NAME}")
    else:
        print(f"✗ 加载失败: {result.stderr}")


def uninstall():
    """卸载定时任务"""
    subprocess.run(["launchctl", "unload", LAUNCHD_PATH], capture_output=True)
    if os.path.exists(LAUNCHD_PATH):
        os.remove(LAUNCHD_PATH)
    print(f"✓ 定时任务已卸载")


def status():
    """查看任务状态"""
    result = subprocess.run(["launchctl", "list"], capture_output=True, text=True)
    if LAUNCHD_NAME in result.stdout:
        print(f"✓ 定时任务 [{LAUNCHD_NAME}] 正在运行中")
        print(f"  plist: {LAUNCHD_PATH}")
        print(f"  脚本: {RUNNER_SCRIPT}")
    else:
        print(f"✗ 定时任务 [{LAUNCHD_NAME}] 未在运行")


def show_help():
    print("用法:")
    print("  python3 setup_scheduler.py install    — 安装定时任务")
    print("  python3 setup_scheduler.py uninstall  — 卸载定时任务")
    print("  python3 setup_scheduler.py status     — 查看状态")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
    elif sys.argv[1] == "install":
        install()
    elif sys.argv[1] == "uninstall":
        uninstall()
    elif sys.argv[1] == "status":
        status()
    else:
        show_help()
