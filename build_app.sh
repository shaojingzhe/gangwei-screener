#!/bin/bash
# ==========================================
#  构建「岗位筛选.app」桌面应用
# ==========================================

PROJECT_DIR="/Users/jz/Desktop/历史粘贴/gangweishaixuan"
APP_NAME="岗位筛选"
DESKTOP_DIR="$HOME/Desktop"
APP_PATH="$DESKTOP_DIR/$APP_NAME.app"

echo "构建 $APP_NAME.app ..."

# 1. 确保 launcher.sh 可执行
chmod +x "$PROJECT_DIR/launcher.sh"

# 2. 创建 .app 目录结构
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 3. 复制启动脚本
cp "$PROJECT_DIR/launcher.sh" "$APP_PATH/Contents/MacOS/launcher.sh"
chmod +x "$APP_PATH/Contents/MacOS/launcher.sh"

# 4. 创建 Info.plist
cat > "$APP_PATH/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>岗位筛选</string>
    <key>CFBundleDisplayName</key>
    <string>岗位筛选</string>
    <key>CFBundleIdentifier</key>
    <string>com.shaojingzhe.jobfilter</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleExecutable</key>
    <string>launcher.sh</string>
    <key>CFBundleIconFile</key>
    <string>appicon</string>
    <key>LSMinimumSystemVersion</key>
    <string>14.0</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
PLIST

# 5. 生成简易图标（纯色圆角矩形 + 文字）
# 使用 sips + 内嵌 Python 生成图标
python3 << 'PYICON'
import subprocess, os

iconset = os.path.expanduser("~/Desktop/岗位筛选.app/Contents/Resources/appicon.iconset")
os.makedirs(iconset, exist_ok=True)

# 用 Python 生成一个简单的 PNG 图标
from PIL import Image, ImageDraw, ImageFont
import struct

# 如果 Pillow 不可用，生成一个纯色的最小图标
sizes = [16, 32, 64, 128, 256, 512]
for s in sizes:
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # 蓝色圆角矩形
    margin = s // 8
    draw.rounded_rectangle(
        [margin, margin, s - margin, s - margin],
        radius=s // 5,
        fill=(0, 113, 227, 255)  # Apple blue
    )
    # 白色文字「岗」
    try:
        font_size = s // 2
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", font_size)
    except:
        font = ImageFont.load_default()
    text = "岗"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((s - tw) / 2, (s - th) / 2 - s // 20), text, fill=(255, 255, 255, 255), font=font)

    fname = f"icon_{s}x{s}.png"
    if s == 512:
        # 也存为 512x512@2x
        img.save(os.path.join(iconset, "icon_512x512@2x.png"))
        img.save(os.path.join(iconset, fname))
    elif s == 256:
        img.save(os.path.join(iconset, fname))
        img.save(os.path.join(iconset, "icon_256x256@2x.png"))
    else:
        img.save(os.path.join(iconset, fname))
        # 存对应的 @2x
        half = s // 2
        if half >= 16:
            img_half = img.resize((half, half), Image.LANCZOS)
            img_half.save(os.path.join(iconset, f"icon_{half}x{half}.png"))

# 用 iconutil 生成 .icns
subprocess.run(
    ["iconutil", "-c", "icns", "-o",
     os.path.expanduser("~/Desktop/岗位筛选.app/Contents/Resources/appicon.icns"),
     iconset],
    check=False
)
# 清理 iconset
import shutil
shutil.rmtree(iconset, ignore_errors=True)
print("图标已生成")
PYICON

echo ""
echo "✅ 完成！"
echo "   App 位置: $APP_PATH"
echo "   双击 $APP_NAME.app 即可启动"
echo ""
echo "   提示：首次打开可能需要右键 → 打开，确认允许运行"
