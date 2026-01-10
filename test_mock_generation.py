#!/usr/bin/env python3
"""
测试个性化模拟卷生成功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_mock_generation():
    print("🧪 测试个性化模拟卷生成")

    # 登录
    login_resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ 登录成功")

    # 创建一些掌握度数据（模拟学习过程）
    print("创建掌握度数据...")
    # 这里我们可以手动创建一些UserKnowledgeState记录
    # 为了简化测试，我们直接调用生成接口

    # 生成个性化模拟卷
    print("生成个性化模拟卷...")
    mock_resp = requests.post(f"{BASE_URL}/exams/mock/generate", json={
        "count": 5,  # 减少题目数量
        "duration_minutes": 30
    }, headers=headers)

    if mock_resp.status_code == 200:
        mock_data = mock_resp.json()
        exam_id = mock_data["exam_id"]
        print(f"✅ 模拟卷生成成功: exam_id={exam_id}")

        # 开始考试
        start_resp = requests.post(f"{BASE_URL}/exams/{exam_id}/start", headers=headers)
        assert start_resp.status_code == 200
        attempt_id = start_resp.json()["attempt_id"]
        print(f"✅ 考试开始成功: attempt_id={attempt_id}")

        # 验证考试类别
        exams_resp = requests.get(f"{BASE_URL}/exams?page=1&size=10", headers=headers)
        if exams_resp.status_code == 200:
            exams = exams_resp.json()["items"]
            mock_exam = next((e for e in exams if e["id"] == exam_id), None)
            if mock_exam:
                assert mock_exam["category"] == "MOCK", f"考试类别错误: {mock_exam['category']}"
                print("✅ 考试类别验证正确: MOCK")

        print("🎉 个性化模拟卷生成功能验证成功！")
    else:
        print(f"❌ 模拟卷生成失败: {mock_resp.status_code} - {mock_resp.text}")

if __name__ == "__main__":
    test_mock_generation()
