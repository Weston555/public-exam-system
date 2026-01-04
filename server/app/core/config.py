from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用配置
    app_name: str = "公考进阶系统"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "public_exam_system.db"
    db_user: str = "root"
    db_password: str = "123456"

    # JWT 配置
    jwt_secret: str = "your-super-secret-jwt-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS 配置
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 文件上传配置
    upload_dir: str = "uploads"
    max_upload_size: int = 10485760  # 10MB

    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    # 管理员默认账号
    admin_username: str = "admin"
    admin_password: str = "admin123"

    # 学习计划配置
    default_plan_days: int = 14
    default_daily_minutes: int = 120
    review_intervals: List[int] = [1, 3, 7, 14, 30]  # 错题复习间隔(天)

    # 推荐算法配置
    mastery_weight: float = 0.7
    difficulty_weight: float = 0.3
    min_practice_questions: int = 10
    max_practice_questions: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        """数据库连接URL"""
        if self.db_name.endswith('.db'):
            # SQLite数据库
            return f"sqlite:///./{self.db_name}"
        else:
            # MySQL数据库
            return f"mysql+mysqlconnector://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def database_url_async(self) -> str:
        """异步数据库连接URL"""
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


# 创建全局配置实例
settings = Settings()
