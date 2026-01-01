from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from pydantic import BaseModel
from math import ceil

from ....core.database import get_db
from ....models.question import Question
from ....models.knowledge import QuestionKnowledgeMap, KnowledgePoint
from ..deps import get_current_admin

router = APIRouter()


class QuestionCreate(BaseModel):
    type: str  # SINGLE, MULTI, JUDGE, FILL, SHORT
    stem: str
    options_json: Optional[List[str]] = None
    answer_json: List[str]
    analysis: Optional[str] = None
    difficulty: int  # 1-5
    knowledge_ids: List[int]


class QuestionUpdate(BaseModel):
    type: Optional[str] = None
    stem: Optional[str] = None
    options_json: Optional[List[str]] = None
    answer_json: Optional[List[str]] = None
    analysis: Optional[str] = None
    difficulty: Optional[int] = None
    knowledge_ids: Optional[List[int]] = None


@router.get("/")
async def get_questions(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    knowledge_id: Optional[int] = None,
    type: Optional[str] = None,
    difficulty: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取题目列表"""
    try:
        query = db.query(Question)

        # 应用过滤条件
        if knowledge_id:
            # 查找与指定知识点关联的题目
            subquery = db.query(QuestionKnowledgeMap.question_id).filter(
                QuestionKnowledgeMap.knowledge_id == knowledge_id
            )
            query = query.filter(Question.id.in_(subquery))

        if type:
            query = query.filter(Question.type == type)

        if difficulty:
            query = query.filter(Question.difficulty == difficulty)

        if search:
            query = query.filter(
                or_(
                    Question.stem.contains(search),
                    Question.analysis.contains(search)
                )
            )

        # 分页
        total = query.count()
        questions = query.offset((page - 1) * size).limit(size).all()

        # 为每个题目添加知识点信息
        result = []
        for question in questions:
            knowledge_points = []
            for kp_map in question.knowledge_points:
                knowledge_points.append({
                    "id": kp_map.knowledge_point.id,
                    "name": kp_map.knowledge_point.name
                })

            result.append({
                "id": question.id,
                "type": question.type,
                "stem": question.stem,
                "options_json": question.options_json,
                "answer_json": question.answer_json,
                "analysis": question.analysis,
                "difficulty": question.difficulty,
                "knowledge_points": knowledge_points,
                "created_at": question.created_at
            })

        return {
            "items": result,
            "total": total,
            "page": page,
            "size": size,
            "pages": ceil(total / size) if total > 0 else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取题目列表失败: {str(e)}"
        )


@router.post("/")
async def create_question(
    request: QuestionCreate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建题目 (管理员权限)"""
    try:
        # 验证知识点ID
        for knowledge_id in request.knowledge_ids:
            knowledge_point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_id).first()
            if not knowledge_point:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"知识点ID {knowledge_id} 不存在"
                )

        # 创建题目
        question = Question(
            type=request.type,
            stem=request.stem,
            options_json=request.options_json,
            answer_json=request.answer_json,
            analysis=request.analysis,
            difficulty=request.difficulty
        )

        db.add(question)
        db.flush()  # 获取question.id

        # 创建题目-知识点映射
        for knowledge_id in request.knowledge_ids:
            mapping = QuestionKnowledgeMap(
                question_id=question.id,
                knowledge_id=knowledge_id
            )
            db.add(mapping)

        db.commit()
        db.refresh(question)

        return {
            "id": question.id,
            "message": "题目创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建题目失败: {str(e)}"
        )


@router.put("/{question_id}")
async def update_question(
    question_id: int,
    request: QuestionUpdate,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新题目 (管理员权限)"""
    try:
        # 查找题目
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )

        # 验证知识点ID
        if request.knowledge_ids is not None:
            for knowledge_id in request.knowledge_ids:
                knowledge_point = db.query(KnowledgePoint).filter(KnowledgePoint.id == knowledge_id).first()
                if not knowledge_point:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"知识点ID {knowledge_id} 不存在"
                    )

        # 更新题目字段
        update_data = request.dict(exclude_unset=True, exclude={"knowledge_ids"})
        for field, value in update_data.items():
            if hasattr(question, field):
                setattr(question, field, value)

        # 更新知识点映射
        if request.knowledge_ids is not None:
            # 删除原有映射
            db.query(QuestionKnowledgeMap).filter(
                QuestionKnowledgeMap.question_id == question_id
            ).delete()

            # 创建新映射
            for knowledge_id in request.knowledge_ids:
                mapping = QuestionKnowledgeMap(
                    question_id=question_id,
                    knowledge_id=knowledge_id
                )
                db.add(mapping)

        db.commit()
        db.refresh(question)

        return {
            "id": question.id,
            "message": "题目更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新题目失败: {str(e)}"
        )


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    current_user: dict = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除题目 (管理员权限)"""
    try:
        # 查找题目
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="题目不存在"
            )

        # 删除题目-知识点映射
        db.query(QuestionKnowledgeMap).filter(
            QuestionKnowledgeMap.question_id == question_id
        ).delete()

        # 删除题目
        db.delete(question)
        db.commit()

        return {"message": "题目删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除题目失败: {str(e)}"
        )
