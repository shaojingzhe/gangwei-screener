#!/usr/bin/env python3
"""首次运行问答向导 — 交互式收集筛选偏好"""

import os
import sys
import yaml

PROJECT_ROOT = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.yaml")


def ask(prompt: str, default: str = "") -> str:
    if default:
        answer = input(f"{prompt} [{default}]: ").strip()
        return answer if answer else default
    return input(f"{prompt}: ").strip()


def ask_yes_no(prompt: str, default: str = "y") -> bool:
    d = "Y/n" if default == "y" else "y/N"
    answer = input(f"{prompt} [{d}]: ").strip().lower()
    if not answer:
        answer = default
    return answer in ("y", "yes", "是")


def ask_multi(prompt: str, options: list) -> list:
    print(f"\n{prompt}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    print("  输入数字（逗号分隔），或直接回车选全部")
    sel = input("> ").strip()
    if not sel:
        return options
    try:
        indices = [int(x.strip()) for x in sel.split(",") if x.strip()]
        return [options[i - 1] for i in indices if 1 <= i <= len(options)]
    except (ValueError, IndexError):
        return options


def run():
    print("\n" + "=" * 50)
    print("  🎯 岗位筛选工具 — 首次设置向导")
    print("=" * 50)
    print("\n这个向导会帮你定制筛选偏好，所有设置后续都可以修改。\n")

    # 1. 目标城市
    print("━" * 40)
    print("📍 目标城市")
    print("━" * 40)
    tier1 = ask_multi("一线城市：", ["北京", "上海", "广州", "深圳"])
    new_tier1 = ask_multi("新一线城市：", [
        "杭州", "成都", "武汉", "南京", "苏州", "西安", "长沙",
        "重庆", "天津", "郑州", "东莞", "青岛", "合肥", "宁波",
    ])
    hometown = input("\n家乡及周边省份（如：江苏）: ").strip()
    hometown_list = [hometown] if hometown else ["江苏"]
    accept_all = ask_yes_no("\n是否也接受其他城市的岗位？", "y")

    # 2. 意向行业
    print("\n" + "━" * 40)
    print("🏭 意向行业")
    print("━" * 40)
    industries = ask_multi("你感兴趣的行业：", [
        "互联网/科技", "传媒/广告/公关", "教育/培训", "快消/零售",
        "咨询/服务", "金融/保险", "医疗/健康", "制造业",
    ])

    ind_map = {
        "互联网/科技": "互联网",
        "传媒/广告/公关": "传媒",
        "教育/培训": "教育",
        "快消/零售": "快消",
        "咨询/服务": "咨询",
        "金融/保险": "金融",
        "医疗/健康": "医疗",
        "制造业": "制造",
    }
    preferred_industries = [ind_map.get(i, i) for i in industries]

    print("\n是否有不感兴趣的行业？直接回车跳过")
    excluded = input("> ").strip()
    excluded_industries = [x.strip() for x in excluded.split(",") if x.strip()]

    # 3. 企业类型偏好
    print("\n" + "━" * 40)
    print("🏢 企业类型偏好")
    print("━" * 40)
    print("按优先级排序（输入数字，如：1,2,3）")
    print("  1. 央国企（稳定、福利好）")
    print("  2. 外企（薪资高、国际化）")
    print("  3. 民企（机会多、成长快）")
    order_input = input("排序 > ").strip()
    type_order = {"1": "央国企", "2": "外企", "3": "民企"}
    if order_input:
        company_order = [type_order.get(x.strip(), "民企") for x in order_input.split(",")]
    else:
        company_order = ["央国企", "外企", "民企"]

    # 4. 岗位类型
    print("\n" + "━" * 40)
    print("💼 目标岗位")
    print("━" * 40)
    default_positions = ["项目经理", "市场运营", "新媒体运营", "品牌策划", "数据分析", "产品运营"]
    print("当前检测到的简历求职意向可能是：项目经理/市场运营/项目专员等")
    print("以下是目标岗位关键词列表：")
    for i, pos in enumerate(default_positions, 1):
        print(f"  {i}. {pos}")
    print("  输入数字选择（逗号分隔），回车选全部")
    pos_input = input("> ").strip()
    if pos_input:
        try:
            indices = [int(x.strip()) for x in pos_input.split(",")]
            target_positions = [default_positions[i - 1] for i in indices if 1 <= i <= len(default_positions)]
        except (ValueError, IndexError):
            target_positions = default_positions
    else:
        target_positions = default_positions

    # 5. 其他偏好
    print("\n" + "━" * 40)
    print("⚙️ 其他偏好")
    print("━" * 40)
    accept_travel = ask_yes_no("是否接受出差？", "y")
    accept_relocate = ask_yes_no("是否接受异地/跨城市工作？", "y")

    # 6. 排除关键词
    print("\n是否有些公司或行业你不想看到？输入关键词（逗号分隔），回车跳过")
    excluded_kws = input("> ").strip()
    excluded_keywords = [x.strip() for x in excluded_kws.split(",") if x.strip()]

    # 汇总确认
    config = {
        "cities": {
            "tier1": tier1,
            "new_tier1": new_tier1,
            "hometown_priority": hometown_list,
            "accept_all": accept_all,
        },
        "industries": {
            "preferred": preferred_industries,
            "excluded": excluded_industries,
        },
        "company_preference": {
            "order": company_order,
        },
        "job_types": {
            "preferred": target_positions,
        },
        "salary": {
            "min_monthly": 0,
        },
        "excluded_keywords": excluded_keywords,
        "other": {
            "accept_business_travel": accept_travel,
            "accept_relocation": accept_relocate,
        },
    }

    print("\n" + "=" * 50)
    print("📋 配置预览")
    print("=" * 50)
    print(yaml.dump(config, allow_unicode=True, default_flow_style=False))

    if ask_yes_no("\n是否保存以上配置？", "y"):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        print(f"✓ 配置已保存到: {CONFIG_PATH}")
    else:
        print("配置未保存，可以稍后手动编辑 config.yaml")

    print("\n" + "=" * 50)
    print("  设置完成！")
    print(f"  启动 Web 界面: python3 app.py")
    print(f"  手动爬取岗位: python3 run_scraper.py")
    print(f"  注入测试数据: python3 inject_test_data.py")
    print("=" * 50)
    print()


if __name__ == "__main__":
    run()
