# API 文档

## 概述

本文档描述了"公考进阶"个性化学习路径推荐系统的RESTful API接口。

## 基础信息

- Base URL: `http://localhost:8000/api/v1`
- 认证方式: JWT Bearer Token
- 数据格式: JSON
- 字符编码: UTF-8

## 认证接口

### 用户注册
```
POST /auth/register
```

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "message": "用户注册成功",
  "user_id": 1
}
```

### 用户登录
```
POST /auth/login
```

**请求体:**
```json
{
  "username": "string",
  "password": "string"
}
```

**响应:**
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "role": "STUDENT|ADMIN",
  "expires_in": 3600
}
```

### 获取当前用户信息
```
GET /users/me
```

**响应:**
```json
{
  "id": 1,
  "username": "string",
  "role": "STUDENT|ADMIN",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 知识点管理接口

### 获取知识点树
```
GET /knowledge/tree
```

**响应:**
```json
{
  "tree": [
    {
      "id": 1,
      "name": "公务员考试",
      "code": "GOV_EXAM",
      "weight": 1.0,
      "estimated_minutes": 30,
      "children": [
        {
          "id": 2,
          "name": "行测",
          "code": "MATH_TEST",
          "weight": 0.6,
          "estimated_minutes": 45,
          "children": []
        }
      ]
    }
  ]
}
```

### 创建知识点 (管理员)
```
POST /admin/knowledge
```

**请求体:**
```json
{
  "parent_id": 1,
  "name": "新知识点",
  "code": "NEW_POINT",
  "weight": 1.0,
  "estimated_minutes": 30
}
```

## 题库管理接口

### 获取题目列表
```
GET /questions?page=1&size=20&knowledge_id=1&type=SINGLE&difficulty=3
```

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "type": "SINGLE",
      "stem": "题目内容...",
      "options_json": ["A. 选项1", "B. 选项2"],
      "answer_json": ["A"],
      "analysis": "解析内容...",
      "difficulty": 3,
      "knowledge_points": [
        {"id": 1, "name": "知识点1"}
      ]
    }
  ],
  "total": 100,
  "page": 1,
  "size": 20
}
```

### 创建题目 (管理员)
```
POST /admin/questions
```

**请求体:**
```json
{
  "type": "SINGLE",
  "stem": "题目内容",
  "options_json": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
  "answer_json": ["A"],
  "analysis": "解析内容",
  "difficulty": 3,
  "knowledge_ids": [1, 2]
}
```

## 试卷和考试管理接口

### 获取考试列表
```
GET /exams?category=DIAGNOSTIC
```

**响应:**
```json
{
  "items": [
    {
      "id": 1,
      "title": "基线诊断考试",
      "category": "DIAGNOSTIC",
      "duration_minutes": 120,
      "status": "PUBLISHED",
      "total_questions": 50,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### 开始考试
```
POST /exams/{exam_id}/start
```

**响应:**
```json
{
  "attempt_id": 1,
  "exam": {
    "id": 1,
    "title": "基线诊断考试",
    "duration_minutes": 120
  },
  "questions": [
    {
      "id": 1,
      "order_no": 1,
      "question": {
        "id": 1,
        "type": "SINGLE",
        "stem": "题目内容...",
        "options_json": ["A. 选项1", "B. 选项2"]
      }
    }
  ]
}
```

### 提交单题答案
```
POST /attempts/{attempt_id}/answer
```

**请求体:**
```json
{
  "question_id": 1,
  "answer_json": ["A"],
  "time_spent_seconds": 30
}
```

### 提交考试
```
POST /attempts/{attempt_id}/submit
```

**响应:**
```json
{
  "attempt_id": 1,
  "total_score": 85.5,
  "correct_count": 43,
  "total_count": 50,
  "submitted_at": "2024-01-01T02:00:00Z",
  "results": [
    {
      "question_id": 1,
      "is_correct": true,
      "score_awarded": 2.0,
      "correct_answer": ["A"],
      "user_answer": ["A"]
    }
  ]
}
```

## 目标和学习计划接口

### 设置学习目标
```
POST /goals
```

**请求体:**
```json
{
  "exam_date": "2024-12-01",
  "target_score": 120.0,
  "daily_minutes": 120
}
```

### 生成学习计划
```
POST /plans/generate
```

**响应:**
```json
{
  "plan_id": 1,
  "start_date": "2024-01-01",
  "end_date": "2024-01-15",
  "items": [
    {
      "id": 1,
      "date": "2024-01-01",
      "type": "LEARN",
      "knowledge_id": 1,
      "expected_minutes": 60,
      "reason_json": {
        "mastery": 0.2,
        "weight": 0.8,
        "priority": 0.64,
        "explanation": "该知识点掌握度较低，权重较高，优先学习"
      }
    }
  ]
}
```

## 数据分析接口

### 获取学习进度
```
GET /analytics/progress
```

**响应:**
```json
{
  "plan_completion_rate": 0.75,
  "average_mastery": 0.68,
  "wrong_questions_count": 25,
  "daily_study_minutes": [
    {"date": "2024-01-01", "minutes": 120},
    {"date": "2024-01-02", "minutes": 90}
  ]
}
```

### 获取成绩趋势
```
GET /analytics/score-trend
```

**响应:**
```json
{
  "diagnostic_scores": [
    {"date": "2024-01-01", "score": 65.5, "category": "DIAGNOSTIC"},
    {"date": "2024-01-08", "score": 78.0, "category": "DIAGNOSTIC"}
  ],
  "mock_scores": [
    {"date": "2024-01-15", "score": 95.5, "category": "MOCK"}
  ]
}
```

## 管理员专用接口

### 系统概览数据
```
GET /admin/analytics/overview
```

**响应:**
```json
{
  "total_users": 1250,
  "active_users": 380,
  "average_completion_rate": 0.72,
  "average_score_improvement": 15.5,
  "total_questions": 2500,
  "total_exams": 45
}
```

### 脱敏数据导出
```
GET /admin/export/anonymized?start_date=2024-01-01&end_date=2024-12-31
```

**响应:** CSV文件下载

## 错误响应格式

```json
{
  "detail": "错误描述信息",
  "code": "ERROR_CODE"
}
```

## 常见错误码

- `INVALID_CREDENTIALS`: 无效的登录凭据
- `EXAM_ALREADY_STARTED`: 考试已开始
- `EXAM_TIME_EXPIRED`: 考试时间已过期
- `QUESTION_NOT_FOUND`: 题目不存在
- `PERMISSION_DENIED`: 权限不足
