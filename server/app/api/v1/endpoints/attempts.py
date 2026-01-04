from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Union
from pydantic import BaseModel
from datetime import datetime, timedelta

from ....core.database import get_db
from ....models.attempt import Attempt, Answer
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap
from ....models.progress import UserKnowledgeState, WrongQuestion
from ..deps import get_current_student

router = APIRouter()


class AnswerSubmit(BaseModel):
    question_id: int
    answer: Union[str, List[str]]
    time_spent_seconds: int = 0


class AttemptSubmit(BaseModel):
    answers: List[AnswerSubmit]


@router.post("/{attempt_id}/answer")
async def submit_single_answer(
    attempt_id: int,
    answer_data: AnswerSubmit,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """提交单题答案"""
    try:
        # 验证作答记录存在且属于当前用户
        attempt = db.query(Attempt).filter(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"]
        ).first()

        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作答记录不存在"
            )

        if attempt.status != "DOING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="考试已结束，无法提交答案"
            )

        # 验证题目存在且属于该考试
        question = db.query(Question).filter(
            Question.id == answer_data.question_id
        ).first()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )

        # 标准化答案格式
        if isinstance(answer_data.answer, list):
            # 多选题：排序并转换为字符串列表
            normalized_answer = sorted([str(ans).strip().upper() for ans in answer_data.answer if ans])
        else:
            # 单选/判断/填空：转换为字符串列表
            normalized_answer = [str(answer_data.answer).strip()]

        # 检查是否已存在答案记录，如存在则更新，否则创建
        existing_answer = db.query(Answer).filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == answer_data.question_id
        ).first()

        if existing_answer:
            # 更新答案
            existing_answer.answer_json = normalized_answer
            existing_answer.time_spent_seconds = answer_data.time_spent_seconds
            db.commit()
        else:
            # 创建新答案
            new_answer = Answer(
                attempt_id=attempt_id,
                question_id=answer_data.question_id,
                answer_json=normalized_answer,
                time_spent_seconds=answer_data.time_spent_seconds
            )
            db.add(new_answer)
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
async def submit_attempt(
    attempt_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """提交整个考试并进行判分"""
    try:
        # 验证作答记录存在且属于当前用户
        attempt = db.query(Attempt).filter(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"]
        ).first()

        if not attempt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="作答记录不存在"
            )

        if attempt.status != "DOING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="考试已提交"
            )

        # 获取所有答案
        answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()

        if not answers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="未找到任何答案记录"
            )

        # 判分逻辑
        total_score = 0
        correct_count = 0
        total_questions = len(answers)
        results = []
        wrong_questions_data = []
        knowledge_updates = {}

        for answer in answers:
            question = db.query(Question).filter(Question.id == answer.question_id).first()
            if not question:
                continue

            # 按题型进行判分
            is_correct = False
            user_answer = answer.answer_json or []
            correct_answer = question.answer_json or []

            if question.type == "SINGLE":
                # 单选题：比较第一个答案
                user_ans = user_answer[0] if user_answer else ""
                correct_ans = correct_answer[0] if correct_answer else ""
                is_correct = str(user_ans).strip().upper() == str(correct_ans).strip().upper()

            elif question.type == "MULTI":
                # 多选题：比较集合
                user_set = set(str(ans).strip().upper() for ans in user_answer)
                correct_set = set(str(ans).strip().upper() for ans in correct_answer)
                is_correct = user_set == correct_set

            elif question.type == "JUDGE":
                # 判断题：支持多种格式
                user_ans = (user_answer[0] if user_answer else "").strip().upper()
                correct_ans = (correct_answer[0] if correct_answer else "").strip().upper()

                # 标准化判断题答案
                true_values = {"T", "TRUE", "正确", "是", "YES", "Y"}
                false_values = {"F", "FALSE", "错误", "否", "NO", "N"}

                user_bool = user_ans in true_values if user_ans in true_values | false_values else None
                correct_bool = correct_ans in true_values if correct_ans in true_values | false_values else None

                is_correct = user_bool == correct_bool and user_bool is not None

            elif question.type == "FILL":
                # 填空题：严格字符串匹配（可后续扩展模糊匹配）
                user_ans = (user_answer[0] if user_answer else "").strip()
                correct_ans = (correct_answer[0] if correct_answer else "").strip()
                is_correct = user_ans == correct_ans

            else:
                # 其他题型（简答等）：暂时不判分
                is_correct = False

            # 计算得分
            score_awarded = 2.0 if is_correct else 0.0

            # 更新答案记录
            answer.is_correct = is_correct
            answer.score_awarded = score_awarded

            total_score += score_awarded
            if is_correct:
                correct_count += 1

            # 收集结果
            results.append({
                "question_id": question.id,
                "question_stem": question.stem,
                "is_correct": is_correct,
                "score_awarded": score_awarded,
                "correct_answer": question.answer_json,
                "user_answer": answer.answer_json,
                "analysis": question.analysis
            })

            # 为知识点更新掌握度统计
            for kp_map in question.knowledge_points:
                kp_id = str(kp_map.knowledge_id)
                if kp_id not in knowledge_updates:
                    knowledge_updates[kp_id] = {"correct": 0, "total": 0}
                knowledge_updates[kp_id]["total"] += 1
                if is_correct:
                    knowledge_updates[kp_id]["correct"] += 1

            # 收集错题数据（只针对答错的题目）
            if not is_correct:
                wrong_questions_data.append({
                    "question_id": question.id
                })

        # 更新错题本
        for wrong_data in wrong_questions_data:
            # 检查是否已存在错题记录
            existing_wrong = db.query(WrongQuestion).filter(
                WrongQuestion.user_id == current_user["id"],
                WrongQuestion.question_id == wrong_data["question_id"]
            ).first()

            # 计算下次复习时间（简单遗忘曲线）
            def calculate_next_review(wrong_count: int) -> datetime:
                intervals = [1, 3, 7, 14, 30]  # 错题次数对应的复习间隔（天）
                days = intervals[min(wrong_count - 1, len(intervals) - 1)]
                return datetime.utcnow() + timedelta(days=days)

            if existing_wrong:
                existing_wrong.wrong_count += 1
                existing_wrong.last_wrong_at = datetime.utcnow()
                existing_wrong.next_review_at = calculate_next_review(existing_wrong.wrong_count)
            else:
                new_wrong = WrongQuestion(
                    user_id=current_user["id"],
                    question_id=wrong_data["question_id"],
                    wrong_count=1,
                    last_wrong_at=datetime.utcnow(),
                    next_review_at=calculate_next_review(1)
                )
                db.add(new_wrong)

        # 更新知识点掌握度
        for knowledge_id_str, stats in knowledge_updates.items():
            knowledge_id = int(knowledge_id_str)

            # 计算新的掌握度 (使用简单平均，可以后续优化为更复杂的算法)
            new_mastery = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0

            # 查找或创建知识点掌握状态
            existing_state = db.query(UserKnowledgeState).filter(
                UserKnowledgeState.user_id == current_user["id"],
                UserKnowledgeState.knowledge_id == knowledge_id
            ).first()

            if existing_state:
                # 使用指数移动平均更新掌握度
                alpha = 0.3  # 学习率
                existing_state.mastery = alpha * new_mastery + (1 - alpha) * existing_state.mastery
            else:
                new_state = UserKnowledgeState(
                    user_id=current_user["id"],
                    knowledge_id=knowledge_id,
                    mastery=new_mastery
                )
                db.add(new_state)

        # 更新作答记录
        attempt.submitted_at = datetime.utcnow()
        attempt.total_score = total_score
        attempt.status = "SUBMITTED"

        db.commit()

        return {
            "attempt_id": attempt_id,
            "total_score": total_score,
            "correct_count": correct_count,
            "total_questions": total_questions,
            "submitted_at": attempt.submitted_at.isoformat(),
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
        Attempt.user_id == current_user["id"]
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作答记录不存在"
        )

    if attempt.status != "SUBMITTED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="考试尚未完成"
        )

    # 获取答案详情
    answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
    results = []

    for answer in answers:
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if question:
            results.append({
                "question_id": question.id,
                "question_stem": question.stem,
                "is_correct": answer.is_correct,
                "score_awarded": answer.score_awarded,
                "correct_answer": question.answer_json,
                "user_answer": answer.answer_json,
                "analysis": question.analysis,
                "time_spent_seconds": answer.time_spent_seconds
            })

    return {
        "attempt_id": attempt.id,
        "exam_title": attempt.exam.title if attempt.exam else "未知考试",
        "total_score": attempt.total_score,
        "submitted_at": attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        "results": results
    }