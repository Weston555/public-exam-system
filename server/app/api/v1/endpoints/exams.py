from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ....core.database import get_db
from ....models.paper import Exam, Paper, PaperQuestion
from ....models.attempt import Attempt
from ....models.question import Question
from ..deps import get_current_student

router = APIRouter()


@router.get("/")
async def get_exams(
    category: Optional[str] = Query(None, description="考试类别: DIAGNOSTIC, PRACTICE, MOCK"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取考试列表"""
    try:
        stmt = select(Exam).where(Exam.status == "PUBLISHED")

        if category:
            stmt = stmt.where(Exam.category == category)

        # 按创建时间倒序
        stmt = stmt.order_by(desc(Exam.created_at))

        # 获取总数
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.execute(count_stmt).scalar_one()

        # 分页获取数据
        exams = db.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()

        result = []
        for exam in exams:
            # 获取题目数量
            questions_stmt = select(func.count()).select_from(PaperQuestion).where(PaperQuestion.paper_id == exam.paper_id)
            total_questions = db.execute(questions_stmt).scalar_one()
            result.append({
                "id": exam.id,
                "title": exam.title,
                "category": exam.category,
                "duration_minutes": exam.duration_minutes,
                "status": exam.status,
                "total_questions": total_questions,
                "created_at": exam.created_at.isoformat() if exam.created_at else None
            })

        return {
            "items": result,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size if total > 0 else 0
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取考试列表失败: {str(e)}"
        )


@router.post("/{exam_id}/start")
async def start_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """开始考试"""
    try:
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
            Attempt.user_id == current_user["id"],
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
            user_id=current_user["id"],
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

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始考试失败: {str(e)}"
        )
