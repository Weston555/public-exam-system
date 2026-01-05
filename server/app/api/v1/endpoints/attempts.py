from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import re

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
        attempt_stmt = select(Attempt).where(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"]
        )
        attempt = db.execute(attempt_stmt).scalar_one_or_none()

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
        question_stmt = select(Question).where(Question.id == answer_data.question_id)
        question = db.execute(question_stmt).scalar_one_or_none()

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
        existing_answer_stmt = select(Answer).where(
            Answer.attempt_id == attempt_id,
            Answer.question_id == answer_data.question_id
        )
        existing_answer = db.execute(existing_answer_stmt).scalar_one_or_none()

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
        attempt_stmt = select(Attempt).where(
            Attempt.id == attempt_id,
            Attempt.user_id == current_user["id"]
        )
        attempt = db.execute(attempt_stmt).scalar_one_or_none()

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
        answers_stmt = select(Answer).where(Answer.attempt_id == attempt_id)
        answers = db.execute(answers_stmt).scalars().all()

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

            # 获取题目分数（从PaperQuestion读取）
            paper_question = db.query(PaperQuestion).filter(
                PaperQuestion.paper_id == attempt.exam.paper_id,
                PaperQuestion.question_id == question.id
            ).first()
            question_score = float(paper_question.score) if paper_question else 2.0

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
                # 填空题：规范化比较（去首尾空白、连续空格压缩、忽略大小写）
                def normalize_text(s: str) -> str:
                    s2 = re.sub(r"\s+", " ", s.strip())
                    return s2.lower()

                user_ans_raw = (user_answer[0] if user_answer else "")
                user_norm = normalize_text(str(user_ans_raw))

                # support multiple correct answers
                is_correct = False
                if isinstance(correct_answer, list) and correct_answer:
                    for ca in correct_answer:
                        if normalize_text(str(ca)) == user_norm:
                            is_correct = True
                            break
                else:
                    correct_ans = (correct_answer[0] if correct_answer else "")
                    is_correct = normalize_text(str(correct_ans)) == user_norm

            elif question.type == "SHORT":
                # 简答题：关键词命中评分（MVP）
                # Expect question.answer_json to be like: {"keywords": [...], "min_hit": 2}
                matched_keywords = []
                user_text = (user_answer[0] if user_answer else "") if isinstance(user_answer, list) else (user_answer or "")
                user_text_norm = user_text.lower()

                score_awarded = 0.0
                is_correct = False

                if isinstance(correct_answer, dict) and "keywords" in correct_answer:
                    keywords = [str(k).lower() for k in correct_answer.get("keywords", [])]
                    min_hit = int(correct_answer.get("min_hit", max(1, len(keywords))))
                    for kw in keywords:
                        if kw and kw in user_text_norm:
                            matched_keywords.append(kw)
                    hit = len(matched_keywords)
                    if hit >= min_hit:
                        is_correct = True
                        score_awarded = question_score
                    else:
                        # fallback: partial credit if any keyword matched
                        if hit > 0:
                            is_correct = False
                            score_awarded = question_score * 0.5  # 半分
                        else:
                            is_correct = False
                            score_awarded = 0.0
                else:
                    # fallback: if correct_answer provided as list of keywords
                    if isinstance(correct_answer, list) and correct_answer:
                        keywords = [str(k).lower() for k in correct_answer]
                        for kw in keywords:
                            if kw and kw in user_text_norm:
                                matched_keywords.append(kw)
                        if matched_keywords:
                            is_correct = False
                            score_awarded = question_score * 0.5  # 半分
                        else:
                            is_correct = False
                            score_awarded = 0.0
                    else:
                        # no scoring rule available, default no score
                        is_correct = False
                        score_awarded = 0.0

            # 计算得分及更新答案记录
            # For SHORT we may have already set score_awarded above
            if question.type != "SHORT":
                score_awarded = question_score if is_correct else 0.0

            # Update answer record
            answer.is_correct = is_correct
            answer.score_awarded = float(score_awarded)

            total_score += score_awarded
            if is_correct:
                correct_count += 1

            # 收集结果
            res_item = {
                "question_id": question.id,
                "question_stem": question.stem,
                "is_correct": is_correct,
                "score_awarded": float(score_awarded),
                "correct_answer": question.answer_json,
                "user_answer": answer.answer_json,
                "analysis": question.analysis
            }
            # include matched keywords for SHORT if available
            if question.type == "SHORT":
                res_item["matched_keywords"] = matched_keywords if 'matched_keywords' in locals() else []

            results.append(res_item)

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


@router.get("/history")
async def get_attempts_history(
    category: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取当前用户的作答历史（可按考试类别过滤）"""
    try:
        query = db.query(Attempt).filter(Attempt.user_id == current_user["id"], Attempt.status == "SUBMITTED")
        if category:
            # join Exam
            from ....models.paper import Exam as ExamModel
            query = query.join(ExamModel, Attempt.exam_id == ExamModel.id).filter(ExamModel.category == category)

        attempts = query.order_by(Attempt.submitted_at.desc()).limit(limit).all()
        items = []
        for a in attempts:
            items.append({
                "attempt_id": a.id,
                "exam_id": a.exam_id,
                "exam_title": a.exam.title if a.exam else None,
                "total_score": float(a.total_score) if a.total_score is not None else None,
                "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
                "duration_minutes": a.exam.duration_minutes if a.exam else None
            })
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{attempt_id}")
async def get_attempt_detail(
    attempt_id: int,
    current_user: dict = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """获取 attempt 详情（用于答题页面恢复）"""
    attempt = db.query(Attempt).filter(
        Attempt.id == attempt_id,
        Attempt.user_id == current_user["id"]
    ).first()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="作答记录不存在"
        )

    # exam info
    exam = attempt.exam
    exam_info = {
        "id": exam.id if exam else None,
        "title": exam.title if exam else None,
        "category": exam.category if exam else None,
        "duration_minutes": exam.duration_minutes if exam else None
    }

    # gather questions from paper ordered by order_no
    questions = []
    if exam and exam.paper_id:
        # query PaperQuestion model to build list
        from ....models.paper import PaperQuestion
        pqs = db.query(PaperQuestion).filter(PaperQuestion.paper_id == exam.paper_id).order_by(PaperQuestion.order_no).all()

        for pq in pqs:
            q = db.query(Question).filter(Question.id == pq.question_id).first()
            if not q:
                continue
            # find saved answer if any
            ans = db.query(Answer).filter(Answer.attempt_id == attempt_id, Answer.question_id == q.id).first()
            saved = ans.answer_json if ans and ans.answer_json is not None else None

            questions.append({
                "id": q.id,
                "order_no": pq.order_no,
                "question": {
                    "id": q.id,
                    "type": q.type,
                    "stem": q.stem,
                    "options_json": q.options_json
                },
                "saved_answer": saved
            })

    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "started_at": attempt.started_at.isoformat() if attempt.started_at else None,
        "exam": exam_info,
        "questions": questions
    }