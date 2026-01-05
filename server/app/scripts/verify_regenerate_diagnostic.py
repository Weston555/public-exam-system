#!/usr/bin/env python3
"""
诊断卷重新生成验收脚本

验证诊断卷生成服务的完整性：
1. admin 登录并调用重新生成接口
2. student 登录并拉取诊断考试列表
3. 验证有至少一个诊断考试
4. 开始考试验证题目非空

运行方式: python verify_regenerate_diagnostic.py
"""
import sys
import os
import requests
import json
from datetime import datetime

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    """主函数"""
    # API 基础地址 (假设服务器运行在 localhost:8000)
    base_url = "http://localhost:8000/api/v1"

    print("🚀 开始诊断卷重新生成验收测试...")

    # 1. admin 登录并重新生成诊断卷
    print("📋 步骤1: admin 登录并重新生成诊断卷...")
    admin_login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(f"{base_url}/auth/login", json=admin_login_data)
        response.raise_for_status()
        admin_result = response.json()
        admin_token = admin_result["access_token"]
        print("✅ admin 登录成功")
    except requests.exceptions.RequestException as e:
        print(f"❌ admin 登录失败: {e}")
        print("请确保服务器正在运行且数据库已初始化")
        return False

    admin_headers = {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }

    # 调用重新生成接口
    try:
        response = requests.post(f"{base_url}/admin/exams/diagnostic/regenerate", headers=admin_headers)
        response.raise_for_status()
        regenerate_result = response.json()
        print(f"✅ 诊断卷重新生成成功: {regenerate_result['message']}")
        print(f"   考试ID: {regenerate_result['exam_id']}")
        print(f"   试卷ID: {regenerate_result['paper_id']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 重新生成诊断卷失败: {e}")
        return False

    # 2. student 登录
    print("📋 步骤2: student 登录...")
    student_login_data = {
        "username": "student01",
        "password": "123456"
    }

    try:
        response = requests.post(f"{base_url}/auth/login", json=student_login_data)
        response.raise_for_status()
        student_result = response.json()
        student_token = student_result["access_token"]
        print("✅ student 登录成功")
    except requests.exceptions.RequestException as e:
        print(f"❌ student 登录失败: {e}")
        return False

    student_headers = {
        "Authorization": f"Bearer {student_token}",
        "Content-Type": "application/json"
    }

    # 3. 拉取诊断考试列表
    print("📋 步骤3: 拉取诊断考试列表...")
    try:
        response = requests.get(f"{base_url}/exams?category=DIAGNOSTIC", headers=student_headers)
        response.raise_for_status()
        exams_result = response.json()
        exams = exams_result.get("items", [])

        if not exams:
            print("❌ 验收失败：没有找到诊断考试")
            return False

        print(f"✅ 找到 {len(exams)} 个诊断考试")
        for exam in exams:
            print(f"   - {exam['title']} (ID: {exam['id']}, 题目数: {exam['total_questions']})")

        # 选择第一个考试
        first_exam = exams[0]
        exam_id = first_exam["id"]

    except requests.exceptions.RequestException as e:
        print(f"❌ 拉取诊断考试列表失败: {e}")
        return False

    # 4. 开始考试验证题目
    print("📋 步骤4: 开始考试验证题目...")
    try:
        response = requests.post(f"{base_url}/exams/{exam_id}/start", headers=student_headers)
        response.raise_for_status()
        start_result = response.json()

        questions = start_result.get("questions", [])
        if not questions:
            print("❌ 验收失败：考试题目为空")
            return False

        print(f"✅ 考试开始成功，包含 {len(questions)} 道题目")
        print(f"   考试标题: {start_result['exam']['title']}")
        print(f"   考试时长: {start_result['exam']['duration_minutes']} 分钟")

        # 检查题目结构
        sample_question = questions[0]
        if "question" not in sample_question or "type" not in sample_question["question"]:
            print("❌ 验收失败：题目结构不完整")
            return False

        print(f"   示例题目: {sample_question['question']['stem'][:50]}...")
        print(f"   题目类型: {sample_question['question']['type']}")

        print("🎉 验收通过！诊断卷重新生成功能工作正常")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ 开始考试失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 所有验收测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 验收测试失败！")
        sys.exit(1)
