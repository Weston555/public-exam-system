import sys
import os

# 添加当前目录和上级目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
server_dir = os.path.dirname(parent_dir)
sys.path.insert(0, server_dir)

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models.user import User
from app.models.knowledge import KnowledgePoint
from app.models.question import Question
from app.models.knowledge import QuestionKnowledgeMap
from app.models.paper import Paper, PaperQuestion, Exam
from app.models.progress import UserKnowledgeState


def create_knowledge_tree(db: Session):
    """创建公务员考试知识点树（幂等操作）"""

    # 检查是否已存在根节点
    stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id.is_(None))
    root_exists = db.execute(stmt).scalar_one_or_none()
    if root_exists:
        print("ℹ️ 知识点树已存在，检查并补充缺失节点")
        # 检查并补充缺失的节点
        ensure_complete_tree(db)
        return

    print("🏗️ 创建公务员考试知识点树")

    # 创建根节点
    root = KnowledgePoint(
        name="公务员考试",
        code="GONGKAO_ROOT",
        weight=1.0,
        estimated_minutes=0  # 根节点不需要时间
    )
    db.add(root)
    db.flush()
    print(f"✅ 创建根节点: {root.name}")

    # 行测模块
    xingce_modules = [
        {
            "name": "数量关系",
            "code": "XINGCE_QUANTITATIVE",
            "weight": 1.2,
            "estimated_minutes": 25,
            "sub_points": [
                {"name": "算术问题", "code": "XINGCE_QUANT_ARITHMETIC"},
                {"name": "工程问题", "code": "XINGCE_QUANT_ENGINEERING"},
                {"name": "行程问题", "code": "XINGCE_QUANT_TRAVEL"},
                {"name": "比例问题", "code": "XINGCE_QUANT_RATIO"}
            ]
        },
        {
            "name": "判断推理",
            "code": "XINGCE_LOGICAL",
            "weight": 1.3,
            "estimated_minutes": 30,
            "sub_points": [
                {"name": "图形推理", "code": "XINGCE_LOGIC_GRAPH"},
                {"name": "定义判断", "code": "XINGCE_LOGIC_DEFINITION"},
                {"name": "类比推理", "code": "XINGCE_LOGIC_ANALOGY"},
                {"name": "逻辑判断", "code": "XINGCE_LOGIC_JUDGMENT"}
            ]
        },
        {
            "name": "言语理解与表达",
            "code": "XINGCE_LANGUAGE",
            "weight": 1.1,
            "estimated_minutes": 35,
            "sub_points": [
                {"name": "阅读理解", "code": "XINGCE_LANG_READING"},
                {"name": "逻辑填空", "code": "XINGCE_LANG_BLANK"},
                {"name": "语句表达", "code": "XINGCE_LANG_EXPRESSION"},
                {"name": "病句辨析", "code": "XINGCE_LANG_GRAMMAR"}
            ]
        },
        {
            "name": "资料分析",
            "code": "XINGCE_DATA",
            "weight": 1.4,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "文字资料", "code": "XINGCE_DATA_TEXT"},
                {"name": "表格资料", "code": "XINGCE_DATA_TABLE"},
                {"name": "图形资料", "code": "XINGCE_DATA_CHART"},
                {"name": "综合资料", "code": "XINGCE_DATA_MIXED"}
            ]
        },
        {
            "name": "常识判断",
            "code": "XINGCE_COMMON",
            "weight": 0.8,
            "estimated_minutes": 15,
            "sub_points": [
                {"name": "政治常识", "code": "XINGCE_COMMON_POLITICS"},
                {"name": "法律常识", "code": "XINGCE_COMMON_LAW"},
                {"name": "人文常识", "code": "XINGCE_COMMON_HUMANITIES"},
                {"name": "科技常识", "code": "XINGCE_COMMON_SCIENCE"}
            ]
        }
    ]

    # 申论模块
    shenlun_modules = [
        {
            "name": "归纳概括",
            "code": "SHENLUN_SUMMARY",
            "weight": 1.2,
            "estimated_minutes": 25,
            "sub_points": [
                {"name": "概括主题", "code": "SHENLUN_SUM_THEME"},
                {"name": "提取要点", "code": "SHENLUN_SUM_POINTS"},
                {"name": "总结观点", "code": "SHENLUN_SUM_VIEW"}
            ]
        },
        {
            "name": "综合分析",
            "code": "SHENLUN_ANALYSIS",
            "weight": 1.3,
            "estimated_minutes": 30,
            "sub_points": [
                {"name": "原因分析", "code": "SHENLUN_ANA_CAUSE"},
                {"name": "影响分析", "code": "SHENLUN_ANA_IMPACT"},
                {"name": "利弊分析", "code": "SHENLUN_ANA_PROS_CONS"}
            ]
        },
        {
            "name": "提出对策",
            "code": "SHENLUN_SOLUTIONS",
            "weight": 1.4,
            "estimated_minutes": 35,
            "sub_points": [
                {"name": "问题诊断", "code": "SHENLUN_SOL_DIAGNOSIS"},
                {"name": "对策制定", "code": "SHENLUN_SOL_STRATEGY"},
                {"name": "实施方案", "code": "SHENLUN_SOL_IMPLEMENT"}
            ]
        },
        {
            "name": "应用文写作",
            "code": "SHENLUN_APPLICATION",
            "weight": 1.1,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "公文写作", "code": "SHENLUN_APP_OFFICIAL"},
                {"name": "方案写作", "code": "SHENLUN_APP_PLAN"},
                {"name": "报告写作", "code": "SHENLUN_APP_REPORT"}
            ]
        },
        {
            "name": "文章写作",
            "code": "SHENLUN_ESSAY",
            "weight": 1.5,
            "estimated_minutes": 45,
            "sub_points": [
                {"name": "审题立意", "code": "SHENLUN_ESS_TOPIC"},
                {"name": "结构布局", "code": "SHENLUN_ESS_STRUCTURE"},
                {"name": "语言表达", "code": "SHENLUN_ESS_LANGUAGE"}
            ]
        }
    ]

    # 创建行测大类节点
    xingce_category = KnowledgePoint(
        name="行测",
        code="XINGCE_CATEGORY",
        parent_id=root.id,
        weight=1.0,
        estimated_minutes=0  # 大类节点不需要时间
    )
    db.add(xingce_category)
    db.flush()
    print(f"✅ 创建行测大类: {xingce_category.name}")

    # 创建申论大类节点
    shenlun_category = KnowledgePoint(
        name="申论",
        code="SHENLUN_CATEGORY",
        parent_id=root.id,
        weight=1.0,
        estimated_minutes=0  # 大类节点不需要时间
    )
    db.add(shenlun_category)
    db.flush()
    print(f"✅ 创建申论大类: {shenlun_category.name}")

    # 创建行测模块和子节点
    for module in xingce_modules:
        module_node = KnowledgePoint(
            name=module["name"],
            code=module["code"],
            parent_id=xingce_category.id,
            weight=module["weight"],
            estimated_minutes=module["estimated_minutes"]
        )
        db.add(module_node)
        db.flush()
        print(f"✅ 创建行测模块: {module_node.name}")

        # 创建子节点
        for sub_point in module["sub_points"]:
            sub_node = KnowledgePoint(
                name=sub_point["name"],
                code=sub_point["code"],
                parent_id=module_node.id,
                weight=1.0,
                estimated_minutes=5  # 子节点基础时间
            )
            db.add(sub_node)
        print(f"  └─ 创建 {len(module['sub_points'])} 个子知识点")

    # 创建申论模块和子节点
    for module in shenlun_modules:
        module_node = KnowledgePoint(
            name=module["name"],
            code=module["code"],
            parent_id=shenlun_category.id,
            weight=module["weight"],
            estimated_minutes=module["estimated_minutes"]
        )
        db.add(module_node)
        db.flush()
        print(f"✅ 创建申论模块: {module_node.name}")

        # 创建子节点
        for sub_point in module["sub_points"]:
            sub_node = KnowledgePoint(
                name=sub_point["name"],
                code=sub_point["code"],
                parent_id=module_node.id,
                weight=1.0,
                estimated_minutes=5  # 子节点基础时间
            )
            db.add(sub_node)
        print(f"  └─ 创建 {len(module['sub_points'])} 个子知识点")

    print("🎉 公务员考试知识点树创建完成！")


