"""投递建议生成器：为每个岗位生成简历优化建议 + 投递策略 + 面试重点"""

import logging
from typing import Dict

from .job_matcher import JobMatcher, classify_company, get_company_fame_level

logger = logging.getLogger("analyzer.prioritizer")


class AdviceGenerator:
    def __init__(self, profile: dict):
        self.profile = profile

    def generate(self, job: dict, match_result: dict) -> str:
        """为岗位生成完整的投递建议"""
        parts = []

        resume_advice = self._resume_advice(job, match_result)
        if resume_advice:
            parts.append("📝 简历优化\n" + resume_advice)

        strategy_advice = self._strategy_advice(job, match_result)
        if strategy_advice:
            parts.append("📤 投递策略\n" + strategy_advice)

        interview_advice = self._interview_advice(job, match_result)
        if interview_advice:
            parts.append("🎯 面试准备\n" + interview_advice)

        return "\n\n".join(parts)

    def _resume_advice(self, job: dict, match: dict) -> str:
        lines = []
        title = job.get("title", "")
        comp = job.get("company", "")
        desc = (job.get("description", "") + " " + job.get("requirements", "")).lower()
        details = match.get("details", {})

        # 岗位匹配度分析
        pos_score = details.get("position", 0)
        if pos_score >= 80:
            lines.append(f"✓ 岗位名称「{title}」与求职意向高度匹配，简历中的目标岗位描述无需调整")
        elif pos_score >= 50:
            lines.append(f"• 岗位「{title}」与求职意向部分匹配，建议在简历求职意向中增加「{title}」相关表述")
        else:
            lines.append(f"• 岗位「{title}」与求职意向偏差较大，如需投递建议定制化修改求职目标")

        # 技能匹配分析
        skill_score = details.get("skill", 0)
        if skill_score >= 70:
            lines.append("✓ 技能匹配度较高，简历中的技能描述与JD要求吻合")
        elif skill_score >= 40:
            # 找出简历有但JD没覆盖的技能
            missing_in_jd = self._find_missing_skills(desc)
            if missing_in_jd:
                lines.append(f"• JD中可能需要但简历未体现的技能/关键词：{', '.join(missing_in_jd[:5])}")
                lines.append("  建议：如有相关经验，在简历对应经历中自然融入这些关键词")
        else:
            missing = self._find_missing_skills(desc)
            if missing:
                lines.append(f"• 技能匹配度偏低，建议重点补充：{', '.join(missing[:5])}")

        # 学历建议
        edu_score = details.get("education", 0)
        if edu_score >= 80:
            lines.append("✓ 学历和经验要求匹配")
        elif edu_score < 50:
            if "3年" in desc or "5年" in desc:
                lines.append("• 该岗位经验要求较高，建议在简历中突出实习+项目经历的深度，用成果数据弥补年限差距")

        # 根据企业类型给建议
        comp_type = job.get("company_type", classify_company(comp))
        if comp_type == "央国企":
            lines.append("• 央国企岗位：建议简历中突出「政治面貌」（如党员/团员）、校级荣誉、学生干部经历")
        elif comp_type == "外企":
            lines.append("• 外企岗位：建议准备中英文简历，突出跨文化沟通能力和国际视野")
        elif comp_type == "民企":
            if get_company_fame_level(comp) >= 2:
                lines.append("• 头部民企：建议强调实际项目成果和数据驱动的思维，突出「落地能力」")

        return "\n".join(lines) if lines else ""

    def _strategy_advice(self, job: dict, match: dict) -> str:
        lines = []
        comp = job.get("company", "")
        comp_type = job.get("company_type", classify_company(comp))
        source = job.get("source", "")
        score = match.get("score", 0)

        # 投递渠道建议
        if comp_type == "央国企":
            lines.append(f"• 推荐投递渠道：{comp}官网招聘页 > iguopin.com > 国聘公众号")
            lines.append("• 央国企流程较长（1-3个月），建议耐心等待并关注笔试通知")
        elif comp_type == "外企":
            lines.append(f"• 推荐投递渠道：LinkedIn > {comp}官网 > 猎聘")
            lines.append("• 外企通常反馈较快，建议投递后7天内关注邮件")
        else:
            fame = get_company_fame_level(comp)
            if fame >= 2:
                lines.append(f"• 推荐投递渠道：{comp}官网 > Boss直聘/拉勾 > 猎聘")
                lines.append("• 大厂竞争激烈，建议找内推码，投递时附上项目作品集")
            else:
                lines.append(f"• 推荐投递渠道：Boss直聘 > 拉勾 > 猎聘")

        # 竞争难度提示
        diff_label = match.get("difficulty_label", "适中")
        if diff_label == "容易":
            lines.append("• 🟢 竞争难度：容易 — 投递成功率较高，建议尽早投递占位")
        elif diff_label == "适中":
            lines.append("• 🟡 竞争难度：适中 — 认真准备简历和面试，机会较大")
        elif diff_label == "挑战":
            lines.append("• 🟠 竞争难度：挑战 — 需要在简历中突出差异化优势")
        elif diff_label == "冲刺":
            lines.append("• 🔴 竞争难度：冲刺 — 竞争极其激烈，建议同时多投同类型普通公司保底")

        # 投递时机
        publish_date = job.get("publish_date", "")
        if publish_date:
            lines.append(f"• 岗位发布于 {publish_date}，新发布24h内投递回复率最高")

        # 优先级判断
        if score >= 75:
            lines.append("• ⭐ 强烈推荐优先投递，该岗位在薪资、稳定、发展三方面均衡")
        elif score >= 55:
            lines.append("• 推荐投递，建议72小时内完成投递")

        return "\n".join(lines)

    def _interview_advice(self, job: dict, match: dict) -> str:
        lines = []
        title = job.get("title", "")
        comp = job.get("company", "")
        desc = (job.get("description", "") + " " + job.get("requirements", "")).lower()
        comp_type = job.get("company_type", classify_company(comp))

        # 基于JD关键词推断面试重点
        interview_topics = []

        if any(kw in desc for kw in ["数据分析", "数据驱动", "sql", "excel", "spss"]):
            interview_topics.append("可能会被问到数据分析相关项目经验，准备好你在实习中用SPSS/R做量化分析的案例")
        if any(kw in desc for kw in ["项目管理", "项目统筹", "项目推进", "pm"]):
            interview_topics.append("项目管理能力是考察重点，准备好阐述你统筹校园活动的全流程管理经验")
        if any(kw in desc for kw in ["用户", "运营", "社群"]):
            interview_topics.append("用户运营相关面试题：准备好你社群运营中「500人→600人且活跃度提升18%」的具体案例")
        if any(kw in desc for kw in ["营销", "市场", "品牌", "推广"]):
            interview_topics.append("营销类面试题：准备好讲述你市场部实习中用户洞察→策略→落地的完整链路")
        if any(kw in desc for kw in ["沟通", "协作", "跨部门", "团队"]):
            interview_topics.append("跨部门协作是常见面试题，用你统筹校园活动时的多角色协同案例作答")

        if interview_topics:
            lines.append("【可能的面试考察点】")
            for t in interview_topics[:4]:
                lines.append(f"  • {t}")

        # 面试风格预判
        if comp_type == "央国企":
            lines.append("\n【面试风格】结构化面试为主，可能有无领导小组讨论")
            lines.append("  • 准备方向：时事政治、企业文化、行为面试题（STAR法则）")
        elif comp_type == "外企":
            lines.append("\n【面试风格】行为面试为主，可能有多轮1v1")
            lines.append("  • 准备方向：英文自我介绍、宝洁八大问、跨文化沟通案例")
        elif comp_type == "民企":
            fame = get_company_fame_level(comp)
            if fame >= 2:
                lines.append("\n【面试风格】业务面+HR面，注重实战能力")
                lines.append("  • 准备方向：项目复盘（从0到1做了什么）、数据成果、对业务的理解")

        return "\n".join(lines)

    def _find_missing_skills(self, desc: str) -> list:
        """找出JD中有但简历未体现的技能关键词"""
        jd_skill_keywords = [
            "竞品分析", "A/B测试", "用户增长", "转化率", "留存", "DAU", "MAU",
            "ROI", "KPI", "OKR", "SOP", "需求文档", "产品规划",
            "Photoshop", "PR", "剪辑", "文案", "公众号", "短视频",
            "SCRM", "CRM", "自动化", "敏捷", "Scrum", "看板",
            "数据看板", "BI", "Tableau", "Power BI",
            "用户画像", "漏斗分析", "归因分析", "用户旅程",
            "内容运营", "活动运营", "产品运营", "电商运营",
            "SEO", "SEM", "信息流", "投放", "千川", "巨量",
        ]

        all_skills = [s.lower() for s in self.profile.get("all_skills", [])]
        missing = []
        for kw in jd_skill_keywords:
            if kw.lower() in desc and not any(kw.lower() in s for s in all_skills):
                missing.append(kw)
        return missing


def batch_score_and_advise(profile: dict, jobs: list) -> list:
    """批量打分并生成建议"""
    matcher = JobMatcher(profile)
    adviser = AdviceGenerator(profile)

    for job in jobs:
        result = matcher.compute_total(job, classify=True)
        job["score"] = result["score"]
        job["priority_level"] = result["priority_level"]
        job["difficulty"] = result["difficulty"]
        job["difficulty_label"] = result["difficulty_label"]
        job["company_type"] = classify_company(job.get("company", ""))
        job["advice"] = adviser.generate(job, result)

    # 按score降序排序
    jobs.sort(key=lambda j: j.get("score", 0), reverse=True)
    return jobs
