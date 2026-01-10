"""
个性化模拟卷生成服务
根据用户薄弱知识点智能生成模拟考试
"""

from sqlalchemy import select, func
from sqlalchemy.orm import Session
from datetime import datetime
import random

from ..models.question import Question
from ..models.knowledge import QuestionKnowledgeMap, KnowledgePoint
from ..models.progress import UserKnowledgeState
from ..models.paper import Paper, PaperQuestion, Exam


def generate_personalized_mock_exam(db: Session, user_id: int, count: int = 3, duration_minutes: int = 60) -> Exam:
    """
    根据用户薄弱知识点生成个性化模拟考试

    Args:
        db: 数据库会话
        user_id: 用户ID
        count: 题目数量，默认20题
        duration_minutes: 考试时长，默认60分钟

    Returns:
        Exam: 生成的考试对象

    Raises:
        HTTPException: 当题库不足时抛出异常
    """
    # 1. 获取用户薄弱知识点：mastery < 0.6，按mastery升序取前6个
    weak_kps_stmt = select(UserKnowledgeState).where(
        UserKnowledgeState.user_id == user_id,
        UserKnowledgeState.mastery < 0.6
    ).order_by(UserKnowledgeState.mastery.asc()).limit(6)

    weak_kps = db.execute(weak_kps_stmt).scalars().all()
    weak_kp_ids = [kp.knowledge_id for kp in weak_kps]

    # 如果没有薄弱知识点，则取所有知识点
    if not weak_kp_ids:
        all_kps_stmt = select(KnowledgePoint.id)
        all_kps = db.execute(all_kps_stmt).scalars().all()
        weak_kp_ids = list(all_kps)[:6]  # 取前6个

    if not weak_kp_ids:
        raise Exception("暂无知识点数据，无法生成模拟卷")

    # 2. 根据薄弱知识点获取题目，优先抽SINGLE/MULTI/JUDGE，难度1-3
    question_candidates = []

    for kp_id in weak_kp_ids:
        # 获取该知识点的题目
        kp_questions_stmt = select(Question).join(
            QuestionKnowledgeMap,
            Question.id == QuestionKnowledgeMap.question_id
        ).where(
            QuestionKnowledgeMap.knowledge_id == kp_id,
            Question.type.in_(['SINGLE', 'MULTI', 'JUDGE']),  # 优先选择客观题
            Question.difficulty.in_([1, 2, 3])  # 中等难度
        )

        questions = db.execute(kp_questions_stmt).scalars().all()
        question_candidates.extend(questions)

    # 去重
    seen_ids = set()
    unique_questions = []
    for q in question_candidates:
        if q.id not in seen_ids:
            unique_questions.append(q)
            seen_ids.add(q.id)

    # 如果不够，补充其他题目
    if len(unique_questions) < count:
        remaining_count = count - len(unique_questions)
        all_questions_stmt = select(Question).where(
            Question.type.in_(['SINGLE', 'MULTI', 'JUDGE'])
        ).order_by(func.random()).limit(remaining_count * 2)  # 多取一些用于去重

        additional_questions = db.execute(all_questions_stmt).scalars().all()

        for q in additional_questions:
            if q.id not in seen_ids and len(unique_questions) < count:
                unique_questions.append(q)
                seen_ids.add(q.id)

    if len(unique_questions) < count:
        raise Exception(f"题库题目不足，无法生成{count}题的模拟卷")

    # 随机选择指定数量的题目
    selected_questions = random.sample(unique_questions, count)

    # 3. 创建Paper
    paper = Paper(
        title=f"个性化模拟考试 - {user_id}",
        mode="AUTO",
        config_json={
            "type": "personalized_mock",
            "weak_knowledge_points": weak_kp_ids,
            "count": count,
            "generated_at": datetime.utcnow().isoformat()
        },
        total_score=float(count * 2.0),
        created_by=user_id
    )
    db.add(paper)
    db.flush()

    # 4. 创建PaperQuestion
    order_no = 1
    for question in selected_questions:
        pq = PaperQuestion(
            paper_id=paper.id,
            question_id=question.id,
            order_no=order_no,
            score=2.0
        )
        db.add(pq)
        order_no += 1

    # 5. 创建Exam
    exam = Exam(
        paper_id=paper.id,
        title=f"个性化模拟考试 - {datetime.now().strftime('%Y%m%d %H:%M')}",
        category="MOCK",
        duration_minutes=duration_minutes,
        status="PUBLISHED",
        created_by=user_id
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)

    return exam
