import uuid
from datetime import datetime, timedelta

from passlib.context import CryptContext
import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware

from test_backend.db import User, get_db, UserSession

#%% Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


app = FastAPI()

#%% middleware

class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("MIDDLEWARE: entered dispatch DBSessionMiddleware")
        db = next(get_db())
        request.state.db = db
        try:
            response = await call_next(request)
        finally:
            db.close()
        return response

class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print("MIDDLEWARE: entered dispatch SessionMiddleware")
        # Extract the session_id from cookies
        session_id = request.cookies.get("session_id")

        # Check if session_id is present and valid
        if session_id:
            # Here you would typically look up the session in your database
            db: Session = request.state.db
            session = db.query(UserSession).filter(
                UserSession.session_id == session_id,
                datetime.now() < UserSession.expires_at).first()

            if session is None or session.revoked_at is not None:
                raise HTTPException(status_code=401, detail="Invalid session")

            # Attach the user to the request state for later use
            request.state.user = session.user  # Assuming you have a user relationship

        # Proceed to the next middleware or request handler
        response = await call_next(request)
        return response


# Add middleware to the FastAPI app
app.add_middleware(SessionMiddleware)
app.add_middleware(DBSessionMiddleware)  # <- needs to run first, added last

def get_current_user(request: Request):
    if not hasattr(request.state, "user"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user

@app.get("/check-session")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello, {current_user.email}!"}

#%% API GATEWAYS

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

def generate_random_session_id() -> str:
    return str(uuid.uuid4())


@app.post("/auth/login")
def login(user: UserLogin, db: Session = Depends(get_db), request: Request = None):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create a new session
    session_id = generate_random_session_id()  # Implement this function to create a random session ID
    user_agent = request.headers.get("user-agent")
    ip_address = request.client.host  # This gives you the client's IP address
    expires_at = datetime.now() + timedelta(hours=24)
    new_session = UserSession(user_id=db_user.id, session_id=session_id, user_agent=user_agent, ip=ip_address,
                              expires_at=expires_at)
    db.add(new_session)
    db.commit()

    # Set the session_id cookie
    response = JSONResponse(content={"message": "Logged in successfully"})
    response.set_cookie(key="session_id", value=session_id, httponly=True, secure=True, samesite="lax")
    return response


@app.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Revoke the session
    db.query(UserSession).filter(UserSession.user_id == current_user.id).delete()
    db.commit()

    # Clear the session_id cookie
    response = JSONResponse(content={"message": "Logged out successfully"})
    response.delete_cookie("session_id")
    return response

if __name__ == "__main__":
    uvicorn.run("src.test_backend.api:app", host="0.0.0.0", port=8000, reload=True)