"""
公考模板化组卷服务
提供结构化的组卷算法，确保诊断试卷和模拟试卷按模块配比抽题
"""

from sqlalchemy import select, func, update
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
import random

from ..models.paper import Exam, Paper, PaperQuestion
from ..models.knowledge import KnowledgePoint, QuestionKnowledgeMap
from ..models.question import Question


def build_diagnostic_paper(
    db: Session,
    subject: str = "XINGCE",
    per_module: int = 2,
    created_by: int = 1
) -> Tuple[Paper, Exam]:
    """
    构建诊断试卷：从指定科目（如行测）的各模块节点下按配比抽题

    Args:
        db: 数据库会话
        subject: 科目类型 ("XINGCE" 或 "SHENLUN")
        per_module: 每个模块至少抽取的题目数量
        created_by: 创建者用户ID

    Returns:
        Tuple[Paper, Exam]: 创建的试卷和考试对象

    Raises:
        ValueError: 当题库不足时抛出异常

    抽题策略：
    1. 优先从模块节点（非叶子节点）下抽题
    2. SINGLE/MULTI/JUDGE优先，难度1-3
    3. 如果模块题目不足，扩大到模块的子节点
    4. 如果仍不足，扩大难度范围到1-4
    5. 记录每模块的抽题情况到config_json
    """
    # 获取指定科目的模块节点
    module_nodes = _get_subject_module_nodes(db, subject)
    if not module_nodes:
        raise ValueError(f"未找到{subject}科目的模块节点")

    selected_questions = []
    selected_question_ids = set()
    module_stats = []

    for module in module_nodes:
        module_questions = []
        actual_strategy = ""

        # 从模块节点直接抽题（包括子树中的所有题目）
        kp_tree_ids = _get_knowledge_point_tree_ids(db, module.id)
        questions = _get_questions_by_knowledge_points(
            db, kp_tree_ids, question_types=['SINGLE', 'MULTI', 'JUDGE'], max_difficulty=3
        )

        if len(questions) >= per_module:
            # 模块题目充足
            available_questions = [q for q in questions if q.id not in selected_question_ids]
            selected = _random_sample_questions(available_questions, per_module)
            actual_strategy = "模块直接抽题"
        else:
            # 策略2：扩大难度范围
            questions = _get_questions_by_knowledge_points(
                db, kp_tree_ids, question_types=['SINGLE', 'MULTI', 'JUDGE'], max_difficulty=4
            )
            available_questions = [q for q in questions if q.id not in selected_question_ids]
            selected = _random_sample_questions(available_questions, per_module)
            actual_strategy = "扩大难度范围"

        # 如果还是不够，取所有可用题目
        if len(selected) < per_module:
            all_available = [q for q in questions if q.id not in selected_question_ids]
            selected = _random_sample_questions(all_available, min(per_module, len(all_available)))
            actual_strategy += " (题目不足)"

        # 记录选中的题目
        selected_ids = []
        for q in selected:
            selected_question_ids.add(q.id)
            selected_ids.append(q.id)
            selected_questions.append(q)

        # 统计信息
        module_stats.append({
            "module_id": module.id,
            "module_name": module.name,
            "module_code": module.code,
            "target_count": per_module,
            "actual_count": len(selected),
            "strategy": actual_strategy,
            "question_ids": selected_ids,
            "available_questions": len([q for q in questions if q.id not in selected_question_ids])
        })

    if not selected_questions:
        raise ValueError("题库题目不足，无法生成诊断试卷")

    # 创建试卷配置
    paper_config = {
        "type": "diagnostic",
        "subject": subject,
        "generation_rule": "按模块配比抽题，智能降级策略",
        "per_module": per_module,
        "module_count": len(module_nodes),
        "modules": module_stats,
        "total_questions": len(selected_questions),
        "total_score": len(selected_questions) * 2.0,
        "generated_at": datetime.now().isoformat(),
        "algorithm_description": f"诊断试卷生成：基于{subject}各模块配比抽题，优先保证模块覆盖，智能降级确保题目充足"
    }

    # 创建试卷
    paper = Paper(
        title=f"{subject}基线诊断试卷 (模板化生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        mode="AUTO",
        config_json=paper_config,
        total_score=float(len(selected_questions) * 2.0),
        created_by=created_by
    )
    db.add(paper)
    db.flush()

    # 添加题目到试卷
    for i, question in enumerate(selected_questions):
        paper_question = PaperQuestion(
            paper_id=paper.id,
            question_id=question.id,
            order_no=i + 1,
            score=2.0
        )
        db.add(paper_question)

    # 创建考试
    exam = Exam(
        paper_id=paper.id,
        title=f"{subject}基线诊断考试 (模板化生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        category="DIAGNOSTIC",
        duration_minutes=30,
        status="PUBLISHED",
        created_by=created_by
    )
    db.add(exam)

    # 归档旧的诊断考试
    _archive_existing_exams(db, "DIAGNOSTIC")

    db.commit()
    return paper, exam


