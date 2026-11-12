#!/usr/bin/env python3
"""Flask Web 应用入口"""

import os
import sys

PROJECT_ROOT = os.path.dirname(__file__)
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask
from storage.database import init_db
from web.routes import web


def create_app():
    app = Flask(__name__)
    app.register_blueprint(web)

    # 启动时初始化数据库
    init_db()

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 50)
    print("  🎯 岗位筛选工具已启动")
    print(f"  打开浏览器访问: http://localhost:5050")
    print("=" * 50 + "\n")
    app.run(host="127.0.0.1", port=5050, debug=False)
