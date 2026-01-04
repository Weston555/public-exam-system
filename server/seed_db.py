#!/usr/bin/env python3
"""
数据库初始化脚本
运行方式: python seed_db.py
"""
import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.core.security import get_password_hash
from app.models.user import User

def seed_database():
    """初始化数据库数据"""
    print("🚀 开始初始化数据库...")

    # 创建表
    print("📋 创建数据库表...")
    create_tables()
    print("✅ 数据库表创建完成")

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
        else:
            print("ℹ️ 管理员用户已存在")

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
            else:
                print(f"ℹ️ 测试学员 {username} 已存在")

        db.commit()
        print("🎉 数据库初始化完成！")

    except Exception as e:
        db.rollback()
        print(f"❌ 初始化失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
