#!/usr/bin/env python3
"""
自测脚本：验证热修后的功能
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_hotfix():
    print("🔥 开始热修复验证...")

    # 1. 登录
    print("1. 登录 student01...")
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200, f"登录失败: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 2. 测试获取诊断考试（用于测试判分功能）
    print("2. 获取诊断考试列表...")
    exams_resp = requests.get(f"{BASE_URL}/exams?category=DIAGNOSTIC&page=1&size=1", headers=headers)
    assert exams_resp.status_code == 200, f"获取考试列表失败: {exams_resp.text}"

    exams_data = exams_resp.json()
    if not exams_data["items"]:
        print("⚠️ 没有诊断考试，跳过判分测试")
        attempt_id = None
    else:
        exam_id = exams_data["items"][0]["id"]
        print(f"找到诊断考试，exam_id: {exam_id}")

        # 3. 开始考试
        print("3. 开始诊断考试...")
        start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
        assert start_resp.status_code == 200, f"开始考试失败: {start_resp.text}"
        attempt_id = start_resp.json()["attempt_id"]
        print(f"✅ 开始考试成功，attempt_id: {attempt_id}")

        # 4. 提交至少一题答案
        questions = start_resp.json()["questions"]
        if questions:
            print("4. 提交答案...")
            question_data = questions[0]
            question = question_data["question"]

            # 根据题型构造答案
            if question["type"] == "SINGLE":
                answer = "A"
            elif question["type"] == "MULTI":
                answer = ["A"]
            elif question["type"] == "JUDGE":
                answer = "T"
            else:
                answer = "test"

            submit_answer_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/answer", json={
                "question_id": question["id"],
                "answer": answer,
                "time_spent_seconds": 30
            }, headers=headers)
            assert submit_answer_resp.status_code == 200, f"提交答案失败: {submit_answer_resp.text}"
            print("✅ 提交答案成功")

            # 5. 提交考试（测试判分功能和PaperQuestion导入）
            print("5. 提交考试（测试判分和PaperQuestion导入）...")
            submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
            assert submit_resp.status_code == 200, f"提交考试失败: {submit_resp.text}"
            print(f"✅ 提交考试成功，total_score: {submit_resp.json().get('total_score')}")
        else:
            print("⚠️ 考试没有题目，跳过答案提交")
            attempt_id = None

    # 6. 测试错题本接口
    print("6. 测试错题本接口...")
    wrong_resp = requests.get(f"{BASE_URL}/wrong-questions?due_only=false&page=1&size=20", headers=headers)
    assert wrong_resp.status_code == 200, f"错题本查询失败: {wrong_resp.text}"
    wrong_data = wrong_resp.json()
    assert "total" in wrong_data, "返回数据缺少total字段"
    assert isinstance(wrong_data["total"], int), "total不是整数"
    print(f"✅ 错题本查询成功，total: {wrong_data['total']}, items: {len(wrong_data['items'])}")

    print("🎉 所有热修复验证通过！")

if __name__ == "__main__":
    test_hotfix()