#!/usr/bin/env python3
"""
测试模块掌握度聚合接口
"""

import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_module_mastery():
    print("🧪 测试模块掌握度聚合接口")

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

    # 测试行测模块掌握度
    print("\n1. 测试行测模块掌握度...")
    xingce_resp = requests.get(f"{BASE_URL}/analytics/student/module-mastery?subject=XINGCE", headers=student_headers)
    print(f"   状态码: {xingce_resp.status_code}")
    if xingce_resp.status_code == 200:
        xingce_data = xingce_resp.json()
        print("   ✅ 行测模块掌握度获取成功")
        print(f"   科目: {xingce_data.get('subject')}")
        print(f"   模块数量: {len(xingce_data.get('items', []))}")
        for item in xingce_data.get('items', [])[:3]:  # 只显示前3个
            print(f"     - {item['module']}: {item['mastery']}%")
    else:
        print(f"   ❌ 行测模块掌握度获取失败: {xingce_resp.text}")

    # 测试申论模块掌握度
    print("\n2. 测试申论模块掌握度...")
    shenlun_resp = requests.get(f"{BASE_URL}/analytics/student/module-mastery?subject=SHENLUN", headers=student_headers)
    print(f"   状态码: {shenlun_resp.status_code}")
    if shenlun_resp.status_code == 200:
        shenlun_data = shenlun_resp.json()
        print("   ✅ 申论模块掌握度获取成功")
        print(f"   科目: {shenlun_data.get('subject')}")
        print(f"   模块数量: {len(shenlun_data.get('items', []))}")
        for item in shenlun_data.get('items', [])[:3]:  # 只显示前3个
            print(f"     - {item['module']}: {item['mastery']}%")
    else:
        print(f"   ❌ 申论模块掌握度获取失败: {shenlun_resp.text}")

    # 测试无效科目参数
    print("\n3. 测试无效科目参数...")
    invalid_resp = requests.get(f"{BASE_URL}/analytics/student/module-mastery?subject=INVALID", headers=student_headers)
    print(f"   状态码: {invalid_resp.status_code}")
    if invalid_resp.status_code == 400:
        print("   ✅ 无效科目参数正确返回400错误")
    else:
        print(f"   ❌ 无效科目参数处理异常: {invalid_resp.text}")

if __name__ == "__main__":
    test_module_mastery()
