"""岗位-简历匹配打分"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger("analyzer.matcher")


# 知名企业列表（用于企业稳定性评分和公司类型推断）
FAMOUS_COMPANIES = {
    "央国企": [
        "中国石油", "中国石化", "中国海油", "国家电网", "南方电网", "中国华能", "中国大唐",
        "中国华电", "国家能源", "中国移动", "中国联通", "中国电信", "中粮", "中化",
        "中国建筑", "中铁", "中交", "中航", "中核", "中国烟草", "招商局", "华润",
        "保利", "中国电子", "中国电科", "中国兵器", "中船", "一汽", "东风", "长安",
        "宝钢", "鞍钢", "中国铝业", "五矿", "国投", "中国诚通", "中国中车",
    ],
    "知名外企": [
        "宝洁", "联合利华", "欧莱雅", "雀巢", "可口可乐", "百事", "玛氏", "达能",
        "微软", "苹果", "谷歌", "亚马逊", "IBM", "英特尔", "SAP", "Oracle",
        "麦肯锡", "波士顿", "贝恩", "德勤", "普华永道", "安永", "毕马威",
        "强生", "辉瑞", "罗氏", "诺华", "拜耳", "阿斯利康",
        "阿迪达斯", "耐克", "LVMH", "开云", "历峰", "爱马仕",
        "西门子", "博世", "通用电气", "霍尼韦尔", "3M",
        "汇丰", "花旗", "摩根", "高盛", "瑞银",
    ],
    "行业头部民企": [
        "华为", "腾讯", "阿里巴巴", "字节跳动", "美团", "京东", "拼多多", "网易",
        "百度", "小米", "比亚迪", "宁德时代", "大疆", "海康威视", "三一重工",
        "格力", "美的", "海尔", "顺丰", "万科", "碧桂园", "龙湖", "万达",
        "新东方", "好未来", "学而思", "分众传媒", "蓝色光标", "奥美",
    ],
}


def classify_company(company_name: str) -> str:
    """根据公司名称推断企业类型"""
    for kw in FAMOUS_COMPANIES["央国企"]:
        if kw in company_name:
            return "央国企"
    for kw in FAMOUS_COMPANIES["知名外企"]:
        if kw in company_name:
            return "外企"
    for kw in FAMOUS_COMPANIES["行业头部民企"]:
        if kw in company_name:
            return "民企"
    return "其他"


def get_company_fame_level(company_name: str) -> int:
    """企业知名度等级: 3=知名, 2=较知名, 1=一般, 0=未知"""
    for kw in FAMOUS_COMPANIES["央国企"] + FAMOUS_COMPANIES["知名外企"]:
        if kw in company_name:
            return 3
    for kw in FAMOUS_COMPANIES["行业头部民企"]:
        if kw in company_name:
            return 2
    return 1


class JobMatcher:
    def __init__(self, profile: dict):
        self.profile = profile

    def score_position_match(self, title: str) -> float:
        """岗位标题与求职意向的匹配度 (0-100)"""
        title_lower = title.lower()
        targets = self.profile.get("target_positions", [])
        keywords = self.profile.get("position_keywords", [])

        score = 0
        # 精确匹配目标岗位
        for t in targets:
            if t in title or any(c in title for c in t):
                score += 40
                break

        # 关键词匹配
        matched = 0
        for kw in keywords:
            if kw in title:
                matched += 1
        if matched > 0:
            score += min(matched * 8, 40)

        # 排除不相关岗位
        exclude_keywords = ["开发工程师", "Java", "前端", "后端", "算法工程师", "运维", "测试开发",
                           "销售代表", "电话销售", "客服", "保险", "房产"]
        for ex in exclude_keywords:
            if ex in title:
                score = max(0, score - 50)
                break

        return min(score, 100)

    def score_skill_match(self, description: str, requirements: str) -> float:
        """技能匹配度 (0-100)"""
        text = (description + " " + requirements).lower()
        all_skills = self.profile.get("all_skills", [])

        if not all_skills:
            return 30

        matched = 0
        for skill in all_skills:
            if skill.lower() in text:
                matched += 1

        ratio = matched / len(all_skills) if all_skills else 0
        return min(ratio * 100, 100)

    def score_education_match(self, description: str) -> float:
        """学历/经验匹配度 (0-100)"""
        score = 50  # 基准分

        text = description.lower()

        # 学历加分
        if self.profile.get("highest_degree") == "硕士":
            if any(w in text for w in ["硕士", "研究生", "master"]):
                score += 20
            elif any(w in text for w in ["本科", "学士", "bachelor"]):
                score += 10  # 硕士投本科要求岗位有优势
            else:
                score += 15  # 没明确要求的也加分

        # 经验要求匹配
        if any(w in text for w in ["应届", "校招", "毕业生", "无经验", "不限经验"]):
            score += 20
        elif any(w in text for w in ["1年", "一年", "1-3"]):
            score += 10  # 实习+项目经验可部分替代
        elif any(w in text for w in ["3-5年", "5年", "3年以上"]):
            score -= 30  # 经验要求过高

        # 专业相关
        majors = self.profile.get("majors", [])
        if majors:
            major_kw = ["传媒", "传播", "营销", "市场", "教育", "管理"]
            for kw in major_kw:
                if kw in text:
                    score += 5
                    break

        return max(0, min(score, 100))

    def score_salary(self, salary_text: str) -> float:
        """薪资竞争力评分 (0-100)"""
        if not salary_text:
            return 50  # 面议/未知，给中性分

        # 提取数字
        numbers = re.findall(r"(\d+)[kK千]?[-~至到]*(\d+)?[kK千]?", salary_text)
        if not numbers:
            numbers = re.findall(r"(\d+)\s*[-~至到]\s*(\d+)", salary_text)

        if not numbers:
            return 50

        try:
            # 取范围中值
            parts = numbers[0]
            lo = int(parts[0])
            hi = int(parts[1]) if len(parts) > 1 and parts[1] else lo

            # 如果数值较小(可能是万)，转换为k
            if lo < 50:
                lo *= 1000
                hi *= 1000

            monthly = (lo + hi) / 2
            if monthly < 3000:
                return 10
            elif monthly < 5000:
                return 25
            elif monthly < 8000:
                return 45
            elif monthly < 12000:
                return 60
            elif monthly < 18000:
                return 75
            elif monthly < 25000:
                return 85
            else:
                return 95
        except (ValueError, IndexError, TypeError):
            return 50

    def score_stability(self, company: str, company_type: str) -> float:
        """企业稳定性评分 (0-100)"""
        if company_type == "央国企":
            base = 85
        elif company_type == "外企":
            base = 65
        elif company_type == "民企":
            base = 45
        else:
            base = 40

        fame = get_company_fame_level(company)
        if fame == 3:
            base += 10
        elif fame == 2:
            base += 5

        return min(base, 100)

    def score_career_growth(self, company: str, title: str, description: str) -> float:
        """职业发展/跳槽价值 (0-100)"""
        score = 40  # 基准
        text = description.lower()

        # 平台知名度
        fame = get_company_fame_level(company)
        score += fame * 10

        # 技能成长空间
        growth_keywords = ["培训", "导师", "轮岗", "管培", "学习", "成长", "晋升", "发展空间"]
        for kw in growth_keywords:
            if kw in text or kw in title.lower():
                score += 3

        # 行业前景
        future_industries = ["互联网", "科技", "AI", "人工智能", "大数据", "新能源", "半导体", "医疗", "金融科技"]
        for kw in future_industries:
            if kw in text or kw in company:
                score += 3
                break

        return min(score, 100)

    def score_city(self, city: str) -> float:
        """城市偏好 (0-100)"""
        if not city:
            return 50

        tier1 = {"北京", "上海", "广州", "深圳"}
        new_tier1 = {"杭州", "成都", "武汉", "南京", "苏州", "西安", "长沙", "重庆", "天津",
                     "郑州", "东莞", "青岛", "合肥", "佛山", "宁波", "昆明", "沈阳", "厦门", "福州", "无锡"}
        jiangsu = {"江苏", "连云港", "南京", "苏州", "无锡", "常州", "南通", "徐州", "扬州", "镇江", "盐城", "淮安", "泰州", "宿迁"}

        for c in tier1:
            if c in city:
                return 90
        for c in new_tier1:
            if c in city:
                return 75
        for c in jiangsu:
            if c in city:
                return 85
        return 60  # 其他城市

    def score_competitiveness(self, company: str, title: str, description: str, requirements: str, city: str = "", salary: str = "") -> float:
        """竞争难度评分：分数越高=越容易拿到面试，分数越低=竞争越激烈 (0-100)"""
        score = 60  # 基准
        text = (description + " " + requirements).lower()
        title_lower = title.lower()

        # 1. 公司知名度（越知名竞争越大）- up to -25
        fame = get_company_fame_level(company)
        if fame == 3:
            score -= 25  # 头部公司竞争极其激烈
        elif fame == 2:
            score -= 12  # 知名企业竞争较大

        # 2. 学历门槛 - up to -15
        edu_gate = 0
        if any(w in text for w in ["985", "211", "双一流", "qs前", "qs100", "常春藤", "清北"]):
            edu_gate = 15
        elif any(w in text for w in ["硕士及以上", "硕士研究生", "博士"]):
            edu_gate = 10
        elif any(w in text for w in ["硕士优先", "研究生优先"]):
            edu_gate = 5
        score -= edu_gate

        # 3. 经验门槛 - up to -15
        exp_gate = 0
        if any(w in text for w in ["3年以上", "3-5年", "5年以上", "5-10年"]):
            exp_gate = 15
        elif any(w in text for w in ["1-3年", "2年以上", "三年"]):
            exp_gate = 8
        elif any(w in text for w in ["1年以下", "1年以上"]):
            exp_gate = 3
        # "应届"/"校招"/"经验不限"不加扣分
        score -= exp_gate

        # 4. 城市竞争度 - up to -10
        tier1_cities = ["北京", "上海", "深圳"]
        for c in tier1_cities:
            if c in city:
                score -= 10
                break
        else:
            if any(c in city for c in ["广州", "杭州"]):
                score -= 6
            elif any(c in city for c in ["成都", "武汉", "南京", "苏州"]):
                score -= 3

        # 5. 薪资水平（高薪=更多人抢）- up to -10
        salary_score = self.score_salary(salary)
        if salary_score >= 85:
            score -= 10
        elif salary_score >= 70:
            score -= 5

        # 6. 略微加分：中小公司、地方企业
        if fame <= 1:
            score += 8  # 普通公司竞争小

        return max(5, min(score, 100))

    def compute_total(self, job: dict, classify: bool = True) -> dict:
        """综合评分，返回 {score, priority_level, details}"""
        # 自动推断企业类型
        if classify and job.get("company_type", "其他") == "其他":
            job["company_type"] = classify_company(job.get("company", ""))

        scores = {
            "position": self.score_position_match(job.get("title", "")),
            "skill": self.score_skill_match(
                job.get("description", ""), job.get("requirements", "")
            ),
            "education": self.score_education_match(
                job.get("description", "") + " " + job.get("requirements", "")
            ),
            "salary": self.score_salary(job.get("salary", "")),
            "stability": self.score_stability(
                job.get("company", ""), job.get("company_type", "其他")
            ),
            "career": self.score_career_growth(
                job.get("company", ""), job.get("title", ""), job.get("description", "")
            ),
            "city": self.score_city(job.get("city", "")),
        }

        # 加权求和
        weights = {
            "position": 0.25,
            "skill": 0.20,
            "education": 0.10,
            "salary": 0.15,
            "stability": 0.15,
            "career": 0.10,
            "city": 0.05,
        }

        # 竞争难度
        comp_score = self.score_competitiveness(
            job.get("company", ""), job.get("title", ""),
            job.get("description", ""), job.get("requirements", ""),
            job.get("city", ""), job.get("salary", ""),
        )

        total = sum(scores[k] * weights[k] for k in weights)

        # 优先级分级
        if total >= 75:
            level = "强烈推荐"
        elif total >= 55:
            level = "推荐投递"
        elif total >= 40:
            level = "可以考虑"
        else:
            level = "仅供参考"

        # 竞争难度标签
        if comp_score >= 60:
            diff_label = "容易"
        elif comp_score >= 40:
            diff_label = "适中"
        elif comp_score >= 20:
            diff_label = "挑战"
        else:
            diff_label = "冲刺"

        return {
            "score": round(total),
            "priority_level": level,
            "difficulty": round(comp_score),
            "difficulty_label": diff_label,
            "details": {k: round(v) for k, v in scores.items()},
        }
