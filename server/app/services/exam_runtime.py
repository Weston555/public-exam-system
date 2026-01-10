"""
考试运行时服务
负责考试开始、答题、提交等核心业务逻辑
"""

from sqlalchemy import select
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from ..models.attempt import Attempt
from ..models.question import Question
from ..models.paper import Exam, PaperQuestion


def start_exam_for_user(db: Session, exam_id: int, user_id: int) -> Dict[str, Any]:
    """
    为用户开始考试

    Args:
        db: 数据库会话
        exam_id: 考试ID
        user_id: 用户ID

    Returns:
        dict: 包含attempt_id, exam, questions, started_at的响应数据

    Raises:
        HTTPException: 当考试不存在、未发布或用户已有进行中的考试时
    """
    from fastapi import HTTPException, status

    # 验证考试存在且已发布
    exam_stmt = select(Exam).where(Exam.id == exam_id, Exam.status == "PUBLISHED")
    exam = db.execute(exam_stmt).scalar_one_or_none()

    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="考试不存在或未发布"
        )

    # 检查用户是否已有进行中的attempt
    attempt_stmt = select(Attempt).where(
        Attempt.exam_id == exam_id,
        Attempt.user_id == user_id,
        Attempt.status == "DOING"
    )
    existing_attempt = db.execute(attempt_stmt).scalar_one_or_none()

    if existing_attempt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="您已有正在进行的考试"
        )

    # 创建新的attempt
    attempt = Attempt(
        exam_id=exam_id,
        user_id=user_id,
        started_at=datetime.utcnow(),
        status="DOING"
    )

    db.add(attempt)
    db.flush()  # 获取attempt.id

    # 获取试卷题目
    paper_questions_stmt = select(PaperQuestion).where(
        PaperQuestion.paper_id == exam.paper_id
    ).order_by(PaperQuestion.order_no)
    paper_questions = db.execute(paper_questions_stmt).scalars().all()

    questions = []
    for pq in paper_questions:
        question_stmt = select(Question).where(Question.id == pq.question_id)
        question = db.execute(question_stmt).scalar_one_or_none()
        if question:
            questions.append({
                "id": question.id,
                "order_no": pq.order_no,
                "question": {
                    "id": question.id,
                    "type": question.type,
                    "stem": question.stem,
                    "options_json": question.options_json
                }
            })

    db.commit()

    return {
        "attempt_id": attempt.id,
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "category": exam.category,
            "duration_minutes": exam.duration_minutes
        },
        "questions": questions,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None
    }
