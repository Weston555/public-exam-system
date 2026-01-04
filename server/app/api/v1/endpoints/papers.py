from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from ....core.database import get_db
from ....models.paper import Paper, PaperQuestion
from ..deps import get_current_admin

router = APIRouter()


@router.get("/")
async def get_papers(page: int = Query(1, ge=1), size: int = Query(20, ge=1), db: Session = Depends(get_db)):
    try:
        query = db.query(Paper)
        total = query.count()
        papers = query.offset((page - 1) * size).limit(size).all()
        items = []
        for p in papers:
            items.append({
                "id": p.id,
                "title": p.title,
                "mode": p.mode,
                "total_score": float(p.total_score) if p.total_score is not None else None,
                "created_by": p.created_by,
                "created_at": p.created_at.isoformat() if p.created_at else None
            })
        return {"items": items, "total": total, "page": page, "size": size}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/")
async def create_paper(payload: dict, current_user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        paper = Paper(
            title=payload.get("title", "Untitled"),
            mode=payload.get("mode", "AUTO"),
            total_score=payload.get("total_score", 0),
            created_by=current_user["id"]
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)
        return {"id": paper.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
