from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取考试列表"""
    try:
        query = db.query(Exam).filter(Exam.status == "PUBLISHED")

        if category:
            query = query.filter(Exam.category == category)

        total = query.count()
        exams = query.offset(skip).limit(limit).all()

        result = []
        for exam in exams:
            result.append({
                "id": exam.id,
                "title": exam.title,
                "category": exam.category,
                "duration_minutes": exam.duration_minutes,
                "status": exam.status,
                "created_at": exam.created_at
            })

        return {
            "items": result,
            "total": total,
            "skip": skip,
            "limit": limit
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
        exam = db.query(Exam).filter(
            Exam.id == exam_id,
            Exam.status == "PUBLISHED"
        ).first()

        if not exam:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考试不存在或未发布"
            )

        # 检查用户是否已有进行中的attempt
        existing_attempt = db.query(Attempt).filter(
            Attempt.exam_id == exam_id,
            Attempt.user_id == current_user["id"],
            Attempt.status == "DOING"
        ).first()

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
        paper_questions = db.query(PaperQuestion).filter(
            PaperQuestion.paper_id == exam.paper_id
        ).order_by(PaperQuestion.order_no).all()

        questions = []
        for pq in paper_questions:
            question = db.query(Question).filter(Question.id == pq.question_id).first()
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
            "questions": questions
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始考试失败: {str(e)}"
        )
