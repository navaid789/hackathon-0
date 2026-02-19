"""
AutoOps AI — Database Layer
-----------------------------
Development: SQLite (autoops.db)
Production:  PostgreSQL (DATABASE_URL env variable set karo)

PostgreSQL URL format:
    postgresql://user:password@localhost:5432/autoops_ai
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# ─── Database URL ─────────────────────────────────────────
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./autoops.db"   # Dev: SQLite | Prod: PostgreSQL URL
)

# PostgreSQL ke liye check
IS_POSTGRES = DATABASE_URL.startswith("postgresql")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if not IS_POSTGRES else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ──────────────────────────────────────────────

class UserModel(Base):
    """Users table — auth ke liye."""
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role          = Column(String(20), default="viewer")
    full_name     = Column(String(100))
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)


class TaskModel(Base):
    """Tasks table — workflow tracking ke liye."""
    __tablename__ = "tasks"

    id          = Column(Integer, primary_key=True, index=True)
    filename    = Column(String(255), nullable=False)
    content     = Column(Text)
    status      = Column(String(50), default="needs_action")
    priority    = Column(String(20), default="Low")
    client      = Column(String(255), default="Unknown")
    assigned_to = Column(String(50), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailLogModel(Base):
    """Email logs — saare sent/received emails ka record."""
    __tablename__ = "email_logs"

    id          = Column(Integer, primary_key=True, index=True)
    filename    = Column(String(255))
    to_email    = Column(String(255))
    subject     = Column(String(500))
    status      = Column(String(50))    # sent / rejected / pending
    action_by   = Column(String(50))    # approved_by / rejected_by
    created_at  = Column(DateTime, default=datetime.utcnow)


class AuditLogModel(Base):
    """Audit trail — kaun ne kya kiya."""
    __tablename__ = "audit_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user       = Column(String(50))
    action     = Column(String(100))   # login / approve / reject / logout
    detail     = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── DB Init ─────────────────────────────────────────────

def init_db():
    """Tables banao + default users add karo."""
    Base.metadata.create_all(bind=engine)
    _seed_users()


def _seed_users():
    """Default users insert karo agar exist nahi karte."""
    from passlib.context import CryptContext
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    db  = SessionLocal()
    try:
        defaults = [
            {"username": "admin",   "hashed_password": pwd.hash("admin123"),   "role": "admin",   "full_name": "Admin User"},
            {"username": "manager", "hashed_password": pwd.hash("manager123"), "role": "manager", "full_name": "Manager User"},
            {"username": "viewer",  "hashed_password": pwd.hash("viewer123"),  "role": "viewer",  "full_name": "Viewer User"},
        ]
        for u in defaults:
            exists = db.query(UserModel).filter(UserModel.username == u["username"]).first()
            if not exists:
                db.add(UserModel(**u))
        db.commit()
    finally:
        db.close()


def get_db():
    """FastAPI dependency — DB session provide karo."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
