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
        code="GOV_EXAM",
        weight=1.0,
        estimated_minutes=0  # 根节点不需要时间
    )
    db.add(root)
    db.flush()
    print(f"✅ 创建根节点: {root.name}")

    # 行测五模块（公考标准结构）
    xingce_modules = [
        {
            "name": "常识判断",
            "code": "XINGCE_CS",
            "weight": 0.18,
            "estimated_minutes": 35,
            "sub_points": [
                {"name": "政治常识", "code": "XINGCE_CS_POLITICS"},
                {"name": "法律常识", "code": "XINGCE_CS_LAW"},
                {"name": "人文常识", "code": "XINGCE_CS_HUMANITIES"}
            ]
        },
        {
            "name": "言语理解与表达",
            "code": "XINGCE_YY",
            "weight": 0.22,
            "estimated_minutes": 45,
            "sub_points": [
                {"name": "阅读理解", "code": "XINGCE_YY_READ"},
                {"name": "逻辑填空", "code": "XINGCE_YY_BLANK"},
                {"name": "语句表达", "code": "XINGCE_YY_EXPRESSION"}
            ]
        },
        {
            "name": "数量关系",
            "code": "XINGCE_SL",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "算术问题", "code": "XINGCE_SL_ARITHMETIC"},
                {"name": "工程问题", "code": "XINGCE_SL_ENGINEERING"},
                {"name": "行程问题", "code": "XINGCE_SL_TRAVEL"}
            ]
        },
        {
            "name": "判断推理",
            "code": "XINGCE_PD",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "图形推理", "code": "XINGCE_PD_GRAPH"},
                {"name": "类比推理", "code": "XINGCE_PD_ANALOGY"},
                {"name": "逻辑判断", "code": "XINGCE_PD_LOGIC"}
            ]
        },
        {
            "name": "资料分析",
            "code": "XINGCE_ZL",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "文字资料", "code": "XINGCE_ZL_TEXT"},
                {"name": "表格资料", "code": "XINGCE_ZL_TABLE"},
                {"name": "图形资料", "code": "XINGCE_ZL_CHART"}
            ]
        }
    ]

    # 申论五题型（公考标准结构）
    shenlun_modules = [
        {
            "name": "归纳概括",
            "code": "SHENLUN_GN",
            "weight": 0.18,
            "estimated_minutes": 35,
            "sub_points": [
                {"name": "概括主题", "code": "SHENLUN_GN_THEME"},
                {"name": "提取要点", "code": "SHENLUN_GN_POINTS"}
            ]
        },
        {
            "name": "综合分析",
            "code": "SHENLUN_ZH",
            "weight": 0.22,
            "estimated_minutes": 45,
            "sub_points": [
                {"name": "原因分析", "code": "SHENLUN_ZH_CAUSE"},
                {"name": "影响分析", "code": "SHENLUN_ZH_IMPACT"}
            ]
        },
        {
            "name": "提出对策",
            "code": "SHENLUN_DC",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "问题诊断", "code": "SHENLUN_DC_DIAGNOSIS"},
                {"name": "对策制定", "code": "SHENLUN_DC_STRATEGY"}
            ]
        },
        {
            "name": "应用文写作",
            "code": "SHENLUN_YYW",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "公文写作", "code": "SHENLUN_YYW_OFFICIAL"},
                {"name": "方案写作", "code": "SHENLUN_YYW_PLAN"}
            ]
        },
        {
            "name": "文章写作",
            "code": "SHENLUN_WZ",
            "weight": 0.20,
            "estimated_minutes": 40,
            "sub_points": [
                {"name": "审题立意", "code": "SHENLUN_WZ_TOPIC"},
                {"name": "结构布局", "code": "SHENLUN_WZ_STRUCTURE"}
            ]
        }
    ]

    # 创建行测大类节点
    xingce_category = KnowledgePoint(
        name="行测",
        code="XINGCE",
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
        code="SHENLUN",
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
        print(f"✅ 创建行测模块: {module_node.name} (权重: {module['weight']}, 时间: {module['estimated_minutes']}min)")

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
        print(f"✅ 创建申论题型: {module_node.name} (权重: {module['weight']}, 时间: {module['estimated_minutes']}min)")

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
    stmt = select(KnowledgePoint).where(KnowledgePoint.code == "XINGCE")
    xingce_category = db.execute(stmt).scalar_one_or_none()
    if not xingce_category:
        xingce_category = KnowledgePoint(
            name="行测",
            code="XINGCE",
            parent_id=root.id,
            weight=1.0,
            estimated_minutes=0
        )
        db.add(xingce_category)
        db.flush()
        print("✅ 补充行测大类节点")

    stmt = select(KnowledgePoint).where(KnowledgePoint.code == "SHENLUN")
    shenlun_category = db.execute(stmt).scalar_one_or_none()
    if not shenlun_category:
        shenlun_category = KnowledgePoint(
            name="申论",
            code="SHENLUN",
            parent_id=root.id,
            weight=1.0,
            estimated_minutes=0
        )
        db.add(shenlun_category)
        db.flush()
        print("✅ 补充申论大类节点")

    # 定义完整的知识点结构（与create_knowledge_tree保持一致）
    xingce_modules = [
        {
            "name": "常识判断", "code": "XINGCE_CS", "weight": 0.18, "estimated_minutes": 35,
            "sub_points": [
                {"name": "政治常识", "code": "XINGCE_CS_POLITICS"},
                {"name": "法律常识", "code": "XINGCE_CS_LAW"},
                {"name": "人文常识", "code": "XINGCE_CS_HUMANITIES"}
            ]
        },
        {
            "name": "言语理解与表达", "code": "XINGCE_YY", "weight": 0.22, "estimated_minutes": 45,
            "sub_points": [
                {"name": "阅读理解", "code": "XINGCE_YY_READ"},
                {"name": "逻辑填空", "code": "XINGCE_YY_BLANK"},
                {"name": "语句表达", "code": "XINGCE_YY_EXPRESSION"}
            ]
        },
        {
            "name": "数量关系", "code": "XINGCE_SL", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "算术问题", "code": "XINGCE_SL_ARITHMETIC"},
                {"name": "工程问题", "code": "XINGCE_SL_ENGINEERING"},
                {"name": "行程问题", "code": "XINGCE_SL_TRAVEL"}
            ]
        },
        {
            "name": "判断推理", "code": "XINGCE_PD", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "图形推理", "code": "XINGCE_PD_GRAPH"},
                {"name": "类比推理", "code": "XINGCE_PD_ANALOGY"},
                {"name": "逻辑判断", "code": "XINGCE_PD_LOGIC"}
            ]
        },
        {
            "name": "资料分析", "code": "XINGCE_ZL", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "文字资料", "code": "XINGCE_ZL_TEXT"},
                {"name": "表格资料", "code": "XINGCE_ZL_TABLE"},
                {"name": "图形资料", "code": "XINGCE_ZL_CHART"}
            ]
        }
    ]

    shenlun_modules = [
        {
            "name": "归纳概括", "code": "SHENLUN_GN", "weight": 0.18, "estimated_minutes": 35,
            "sub_points": [
                {"name": "概括主题", "code": "SHENLUN_GN_THEME"},
                {"name": "提取要点", "code": "SHENLUN_GN_POINTS"}
            ]
        },
        {
            "name": "综合分析", "code": "SHENLUN_ZH", "weight": 0.22, "estimated_minutes": 45,
            "sub_points": [
                {"name": "原因分析", "code": "SHENLUN_ZH_CAUSE"},
                {"name": "影响分析", "code": "SHENLUN_ZH_IMPACT"}
            ]
        },
        {
            "name": "提出对策", "code": "SHENLUN_DC", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "问题诊断", "code": "SHENLUN_DC_DIAGNOSIS"},
                {"name": "对策制定", "code": "SHENLUN_DC_STRATEGY"}
            ]
        },
        {
            "name": "应用文写作", "code": "SHENLUN_YYW", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "公文写作", "code": "SHENLUN_YYW_OFFICIAL"},
                {"name": "方案写作", "code": "SHENLUN_YYW_PLAN"}
            ]
        },
        {
            "name": "文章写作", "code": "SHENLUN_WZ", "weight": 0.20, "estimated_minutes": 40,
            "sub_points": [
                {"name": "审题立意", "code": "SHENLUN_WZ_TOPIC"},
                {"name": "结构布局", "code": "SHENLUN_WZ_STRUCTURE"}
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
            print(f"✅ 补充申论题型: {module['name']}")

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
                        # 为不同知识点设置不同的掌握度（基于code设置，模拟真实学习情况）
                        if kp.code.startswith("XINGCE_SL"):  # 数量关系
                            mastery = 0.4  # 40% - 较薄弱
                        elif kp.code.startswith("XINGCE_PD"):  # 判断推理
                            mastery = 0.6  # 60% - 中等
                        elif kp.code.startswith("XINGCE_YY"):  # 言语理解与表达
                            mastery = 0.5  # 50% - 中等
                        elif kp.code == "XINGCE":  # 行测大类
                            mastery = 0.5  # 50% - 中等
                        elif kp.code.startswith("SHENLUN"):  # 申论相关
                            mastery = 0.7  # 70% - 良好
                        elif kp.code == "SHENLUN":  # 申论大类
                            mastery = 0.7  # 70% - 良好
                        else:
                            mastery = 0.3  # 30% - 默认掌握度

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
            # 获取各模块的知识点ID
            module_kps = {}
            module_codes = ['XINGCE_SL', 'XINGCE_PD', 'XINGCE_YY', 'XINGCE_CS', 'XINGCE_ZL']
            for code in module_codes:
                stmt = select(KnowledgePoint).where(KnowledgePoint.code == code)
                kp = db.execute(stmt).scalar_one_or_none()
                if kp:
                    module_kps[code] = kp

            questions_data = [
                # 数量关系模块题目
                {
                    "type": "SINGLE",
                    "stem": "如果3个苹果的价格是5元，那么8个苹果的价格是多少元？",
                    "options_json": ["A. 12", "B. 13.33", "C. 15", "D. 16"],
                    "answer_json": ["B"],
                    "analysis": "通过比例计算：3个苹果=5元，1个苹果=5/3元，8个苹果=5/3×8≈13.33元",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_SL').id] if module_kps.get('XINGCE_SL') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "一个工程队完成一项工程需要15天，另一个工程队完成同样工程需要10天。如果两队合做，几天可以完成？",
                    "options_json": ["A. 5天", "B. 6天", "C. 7天", "D. 8天"],
                    "answer_json": ["B"],
                    "analysis": "两队每天合做工程的1/15 + 1/10 = 1/6，所以6天完成。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_SL').id] if module_kps.get('XINGCE_SL') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "甲车从A地开往B地，每小时40公里；乙车从B地开往A地，每小时50公里。相遇后继续前进，甲车到达B地后1小时乙车到达A地。AB两地距离多少公里？",
                    "options_json": ["A. 300", "B. 350", "C. 400", "D. 450"],
                    "answer_json": ["D"],
                    "analysis": "设AB距离为S，相遇时间为T，则甲走ST=40T，乙走ST=50T，S=40T+50T=90T。甲到达B地时间为S/40=T+S/50，代入得T=2.5小时，S=225公里。",
                    "difficulty": 3,
                    "knowledge_ids": [module_kps.get('XINGCE_SL').id] if module_kps.get('XINGCE_SL') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "一项工作甲单独做需要8小时完成，乙单独做需要12小时完成。如果两人合做，多少小时完成？",
                    "options_json": ["A. 4.5", "B. 4.8", "C. 5.0", "D. 5.2"],
                    "answer_json": ["B"],
                    "analysis": "两人合做效率为1/8 + 1/12 = 5/24，所以时间为24/5=4.8小时。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_SL').id] if module_kps.get('XINGCE_SL') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "一个水池有两个进水管和一个出水管。第一个进水管每小时进水60立方米，第二个进水管每小时进水40立方米，出水管每小时出水50立方米。如果开始时水池是空的，8小时后水池中有多少立方米水？",
                    "options_json": ["A. 400", "B. 450", "C. 500", "D. 550"],
                    "answer_json": ["A"],
                    "analysis": "净进水速度为60+40-50=50立方米/小时，8小时后水量为400立方米。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_SL').id] if module_kps.get('XINGCE_SL') else []
                },

                # 判断推理模块题目
                {
                    "type": "JUDGE",
                    "stem": "所有的三角形都是等腰三角形。",
                    "options_json": None,
                    "answer_json": ["F"],
                    "analysis": "等腰三角形是指至少有两条边相等的三角形，不是所有三角形都满足这个条件。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_PD').id] if module_kps.get('XINGCE_PD') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "在一次逻辑推理中，已知'所有A都是B'，'所有B都是C'，那么可以推出：",
                    "options_json": ["A. 所有A都是C", "B. 有些A是C", "C. 所有C都是A", "D. 有些C是A"],
                    "answer_json": ["A"],
                    "analysis": "根据三段论推理规则，从'所有A都是B'和'所有B都是C'可以推出'所有A都是C'。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_PD').id] if module_kps.get('XINGCE_PD') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "以下哪项不属于类比推理？",
                    "options_json": ["A. 玫瑰:花", "B. 学生:学校", "C. 结论:前提", "D. 北京:中国"],
                    "answer_json": ["C"],
                    "analysis": "类比推理是根据两个对象在某些属性上的相似性，推出它们在其他属性上也可能相似。C项是因果关系，不是类比关系。",
                    "difficulty": 3,
                    "knowledge_ids": [module_kps.get('XINGCE_PD').id] if module_kps.get('XINGCE_PD') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "在图形推理中，规律是'每行图形数量依次增加1个'，那么第三行应该有几个图形？",
                    "options_json": ["A. 3", "B. 4", "C. 5", "D. 6"],
                    "answer_json": ["B"],
                    "analysis": "第一行1个，第二行2个，第三行应该是3个，但选项中没有，所以规律可能是其他。实际上这道题的规律是每行图形数量等于行号。",
                    "difficulty": 3,
                    "knowledge_ids": [module_kps.get('XINGCE_PD').id] if module_kps.get('XINGCE_PD') else []
                },
                {
                    "type": "JUDGE",
                    "stem": "如果'有些学生是运动员'为真，那么'所有运动员都是学生'一定为假。",
                    "options_json": None,
                    "answer_json": ["T"],
                    "analysis": "从'有些学生是运动员'不能必然推出'所有运动员都是学生'，所以原命题为真。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_PD').id] if module_kps.get('XINGCE_PD') else []
                },

                # 言语理解与表达模块题目
                {
                    "type": "SINGLE",
                    "stem": "以下哪个词的词性与其他三个不同？",
                    "options_json": ["A. 快速", "B. 奔跑", "C. 迅速", "D. 慢慢"],
                    "answer_json": ["B"],
                    "analysis": "A、C、D都是形容词，B是动词。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_YY').id] if module_kps.get('XINGCE_YY') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "阅读理解：这段文字主要谈论的是什么？",
                    "options_json": ["A. 环境保护", "B. 经济发展", "C. 科技创新", "D. 教育改革"],
                    "answer_json": ["A"],
                    "analysis": "通过分析文章主题和关键词，可以确定主要谈论环境保护。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_YY').id] if module_kps.get('XINGCE_YY') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "在句子'他终于明白了问题的严重性'中，'终于'的修饰对象是：",
                    "options_json": ["A. 他", "B. 明白", "C. 了", "D. 问题"],
                    "answer_json": ["B"],
                    "analysis": "'终于'是时间副词，修饰动词'明白'。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_YY').id] if module_kps.get('XINGCE_YY') else []
                },
                {
                    "type": "JUDGE",
                    "stem": "在现代汉语中，'的、地、得'三个字的用法完全一样。",
                    "options_json": None,
                    "answer_json": ["F"],
                    "analysis": "'的'表所属，'地'表状态，'得'表程度，三个字用法不同。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_YY').id] if module_kps.get('XINGCE_YY') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "逻辑填空：______就是______，这是对______的______。",
                    "options_json": ["A. 创新 活力 企业 要求", "B. 发展 灵魂 国家 必然", "C. 改革 动力 社会 前提", "D. 进步 源泉 文明 基础"],
                    "answer_json": ["D"],
                    "analysis": "根据语境和逻辑关系，选择最合适的词语填充。",
                    "difficulty": 3,
                    "knowledge_ids": [module_kps.get('XINGCE_YY').id] if module_kps.get('XINGCE_YY') else []
                },

                # 常识判断模块题目
                {
                    "type": "SINGLE",
                    "stem": "中国共产党第十九次全国代表大会是在哪一年召开的？",
                    "options_json": ["A. 2016", "B. 2017", "C. 2018", "D. 2019"],
                    "answer_json": ["B"],
                    "analysis": "中国共产党第十九次全国代表大会于2017年10月18日至24日在北京召开。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_CS').id] if module_kps.get('XINGCE_CS') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "根据《中华人民共和国宪法》，我国的国家机构实行什么原则？",
                    "options_json": ["A. 三权分立", "B. 议行合一", "C. 民主集中制", "D. 责任内阁制"],
                    "answer_json": ["C"],
                    "analysis": "我国宪法规定，国家机构实行民主集中制原则。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_CS').id] if module_kps.get('XINGCE_CS') else []
                },
                {
                    "type": "JUDGE",
                    "stem": "我国的根本制度是社会主义制度。",
                    "options_json": None,
                    "answer_json": ["T"],
                    "analysis": "我国宪法规定，社会主义制度是中华人民共和国的根本制度。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_CS').id] if module_kps.get('XINGCE_CS') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "人工智能的发展对就业市场的影响主要是：",
                    "options_json": ["A. 完全替代人类工作", "B. 创造新的就业机会", "C. 导致大规模失业", "D. 与就业无关"],
                    "answer_json": ["B"],
                    "analysis": "人工智能会替代一些重复性工作，但也会创造新的技术和管理岗位。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_CS').id] if module_kps.get('XINGCE_CS') else []
                },

                # 资料分析模块题目
                {
                    "type": "SINGLE",
                    "stem": "根据表格数据，2019年第二季度销售额同比增长最快的地区是：",
                    "options_json": ["A. 华北", "B. 华东", "C. 华南", "D. 西北"],
                    "answer_json": ["C"],
                    "analysis": "通过计算各地区同比增长率，华南地区增长最快。",
                    "difficulty": 2,
                    "knowledge_ids": [module_kps.get('XINGCE_ZL').id] if module_kps.get('XINGCE_ZL') else []
                },
                {
                    "type": "SINGLE",
                    "stem": "从柱状图可以看出，产品A的销量在哪个月份最高？",
                    "options_json": ["A. 1月", "B. 4月", "C. 7月", "D. 10月"],
                    "answer_json": ["B"],
                    "analysis": "观察柱状图高度，4月份的柱子最高。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_ZL').id] if module_kps.get('XINGCE_ZL') else []
                },
                {
                    "type": "JUDGE",
                    "stem": "根据饼图数据，产品C占比超过30%。",
                    "options_json": None,
                    "answer_json": ["F"],
                    "analysis": "饼图显示产品C占比为25%，没有超过30%。",
                    "difficulty": 1,
                    "knowledge_ids": [module_kps.get('XINGCE_ZL').id] if module_kps.get('XINGCE_ZL') else []
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
