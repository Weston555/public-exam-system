import random
import json
from typing import List, Dict, Any
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..models.paper import Exam, Paper, PaperQuestion
from ..models.knowledge import KnowledgePoint, QuestionKnowledgeMap
from ..models.question import Question


def generate_diagnostic_exam(
    db: Session,
    created_by: int,
    per_top_kp: int = 2,
    max_difficulty: int = 2
) -> Exam:
    """
    生成基线诊断考试

    Args:
        db: 数据库会话
        created_by: 创建者用户ID
        per_top_kp: 每个一级知识点抽取的题目数量
        max_difficulty: 最大难度等级（1-5）

    Returns:
        Exam: 生成的诊断考试对象
    """
    # 1. 获取一级知识点
    top_level_kps = _get_top_level_knowledge_points(db)

    if not top_level_kps:
        raise ValueError("没有找到一级知识点，无法生成诊断试卷")

    # 2. 为每个一级知识点收集题目，避免重复
    selected_questions = []
    selected_question_ids = set()  # 记录已选题目ID，避免重复
    duplicates_removed = 0  # 记录去重移除的题目数量
    kp_stats = []  # 记录每个知识点的抽题统计

    for kp in top_level_kps:
        # 获取该知识点树的所有ID
        kp_ids = _get_knowledge_point_tree_ids(db, kp.id)

        # 获取相关题目
        questions = _get_questions_for_knowledge_points(db, kp_ids, max_difficulty)

        # 过滤掉已被其他知识点选中的题目
        available_questions = [q for q in questions if q.id not in selected_question_ids]
        filtered_count = len(questions) - len(available_questions)
        duplicates_removed += filtered_count

        # 随机抽取指定数量的题目
        selected = _random_sample_questions(available_questions, per_top_kp)

        # 记录选中的题目ID
        selected_ids_for_kp = []
        for q in selected:
            selected_question_ids.add(q.id)
            selected_ids_for_kp.append(q.id)

        selected_questions.extend(selected)

        # 记录统计信息
        kp_stats.append({
            "knowledge_point_id": kp.id,
            "knowledge_point_name": kp.name,
            "total_available": len(questions),
            "filtered_duplicates": filtered_count,
            "available_after_filter": len(available_questions),
            "selected_count": len(selected),
            "selected_question_ids": selected_ids_for_kp
        })

    if not selected_questions:
        raise ValueError("没有找到符合条件的题目，无法生成诊断试卷")

    # 3. 创建试卷
    paper_config = {
        "type": "diagnostic",
        "generation_rule": "按一级知识点随机抽题，避免重复",
        "per_top_kp": per_top_kp,
        "max_difficulty": max_difficulty,
        "top_level_kp_count": len(top_level_kps),
        "knowledge_points": kp_stats,
        "total_questions": len(selected_questions),
        "unique_questions": len(selected_questions),  # 去重后的题目数量
        "duplicates_removed": duplicates_removed,  # 本次去重移除的数量
        "total_score": len(selected_questions) * 2.0,
        "generated_at": datetime.now().isoformat(),
        "algorithm_description": "智能诊断试卷生成：基于知识点树结构，按一级知识点分类抽题，确保知识点覆盖全面且题目不重复"
    }

    paper = Paper(
        title=f"基线诊断试卷 (智能生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        mode="AUTO",
        config_json=paper_config,
        total_score=float(len(selected_questions) * 2.0),
        created_by=created_by
    )
    db.add(paper)
    db.flush()

    # 4. 添加题目到试卷（按顺序）
    for i, question in enumerate(selected_questions):
        paper_question = PaperQuestion(
            paper_id=paper.id,
            question_id=question.id,
            order_no=i + 1,
            score=2.0
        )
        db.add(paper_question)

    # 5. 创建考试
    exam = Exam(
        paper_id=paper.id,
        title=f"基线诊断考试 (智能生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        category="DIAGNOSTIC",
        duration_minutes=30,
        status="PUBLISHED",
        created_by=created_by
    )
    db.add(exam)

    # 6. 归档旧的诊断考试
    _archive_existing_diagnostic_exams(db)

    return exam


def _get_top_level_knowledge_points(db: Session) -> List[KnowledgePoint]:
    """
    获取一级知识点
    规则：如果只有一个根节点且有子节点，则一级知识点是子节点，否则就是根节点
    """
    # 获取所有根节点
    stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id.is_(None))
    roots = db.execute(stmt).scalars().all()

    if len(roots) == 1:
        # 检查这个根节点是否有子节点
        child_stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id == roots[0].id)
        children = db.execute(child_stmt).scalars().all()

        if children:
            # 如果有子节点，返回子节点作为一级知识点
            return children

    # 否则返回根节点作为一级知识点
    return roots


def _get_knowledge_point_tree_ids(db: Session, root_kp_id: int) -> List[int]:
    """
    获取知识点树的所有节点ID（包括子孙节点）
    使用递归方式在内存中构建树
    """
    ids = []
    _collect_child_ids(db, root_kp_id, ids)
    return ids


def _collect_child_ids(db: Session, parent_id: int, ids: List[int]):
    """递归收集子节点ID"""
    ids.append(parent_id)

    child_stmt = select(KnowledgePoint.id).where(KnowledgePoint.parent_id == parent_id)
    children = db.execute(child_stmt).scalars().all()

    for child_id in children:
        _collect_child_ids(db, child_id, ids)


def _get_questions_for_knowledge_points(
    db: Session,
    kp_ids: List[int],
    max_difficulty: int
) -> List[Question]:
    """
    获取指定知识点相关的所有题目
    """
    if not kp_ids:
        return []

    # 注意：这里使用随机排序来实现随机抽题
    # 在 SQLAlchemy 2.0 中，我们不能直接使用 func.random()
    # 所以在应用层进行随机排序
    stmt = select(Question).join(
        QuestionKnowledgeMap, Question.id == QuestionKnowledgeMap.question_id
    ).where(
        QuestionKnowledgeMap.knowledge_id.in_(kp_ids),
        Question.difficulty <= max_difficulty
    ).distinct()

    questions = db.execute(stmt).scalars().all()
    # 在应用层随机排序
    random.shuffle(questions)
    return questions


def _random_sample_questions(questions: List[Question], count: int) -> List[Question]:
    """
    从题目列表中随机抽取指定数量的题目
    """
    if len(questions) <= count:
        return questions

    return random.sample(questions, count)


def _archive_existing_diagnostic_exams(db: Session):
    """
    将现有的已发布诊断考试归档
    """
    stmt = update(Exam).where(
        Exam.category == "DIAGNOSTIC",
        Exam.status == "PUBLISHED"
    ).values(status="ARCHIVED")

    db.execute(stmt)