from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class PlaidItem(Base):
    __tablename__ = "plaid_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 关联用户表
    access_token = Column(String, nullable=False)
    item_id = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())  # 自动生成时间戳

    def __repr__(self):
        return f"<PlaidItem(id={self.id}, user_id={self.user_id}, item_id={self.item_id})>"
