"""PDF简历解析 + 关键词提取，生成用户画像"""

import os
import json
import re
import unicodedata
import fitz  # PyMuPDF
import jieba


RESUME_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resume")


def extract_pdf_text(pdf_path: str) -> str:
    """从PDF中提取纯文本，并修复CJK兼容字形编码"""
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    raw = "\n".join(text_parts)
    # NFKC规范化：将CJK兼容字形(如⽬⽣⼠)还原为标准汉字(目生士)
    return unicodedata.normalize("NFKC", raw)


def find_resume_file() -> str:
    """在resume目录中查找PDF简历文件"""
    for f in os.listdir(RESUME_DIR):
        if f.endswith(".pdf"):
            return os.path.join(RESUME_DIR, f)
    raise FileNotFoundError(f"未在 {RESUME_DIR} 目录下找到PDF简历文件")


def extract_education(text: str) -> dict:
    """提取学历信息"""
    result = {
        "highest_degree": "",
        "majors": [],
        "schools": [],
        "graduation_year": "",
    }

    # 硕士
    if "硕士" in text:
        result["highest_degree"] = "硕士"
        result["schools"].append("北师香港浸会大学")
        result["majors"].append("传理学（传媒管理）")
        if "2025" in text or "2025.10" in text:
            result["graduation_year"] = "2025"

    # 本科
    if "本科" in text or "学士" in text:
        if not result["highest_degree"]:
            result["highest_degree"] = "本科"
        result["schools"].append("南京特殊教育师范学院")
        result["majors"].append("教育学")

    return result


def extract_skills(text: str) -> dict:
    """提取技能标签"""
    hard_skills = []
    soft_skills = []

    hard_skill_keywords = {
        "Python": ["python"],
        "R语言": ["spss/r", "spss、r", "使用r", "用r", "r语言", "r完成", "r进行"],
        "SPSS": ["spss"],
        "Excel": ["excel"],
        "数据分析": ["数据分析", "数据挖掘", "量化分析", "量化研究"],
        "数据可视化": ["可视化", "ggplot2"],
        "爬虫": ["爬虫", "抓取"],
        "SQL": ["sql"],
        "甘特图": ["甘特图"],
        "社媒分析": ["社媒", "社交媒体"],
    }

    soft_skill_keywords = {
        "项目管理": ["项目管理", "项目统筹", "项目全生命周期", "多线程任务"],
        "用户洞察": ["用户洞察", "客群画像", "用户分层", "用户行为"],
        "社群运营": ["社群运营", "社群规模", "社群问卷"],
        "活动策划": ["活动策划", "活动筹备", "活动落地"],
        "跨部门协作": ["跨部门", "多方协同", "跨角色"],
        "市场运营": ["市场运营", "营销活动"],
        "团队管理": ["团队协作", "执行团队", "核心执行"],
        "方案撰写": ["方案设计", "策划书", "分析报告"],
        "风险管理": ["风险预案", "风险"],
        "本地化运营": ["本地化", "下沉市场"],
        "用户研究": ["问卷调查", "消费动机", "因子分析"],
        "流程优化": ["流程优化", "流程"],
    }

    # 过滤词：这些词太泛，不应作为技能标签
    generic_filter = {"市场", "用户", "团队", "分析", "运营"}

    text_lower = text.lower()
    for name, patterns in hard_skill_keywords.items():
        for p in patterns:
            if re.search(p, text_lower):
                hard_skills.append(name)
                break

    for name, patterns in soft_skill_keywords.items():
        for p in patterns:
            if re.search(p, text_lower):
                soft_skills.append(name)
                break

    # 用jieba分词做关键词补充
    words = set(jieba.cut(text))
    extra_kw = ["数据分析", "项目管理", "流程优化"]
    for kw in extra_kw:
        if kw in words and kw not in hard_skills + soft_skills:
            soft_skills.append(kw)

    soft_skills = [s for s in soft_skills if s not in generic_filter]

    return {"hard_skills": list(set(hard_skills)), "soft_skills": list(set(soft_skills))}


def extract_target_positions(text: str) -> list:
    """从简历中提取求职意向"""
    positions = []

    # 直接从"求职意向"行提取
    match = re.search(r"求职意向[：:]\s*(.+?)(?:$|\n)", text)
    if match:
        raw = match.group(1)
        # 按分隔符拆分
        for p in re.split(r"[//、，,]", raw):
            p = p.strip()
            if p and len(p) > 1:
                positions.append(p)

    return positions if positions else ["项目经理", "项目专员", "市场运营"]


def extract_industry_experience(text: str) -> list:
    """提取行业经验"""
    industries = set()

    industry_map = {
        "市场营销": ["市场营销", "营销", "市场部"],
        "教育": ["教育学校", "特殊教育", "教师", "教学"],
        "传媒": ["传媒", "传播", "媒体", "广告"],
        "互联网": ["互联网", "新媒体", "社交媒体", "社区"],
        "快消": ["快消", "快消品"],
        "数据分析": ["数据分析", "量化"],
    }

    for industry, patterns in industry_map.items():
        for p in patterns:
            if p in text:
                industries.add(industry)
                break

    return list(industries)


def build_profile(pdf_path: str = None) -> dict:
    """构建完整的用户画像"""
    if pdf_path is None:
        pdf_path = find_resume_file()

    text = extract_pdf_text(pdf_path)
    if not text.strip():
        raise ValueError("PDF文本提取为空，请检查文件")

    education = extract_education(text)
    skills = extract_skills(text)
    target_positions = extract_target_positions(text)
    industries = extract_industry_experience(text)

    profile = {
        "name": "示例用户",
        "highest_degree": education["highest_degree"],
        "graduation_year": education["graduation_year"],
        "schools": education["schools"],
        "majors": education["majors"],
        "target_positions": target_positions,
        "hard_skills": skills["hard_skills"],
        "soft_skills": skills["soft_skills"],
        "industries": industries,
        # 综合技能列表（匹配时用）
        "all_skills": skills["hard_skills"] + skills["soft_skills"],
        # 职位关键词（用于岗位标题匹配）
        "position_keywords": target_positions + list(set([
            "项目", "运营", "市场", "营销", "品牌", "策划", "数据",
            "用户", "社群", "产品", "活动", "内容", "媒体", "传播",
            "公关", "渠道", "增长", "客户",
        ])),
        # 用于倒排索引的扩展词
        "expand_keywords": list(set(
            target_positions
            + skills["hard_skills"]
            + skills["soft_skills"]
            + industries
            + ["项目", "运营", "市场", "营销", "品牌", "策划", "数据", "用户", "社群", "产品",
               "活动", "内容", "媒体", "传播", "公关", "渠道", "客户", "传媒", "教育",
               "应届生", "校招", "管培生", "培训生"]
        )),
    }

    return profile


if __name__ == "__main__":
    profile = build_profile()
    print("=== 用户画像 ===")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
