#!/usr/bin/env python3
"""
手动测试交卷后自动完成计划任务
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_manual_complete():
    print("🧪 手动测试交卷后自动完成计划任务")

    # 登录
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 创建复习考试
    review_resp = requests.post(f"{BASE_URL}/wrong-questions/review/generate", json={
        "count": 5
    }, headers=headers)

    if review_resp.status_code == 200:
        review_data = review_resp.json()
        exam_id = review_data["exam_id"]
        print(f"✅ 复习考试生成成功: exam_id={exam_id}")

        # 开始考试
        start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
        assert start_resp.status_code == 200
        attempt_id = start_resp.json()["attempt_id"]
        print(f"✅ 考试开始成功: attempt_id={attempt_id}")

        # 答题
        questions = start_resp.json()["questions"]
        if questions:
            question = questions[0]["question"]
            answer = "A" if question["type"] == "SINGLE" else ["A"]
            answer_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
                "question_id": question["id"],
                "answer": answer,
                "time_spent_seconds": 30
            }, headers=headers)
            assert answer_resp.status_code == 200
            print("✅ 答题成功")

            # 提交考试 - 这里应该触发自动完成逻辑
            submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
            assert submit_resp.status_code == 200
            print("✅ 考试提交成功")

            print("🎉 交卷成功！如果有对应的计划任务，应该已经自动完成了")
            print("请手动检查学习计划页面是否显示任务完成状态")
        else:
            print("⚠️ 考试没有题目")
    else:
        print(f"❌ 复习考试生成失败: {review_resp.status_code} - {review_resp.text}")

if __name__ == "__main__":
    test_manual_complete()
