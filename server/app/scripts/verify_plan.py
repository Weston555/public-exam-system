#!/usr/bin/env python3
"""
学习计划生成验收脚本

验证推荐算法模块的正确性：
1. 登录 student01/123456 获取 token
2. 检查用户目标，如果没有则创建
3. 生成 14 天学习计划
4. 获取活跃计划并统计任务数量

运行方式: python verify_plan.py
"""
import sys
import os
import requests
import json
from datetime import datetime, timedelta

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    """主函数"""
    # API 基础地址 (假设服务器运行在 localhost:8000)
    base_url = "http://localhost:8000/api/v1"

    print("🚀 开始学习计划生成验收测试...")

    # 1. 登录获取token
    print("📋 步骤1: 登录获取访问令牌...")
    login_data = {
        "username": "student01",
        "password": "123456"
    }

    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        response.raise_for_status()
        login_result = response.json()
        token = login_result["access_token"]
        print("✅ 登录成功，获取到访问令牌")
    except requests.exceptions.RequestException as e:
        print(f"❌ 登录失败: {e}")
        print("请确保服务器正在运行 (python main.py)")
        return False

    # 设置请求头
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # 2. 检查用户目标
    print("📋 步骤2: 检查用户学习目标...")
    try:
        response = requests.get(f"{base_url}/goals/me", headers=headers)
        response.raise_for_status()
        goal = response.json()

        if goal:
            print(f"✅ 用户已有学习目标: 考试日期 {goal['exam_date']}, 每日学习 {goal['daily_minutes']} 分钟")
        else:
            print("ℹ️ 用户暂无学习目标，开始创建...")
            # 创建目标：考试日期为30天后
            exam_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            goal_data = {
                "exam_date": exam_date,
                "target_score": 120.0,
                "daily_minutes": 60
            }

            response = requests.post(f"{base_url}/goals/", json=goal_data, headers=headers)
            response.raise_for_status()
            create_result = response.json()
            print(f"✅ 学习目标创建成功: {create_result['message']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 检查/创建目标失败: {e}")
        return False

    # 3. 生成学习计划
    print("📋 步骤3: 生成14天学习计划...")
    try:
        plan_data = {"days": 14}
        response = requests.post(f"{base_url}/plans/generate", json=plan_data, headers=headers)
        response.raise_for_status()
        plan_result = response.json()
        print(f"✅ 学习计划生成成功: {plan_result['message']}")
        print(f"   计划ID: {plan_result['plan_id']}")
        print(f"   时间范围: {plan_result['start_date']} 至 {plan_result['end_date']}")
        print(f"   总任务数: {plan_result['total_items']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 生成学习计划失败: {e}")
        return False

    # 4. 获取活跃计划并统计
    print("📋 步骤4: 获取活跃计划并统计任务...")
    try:
        response = requests.get(f"{base_url}/plans/active", headers=headers)
        response.raise_for_status()
        active_plan = response.json()

        if active_plan:
            items_by_date = active_plan["items_by_date"]
            date_count = len(items_by_date)
            total_tasks = sum(len(tasks) for tasks in items_by_date.values())

            print("✅ 活跃计划获取成功:")
            print(f"   计划ID: {active_plan['plan_id']}")
            print(f"   时间范围: {active_plan['start_date']} 至 {active_plan['end_date']}")
            print(f"   日期数量: {date_count}")
            print(f"   总任务数: {total_tasks}")

            # 统计任务类型
            task_types = {}
            for date_tasks in items_by_date.values():
                for task in date_tasks:
                    task_type = task["type"]
                    task_types[task_type] = task_types.get(task_type, 0) + 1

            print("   任务类型统计:")
            for task_type, count in task_types.items():
                print(f"     {task_type}: {count} 个")

            # 检查推荐算法是否正确工作
            if total_tasks > 0:
                print("🎉 验收通过！推荐算法模块工作正常")
                return True
            else:
                print("❌ 验收失败：生成的计划中没有任务")
                return False
        else:
            print("❌ 验收失败：未找到活跃的学习计划")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ 获取活跃计划失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 所有验收测试通过！")
        sys.exit(0)
    else:
        print("\n❌ 验收测试失败！")
        sys.exit(1)
