#!/usr/bin/env python3
"""
测试交卷后自动完成计划任务功能
"""

import requests
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_auto_complete():
    print("🧪 测试交卷后自动完成计划任务")

    # 登录
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 创建错题数据，确保有REVIEW任务
    print("创建错题数据...")
    exams_resp = requests.get(f"{BASE_URL}/exams?category=DIAGNOSTIC&page=1&size=1", headers=headers)
    if exams_resp.status_code == 200 and exams_resp.json()["items"]:
        exam_id = exams_resp.json()["items"][0]["id"]
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
                print("✅ 错题数据创建成功")

    # 生成学习计划
    plan_resp = requests.post(f"{BASE_URL}/plans/generate", json={"days": 7}, headers=headers)
    assert plan_resp.status_code == 200
    print("✅ 学习计划生成成功")

    # 查找PRACTICE或REVIEW任务
    active_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
    assert active_resp.status_code == 200
    plan_data = active_resp.json()

    target_item = None
    for date_key, items in plan_data["items_by_date"].items():
        for item in items:
            if item["status"] == "TODO" and item["type"] in ["PRACTICE", "REVIEW"]:
                target_item = item
                break
        if target_item:
            break

    if not target_item:
        print("❌ 没有找到PRACTICE或REVIEW任务，无法测试自动完成")
        return

    print(f"✅ 找到任务: {target_item['type']} - {target_item['title']} (ID: {target_item['id']})")
    print(f"   初始状态: status={target_item['status']}, exam_id={target_item.get('exam_id')}")

    # 开始任务
    start_resp = requests.post(f"{BASE_URL}/plans/items/{target_item['id']}/start", headers=headers)
    assert start_resp.status_code == 200

    start_data = start_resp.json()
    assert start_data["action"] == "EXAM"
    attempt_id = start_data["attempt_id"]

    print(f"✅ 任务开始成功，获得attempt_id: {attempt_id}")

    # 获取考试详情并答题
    attempt_resp = requests.get(f"{BASE_URL}/attempts/{attempt_id}", headers=headers)
    assert attempt_resp.status_code == 200
    attempt_data = attempt_resp.json()
    questions = attempt_data["questions"]

    if questions:
        question = questions[0]["question"]
        # 答题（可以答对或答错）
        answer = "A" if question["type"] == "SINGLE" else ["A"]
        requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
            "question_id": question["id"],
            "answer": answer,
            "time_spent_seconds": 30
        }, headers=headers)

        # 提交考试
        submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
        assert submit_resp.status_code == 200
        print("✅ 考试提交成功")

        # 等待一下确保数据处理完成
        time.sleep(2)

        # 检查计划任务是否自动完成
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
        assert updated_item["status"] == "DONE", f"任务状态未自动更新为DONE，当前: {updated_item['status']}"
        assert updated_item["completed_at"] is not None, "任务完成时间未设置"

        print("✅ 计划任务自动完成验证成功！")
        print(f"   状态变化: {target_item['status']} → {updated_item['status']}")
        print(f"   exam_id: {target_item.get('exam_id')} → {updated_item.get('exam_id')}")
        print(f"   completed_at: {updated_item['completed_at']}")

        print("🎉 交卷后自动完成计划任务功能验证成功！")
    else:
        print("⚠️ 考试没有题目，跳过测试")

if __name__ == "__main__":
    test_auto_complete()
