#!/bin/bash
# ==========================================
#  岗位筛选 — 桌面启动器
#  启动 Flask 服务 + 打开浏览器
# ==========================================

PROJECT_DIR="/Users/jz/Desktop/历史粘贴/gangweishaixuan"
PORT=5050

# 检查是否已在运行
if lsof -i :$PORT -sTCP:LISTEN > /dev/null 2>&1; then
    echo "服务已在运行中，直接打开页面..."
else
    echo "启动服务..."
    cd "$PROJECT_DIR"
    python3 app.py &
    # 等待服务就绪
    for i in 1 2 3 4 5; do
        sleep 1
        if curl -s -o /dev/null "http://localhost:$PORT/"; then
            echo "服务已就绪"
            break
        fi
    done
fi

# 打开浏览器
open "http://localhost:$PORT/"
