# Initial migration - create all tables

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('STUDENT', 'ADMIN', name='user_role'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create knowledge_points table
    op.create_table('knowledge_points',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=True),
        sa.Column('weight', sa.DECIMAL(precision=3, scale=2), nullable=False),
        sa.Column('estimated_minutes', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['knowledge_points.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_knowledge_points_id'), 'knowledge_points', ['id'], unique=False)
    op.create_index(op.f('ix_knowledge_points_parent_id'), 'knowledge_points', ['parent_id'], unique=False)
    op.create_index(op.f('ix_knowledge_points_weight'), 'knowledge_points', ['weight'], unique=False)

    # Create questions table
    op.create_table('questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('type', sa.Enum('SINGLE', 'MULTI', 'JUDGE', 'FILL', 'SHORT', name='question_type'), nullable=False),
        sa.Column('stem', sa.Text(), nullable=False),
        sa.Column('options_json', sa.JSON(), nullable=True),
        sa.Column('answer_json', sa.JSON(), nullable=False),
        sa.Column('analysis', sa.Text(), nullable=True),
        sa.Column('difficulty', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_questions_id'), 'questions', ['id'], unique=False)
    op.create_index(op.f('ix_questions_type'), 'questions', ['type'], unique=False)
    op.create_index(op.f('ix_questions_difficulty'), 'questions', ['difficulty'], unique=False)
    op.create_index(op.f('ix_questions_created_at'), 'questions', ['created_at'], unique=False)

    # Create question_knowledge_map table
    op.create_table('question_knowledge_map',
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['knowledge_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('question_id', 'knowledge_id')
    )

    # Create papers table
    op.create_table('papers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('mode', sa.Enum('MANUAL', 'AUTO', name='paper_mode'), nullable=False),
        sa.Column('config_json', sa.JSON(), nullable=True),
        sa.Column('total_score', sa.DECIMAL(precision=5, scale=1), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_papers_id'), 'papers', ['id'], unique=False)
    op.create_index(op.f('ix_papers_created_by'), 'papers', ['created_by'], unique=False)
    op.create_index(op.f('ix_papers_created_at'), 'papers', ['created_at'], unique=False)

    # Create paper_questions table
    op.create_table('paper_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('order_no', sa.Integer(), nullable=False),
        sa.Column('score', sa.DECIMAL(precision=4, scale=1), nullable=False),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paper_id', 'order_no')
    )
    op.create_index(op.f('ix_paper_questions_id'), 'paper_questions', ['id'], unique=False)

    # Create exams table
    op.create_table('exams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('paper_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('category', sa.Enum('DIAGNOSTIC', 'PRACTICE', 'MOCK', name='exam_category'), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'PUBLISHED', 'ARCHIVED', name='exam_status'), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['paper_id'], ['papers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exams_id'), 'exams', ['id'], unique=False)
    op.create_index(op.f('ix_exams_category'), 'exams', ['category'], unique=False)
    op.create_index(op.f('ix_exams_created_by'), 'exams', ['created_by'], unique=False)

    # Create attempts table
    op.create_table('attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('exam_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('total_score', sa.DECIMAL(precision=5, scale=1), nullable=True),
        sa.Column('status', sa.Enum('DOING', 'SUBMITTED', name='attempt_status'), nullable=False),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_attempts_id'), 'attempts', ['id'], unique=False)
    op.create_index(op.f('ix_attempts_exam_id'), 'attempts', ['exam_id'], unique=False)
    op.create_index(op.f('ix_attempts_user_id'), 'attempts', ['user_id'], unique=False)
    op.create_index(op.f('ix_attempts_started_at'), 'attempts', ['started_at'], unique=False)

    # Create answers table
    op.create_table('answers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('attempt_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('answer_json', sa.JSON(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('score_awarded', sa.DECIMAL(precision=4, scale=1), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['attempt_id'], ['attempts.id'], ),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_answers_id'), 'answers', ['id'], unique=False)
    op.create_index(op.f('ix_answers_attempt_id'), 'answers', ['attempt_id'], unique=False)

    # Create wrong_questions table
    op.create_table('wrong_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('wrong_count', sa.Integer(), nullable=False),
        sa.Column('last_wrong_at', sa.DateTime(), nullable=False),
        sa.Column('next_review_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'question_id')
    )
    op.create_index(op.f('ix_wrong_questions_id'), 'wrong_questions', ['id'], unique=False)
    op.create_index(op.f('ix_wrong_questions_user_id'), 'wrong_questions', ['user_id'], unique=False)
    op.create_index(op.f('ix_wrong_questions_next_review_at'), 'wrong_questions', ['next_review_at'], unique=False)

    # Create user_knowledge_state table
    op.create_table('user_knowledge_state',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('knowledge_id', sa.Integer(), nullable=False),
        sa.Column('mastery', sa.DECIMAL(precision=3, scale=2), nullable=False),
        sa.Column('ability', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'knowledge_id')
    )
    op.create_index(op.f('ix_user_knowledge_state_id'), 'user_knowledge_state', ['id'], unique=False)
    op.create_index(op.f('ix_user_knowledge_state_user_id'), 'user_knowledge_state', ['user_id'], unique=False)

    # Create goals table
    op.create_table('goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('target_score', sa.DECIMAL(precision=5, scale=1), nullable=True),
        sa.Column('daily_minutes', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goals_id'), 'goals', ['id'], unique=False)
    op.create_index(op.f('ix_goals_user_id'), 'goals', ['user_id'], unique=False)
    op.create_index(op.f('ix_goals_exam_date'), 'goals', ['exam_date'], unique=False)

    # Create learning_plans table
    op.create_table('learning_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('strategy_version', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goals.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_learning_plans_id'), 'learning_plans', ['id'], unique=False)
    op.create_index(op.f('ix_learning_plans_user_id'), 'learning_plans', ['user_id'], unique=False)

    # Create plan_items table
    op.create_table('plan_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('type', sa.Enum('LEARN', 'PRACTICE', 'REVIEW', 'MOCK', name='plan_item_type'), nullable=False),
        sa.Column('knowledge_id', sa.Integer(), nullable=True),
        sa.Column('resource_url', sa.String(length=500), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('exam_id', sa.Integer(), nullable=True),
        sa.Column('practice_config_json', sa.JSON(), nullable=True),
        sa.Column('expected_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('TODO', 'DONE', 'SKIPPED', name='plan_item_status'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('reason_json', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ),
        sa.ForeignKeyConstraint(['knowledge_id'], ['knowledge_points.id'], ),
        sa.ForeignKeyConstraint(['plan_id'], ['learning_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_plan_items_id'), 'plan_items', ['id'], unique=False)
    op.create_index(op.f('ix_plan_items_plan_id'), 'plan_items', ['plan_id'], unique=False)
    op.create_index(op.f('ix_plan_items_date'), 'plan_items', ['date'], unique=False)
    op.create_index(op.f('ix_plan_items_type'), 'plan_items', ['type'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('plan_items')
    op.drop_table('learning_plans')
    op.drop_table('goals')
    op.drop_table('user_knowledge_state')
    op.drop_table('wrong_questions')
    op.drop_table('answers')
    op.drop_table('attempts')
    op.drop_table('exams')
    op.drop_table('paper_questions')
    op.drop_table('papers')
    op.drop_table('question_knowledge_map')
    op.drop_table('questions')
    op.drop_table('knowledge_points')
    op.drop_table('users')
