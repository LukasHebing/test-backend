from passlib.context import CryptContext
import uvicorn

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from test_backend.db import User, get_db

app = FastAPI()

class UserCreate(BaseModel):
    email: str
    password: str

@app.get("/test")
def read_root():
    return {"message": "Hello, World!"}


@app.post("/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Validate email and password
    hashed_password = hash_password(user.password)
    # Create user in the database
    new_user = User(email=user.email, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User registered successfully"}

class UserLogin(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # Create and set session here
    return {"message": "Logged in successfully"}


if __name__ == "__main__":
    uvicorn.run("src.test_backend.api:app", host="0.0.0.0", port=8000, reload=True)