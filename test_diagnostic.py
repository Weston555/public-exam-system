#!/usr/bin/env python3
"""
测试诊断卷生成功能
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_diagnostic():
    print("🧪 测试诊断卷生成功能")

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

    # 测试诊断卷生成
    print("\n1. 测试诊断卷生成...")
    diag_resp = requests.post(f"{BASE_URL}/admin/exams/diagnostic/regenerate", headers=admin_headers)
    print(f"   状态码: {diag_resp.status_code}")
    if diag_resp.status_code == 200:
        diag_data = diag_resp.json()
        print(f"   考试ID: {diag_data.get('exam_id')}")
        print(f"   试卷ID: {diag_data.get('paper_id')}")
        print(f"   标题: {diag_data.get('title')}")
        print("   ✅ 诊断卷生成成功")
    else:
        print(f"   ❌ 诊断卷生成失败: {diag_resp.text}")

if __name__ == "__main__":
    test_diagnostic()
