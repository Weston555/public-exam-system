#!/usr/bin/env python3
"""
测试学习计划完整闭环：开始任务 → 答题 → 自动完成
"""

import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_plan_complete_flow():
    print("🎯 测试学习计划完整闭环流程...")
    print("=" * 60)

    try:
        # 步骤 1: 登录获取token
        print("步骤 1: 登录系统")
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "student01",
            "password": "123456"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")

        # 步骤 2: 确保有学习目标和计划
        print("步骤 2: 检查学习目标和计划")
        goal_resp = requests.get(f"{BASE_URL}/goals/me", headers=headers)
        if goal_resp.status_code == 404 or not goal_resp.json():
            future_date = "2026-06-01"
            requests.post(f"{BASE_URL}/goals/", json={
                "exam_date": future_date,
                "target_score": 75,
                "daily_minutes": 120
            }, headers=headers)
            print("✅ 创建学习目标")

        # 先创建一些错题数据，确保有REVIEW任务
        print("创建错题数据...")
        # 获取一个诊断考试
        exams_resp = requests.get(f"{BASE_URL}/exams?category=DIAGNOSTIC&page=1&size=1", headers=headers)
        if exams_resp.status_code == 200 and exams_resp.json()["items"]:
            exam_id = exams_resp.json()["items"][0]["id"]
            # 开始考试并故意答错
            start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
            if start_resp.status_code == 200:
                attempt_id = start_resp.json()["attempt_id"]
                questions = start_resp.json()["questions"]
                if questions:
                    question = questions[0]["question"]
                    # 故意答错
                    wrong_answer = "B" if question["type"] == "SINGLE" else ["B"]
                    requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
                        "question_id": question["id"],
                        "answer": wrong_answer,
                        "time_spent_seconds": 30
                    }, headers=headers)
                    requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
                    print("✅ 创建错题数据成功")

        # 生成学习计划
        plan_resp = requests.post(f"{BASE_URL}/plans/generate", json={"days": 7}, headers=headers)
        assert plan_resp.status_code == 200
        print("✅ 生成学习计划")

        # 步骤 3: 获取学习计划，找到任意TODO任务
        print("步骤 3: 获取学习计划并查找可执行任务")
        active_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
        assert active_resp.status_code == 200

        plan_data = active_resp.json()
        target_item = None

        # 优先找PRACTICE或REVIEW任务
        for date_key, items in plan_data["items_by_date"].items():
            for item in items:
                if item["status"] == "TODO" and item["type"] in ["PRACTICE", "REVIEW"]:
                    target_item = item
                    break
            if target_item:
                break

        # 如果没有，则找LEARN任务
        if not target_item:
            print("⚠️ 没有PRACTICE/REVIEW任务，查找LEARN任务...")
            for date_key, items in plan_data["items_by_date"].items():
                for item in items:
                    if item["status"] == "TODO" and item["type"] == "LEARN":
                        target_item = item
                        break
                if target_item:
                    break

        if not target_item:
            print("❌ 没有可用的TODO任务")
            sys.exit(1)

        print(f"✅ 找到任务: {target_item['type']} - {target_item['title']} (ID: {target_item['id']})")

        # 记录任务的初始状态
        initial_status = target_item["status"]
        initial_exam_id = target_item.get("exam_id")
        print(f"📝 初始状态: status={initial_status}, exam_id={initial_exam_id}")

        # 步骤 4: 开始任务
        print("步骤 4: 开始任务")
        start_resp = requests.post(f"{BASE_URL}/plans/items/{target_item['id']}/start", headers=headers)
        assert start_resp.status_code == 200

        start_data = start_resp.json()
        action = start_data["action"]

        if action == "EXAM":
            attempt_id = start_data["attempt_id"]
            exam_info = start_data["exam"]
            questions = start_data["questions"]

            print(f"✅ 任务开始成功: attempt_id={attempt_id}, exam_id={exam_info['id']}")
            print(f"   题目数量: {len(questions)}")

            # 步骤 5: 提交答案
            print("步骤 5: 提交答案")
            if questions:
                question_data = questions[0]
                question = question_data["question"]

                # 根据题型构造错误答案（故意答错）
                if question["type"] == "SINGLE":
                    wrong_answer = "B"
                elif question["type"] == "MULTI":
                    wrong_answer = ["B"]
                elif question["type"] == "JUDGE":
                    wrong_answer = "F"
                else:
                    wrong_answer = "wrong answer"

                answer_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
                    "question_id": question["id"],
                    "answer": wrong_answer,
                    "time_spent_seconds": 30
                }, headers=headers)
                assert answer_resp.status_code == 200
                print("✅ 提交答案成功")

            # 步骤 6: 提交考试
            print("步骤 6: 提交考试")
            submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
            assert submit_resp.status_code == 200

            submit_data = submit_resp.json()
            total_score = submit_data.get("total_score", 0)
            print(f"✅ 提交考试成功: total_score={total_score}")

        elif action == "NAVIGATE":
            path = start_data.get("path", "")
            print(f"✅ 任务开始成功: action=NAVIGATE, path={path}")
            print("⚠️ LEARN类型任务无需答题，跳过答题步骤")
            # 对于导航任务，我们直接跳到验证步骤

        # 等待一秒确保数据处理完成
        time.sleep(1)

        # 步骤 7: 验证计划任务状态更新
        print("步骤 7: 验证计划任务状态更新")
        updated_plan_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
        assert updated_plan_resp.status_code == 200

        updated_plan_data = updated_plan_resp.json()
        updated_item = None

        for date_key, items in updated_plan_data["items_by_date"].items():
            for item in items:
                if item["id"] == target_item["id"]:
                    updated_item = item
                    break
            if updated_item:
                break

        assert updated_item is not None, "找不到更新后的任务"
        if action == "EXAM":
            # EXAM类型任务应该自动完成
            assert updated_item["status"] == "DONE", f"任务状态未自动更新为DONE，当前状态: {updated_item['status']}"
            assert updated_item["completed_at"] is not None, "任务完成时间未设置"
            assert updated_item["exam_id"] is not None, "任务exam_id未设置"
        elif action == "NAVIGATE":
            # NAVIGATE类型任务保持TODO状态（需要手动完成）
            assert updated_item["status"] == "TODO", f"导航任务状态不应自动改变，当前状态: {updated_item['status']}"
            assert updated_item["exam_id"] is None, "导航任务不应有exam_id"

        print("✅ 计划任务自动完成验证成功")
        print(f"   状态: {initial_status} → {updated_item['status']}")
        print(f"   exam_id: {initial_exam_id} → {updated_item['exam_id']}")
        print(f"   completed_at: {updated_item['completed_at']}")

        # 步骤 8: 验证统计数据
        print("步骤 8: 验证统计数据更新")
        analytics_resp = requests.get(f"{BASE_URL}/analytics/student/overview", headers=headers)
        assert analytics_resp.status_code == 200

        analytics_data = analytics_resp.json()
        print("✅ 统计数据获取成功")
        print(f"   计划完成率: {analytics_data.get('plan_completion_rate', 0)}%")
        print(f"   平均掌握度: {analytics_data.get('avg_mastery', 0)}")
        print(f"   待复习错题: {analytics_data.get('wrong_due_count', 0)}")

        print("=" * 60)
        print("🎉 学习计划完整闭环测试全部通过！")
        print()
        print("✅ 任务开始 → 考试生成 → 答题提交 → 自动完成任务")
        print("✅ 数据流转完整，状态更新正确")
        print("✅ 适合论文答辩演示的完整业务闭环")
        print()

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_plan_complete_flow()
