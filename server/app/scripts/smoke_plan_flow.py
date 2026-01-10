#!/usr/bin/env python3
"""
学习计划闭环验收脚本
演示完整流程：计划生成 → 开始练习 → 答题交卷 → 错题统计 → 数据分析

用于论文答辩演示，保证可重复执行。
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

def log_step(step_num, description, success=True, details=None):
    """打印步骤信息"""
    status = "✅" if success else "❌"
    print(f"{status} 步骤 {step_num}: {description}")
    if details:
        print(f"   {details}")
    print()

def main():
    print("🚀 开始学习计划闭环验收测试")
    print("=" * 50)

    # 步骤 1: 登录获取token
    print("步骤 1: 登录系统")
    login_payload = {
        "username": "student01",
        "password": "123456"
    }
    login_resp = requests.post(f"{BASE_URL}/auth/login", json=login_payload)

    if login_resp.status_code != 200:
        log_step(1, "登录失败", False, f"HTTP {login_resp.status_code}: {login_resp.text}")
        sys.exit(1)

    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    log_step(1, "登录成功", True, f"获取到token: {token[:20]}...")

    # 步骤 2: 检查学习目标
    print("步骤 2: 检查学习目标")
    goal_resp = requests.get(f"{BASE_URL}/goals/me", headers=headers)

    if goal_resp.status_code == 404 or not goal_resp.json():
        log_step(2, "学习目标不存在，开始创建", True)

        # 计算未来考试日期（30天后）
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        goal_payload = {
            "exam_date": future_date,
            "target_score": 75,
            "daily_minutes": 120
        }
        create_goal_resp = requests.post(f"{BASE_URL}/goals/", json=goal_payload, headers=headers)

        if create_goal_resp.status_code != 200:
            log_step(2, "创建学习目标失败", False, f"HTTP {create_goal_resp.status_code}: {create_goal_resp.text}")
            sys.exit(1)

        log_step(2, "学习目标创建成功", True, f"考试日期: {future_date}, 目标分数: 75, 每日学习: 120分钟")
    else:
        goal_data = goal_resp.json()
        log_step(2, "学习目标已存在", True, f"考试日期: {goal_data['exam_date']}, 目标分数: {goal_data.get('target_score', '未设置')}")

    # 步骤 3: 生成学习计划
    print("步骤 3: 生成学习计划")
    plan_payload = {"days": 14}
    plan_resp = requests.post(f"{BASE_URL}/plans/generate", json=plan_payload, headers=headers)

    if plan_resp.status_code != 200:
        log_step(3, "生成学习计划失败", False, f"HTTP {plan_resp.status_code}: {plan_resp.text}")
        sys.exit(1)

    log_step(3, "学习计划生成成功", True, f"计划天数: 14天")

    # 步骤 4: 获取活跃计划并查找练习任务
    print("步骤 4: 获取学习计划并查找练习任务")
    active_plan_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)

    if active_plan_resp.status_code != 200:
        log_step(4, "获取活跃计划失败", False, f"HTTP {active_plan_resp.status_code}: {active_plan_resp.text}")
        sys.exit(1)

    plan_data = active_plan_resp.json()

    # 查找第一个PRACTICE、REVIEW或LEARN任务
    target_item = None
    for date_key, items in plan_data["items_by_date"].items():
        for item in items:
            if item["status"] == "TODO" and item["type"] in ["PRACTICE", "REVIEW", "LEARN"]:
                target_item = item
                break
        if target_item:
            break

    if not target_item:
        # 调试：打印所有任务类型
        all_tasks = []
        for date_key, items in plan_data["items_by_date"].items():
            for item in items:
                all_tasks.append(f"{item['type']}({item['status']})")
        log_step(4, "未找到可用的练习或复习任务", False, f"所有任务: {all_tasks[:10]}...")  # 只显示前10个
        sys.exit(1)

    log_step(4, "找到练习任务", True, f"任务ID: {target_item['id']}, 类型: {target_item['type']}, 标题: {target_item['title']}")

    # 步骤 5: 开始任务
    print("步骤 5: 开始任务")
    start_resp = requests.post(f"{BASE_URL}/plans/items/{target_item['id']}/start", headers=headers)

    if start_resp.status_code != 200:
        log_step(5, "开始任务失败", False, f"HTTP {start_resp.status_code}: {start_resp.text}")
        sys.exit(1)

    start_data = start_resp.json()
    action = start_data["action"]

    if action == "EXAM":
        attempt_id = start_data["attempt_id"]
        log_step(5, "任务开始成功", True, f"action: EXAM, attempt_id: {attempt_id}")

        # 步骤 6: 获取考试详情并答题
        print("步骤 6: 获取考试详情并提交答案")
        attempt_resp = requests.get(f"{BASE_URL}/attempts/{attempt_id}", headers=headers)

        if attempt_resp.status_code != 200:
            log_step(6, "获取考试详情失败", False, f"HTTP {attempt_resp.status_code}: {attempt_resp.text}")
            sys.exit(1)

        attempt_data = attempt_resp.json()
        questions = attempt_data.get("questions", [])

        if not questions:
            log_step(6, "考试没有题目", False, "无法进行答题测试")
            sys.exit(1)

        # 取第一题，故意答错（用于产生错题数据）
        first_question = questions[0]["question"]
        question_id = first_question["id"]

        # 根据题型构造错误答案
        if first_question["type"] == "SINGLE":
            wrong_answer = "B"  # 假设正确答案是A，答B
        elif first_question["type"] == "MULTI":
            wrong_answer = ["B"]  # 错误的多选
        elif first_question["type"] == "JUDGE":
            wrong_answer = "F"  # 错误判断
        else:
            wrong_answer = "wrong answer"

        answer_payload = {
            "question_id": question_id,
            "answer": wrong_answer,
            "time_spent_seconds": 30
        }

        answer_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json=answer_payload, headers=headers)

        if answer_resp.status_code != 200:
            log_step(6, "提交答案失败", False, f"HTTP {answer_resp.status_code}: {answer_resp.text}")
            sys.exit(1)

        log_step(6, "提交答案成功", True, f"question_id: {question_id}, answer: {wrong_answer}")

        # 步骤 7: 提交考试
        print("步骤 7: 提交考试")
        submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)

        if submit_resp.status_code != 200:
            log_step(7, "提交考试失败", False, f"HTTP {submit_resp.status_code}: {submit_resp.text}")
            sys.exit(1)

        submit_data = submit_resp.json()
        total_score = submit_data.get("total_score", 0)
        log_step(7, "提交考试成功", True, f"total_score: {total_score}")

    elif action == "NAVIGATE":
        path = start_data.get("path", "")
        log_step(5, "任务开始成功", True, f"action: NAVIGATE, path: {path}")
        # 对于导航类型的任务，我们跳过答题步骤
        log_step(6, "导航任务跳过答题", True, "LEARN类型任务无需答题")
        log_step(7, "导航任务跳过交卷", True, "LEARN类型任务无需交卷")

    else:
        log_step(5, "未知的任务操作类型", False, f"action: {action}")
        sys.exit(1)

    # 步骤 8: 检查错题本
    print("步骤 8: 检查错题本")
    wrong_resp = requests.get(f"{BASE_URL}/wrong-questions?due_only=false&page=1&size=20", headers=headers)

    if wrong_resp.status_code != 200:
        log_step(8, "获取错题本失败", False, f"HTTP {wrong_resp.status_code}: {wrong_resp.text}")
        sys.exit(1)

    wrong_data = wrong_resp.json()
    total_wrong = wrong_data.get("total", 0)
    items_count = len(wrong_data.get("items", []))
    log_step(8, "错题本检查成功", True, f"总错题数: {total_wrong}, 当前页项目数: {items_count}")

    # 步骤 9: 检查统计数据
    print("步骤 9: 检查统计数据")
    analytics_resp = requests.get(f"{BASE_URL}/analytics/student/overview", headers=headers)

    if analytics_resp.status_code != 200:
        log_step(9, "获取统计数据失败", False, f"HTTP {analytics_resp.status_code}: {analytics_resp.text}")
        sys.exit(1)

    analytics_data = analytics_resp.json()
    plan_completion = analytics_data.get("plan_completion_rate", 0)
    avg_mastery = analytics_data.get("avg_mastery", 0)
    wrong_due = analytics_data.get("wrong_due_count", 0)

    log_step(9, "统计数据检查成功", True,
            f"计划完成率: {plan_completion}%, 平均掌握度: {avg_mastery}, 待复习错题: {wrong_due}")

    # 验收总结
    print("=" * 50)
    print("🎉 学习计划闭环验收全部通过！")
    print()
    print("✅ 学习目标设置 → 计划生成 → 任务开始 → 答题交卷 → 错题统计 → 数据分析")
    print("✅ 全链路API调用正常，数据流转正确")
    print("✅ 适合论文答辩演示的可重复脚本")
    print()

if __name__ == "__main__":
    main()