def ensure_complete_tree(db: Session):
    """确保知识点树完整性，补充缺失的节点"""

    # 获取根节点
    stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id.is_(None))
    root = db.execute(stmt).scalar_one_or_none()
    if not root:
        print("❌ 未找到根节点，需要重新创建完整树")
        create_knowledge_tree(db)
        return

    # 检查并创建大类节点
    stmt = select(KnowledgePoint).where(KnowledgePoint.code == "XINGCE_CATEGORY")
    xingce_category = db.execute(stmt).scalar_one_or_none()
    if not xingce_category:
        xingce_category = KnowledgePoint(
            name="行测",
            code="XINGCE_CATEGORY",
            parent_id=root.id,
            weight=1.0,
            estimated_minutes=0
        )
        db.add(xingce_category)
        db.flush()
        print("✅ 补充行测大类节点")

    stmt = select(KnowledgePoint).where(KnowledgePoint.code == "SHENLUN_CATEGORY")
    shenlun_category = db.execute(stmt).scalar_one_or_none()
    if not shenlun_category:
        shenlun_category = KnowledgePoint(
            name="申论",
            code="SHENLUN_CATEGORY",
            parent_id=root.id,
            weight=1.0,
            estimated_minutes=0
        )
        db.add(shenlun_category)
        db.flush()
        print("✅ 补充申论大类节点")

    # 定义完整的知识点结构
    xingce_modules = [
        {
            "name": "数量关系", "code": "XINGCE_QUANTITATIVE", "weight": 1.2, "estimated_minutes": 25,
            "sub_points": [
                {"name": "算术问题", "code": "XINGCE_QUANT_ARITHMETIC"},
                {"name": "工程问题", "code": "XINGCE_QUANT_ENGINEERING"},
                {"name": "行程问题", "code": "XINGCE_QUANT_TRAVEL"},
                {"name": "比例问题", "code": "XINGCE_QUANT_RATIO"}
            ]
        },
        {
            "name": "判断推理", "code": "XINGCE_LOGICAL", "weight": 1.3, "estimated_minutes": 30,
            "sub_points": [
                {"name": "图形推理", "code": "XINGCE_LOGIC_GRAPH"},
                {"name": "定义判断", "code": "XINGCE_LOGIC_DEFINITION"},
                {"name": "类比推理", "code": "XINGCE_LOGIC_ANALOGY"},
                {"name": "逻辑判断", "code": "XINGCE_LOGIC_JUDGMENT"}
            ]
        },
        {
            "name": "言语理解与表达", "code": "XINGCE_LANGUAGE", "weight": 1.1, "estimated_minutes": 35,
            "sub_points": [
                {"name": "阅读理解", "code": "XINGCE_LANG_READING"},
                {"name": "逻辑填空", "code": "XINGCE_LANG_BLANK"},
                {"name": "语句表达", "code": "XINGCE_LANG_EXPRESSION"},
                {"name": "病句辨析", "code": "XINGCE_LANG_GRAMMAR"}
            ]
        },
        {
            "name": "资料分析", "code": "XINGCE_DATA", "weight": 1.4, "estimated_minutes": 40,
            "sub_points": [
                {"name": "文字资料", "code": "XINGCE_DATA_TEXT"},
                {"name": "表格资料", "code": "XINGCE_DATA_TABLE"},
                {"name": "图形资料", "code": "XINGCE_DATA_CHART"},
                {"name": "综合资料", "code": "XINGCE_DATA_MIXED"}
            ]
        },
        {
            "name": "常识判断", "code": "XINGCE_COMMON", "weight": 0.8, "estimated_minutes": 15,
            "sub_points": [
                {"name": "政治常识", "code": "XINGCE_COMMON_POLITICS"},
                {"name": "法律常识", "code": "XINGCE_COMMON_LAW"},
                {"name": "人文常识", "code": "XINGCE_COMMON_HUMANITIES"},
                {"name": "科技常识", "code": "XINGCE_COMMON_SCIENCE"}
            ]
        }
    ]

    shenlun_modules = [
        {
            "name": "归纳概括", "code": "SHENLUN_SUMMARY", "weight": 1.2, "estimated_minutes": 25,
            "sub_points": [
                {"name": "概括主题", "code": "SHENLUN_SUM_THEME"},
                {"name": "提取要点", "code": "SHENLUN_SUM_POINTS"},
                {"name": "总结观点", "code": "SHENLUN_SUM_VIEW"}
            ]
        },
        {
            "name": "综合分析", "code": "SHENLUN_ANALYSIS", "weight": 1.3, "estimated_minutes": 30,
            "sub_points": [
                {"name": "原因分析", "code": "SHENLUN_ANA_CAUSE"},
                {"name": "影响分析", "code": "SHENLUN_ANA_IMPACT"},
                {"name": "利弊分析", "code": "SHENLUN_ANA_PROS_CONS"}
            ]
        },
        {
            "name": "提出对策", "code": "SHENLUN_SOLUTIONS", "weight": 1.4, "estimated_minutes": 35,
            "sub_points": [
                {"name": "问题诊断", "code": "SHENLUN_SOL_DIAGNOSIS"},
                {"name": "对策制定", "code": "SHENLUN_SOL_STRATEGY"},
                {"name": "实施方案", "code": "SHENLUN_SOL_IMPLEMENT"}
            ]
        },
        {
            "name": "应用文写作", "code": "SHENLUN_APPLICATION", "weight": 1.1, "estimated_minutes": 40,
            "sub_points": [
                {"name": "公文写作", "code": "SHENLUN_APP_OFFICIAL"},
                {"name": "方案写作", "code": "SHENLUN_APP_PLAN"},
                {"name": "报告写作", "code": "SHENLUN_APP_REPORT"}
            ]
        },
        {
            "name": "文章写作", "code": "SHENLUN_ESSAY", "weight": 1.5, "estimated_minutes": 45,
            "sub_points": [
                {"name": "审题立意", "code": "SHENLUN_ESS_TOPIC"},
                {"name": "结构布局", "code": "SHENLUN_ESS_STRUCTURE"},
                {"name": "语言表达", "code": "SHENLUN_ESS_LANGUAGE"}
            ]
        }
    ]

    # 补充行测模块
    for module in xingce_modules:
        stmt = select(KnowledgePoint).where(KnowledgePoint.code == module["code"])
        module_node = db.execute(stmt).scalar_one_or_none()
        if not module_node:
            module_node = KnowledgePoint(
                name=module["name"],
                code=module["code"],
                parent_id=xingce_category.id,
                weight=module["weight"],
                estimated_minutes=module["estimated_minutes"]
            )
            db.add(module_node)
            db.flush()
            print(f"✅ 补充行测模块: {module['name']}")

        # 补充子节点
        for sub_point in module["sub_points"]:
            stmt = select(KnowledgePoint).where(KnowledgePoint.code == sub_point["code"])
            sub_node = db.execute(stmt).scalar_one_or_none()
            if not sub_node:
                sub_node = KnowledgePoint(
                    name=sub_point["name"],
                    code=sub_point["code"],
                    parent_id=module_node.id,
                    weight=1.0,
                    estimated_minutes=5
                )
                db.add(sub_node)

    # 补充申论模块
    for module in shenlun_modules:
        stmt = select(KnowledgePoint).where(KnowledgePoint.code == module["code"])
        module_node = db.execute(stmt).scalar_one_or_none()
        if not module_node:
            module_node = KnowledgePoint(
                name=module["name"],
                code=module["code"],
                parent_id=shenlun_category.id,
                weight=module["weight"],
                estimated_minutes=module["estimated_minutes"]
            )
            db.add(module_node)
            db.flush()
            print(f"✅ 补充申论模块: {module['name']}")

        # 补充子节点
        for sub_point in module["sub_points"]:
            stmt = select(KnowledgePoint).where(KnowledgePoint.code == sub_point["code"])
            sub_node = db.execute(stmt).scalar_one_or_none()
            if not sub_node:
                sub_node = KnowledgePoint(
                    name=sub_point["name"],
                    code=sub_point["code"],
                    parent_id=module_node.id,
                    weight=1.0,
                    estimated_minutes=5
                )
                db.add(sub_node)

    print("✅ 知识点树完整性检查完成")


