"""
AutoOps AI — JWT Authentication
---------------------------------
Users ab database mein hain (SQLite dev / PostgreSQL prod)
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
from api.database import get_db, UserModel, AuditLogModel

# ─── Config ──────────────────────────────────────────────
SECRET_KEY           = "autoops-ai-secret-key-change-in-production"
ALGORITHM            = "HS256"
TOKEN_EXPIRE_MINUTES = 60

# ─── Password Hashing ────────────────────────────────────
pwd_context  = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Schemas ─────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    username:     str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username:  str
    role:      str
    full_name: str


# ─── Helpers ─────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def authenticate_user(username: str, password: str, db: Session):
    user = db.query(UserModel).filter(
        UserModel.username == username,
        UserModel.is_active == True
    ).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire    = datetime.utcnow() + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def log_audit(db: Session, user: str, action: str, detail: str = ""):
    db.add(AuditLogModel(user=user, action=action, detail=detail))
    db.commit()


# ─── Dependency: Current User ─────────────────────────────
async def get_current_user(
    token: str       = Depends(oauth2_scheme),
    db:    Session   = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalid ya expire ho gaya",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(UserModel).filter(UserModel.username == username).first()
    if not user:
        raise credentials_exception
    return User(username=user.username, role=user.role, full_name=user.full_name)


# ─── Role Guards ─────────────────────────────────────────
async def require_manager_or_above(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Manager ya Admin required")
    return current_user

async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Sirf admin yeh kar sakta hai")
    return current_user