def build_mock_paper(
    db: Session,
    subject: str = "XINGCE",
    total: int = 20,
    ratio: Optional[Dict[str, int]] = None,
    created_by: int = 1
) -> Tuple[Paper, Exam]:
    """
    构建模拟试卷：严格按指定比例从各模块抽题

    Args:
        db: 数据库会话
        subject: 科目类型 ("XINGCE" 或 "SHENLUN")
        total: 总题目数量
        ratio: 各模块抽题比例，如 {"YY":4, "SL":4, "PD":4, "ZL":4, "CS":4}
               如果为None，则平均分配
        created_by: 创建者用户ID

    Returns:
        Tuple[Paper, Exam]: 创建的试卷和考试对象

    Raises:
        ValueError: 当题库不足时抛出异常

    抽题策略：
    1. 严格按ratio分配各模块题目数量
    2. 从模块子节点（叶子节点）抽题，保证精细化
    3. 如果某模块题目不足，用其他模块补齐，并记录warnings
    """
    # 获取指定科目的模块节点
    module_nodes = _get_subject_module_nodes(db, subject)
    if not module_nodes:
        raise ValueError(f"未找到{subject}科目的模块节点")

    # 计算各模块应分配的题目数量
    if ratio is None:
        # 默认平均分配
        base_count = total // len(module_nodes)
        remainder = total % len(module_nodes)
        module_counts = {module.code: base_count for module in module_nodes}
        # 余数分配给前几个模块
        for i in range(remainder):
            module_counts[module_nodes[i].code] += 1
    else:
        # 使用指定的ratio
        total_ratio = sum(ratio.values())
        module_counts = {}
        for module in module_nodes:
            if module.code in ratio:
                module_counts[module.code] = ratio[module.code]
            else:
                module_counts[module.code] = 0

    selected_questions = []
    selected_question_ids = set()
    module_stats = []
    warnings = []

    for module in module_nodes:
        target_count = module_counts.get(module.code, 0)
        if target_count == 0:
            continue

        # 从模块的叶子节点抽题
        leaf_nodes = _get_module_leaf_nodes(db, module.id)
        if not leaf_nodes:
            warnings.append(f"模块 {module.name} 没有叶子节点")
            continue

        leaf_kp_ids = [node.id for node in leaf_nodes]
        questions = _get_questions_by_knowledge_points(
            db, leaf_kp_ids, question_types=['SINGLE', 'MULTI', 'JUDGE'], max_difficulty=4
        )

        available_questions = [q for q in questions if q.id not in selected_question_ids]
        actual_selected = _random_sample_questions(available_questions, target_count)

        # 如果题目不足，记录警告
        if len(actual_selected) < target_count:
            warnings.append(
                f"模块 {module.name} 题目不足：需要{target_count}道，实际{len(actual_selected)}道"
            )

        # 记录选中的题目
        selected_ids = []
        for q in actual_selected:
            selected_question_ids.add(q.id)
            selected_ids.append(q.id)
            selected_questions.append(q)

        module_stats.append({
            "module_id": module.id,
            "module_name": module.name,
            "module_code": module.code,
            "target_count": target_count,
            "actual_count": len(actual_selected),
            "available_questions": len(available_questions),
            "question_ids": selected_ids
        })

    # 如果总题目数不足，用其他题目补齐
    total_selected = len(selected_questions)
    if total_selected < total:
        shortfall = total - total_selected
        warnings.append(f"总题目不足：需要{total}道，实际{total_selected}道，缺口{shortfall}道")

        # 从所有可用题目中补齐
        all_questions = _get_questions_by_knowledge_points(
            db, None, question_types=['SINGLE', 'MULTI', 'JUDGE'], max_difficulty=4
        )
        available_supplement = [q for q in all_questions if q.id not in selected_question_ids]

        supplement_selected = _random_sample_questions(available_supplement, shortfall)
        selected_questions.extend(supplement_selected)

        # 记录补齐信息
        supplement_ids = [q.id for q in supplement_selected]
        module_stats.append({
            "module_name": "补充题目",
            "module_code": "SUPPLEMENT",
            "target_count": shortfall,
            "actual_count": len(supplement_selected),
            "question_ids": supplement_ids,
            "note": "从题库其他题目中补齐"
        })

    # 创建试卷配置
    final_total = len(selected_questions)
    paper_config = {
        "type": "mock",
        "subject": subject,
        "generation_rule": "按模块比例严格配比抽题",
        "total_target": total,
        "total_actual": final_total,
        "ratio": ratio,
        "modules": module_stats,
        "warnings": warnings,
        "total_score": final_total * 2.0,
        "generated_at": datetime.now().isoformat(),
        "algorithm_description": f"模拟试卷生成：基于{subject}各模块严格比例配比，确保知识点分布均衡"
    }

    # 创建试卷
    paper = Paper(
        title=f"{subject}模拟考试 (模板化生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        mode="AUTO",
        config_json=paper_config,
        total_score=float(final_total * 2.0),
        created_by=created_by
    )
    db.add(paper)
    db.flush()

    # 添加题目到试卷
    for i, question in enumerate(selected_questions):
        paper_question = PaperQuestion(
            paper_id=paper.id,
            question_id=question.id,
            order_no=i + 1,
            score=2.0
        )
        db.add(paper_question)

    # 创建考试
    exam = Exam(
        paper_id=paper.id,
        title=f"{subject}模拟考试 (模板化生成 {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        category="MOCK",
        duration_minutes=60,
        status="PUBLISHED",
        created_by=created_by
    )
    db.add(exam)

    db.commit()
    return paper, exam


