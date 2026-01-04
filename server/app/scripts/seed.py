import sys
import os

# 添加当前目录和上级目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
server_dir = os.path.dirname(parent_dir)
sys.path.insert(0, server_dir)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models.user import User
from app.models.knowledge import KnowledgePoint
from app.models.question import Question
from app.models.knowledge import QuestionKnowledgeMap
from app.models.paper import Paper, PaperQuestion, Exam

def seed_database():
    """初始化数据库数据"""
    # 创建表
    create_tables()

    db = SessionLocal()
    try:
        # 创建管理员用户
        admin_username = "admin"
        admin_exists = db.query(User).filter(User.username == admin_username).first()
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
            user_exists = db.query(User).filter(User.username == username).first()
            if not user_exists:
                user = User(
                    username=username,
                    password_hash=get_password_hash(password),
                    role="STUDENT",
                    is_active=True
                )
                db.add(user)
                print(f"✅ 创建测试学员: {username}/{password}")

        # 创建知识点树
        if db.query(KnowledgePoint).count() == 0:
            # 一级知识点
            kp1 = KnowledgePoint(
                name="公务员考试",
                code="GOV_EXAM",
                weight=1.0,
                estimated_minutes=30
            )
            db.add(kp1)
            db.flush()

            # 二级知识点
            kp2 = KnowledgePoint(
                parent_id=kp1.id,
                name="行测",
                code="MATH_TEST",
                weight=0.6,
                estimated_minutes=45
            )
            db.add(kp2)

            kp3 = KnowledgePoint(
                parent_id=kp1.id,
                name="申论",
                code="ESSAY_TEST",
                weight=0.4,
                estimated_minutes=60
            )
            db.add(kp3)
            db.flush()

            # 三级知识点
            kp4 = KnowledgePoint(
                parent_id=kp2.id,
                name="数量关系",
                code="QUANTITATIVE",
                weight=0.3,
                estimated_minutes=30
            )
            db.add(kp4)

            kp5 = KnowledgePoint(
                parent_id=kp2.id,
                name="判断推理",
                code="LOGICAL",
                weight=0.4,
                estimated_minutes=35
            )
            db.add(kp5)

            kp6 = KnowledgePoint(
                parent_id=kp3.id,
                name="阅读理解",
                code="READING",
                weight=0.5,
                estimated_minutes=40
            )
            db.add(kp6)

            print("✅ 创建知识点树")

        # 创建测试题目
        if db.query(Question).count() == 0:
            # 获取知识点ID
            quantitative = db.query(KnowledgePoint).filter(KnowledgePoint.code == "QUANTITATIVE").first()
            logical = db.query(KnowledgePoint).filter(KnowledgePoint.code == "LOGICAL").first()
            reading = db.query(KnowledgePoint).filter(KnowledgePoint.code == "READING").first()

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
                    "knowledge_ids": [reading.id] if reading else []
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
        if db.query(Exam).filter(Exam.category == "DIAGNOSTIC").count() == 0:
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
            questions = db.query(Question).all()
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
        existing_mock = db.query(Exam).filter(Exam.category == "MOCK", Exam.title == mock_title).first()
        if not existing_mock:
            # 抽取题库中最多 30 题，尽量覆盖多个知识点
            all_questions = db.query(Question).all()
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
