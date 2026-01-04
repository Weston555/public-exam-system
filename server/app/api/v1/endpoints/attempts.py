from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from ....core.database import get_db
from ....models.attempt import Attempt, Answer
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap
from ....models.progress import UserKnowledgeState, WrongQuestion
from ..deps import get_current_student

router = APIRouter()


class AnswerSubmit(BaseModel):
    question_id: int
    answer: str
    time_spent_seconds: int = 0


@router.post("/{attempt_id}/answer")
async def submit_answer(
    attempt_id: int,
    request: AnswerSubmit,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """提交单题答案"""
    try:
        # 验证attempt属于当前用户且状态为DOING
        attempt = db.query(Attempt).filter(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"],
            Attempt.status == "DOING"
        ).first()

        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考试记录不存在或已结束"
            )

        # 验证题目存在
        question = db.query(Question).filter(Question.id == request.question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="题目不存在"
            )

        # 检查是否已有答案，更新或创建
        existing_answer = db.query(Answer).filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == request.question_id
        ).first()

        if existing_answer:
            # 更新答案
            existing_answer.answer_json = [request.answer]
            existing_answer.time_spent_seconds = request.time_spent_seconds
        else:
            # 创建新答案
            answer = Answer(
                attempt_id=attempt_id,
                question_id=request.question_id,
                answer_json=[request.answer],
                time_spent_seconds=request.time_spent_seconds
            )
            db.add(answer)

        db.commit()

        return {"message": "答案提交成功"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交答案失败: {str(e)}"
        )


@router.post("/{attempt_id}/submit")
async def submit_exam(
    attempt_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """提交考试并判分"""
    try:
        # 验证attempt属于当前用户且状态为DOING
        attempt = db.query(Attempt).filter(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"],
            Attempt.status == "DOING"
        ).first()

        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="考试记录不存在或已结束"
            )

        # 获取所有答案
        answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()

        if not answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未找到任何答案记录"
            )

        total_score = 0
        correct_count = 0
        total_questions = len(answers)
        results = []

        # 逐题判分
        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if not question:
                continue

            # 简单判分 (实际可以更复杂)
            user_answer = answer.answer_json[0] if answer.answer_json else ""
            correct_answer = question.answer_json[0] if question.answer_json else ""

            is_correct = str(user_answer).strip().lower() == str(correct_answer).strip().lower()
            score_awarded = 2.0 if is_correct else 0.0

            # 更新答案记录
            answer.is_correct = is_correct
            answer.score_awarded = score_awarded

            total_score += score_awarded
            if is_correct:
                correct_count += 1

            results.append({
                "question_id": answer.question_id,
                "is_correct": is_correct,
                "score_awarded": score_awarded,
                "correct_answer": question.answer_json,
                "user_answer": answer.answer_json
            })

            # 更新错题本
            if not is_correct:
                wrong_question = db.query(WrongQuestion).filter(
                    WrongQuestion.user_id == current_user["id"],
                    WrongQuestion.question_id == answer.question_id
                ).first()

                if wrong_question:
                    wrong_question.wrong_count += 1
                    wrong_question.last_wrong_at = datetime.utcnow()
                else:
                    wrong_question = WrongQuestion(
                        user_id=current_user["id"],
                        question_id=answer.question_id,
                        wrong_count=1,
                        last_wrong_at=datetime.utcnow()
                    )
                    db.add(wrong_question)

                # 更新知识点掌握度
                question_knowledge = db.query(QuestionKnowledgeMap).filter(
                    QuestionKnowledgeMap.question_id == answer.question_id
                ).all()

                for qk in question_knowledge:
                    knowledge_state = db.query(UserKnowledgeState).filter(
                        UserKnowledgeState.user_id == current_user["id"],
                        UserKnowledgeState.knowledge_id == qk.knowledge_id
                    ).first()

                    if knowledge_state:
                        # 简单更新：答错降低掌握度
                        knowledge_state.mastery = max(0.0, knowledge_state.mastery - 0.1)
                        knowledge_state.updated_at = datetime.utcnow()
                    else:
                        # 创建掌握度记录
                        knowledge_state = UserKnowledgeState(
                            user_id=current_user["id"],
                            knowledge_id=qk.knowledge_id,
                            mastery=0.5  # 默认中等掌握度
                        )
                        db.add(knowledge_state)

        # 更新attempt状态
        attempt.status = "SUBMITTED"
        attempt.submitted_at = datetime.utcnow()
        attempt.total_score = total_score

        db.commit()

        return {
            "attempt_id": attempt_id,
            "total_score": total_score,
            "total_questions": total_questions,
            "correct_count": correct_count,
            "submitted_at": attempt.submitted_at,
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交考试失败: {str(e)}"
        )


@router.get("/{attempt_id}/result")
async def get_attempt_result(
    attempt_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取考试结果"""
    attempt = db.query(Attempt).filter(
        Attempt.id == attempt_id,
        Attempt.user_id == current_user["id"],
        Attempt.status == "SUBMITTED"
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="考试记录不存在或未完成"
        )

    # 获取所有答案和题目详情
    answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    results = []

    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if question:
            results.append({
                "question_id": answer.question_id,
                "question_stem": question.stem,
                "is_correct": answer.is_correct,
                "score_awarded": answer.score_awarded,
                "correct_answer": question.answer_json,
                "user_answer": answer.answer_json,
                "analysis": question.analysis
            })

    return {
        "attempt_id": attempt.id,
        "total_score": attempt.total_score,
        "submitted_at": attempt.submitted_at,
        "results": results
    }
