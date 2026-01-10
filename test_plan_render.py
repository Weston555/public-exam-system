#!/usr/bin/env python3
"""
测试学习计划页面渲染修复
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_plan_render():
    print("🧪 测试学习计划页面渲染...")

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

        # 2. 检查学习目标
        goal_resp = requests.get(f"{BASE_URL}/goals/me", headers=headers)
        if goal_resp.status_code == 404 or not goal_resp.json():
            # 创建学习目标
            from datetime import datetime, timedelta
            future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            requests.post(f"{BASE_URL}/goals/", json={
                "exam_date": future_date,
                "target_score": 75,
                "daily_minutes": 120
            }, headers=headers)
            print("✅ 创建学习目标")

        # 3. 生成学习计划
        plan_resp = requests.post(f"{BASE_URL}/plans/generate", json={"days": 7}, headers=headers)
        assert plan_resp.status_code == 200
        print("✅ 生成学习计划")

        # 4. 获取学习计划数据
        active_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
        assert active_resp.status_code == 200

        plan_data = active_resp.json()
        print("✅ 获取活跃计划")

        # 5. 验证数据结构
        assert "items_by_date" in plan_data, "响应缺少items_by_date字段"
        assert isinstance(plan_data["items_by_date"], dict), "items_by_date不是字典"

        # 检查是否有日期键
        date_keys = list(plan_data["items_by_date"].keys())
        assert len(date_keys) > 0, "items_by_date为空"

        # 检查日期格式（应该类似'2026-01-10'）
        for date_key in date_keys[:3]:  # 检查前3个
            assert len(date_key) == 10, f"日期格式错误: {date_key}"
            assert date_key.count('-') == 2, f"日期格式错误: {date_key}"

            # 检查items数组
            items = plan_data["items_by_date"][date_key]
            assert isinstance(items, list), f"日期{date_key}的items不是数组"
            if len(items) > 0:
                # 检查item结构
                item = items[0]
                required_fields = ["id", "type", "title", "status", "expected_minutes"]
                for field in required_fields:
                    assert field in item, f"item缺少字段: {field}"

        print(f"✅ 数据结构验证通过，发现 {len(date_keys)} 个日期，{sum(len(plan_data['items_by_date'][k]) for k in date_keys)} 个任务")

        # 6. 测试开始任务接口
        # 找到一个LEARN任务来测试
        test_item = None
        for date_key, items in plan_data["items_by_date"].items():
            for item in items:
                if item["status"] == "TODO" and item["type"] in ["PRACTICE", "REVIEW", "LEARN"]:
                    test_item = item
                    break
            if test_item:
                break

        if test_item:
            start_resp = requests.post(f"{BASE_URL}/plans/items/{test_item['id']}/start", headers=headers)
            assert start_resp.status_code == 200
            start_data = start_resp.json()
            assert "action" in start_data, "start响应缺少action字段"
            print(f"✅ 开始任务接口测试通过，action: {start_data['action']}")

        print("🎉 学习计划页面渲染修复验证全部通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_plan_render()
