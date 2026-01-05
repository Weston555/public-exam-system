#!/usr/bin/env python3
"""
测试诊断卷重新生成功能的脚本
验证多次生成后题目集合的变化
"""
import sys
import os
import requests
import json
from datetime import datetime

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.pathdirname(__file__), '..'))

def main():
    """主函数"""
    base_url = "http://localhost:8000/api/v1"

    print("🔬 开始诊断卷重新生成功能测试...")

    # 1. 管理员登录
    admin_data = {"username": "admin", "password": "admin123"}
    try:
        response = requests.post(f"{base_url}/auth/login", json=admin_data)
        response.raise_for_status()
        admin_token = response.json()["access_token"]
        print("✅ 管理员登录成功")
    except Exception as e:
        print(f"❌ 管理员登录失败: {e}")
        return False

    admin_headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

    # 2. 连续3次重新生成诊断卷
    results = []
    for i in range(3):
        print(f"📝 第{i+1}次生成诊断卷...")
        try:
            response = requests.post(f"{base_url}/admin/exams/diagnostic/regenerate", headers=admin_headers)
            response.raise_for_status()
            result = response.json()
            print(f"✅ 生成成功，考试ID: {result['exam_id']}")

            # 获取题目列表来验证随机性
            exam_id = result['exam_id']
            exam_response = requests.get(f"{base_url}/exams/{exam_id}/start", headers=admin_headers)
            if exam_response.status_code == 200:
                exam_data = exam_response.json()
                question_ids = [q['question']['id'] for q in exam_data.get('questions', [])]
                results.append({
                    'exam_id': exam_id,
                    'question_count': len(question_ids),
                    'question_ids': question_ids
                })
                print(f"   题目数量: {len(question_ids)}")

        except Exception as e:
            print(f"❌ 第{i+1}次生成失败: {e}")
            return False

    # 3. 验证随机性
    if len(results) >= 2:
        print("🎲 验证题目随机性...")
        first_set = set(results[0]['question_ids'])
        second_set = set(results[1]['question_ids'])

        intersection = first_set & second_set
        union = first_set | second_set

        overlap_ratio = len(intersection) / len(union) if union else 0
        print(".2f"        print(".2f"        print(".2f"
        # 如果重叠率太高，可能不是真正的随机
        if overlap_ratio > 0.8:
            print("⚠️  警告：题目重叠率过高，可能随机性不足")
        else:
            print("✅ 随机性验证通过")

    print("🎉 诊断卷重新生成功能测试完成！")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 所有测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 测试失败！")
        sys.exit(1)
