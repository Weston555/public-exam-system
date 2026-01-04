from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import random

from ....core.database import get_db
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap
from ....models.progress import UserKnowledgeState
from ....models.paper import Paper, PaperQuestion, Exam
from ..deps import get_current_student

router = APIRouter()


class PracticeGenerateRequest(BaseModel):
    knowledge_id: int
    count: int = 10
    mode: Optional[str] = "ADAPTIVE"  # ADAPTIVE | FIXED


@router.post("/generate")
async def generate_practice(
    request: PracticeGenerateRequest,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """
    生成专项练习（自动组卷）
    """
    try:
        knowledge_id = request.knowledge_id
        count = max(1, int(request.count))
        mode = (request.mode or "ADAPTIVE").upper()

        # 获取符合知识点的题目（不限制难度先）
        q_ids_query = db.query(Question.id, Question.difficulty).join(
            QuestionKnowledgeMap, Question.id == QuestionKnowledgeMap.question_id
        ).filter(QuestionKnowledgeMap.knowledge_id == knowledge_id)

        candidates = q_ids_query.all()
        if not candidates:
            raise HTTPException(status_code=400, detail="所选知识点暂无题目")

        # 简单计算目标难度（若 ADAPTIVE 可基于 user mastery；这里先取中等策略）
        # 尝试按优先级选题：优先选目标难度，若不足则降级兜底
        # 我们先统计 available by difficulty
        by_diff = {}
        for q in candidates:
            by_diff.setdefault(q.difficulty, []).append(q.id)

        # difficulty selection strategy
        def pick_questions(target_diff, need):
            picked = []
            diff = target_diff
            while len(picked) < need and diff >= 1:
                pool = by_diff.get(diff, [])
                remaining = [pid for pid in pool if pid not in picked]
                take = min(len(remaining), need - len(picked))
                if take > 0:
                    picked.extend(random.sample(remaining, take))
                diff -= 1
            return picked

        # Determine user's mastery for this knowledge point (default 0)
        state = db.query(UserKnowledgeState).filter(
            UserKnowledgeState.user_id == current_user["id"],
            UserKnowledgeState.knowledge_id == knowledge_id
        ).first()
        mastery = float(state.mastery) if state and state.mastery is not None else 0.0

        # Map mastery -> target difficulty (explainable rule)
        # mastery < 0.3 -> target_diff = 2
        # 0.3 <= mastery < 0.6 -> target_diff = 3
        # mastery >= 0.6 -> target_diff = 4
        if mode == "ADAPTIVE":
            if mastery < 0.3:
                target = 2
            elif mastery < 0.6:
                target = 3
            else:
                target = 4
        else:
            target = 3

        selected = pick_questions(target, count)
        # If still insufficient, fill from all candidates
        all_ids = [q.id for q in candidates]
        remaining_pool = [pid for pid in all_ids if pid not in selected]
        if len(selected) < count and remaining_pool:
            need = count - len(selected)
            selected.extend(random.sample(remaining_pool, min(need, len(remaining_pool))))

        if not selected:
            raise HTTPException(status_code=400, detail="无法为该知识点抽题")

        # 创建 Paper (AUTO) and PaperQuestion entries
        paper = Paper(
            title=f"PRACTICE_KP_{knowledge_id}_{current_user['id']}",
            mode="AUTO",
            config_json={
                "knowledge_id": knowledge_id,
                "count": count,
                "mode": mode,
                "mastery": mastery,
                "target_diff": target
            },
            total_score= float(len(selected) * 2.0),
            created_by=current_user["id"]
        )
        db.add(paper)
        db.flush()

        order_no = 1
        for qid in selected:
            pq = PaperQuestion(
                paper_id=paper.id,
                question_id=qid,
                order_no=order_no,
                score=2.0
            )
            db.add(pq)
            order_no += 1

        # 创建 Exam 记录（PRACTICE）
        exam = Exam(
            paper_id=paper.id,
            title=f"专项练习 - 知识点 {knowledge_id}",
            category="PRACTICE",
            duration_minutes=0,
            status="PUBLISHED",
            created_by=current_user["id"]
        )
        db.add(exam)
        db.commit()
        db.refresh(exam)

        return {"exam_id": exam.id, "paper_id": paper.id, "count": len(selected)}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"生成练习失败: {e}")


