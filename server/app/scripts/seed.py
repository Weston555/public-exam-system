import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from ..core.database import SessionLocal, create_tables
from ..core.security import get_password_hash
from ..models.user import User

def seed_database():
    """初始化数据库数据"""
    # 创建表
    create_tables()

    db = SessionLocal()
    try:
        # 创建管理员用户
        admin_username = "admin"
        admin_exists = db.query(User).filter(User.username == admin_username).first()
        if not admin_exists:
            admin = User(
                username=admin_username,
                password_hash=get_password_hash("admin123"),
                role="ADMIN",
                is_active=True
            )
            db.add(admin)
            print("✅ 创建管理员用户: admin/admin123")

        # 创建测试学员用户
        test_users = [
            ("student01", "123456"),
            ("student02", "123456")
        ]

        for username, password in test_users:
            user_exists = db.query(User).filter(User.username == username).first()
            if not user_exists:
                user = User(
                    username=username,
                    password_hash=get_password_hash(password),
                    role="STUDENT",
                    is_active=True
                )
                db.add(user)
                print(f"✅ 创建测试学员: {username}/{password}")

        db.commit()
        print("🎉 数据库初始化完成！")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
