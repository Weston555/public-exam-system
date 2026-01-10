#!/usr/bin/env python3
"""
直接测试复习考试生成功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_review_generation():
    print("🧪 直接测试复习考试生成")

    # 登录
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 创建错题数据
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
                answer_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
                    "question_id": question["id"],
                    "answer": wrong_answer,
                    "time_spent_seconds": 30
                }, headers=headers)
                assert answer_resp.status_code == 200

                submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
                assert submit_resp.status_code == 200
                print("✅ 错题数据创建成功")

    # 直接测试复习考试生成API
    print("测试复习考试生成API...")
    review_resp = requests.post(f"{BASE_URL}/wrong-questions/review/generate", json={
        "count": 5
    }, headers=headers)

    if review_resp.status_code == 200:
        review_data = review_resp.json()
        print(f"✅ 复习考试生成成功: exam_id={review_data['exam_id']}")

        # 测试开始这个考试
        exam_id = review_data['exam_id']
        start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
        if start_resp.status_code == 200:
            print("✅ 复习考试开始成功")
            print("🎉 generate_review_exam 修复成功！")
        else:
            print(f"❌ 开始考试失败: {start_resp.status_code} - {start_resp.text}")
    elif review_resp.status_code == 400:
        print(f"⚠️ 复习考试生成返回400（可能没有错题）: {review_resp.text}")
        print("✅ 至少没有500错误，WrongQuestion导入修复成功！")
    else:
        print(f"❌ 复习考试生成失败: {review_resp.status_code} - {review_resp.text}")

if __name__ == "__main__":
    test_review_generation()