def seed_database():
    """初始化数据库数据"""
    # 创建表
    create_tables()

    db = SessionLocal()
    try:
        # 创建管理员用户
        admin_username = "admin"
        stmt = select(User).where(User.username == admin_username)
        admin_exists = db.execute(stmt).scalar_one_or_none()
        if not admin_exists:
            admin = User(
                username=admin_username,
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            print("✅ 创建管理员用户: admin/admin123")

        # 创建测试学员用户
        test_users = [
            ("student01", "123456"),
            ("student02", "123456")
        ]

        for username, password in test_users:
            stmt = select(User).where(User.username == username)
            user_exists = db.execute(stmt).scalar_one_or_none()
            if not user_exists:
                user = User(
                    username=username,
                    password_hash=get_password_hash(password),
                    role="STUDENT",
                    is_active=True
                )
                db.add(user)
                db.flush()  # 获取用户ID
                print(f"✅ 创建测试学员: {username}/{password}")

                # 为新用户创建示例知识点掌握度数据
                stmt = select(func.count()).select_from(UserKnowledgeState).where(UserKnowledgeState.user_id == user.id)
                if db.execute(stmt).scalar() == 0:
                    stmt = select(KnowledgePoint)
                    knowledge_points = db.execute(stmt).scalars().all()
                    for kp in knowledge_points:
                        # 为不同知识点设置不同的掌握度（模拟真实学习情况）
                        if kp.name == "数量关系":
                            mastery = 0.4  # 40% - 较薄弱
                        elif kp.name == "判断推理":
                            mastery = 0.6  # 60% - 中等
                        elif kp.name == "阅读理解":
                            mastery = 0.8  # 80% - 较好
                        elif kp.name == "行测":
                            mastery = 0.5  # 50% - 中等
                        elif kp.name == "申论":
                            mastery = 0.7  # 70% - 良好
                        else:
                            mastery = 0.3  # 30% - 很薄弱

                        user_knowledge_state = UserKnowledgeState(
                            user_id=user.id,
                            knowledge_id=kp.id,
                            mastery=mastery
                        )
                        db.add(user_knowledge_state)
                    print(f"✅ 为用户 {username} 创建知识点掌握度数据")

        # 创建知识点树（幂等操作）
        create_knowledge_tree(db)


        # 创建测试题目
        if db.execute(select(func.count()).select_from(Question)).scalar() == 0:
            # 获取知识点ID
            stmt = select(KnowledgePoint).where(KnowledgePoint.code == "XINGCE_QUANTITATIVE")
            quantitative = db.execute(stmt).scalar_one_or_none()
            stmt = select(KnowledgePoint).where(KnowledgePoint.code == "XINGCE_LOGICAL")
            logical = db.execute(stmt).scalar_one_or_none()
            stmt = select(KnowledgePoint).where(KnowledgePoint.code == "XINGCE_LANGUAGE")
            language = db.execute(stmt).scalar_one_or_none()

            questions_data = [
                {
                    "type": "SINGLE",
                    "stem": "如果3个苹果的价格是5元，那么8个苹果的价格是多少元？",
                    "options_json": ["A. 12", "B. 13.33", "C. 15", "D. 16"],
                    "answer_json": ["B"],
                    "analysis": "通过比例计算：3个苹果=5元，1个苹果=5/3元，8个苹果=5/3×8≈13.33元",
                    "difficulty": 2,
                    "knowledge_ids": [quantitative.id] if quantitative else []
                },
                {
                    "type": "JUDGE",
                    "stem": "所有的三角形都是等腰三角形。",
                    "options_json": None,
                    "answer_json": ["F"],
                    "analysis": "等腰三角形是指至少有两条边相等的三角形，不是所有三角形都满足这个条件。",
                    "difficulty": 1,
                    "knowledge_ids": [logical.id] if logical else []
                },
                {
                    "type": "SINGLE",
                    "stem": "以下哪个词的词性与其他三个不同？",
                    "options_json": ["A. 快速", "B. 奔跑", "C. 迅速", "D. 慢慢"],
                    "answer_json": ["B"],
                    "analysis": "A、C、D都是形容词，B是动词。",
                    "difficulty": 2,
                    "knowledge_ids": [language.id] if language else []
                }
            ]

            for q_data in questions_data:
                question = Question(
                    type=q_data["type"],
                    stem=q_data["stem"],
                    options_json=q_data["options_json"],
                    answer_json=q_data["answer_json"],
                    analysis=q_data["analysis"],
                    difficulty=q_data["difficulty"]
                )
                db.add(question)
                db.flush()

                # 添加知识点关联
                for knowledge_id in q_data["knowledge_ids"]:
                    mapping = QuestionKnowledgeMap(
                        question_id=question.id,
                        knowledge_id=knowledge_id
                    )
                    db.add(mapping)

            print("✅ 创建测试题目")

        # 创建诊断考试
        stmt = select(func.count()).select_from(Exam).where(Exam.category == "DIAGNOSTIC")
        if db.execute(stmt).scalar() == 0:
            # 创建试卷
            paper = Paper(
                title="基线诊断试卷",
                mode="AUTO",
                total_score=6.0,
                created_by=1  # admin用户ID
            )
            db.add(paper)
            db.flush()

            # 获取所有题目
            stmt = select(Question)
            questions = db.execute(stmt).scalars().all()
            for i, question in enumerate(questions):
                paper_question = PaperQuestion(
                    paper_id=paper.id,
                    question_id=question.id,
                    order_no=i+1,
                    score=2.0
                )
                db.add(paper_question)

            # 创建考试
            exam = Exam(
                paper_id=paper.id,
                title="基线诊断考试",
                category="DIAGNOSTIC",
                duration_minutes=30,
                status="PUBLISHED",
                created_by=1
            )
            db.add(exam)

            print("✅ 创建诊断考试")

        # 创建示例 MOCK 考试（避免重复创建）
        mock_title = "模拟考试（样例）"
        stmt = select(Exam).where(Exam.category == "MOCK", Exam.title == mock_title)
        existing_mock = db.execute(stmt).scalar_one_or_none()
        if not existing_mock:
            # 抽取题库中最多 30 题，尽量覆盖多个知识点
            stmt = select(Question)
            all_questions = db.execute(stmt).scalars().all()
            if len(all_questions) >= 1:
                sample_count = min(30, max(5, len(all_questions)))
                # if not enough distinct questions, cycle to fill sample_count
                from itertools import cycle, islice
                samples = list(islice(cycle(all_questions), sample_count))

                # 创建试卷
                mock_paper = Paper(
                    title="模拟考试试卷(样例)",
                    mode="AUTO",
                    total_score=float(len(samples) * 2.0),
                    created_by=1
                )
                db.add(mock_paper)
                db.flush()

                for i, q in enumerate(samples):
                    pq = PaperQuestion(
                        paper_id=mock_paper.id,
                        question_id=q.id,
                        order_no=i+1,
                        score=2.0
                    )
                    db.add(pq)

                mock_exam = Exam(
                    paper_id=mock_paper.id,
                    title=mock_title,
                    category="MOCK",
                    duration_minutes=60,
                    status="PUBLISHED",
                    created_by=1
                )
                db.add(mock_exam)
                print("✅ 创建示例 MOCK 考试")
            else:
                print("⚠️ 题库题目不足，未创建 MOCK 示例")

        db.commit()
        print("🎉 数据库初始化完成！")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