def _get_subject_module_nodes(db: Session, subject: str) -> List[KnowledgePoint]:
    """获取指定科目的模块节点"""
    # 根据subject找到对应的分类节点
    if subject == "XINGCE":
        category_code = "XINGCE"
    elif subject == "SHENLUN":
        category_code = "SHENLUN"
    else:
        return []

    # 获取分类节点
    stmt = select(KnowledgePoint).where(KnowledgePoint.code == category_code)
    category_node = db.execute(stmt).scalar_one_or_none()
    if not category_node:
        return []

    # 获取该分类下的所有直接子节点（模块）
    stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id == category_node.id)
    return db.execute(stmt).scalars().all()


def _get_module_leaf_nodes(db: Session, module_id: int) -> List[KnowledgePoint]:
    """获取模块下的所有叶子节点（最底层的知识点）"""
    all_nodes = []
    _collect_module_nodes(db, module_id, all_nodes)

    # 过滤出叶子节点（没有子节点的节点）
    leaf_nodes = []
    for node in all_nodes:
        stmt = select(func.count()).select_from(KnowledgePoint).where(KnowledgePoint.parent_id == node.id)
        child_count = db.execute(stmt).scalar()
        if child_count == 0:
            leaf_nodes.append(node)

    return leaf_nodes


def _collect_module_nodes(db: Session, parent_id: int, nodes: List[KnowledgePoint]):
    """递归收集模块下的所有节点"""
    stmt = select(KnowledgePoint).where(KnowledgePoint.parent_id == parent_id)
    children = db.execute(stmt).scalars().all()

    for child in children:
        nodes.append(child)
        _collect_module_nodes(db, child.id, nodes)


def _get_knowledge_point_tree_ids(db: Session, root_kp_id: int) -> List[int]:
    """获取知识点树的所有节点ID（包括子孙节点）"""
    ids = []
    _collect_child_ids(db, root_kp_id, ids)
    return ids


def _collect_child_ids(db: Session, parent_id: int, ids: List[int]):
    """递归收集子节点ID"""
    ids.append(parent_id)
    stmt = select(KnowledgePoint.id).where(KnowledgePoint.parent_id == parent_id)
    children = db.execute(stmt).scalars().all()

    for child_id in children:
        _collect_child_ids(db, child_id, ids)


def _get_questions_by_knowledge_points(
    db: Session,
    kp_ids: Optional[List[int]],
    question_types: List[str],
    max_difficulty: int
) -> List[Question]:
    """获取指定知识点相关的题目"""
    if kp_ids is None:
        # 获取所有题目的情况
        stmt = select(Question).where(
            Question.type.in_(question_types),
            Question.difficulty <= max_difficulty
        )
    else:
        if not kp_ids:
            return []

        stmt = select(Question).join(
            QuestionKnowledgeMap, Question.id == QuestionKnowledgeMap.question_id
        ).where(
            QuestionKnowledgeMap.knowledge_id.in_(kp_ids),
            Question.type.in_(question_types),
            Question.difficulty <= max_difficulty
        ).distinct()

    questions = db.execute(stmt).scalars().all()
    # 在应用层随机排序
    random.shuffle(questions)
    return questions


def _random_sample_questions(questions: List[Question], count: int) -> List[Question]:
    """从题目列表中随机抽取指定数量的题目"""
    if len(questions) <= count:
        return questions
    return random.sample(questions, count)


def _archive_existing_exams(db: Session, category: str):
    """将现有的已发布考试归档"""
    stmt = update(Exam).where(
        Exam.category == category,
        Exam.status == "PUBLISHED"
    ).values(status="ARCHIVED")

    db.execute(stmt)
