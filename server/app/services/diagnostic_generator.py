from sqlalchemy import select, func
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

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
        max_difficulty: 最大难度等级

    Returns:
        Exam: 生成的诊断考试对象
    """
    # 1. 获取一级知识点
    top_level_kps = _get_top_level_knowledge_points(db)

    if not top_level_kps:
        raise ValueError("没有找到一级知识点，无法生成诊断试卷")

    # 2. 收集题目
    selected_questions = _collect_questions_for_diagnostic(
        db, top_level_kps, per_top_kp, max_difficulty
    )

    if not selected_questions:
        raise ValueError("没有找到符合条件的题目，无法生成诊断试卷")

    # 3. 创建试卷
    paper_title = f"基线诊断试卷 (自动生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})"
    paper = Paper(
        title=paper_title,
        mode="AUTO",
        total_score=float(len(selected_questions) * 2.0),
        created_by=created_by
    )
    db.add(paper)
    db.flush()

    # 4. 添加题目到试卷
    for i, question in enumerate(selected_questions):
        paper_question = PaperQuestion(
            paper_id=paper.id,
            question_id=question.id,
            order_no=i + 1,
            score=2.0
        )
        db.add(paper_question)

    # 5. 创建考试
    exam_title = f"基线诊断考试 (自动生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})"
    exam = Exam(
        paper_id=paper.id,
        title=exam_title,
        category="DIAGNOSTIC",
        duration_minutes=30,
        status="PUBLISHED",
        created_by=created_by
    )
    db.add(exam)

    # 6. 将旧的已发布诊断考试归档
    _archive_existing_diagnostic_exams(db)

    return exam


def _get_top_level_knowledge_points(db: Session) -> List[KnowledgePoint]:
    """
    获取一级知识点
    规则：如果只有一个根节点，则一级=根节点的子节点；否则 parent_id is NULL 的都算一级
    """
    # 检查是否有根节点
    root_stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id.is_(None))
    roots = db.execute(root_stmt).scalars().all()

    if len(roots) == 1:
        # 只有一个根节点，返回其子节点作为一级知识点
        child_stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id == roots[0].id)
        return db.execute(child_stmt).scalars().all()
    else:
        # 多个根节点或无根节点，直接返回所有 parent_id 为 NULL 的节点
        return roots


def _collect_questions_for_diagnostic(
    db: Session,
    top_level_kps: List[KnowledgePoint],
    per_top_kp: int,
    max_difficulty: int
) -> List[Question]:
    """
    为诊断考试收集题目
    每个一级知识点抽取指定数量的题目
    """
    selected_questions = []

    for kp in top_level_kps:
        # 获取该一级知识点及其所有子孙知识点的ID
        kp_ids = _get_knowledge_point_tree_ids(db, kp.id)

        # 从这些知识点关联的题目中选择
        questions = _get_questions_for_knowledge_points(
            db, kp_ids, per_top_kp, max_difficulty
        )

        selected_questions.extend(questions)

    return selected_questions


def _get_knowledge_point_tree_ids(db: Session, root_kp_id: int) -> List[int]:
    """
    获取知识点树的所有节点ID（包括子孙节点）
    """
    # 使用递归CTE获取所有子孙节点
    # 由于SQLite不支持CTE，我们用Python递归实现
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
    limit: int,
    max_difficulty: int
) -> List[Question]:
    """
    从指定的知识点中获取题目
    """
    if not kp_ids:
        return []

    # 通过QuestionKnowledgeMap关联查询题目
    stmt = select(Question).join(
        QuestionKnowledgeMap, Question.id == QuestionKnowledgeMap.question_id
    ).where(
        QuestionKnowledgeMap.knowledge_id.in_(kp_ids),
        Question.difficulty <= max_difficulty
    ).order_by(
        Question.difficulty.asc(),  # 优先选择简单题目
        Question.id.asc()  # 保证顺序稳定
    ).limit(limit).distinct()

    return db.execute(stmt).scalars().all()


def _archive_existing_diagnostic_exams(db: Session):
    """
    将现有的已发布诊断考试归档
    """
    stmt = select(Exam).where(
        Exam.category == "DIAGNOSTIC",
        Exam.status == "PUBLISHED"
    )

    existing_exams = db.execute(stmt).scalars().all()

    for exam in existing_exams:
        exam.status = "ARCHIVED"
        exam.title = f"{exam.title} (已归档 {datetime.now().strftime('%Y-%m-%d %H:%M')})"
