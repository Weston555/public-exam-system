from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ....core.database import get_db
from ....models.paper import Exam, Paper
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
        query = db.query(Exam)
        if category:
            query = query.filter(Exam.category == category)
        if status:
            query = query.filter(Exam.status == status)
        total = query.count()
        exams = query.offset((page - 1) * size).limit(size).all()
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
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
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
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    exam.status = "ARCHIVED"
    db.commit()
    return {"id": exam.id, "status": exam.status}


