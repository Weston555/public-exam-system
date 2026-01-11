from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from ....core.database import get_db
from ....models.paper import Exam, Paper, PaperQuestion
from ....models.attempt import Attempt
from ....models.question import Question
from ..deps import get_current_student

router = APIRouter()


class MockGenerateRequest(BaseModel):
    count: int = 20
    duration_minutes: int = 60


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
        subq = stmt.order_by(None).with_only_columns(Exam.id).subquery()
        total = db.execute(select(func.count()).select_from(subq)).scalar_one()

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
        from ....services.exam_runtime import start_exam_for_user
        return start_exam_for_user(db, exam_id, current_user["id"])

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"开始考试失败: {str(e)}"
        )


@router.post("/mock/generate")
async def generate_mock_exam(
    request: MockGenerateRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """生成个性化模拟考试"""
    try:
        # 使用模板化组卷服务生成模拟考试
        from ....services.paper_template import build_mock_paper

        # 根据题目数量计算比例（简化版：平均分配到5个模块）
        total_questions = request.count
        base_count = total_questions // 5
        remainder = total_questions % 5

        # 行测5个模块的简写
        ratio = {
            "XINGCE_QUANTITATIVE": base_count + (1 if remainder > 0 else 0),  # 数量关系
            "XINGCE_LOGICAL": base_count + (1 if remainder > 1 else 0),      # 判断推理
            "XINGCE_LANGUAGE": base_count + (1 if remainder > 2 else 0),     # 言语理解
            "XINGCE_DATA": base_count + (1 if remainder > 3 else 0),         # 资料分析
            "XINGCE_COMMON": base_count                                      # 常识判断
        }

        paper, exam = build_mock_paper(
            db=db,
            subject="XINGCE",
            total=request.count,
            ratio=ratio,
            created_by=current_user["id"]
        )

        return {
            "exam_id": exam.id,
            "paper_id": paper.id,
            "count": request.count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成模拟考试失败: {str(e)}"
        )
