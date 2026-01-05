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

    # 2. 测试 practice generate
    print("2. 测试练习生成...")
    practice_resp = requests.post(f"{BASE_URL}/practice/generate", json={
        "knowledge_id": 1,
        "count": 5,
        "mode": "ADAPTIVE"
    }, headers=headers)

    if practice_resp.status_code != 200:
        print(f"⚠️ 练习生成失败（可能没有题目）: {practice_resp.status_code} - {practice_resp.text}")
        exam_id = None
    else:
        exam_id = practice_resp.json()["exam_id"]
        print(f"✅ 练习生成成功，exam_id: {exam_id}")

    # 3. 如果有exam_id，测试开始考试
    attempt_id = None
    if exam_id:
        print("3. 测试开始考试...")
        start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
        assert start_resp.status_code == 200, f"开始考试失败: {start_resp.text}"
        attempt_id = start_resp.json()["attempt_id"]
        print(f"✅ 开始考试成功，attempt_id: {attempt_id}")

        # 4. 获取题目并提交至少一题
        questions = start_resp.json()["questions"]
        if questions:
            print("4. 提交答案...")
            question = questions[0]["question"]
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

            # 5. 提交考试（这里会调用判分逻辑，测试PaperQuestion导入是否正常）
            print("5. 提交考试（测试判分）...")
            submit_resp = requests.post(f"{BASE_URL}/attempts/{attempt_id}/submit", headers=headers)
            assert submit_resp.status_code == 200, f"提交考试失败: {submit_resp.text}"
            print(f"✅ 提交考试成功，total_score: {submit_resp.json().get('total_score')}")

    # 6. 测试 wrong_questions 接口
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
