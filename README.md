# 公考进阶 - 个性化学习路径推荐系统

## 项目简介

"公考进阶"是一款基于人工智能的个性化学习路径推荐系统，专为公务员考试考生设计。通过构建"考试大纲—知识点—题目—难度—目标成绩"的一体化模型，系统能够为每位考生提供可解释、可配置的个性化学习路径，解决传统学习方法存在的路径同质化、练习与大纲脱节、复习缺乏针对性等痛点。

## 核心特性

### 学员端功能
- 🔍 **基线诊断**：智能评估当前能力水平
- 📚 **个性化学习路径**：基于诊断结果生成定制学习计划
- 🎯 **针对性练习**：按知识点和难度智能推荐题目
- 📊 **学习进度追踪**：可视化学习效果和进度
- 📝 **模拟测验**：全真考试环境模拟
- 🔄 **错题回流**：智能复习错题巩固知识

### 管理员端功能
- 🌳 **知识点树管理**：维护考试大纲和知识体系
- 📋 **题库管理**：多题型题目维护和组织
- 📄 **试卷管理**：智能组卷和考试发布
- 👥 **用户管理**：用户权限和状态管理
- 📈 **数据分析**：学习效果和系统使用情况监控

## 技术架构

### 前端技术栈
- **框架**：Vue 3 + Composition API
- **构建工具**：Vite
- **路由**：Vue Router 4
- **状态管理**：Pinia
- **UI组件库**：Element Plus
- **图表库**：ECharts
- **HTTP客户端**：Axios

### 后端技术栈
- **框架**：FastAPI (Python)
- **数据库ORM**：SQLAlchemy 2.0
- **数据库**：MySQL 8.0
- **身份认证**：JWT
- **数据验证**：Pydantic
- **迁移工具**：Alembic

### 部署与容器化
- **容器化**：Docker + Docker Compose
- **Web服务器**：Nginx (可选)
- **数据库**：MySQL 8.0

## 快速开始

### 环境要求
- Node.js 16+
- Python 3.11+
- Docker & Docker Compose
- MySQL 8.0 (或使用容器化版本)

### 一键启动 (推荐)

1. 克隆项目
```bash
git clone <repository-url>
cd public-exam-system
```

2. 启动所有服务
```bash
docker-compose up --build
```

3. 访问应用
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 手动启动

#### 后端启动
```bash
cd server
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### 前端启动
```bash
cd web
npm install
npm run dev
```

#### 数据库
确保MySQL服务运行，并创建数据库：
```sql
CREATE DATABASE public_exam_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 默认账号

### 管理员账号
- 用户名: `admin`
- 密码: `admin123`

### 测试学员账号
- 用户名: `student01`
- 密码: `123456`

## 项目结构

```
public-exam-system/
├── web/                    # Vue3 前端
│   ├── src/
│   │   ├── components/     # 组件
│   │   ├── views/          # 页面
│   │   ├── stores/         # 状态管理
│   │   ├── router/         # 路由配置
│   │   └── layout/         # 布局组件
│   ├── package.json
│   └── vite.config.js
├── server/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # 数据验证
│   │   ├── api/            # API路由
│   │   └── services/       # 业务逻辑
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt
├── deploy/                 # 部署配置
│   ├── docker-compose.yml
│   ├── Dockerfile.web
│   └── Dockerfile.server
├── docs/                   # 项目文档
│   ├── REQUIREMENTS.md     # 需求规格
│   ├── API.md             # API文档
│   └── DB.md              # 数据库设计
└── README.md
```

## 开发指南

### 代码规范
- 前端：ESLint + Prettier
- 后端：Black + isort + mypy
- 提交信息：遵循 Conventional Commits

### 测试
```bash
# 后端测试
cd server
pytest

# 前端测试
cd web
npm run test
```

### 构建生产版本
```bash
# 前端构建
cd web
npm run build

# 后端构建 (如需)
cd server
# 生产部署使用 Docker
```

## 文档

- [详细需求规格](./docs/REQUIREMENTS.md)
- [API 接口文档](./docs/API.md)
- [数据库设计](./docs/DB.md)

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系我们

如有问题或建议，请通过以下方式联系：
- 邮箱: your-email@example.com
- 项目Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**🎓 毕业设计项目 - 基于人工智能的个性化学习系统**
