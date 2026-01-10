#!/usr/bin/env python3
"""
测试 GET /api/v1/plans/active 接口是否返回 exam_id 字段
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_exam_id_field():
    print("🧪 测试学习计划接口 exam_id 字段...")

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

        # 4. 获取学习计划并检查exam_id字段
        active_resp = requests.get(f"{BASE_URL}/plans/active", headers=headers)
        assert active_resp.status_code == 200

        plan_data = active_resp.json()
        print("✅ 获取活跃计划")

        # 5. 验证exam_id字段存在
        assert "items_by_date" in plan_data, "响应缺少items_by_date字段"

        found_exam_id = False
        total_items = 0

        for date_key, items in plan_data["items_by_date"].items():
            for item in items:
                total_items += 1
                assert "exam_id" in item, f"item缺少exam_id字段: {item}"

                # exam_id 可以是 null 或数字
                exam_id = item["exam_id"]
                if exam_id is not None:
                    assert isinstance(exam_id, int), f"exam_id不是整数: {exam_id}"
                    found_exam_id = True
                    print(f"✅ 发现exam_id: {exam_id} (日期: {date_key}, 任务类型: {item['type']})")

                # 验证其他必需字段
                required_fields = ["id", "type", "title", "knowledge_id", "expected_minutes", "status"]
                for field in required_fields:
                    assert field in item, f"item缺少必需字段: {field}"

        print(f"✅ 验证完成，共检查 {total_items} 个任务")
        print(f"✅ 所有任务都包含exam_id字段 (其中 {1 if found_exam_id else 0} 个有值)")

        print("🎉 exam_id 字段验证全部通过！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_exam_id_field()
