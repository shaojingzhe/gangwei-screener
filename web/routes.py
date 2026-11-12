"""Flask 路由"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from storage.database import (
    get_jobs, get_job_by_id, update_job_status, get_stats, set_config, get_config
)
from analyzer.resume_parser import build_profile

web = Blueprint("web", __name__, template_folder="templates", static_folder="static")


@web.route("/")
def index():
    """岗位列表主页"""
    return render_template("index.html")


@web.route("/api/jobs")
def api_jobs():
    """岗位列表 API（支持搜索、筛选、排序）"""
    filters = {}
    status = request.args.get("status", "")
    if status:
        filters["status"] = status
    company_type = request.args.get("company_type", "")
    if company_type:
        filters["company_type"] = company_type
    city = request.args.get("city", "")
    if city:
        filters["city_keyword"] = city
    title = request.args.get("title", "")
    if title:
        filters["title_keyword"] = title
    priority = request.args.get("priority", "")
    if priority:
        filters["priority_level"] = priority
    difficulty = request.args.get("difficulty", "")
    if difficulty:
        filters["difficulty"] = difficulty

    order_by = request.args.get("order_by", "score DESC")
    page = int(request.args.get("page", 1))
    per_page = 30
    offset = (page - 1) * per_page

    jobs = get_jobs(filters=filters, order_by=order_by, limit=per_page + offset)
    # 简单分页
    total = len(jobs)
    jobs = jobs[offset:offset + per_page]

    return jsonify({
        "jobs": [dict(j) for j in jobs],
        "total": total,
        "page": page,
        "has_more": len(jobs) == per_page,
    })


@web.route("/api/jobs/<int:job_id>")
def api_job_detail(job_id: int):
    """岗位详情 API"""
    job = get_job_by_id(job_id)
    if not job:
        return jsonify({"error": "岗位不存在"}), 404
    return jsonify(dict(job))


@web.route("/api/jobs/<int:job_id>/status", methods=["POST"])
def api_update_status(job_id: int):
    """更新投递状态"""
    data = request.get_json()
    new_status = data.get("status", "")
    valid_statuses = ["新岗位", "待投递", "已投递", "面试中", "已结束"]
    if new_status not in valid_statuses:
        return jsonify({"error": "无效的状态"}), 400
    update_job_status(job_id, new_status)
    return jsonify({"ok": True})


@web.route("/api/stats")
def api_stats():
    """统计数据 API"""
    stats = get_stats()
    return jsonify(stats)


@web.route("/api/profile")
def api_profile():
    """用户画像 API"""
    try:
        profile = build_profile()
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@web.route("/job/<int:job_id>")
def job_detail(job_id: int):
    """岗位详情页"""
    return render_template("detail.html", job_id=job_id)


@web.route("/settings")
def settings():
    """筛选设置页"""
    return render_template("settings.html")
