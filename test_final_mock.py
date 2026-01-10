#!/usr/bin/env python3
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 登录
login_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "student01",
    "password": "123456"
})
token = login_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("Testing mock generate API...")
r = requests.post(f"{BASE_URL}/exams/mock/generate", json={
    "count": 3,
    "duration_minutes": 30
}, headers=headers)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ Success!")
    print(f"Response: {r.json()}")
else:
    print(f"❌ Error: {r.text}")
