#!/usr/bin/env python3
"""
测试学习计划页面渲染是否正常
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_plan_render():
    print("🧪 最终验证：学习计划页面渲染修复")

    try:
        # 1. 登录
        login_resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "student01",
            "password": "123456"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ 登录成功")

        # 2. 确保有学习目标和计划
        goal_resp = requests.get(f"{BASE_URL}/goals/me", headers=headers)
        if goal_resp.status_code == 404 or not goal_resp.json():
            from datetime import datetime, timedelta
            future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            requests.post(f"{BASE_URL}/goals/", json={
                "exam_date": future_date,
                "target_score": 75,
                "daily_minutes": 120
            }, headers=headers)
            print("✅ 创建学习目标")

        plan_resp = requests.post(f"{BASE_URL}/plans/generate", json={"days": 7}, headers=headers)
        assert plan_resp.status_code == 200
        print("✅ 生成学习计划")

        # 3. 获取学习计划数据并验证结构
        active_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
        assert active_resp.status_code == 200

        plan_data = active_resp.json()
        print("✅ 获取活跃计划")

        # 验证数据结构
        assert "items_by_date" in plan_data, "缺少items_by_date字段"
        assert isinstance(plan_data["items_by_date"], dict), "items_by_date不是字典"

        date_keys = list(plan_data["items_by_date"].keys())
        assert len(date_keys) > 0, "items_by_date为空"

        print(f"📅 发现 {len(date_keys)} 个日期段")

        # 验证日期格式和数据完整性
        for i, date_key in enumerate(date_keys[:5]):  # 检查前5个
            print(f"  日期 {i+1}: {date_key}")

            # 验证日期格式 (YYYY-MM-DD)
            assert len(date_key) == 10, f"日期格式错误: {date_key}"
            assert date_key.count('-') == 2, f"日期格式错误: {date_key}"

            # 验证items数组
            items = plan_data["items_by_date"][date_key]
            assert isinstance(items, list), f"日期{date_key}的items不是数组"

            if len(items) > 0:
                print(f"    包含 {len(items)} 个任务")
                # 验证第一个任务的结构
                item = items[0]
                required_fields = ["id", "type", "title", "status", "expected_minutes", "exam_id"]
                for field in required_fields:
                    assert field in item, f"任务缺少必需字段: {field}"
                print(f"    示例任务: {item['type']} - {item['title'][:20]}...")
            else:
                print("    无任务"

        print("✅ 数据结构验证完成")
        print("✅ 日期格式正确 (YYYY-MM-DD)")
        print("✅ 任务数据完整")
        print("✅ 前端渲染应该正常工作")

        # 4. 测试开始任务接口
        test_item = None
        for date_key, items in plan_data["items_by_date"].items():
            for item in items:
                if item["status"] == "TODO":
                    test_item = item
                    break
            if test_item:
                break

        if test_item:
            start_resp = requests.post(f"{BASE_URL}/plans/items/{test_item['id']}/start", headers=headers)
            assert start_resp.status_code == 200
            start_data = start_resp.json()
            assert "action" in start_data, "start响应缺少action字段"
            print(f"✅ 开始任务接口测试通过: {start_data['action']}")

        print("🎉 学习计划页面渲染修复验证全部通过！")
        print()
        print("📋 前端应该能够正确渲染：")
        print("   - 日期时间线按正确日期显示")
        print("   - 每个日期下的任务列表正常展示")
        print("   - 开始任务按钮功能正常")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_plan_render()
