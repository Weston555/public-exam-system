from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
import csv
import io
import hashlib

from ....core.database import get_db
from ....core.config import settings
from ..deps import get_current_admin
from ....models.user import User
from ....models.attempt import Attempt
from ....models.progress import UserKnowledgeState, WrongQuestion

router = APIRouter()


def anonymize_user_id(user_id: int) -> str:
    s = f"{user_id}:{settings.jwt_secret}"
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return h[:16]


@router.get("/anonymized")
async def export_anonymized(current_user: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    try:
        # Prepare CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        # header
        writer.writerow(["anon_user_id", "attempt_id", "exam_id", "submitted_at", "total_score", "knowledge_id", "mastery", "wrong_question_id", "wrong_count", "next_review_at"])

        # For each user, export attempts and mastery and wrong_questions
        users_stmt = select(User)
        users = db.execute(users_stmt).scalars().all()
        for u in users:
            anon = anonymize_user_id(u.id)
            # attempts
            attempts_stmt = select(Attempt).where(Attempt.user_id == u.id, Attempt.status == "SUBMITTED")
            attempts = db.execute(attempts_stmt).scalars().all()
            for a in attempts:
                # write attempt row (knowledge/mastery/wrong fields empty)
                writer.writerow([anon, a.id, a.exam_id, a.submitted_at.isoformat() if a.submitted_at else "", a.total_score, "", "", "", "", ""])
            # mastery
            states_stmt = select(UserKnowledgeState).where(UserKnowledgeState.user_id == u.id)
            states = db.execute(states_stmt).scalars().all()
            for s in states:
                writer.writerow([anon, "", "", "", "", s.knowledge_id, float(s.mastery), "", "", ""])
            # wrong questions
            wrongs_stmt = select(WrongQuestion).where(WrongQuestion.user_id == u.id)
            wrongs = db.execute(wrongs_stmt).scalars().all()
            for w in wrongs:
                writer.writerow([anon, "", "", "", "", "", "", w.id, w.wrong_count, w.next_review_at.isoformat() if w.next_review_at else ""])

        output.seek(0)
        headers = {
            'Content-Disposition': 'attachment; filename="anonymized_export.csv"'
        }
        return StreamingResponse(iter([output.read()]), media_type="text/csv", headers=headers)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


