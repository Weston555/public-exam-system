#!/usr/bin/env python3
"""
测试复习任务开始功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_review_start():
    print("🧪 测试复习任务开始功能")

    # 登录
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 先创建一些错题数据，确保有REVIEW任务
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

    # 生成计划
    requests.post(f"{BASE_URL}/plans/generate", json={"days": 14}, headers=headers)
    print("✅ 学习计划生成成功")

    # 获取活跃计划
    plan_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
    assert plan_resp.status_code == 200
    plan = plan_resp.json()

    # 查找REVIEW任务
    item = None
    for d, items in plan['items_by_date'].items():
        for it in items:
            if it['status'] == 'TODO' and it['type'] == 'REVIEW':
                item = it
                break
        if item:
            break

    print(f"REVIEW item: {item and item['id']}")

    if item:
        # 测试开始REVIEW任务
        r = requests.post(f"{BASE_URL}/plans/items/{item['id']}/start", headers=headers)
        print(f"开始任务响应: {r.status_code}")
        if r.status_code == 200:
            print(f"响应内容: {r.json()}")
            print("✅ REVIEW任务开始成功！")
        else:
            print(f"❌ 开始失败: {r.text}")
    else:
        print("⚠️ 没有找到REVIEW任务")

if __name__ == "__main__":
    test_review_start()
