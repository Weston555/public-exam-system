#!/usr/bin/env python3
"""
测试模板化组卷功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_paper_template():
    print("🧪 测试模板化组卷功能")

    # 登录管理员
    admin_login = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if admin_login.status_code != 200:
        print("❌ 管理员登录失败")
        return

    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("✅ 管理员登录成功")

    # 测试诊断试卷生成
    print("\n1. 测试诊断试卷生成...")
    diag_resp = requests.post(f"{BASE_URL}/admin/exams/diagnostic/regenerate", headers=admin_headers)
    print(f"   状态码: {diag_resp.status_code}")
    if diag_resp.status_code == 200:
        diag_data = diag_resp.json()
        print(f"   生成考试ID: {diag_data.get('exam_id')}")
        print("   ✅ 诊断试卷生成成功")
    else:
        print(f"   ❌ 诊断试卷生成失败: {diag_resp.text}")

    # 登录学生
    student_login = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "student01",
        "password": "123456"
    })
    if student_login.status_code != 200:
        print("❌ 学生登录失败")
        return

    student_token = student_login.json()["access_token"]
    student_headers = {"Authorization": f"Bearer {student_token}"}
    print("✅ 学生登录成功")

    # 测试模拟试卷生成
    print("\n2. 测试模拟试卷生成...")
    mock_resp = requests.post(f"{BASE_URL}/exams/mock/generate", json={
        "count": 10,
        "duration_minutes": 30
    }, headers=student_headers)

    print(f"   状态码: {mock_resp.status_code}")
    if mock_resp.status_code == 200:
        mock_data = mock_resp.json()
        print(f"   生成考试ID: {mock_data.get('exam_id')}")
        print("   ✅ 模拟试卷生成成功")
    else:
        print(f"   ❌ 模拟试卷生成失败: {mock_resp.text}")

if __name__ == "__main__":
    test_paper_template()
