from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from ....core.database import get_db
from ....models.paper import Exam, Paper, PaperQuestion
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap
from ....services.diagnostic_generator import generate_diagnostic_exam
from ..deps import get_current_admin

router = APIRouter()


class AdminExamCreate(BaseModel):
    title: str
    category: str  # DIAGNOSTIC | MOCK
    duration_minutes: Optional[int] = 0
    paper_id: Optional[int] = None


@router.get("/")
async def admin_list_exams(
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        stmt = select(Exam)
        if category:
            stmt = stmt.where(Exam.category == category)
        if status:
            stmt = stmt.where(Exam.status == status)

        # 获取总数
        subq = stmt.order_by(None).with_only_columns(Exam.id).subquery()
        total = db.execute(select(func.count()).select_from(subq)).scalar_one()

        # 获取分页数据
        exams = db.execute(stmt.offset((page - 1) * size).limit(size)).scalars().all()
        items = []
        for e in exams:
            items.append({
                "id": e.id,
                "title": e.title,
                "category": e.category,
                "duration_minutes": e.duration_minutes,
                "status": e.status,
                "paper_id": e.paper_id,
                "created_at": e.created_at.isoformat() if e.created_at else None
            })
        return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def admin_create_exam(
    payload: AdminExamCreate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    try:
        # 如果提供了 paper_id，验证试卷存在
        if payload.paper_id:
            paper_stmt = select(Paper).where(Paper.id == payload.paper_id)
            paper = db.execute(paper_stmt).scalar_one_or_none()
            if not paper:
                raise HTTPException(status_code=400, detail="指定的试卷不存在")

        exam = Exam(
            paper_id=payload.paper_id,
            title=payload.title,
            category=payload.category,
            duration_minutes=payload.duration_minutes or 0,
            status="DRAFT",
            created_by=current_user["id"]
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)
        return {"id": exam.id, "message": "创建成功", "status": exam.status}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{exam_id}/publish")
async def admin_publish_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    stmt = select(Exam).where(Exam.id == exam_id)
    exam = db.execute(stmt).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.status = "PUBLISHED"
    db.commit()
    return {"id": exam.id, "status": exam.status}


@router.put("/{exam_id}/archive")
async def admin_archive_exam(
    exam_id: int,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    stmt = select(Exam).where(Exam.id == exam_id)
    exam = db.execute(stmt).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.status = "ARCHIVED"
    db.commit()
    return {"id": exam.id, "status": exam.status}


@router.post("/diagnostic/regenerate")
async def admin_regenerate_diagnostic_exam(
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """重新生成基线诊断考试"""
    try:
        # 使用模板化组卷服务生成诊断考试
        from ....services.paper_template import build_diagnostic_paper

        paper, exam = build_diagnostic_paper(
            db=db,
            subject="XINGCE",  # 默认行测诊断
            per_module=1,      # 每个模块至少1道题（测试用，生产环境可调整）
            created_by=current_user["id"]
        )

        # build_diagnostic_paper 已经提交了事务，这里不需要再提交
        return {
            "exam_id": exam.id,
            "paper_id": paper.id,
            "title": exam.title,
            "message": "基线诊断考试重新生成成功"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重新生成诊断考试失败: {str(e)}")


