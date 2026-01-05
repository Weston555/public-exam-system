from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from ....core.database import get_db
from ....models.paper import Exam, Paper, PaperQuestion, Question
from ....models.question import QuestionKnowledgeMap
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
        count_stmt = stmt.with_only_columns(Exam.id)
        total = db.execute(count_stmt).scalars().count()

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
        # 1. 将现有的DIAGNOSTIC考试状态改为ARCHIVED
        stmt = select(Exam).where(Exam.category == "DIAGNOSTIC", Exam.status != "ARCHIVED")
        existing_exams = db.execute(stmt).scalars().all()

        for exam in existing_exams:
            exam.status = "ARCHIVED"
            exam.title = f"{exam.title} (已归档 {datetime.now().strftime('%Y-%m-%d %H:%M')})"

        # 2. 创建新的诊断试卷
        # 获取所有问题（通常是基线诊断用的题目）
        questions_stmt = select(Question)
        questions = db.execute(questions_stmt).scalars().all()

        if not questions:
            raise HTTPException(status_code=400, detail="没有可用的题目，无法生成诊断试卷")

        # 创建试卷
        paper_title = f"基线诊断试卷 (重新生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})"
        paper = Paper(
            title=paper_title,
            mode="AUTO",
            total_score=float(len(questions) * 2.0),
            created_by=current_user["id"]
        )
        db.add(paper)
        db.flush()

        # 添加题目到试卷
        for i, question in enumerate(questions):
            paper_question = PaperQuestion(
                paper_id=paper.id,
                question_id=question.id,
                order_no=i + 1,
                score=2.0
            )
            db.add(paper_question)

        # 3. 创建新的诊断考试
        exam = Exam(
            paper_id=paper.id,
            title=f"基线诊断考试 (重新生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
            category="DIAGNOSTIC",
            duration_minutes=30,
            status="PUBLISHED",
            created_by=current_user["id"]
        )
        db.add(exam)

        db.commit()
        db.refresh(exam)

        return {
            "id": exam.id,
            "message": "基线诊断考试重新生成成功",
            "title": exam.title,
            "paper_id": paper.id
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"重新生成诊断考试失败: {str(e)}")


