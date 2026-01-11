#!/usr/bin/env python3
"""
测试MOCK组卷功能 - 验证ratio key修复
"""
import requests
import sys
import os

# 添加服务器路径
sys.path.append('server')

def test_mock_generation():
    print("🧪 测试MOCK组卷功能")

    # 1. 登录获取token
    try:
        response = requests.post('http://localhost:8000/api/v1/auth/login', json={
            'username': 'student01',
            'password': '123456'
        })
        response.raise_for_status()
        token = response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print("✅ 管理员登录成功")
    except Exception as e:
        print(f"❌ 登录失败: {e}")
        return False

    # 2. 生成MOCK考试
    try:
        response = requests.post('http://localhost:8000/api/v1/exams/mock/generate',
                               json={'count': 20, 'duration_minutes': 60},
                               headers=headers)
        response.raise_for_status()
        data = response.json()
        exam_id = data['exam_id']
        paper_id = data['paper_id']
        print(f"✅ 模拟卷生成成功: exam_id={exam_id}, paper_id={paper_id}")
    except Exception as e:
        print(f"❌ 模拟卷生成失败: {e}")
        return False

    # 3. 开始考试验证有题目
    try:
        response = requests.post(f'http://localhost:8000/api/v1/exams/{exam_id}/start',
                               headers=headers)
        response.raise_for_status()
        attempt_data = response.json()
        attempt_id = attempt_data['attempt_id']

        # 获取第一道题目验证
        response = requests.get(f'http://localhost:8000/api/v1/attempts/{attempt_id}',
                               headers=headers)
        response.raise_for_status()
        attempt_detail = response.json()

        questions = attempt_detail.get('questions', [])
        if len(questions) > 0:
            print(f"✅ 考试开始成功，获取到 {len(questions)} 道题目")
            return True
        else:
            print("❌ 考试开始成功但没有题目")
            return False

    except Exception as e:
        print(f"❌ 考试开始失败: {e}")
        return False

if __name__ == '__main__':
    success = test_mock_generation()
    if success:
        print("\n🎉 MOCK组卷功能测试通过")
    else:
        print("\n💥 MOCK组卷功能测试失败")
        sys.exit(1)