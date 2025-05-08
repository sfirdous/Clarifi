from fastapi import APIRouter,HTTPException,Depends
from backend.schemas.user_schema import UserCreate,UserLogin
from backend.models import users
from backend.database import database
import uuid
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.database import get_db, Base, engine
from uuid import uuid4



Base.metadata.create_all(bind=engine)

router = APIRouter()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/register")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    print("Register API called")
    print("Received data:", user.dict())

    # Check if email or username already exists
    existing_user_query = users.select().where(
        (users.c.email == user.email) | (users.c.username == user.username)
    )
    existing_user = await database.fetch_one(existing_user_query)

    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists.")

    # Generate user ID and hash password
    user_id = str(uuid4())
    hashed_pw = hash_password(user.password)

    # Insert new user
    insert_query = users.insert().values(
        user_id=user_id,
        username=user.username,
        email=user.email,
        password=hashed_pw,
        bank_name=user.bank_name
    )

    try:
        await database.execute(insert_query)
        return {"message": "User registered successfully", "user_id": user_id}
    except Exception as e:
        print("Registration error:", e)
        raise HTTPException(status_code=500, detail="Internal server error during registration.")

@router.post("/login")
async def login_user(user: UserLogin):
    print("Login API called")
    query = users.select().where(users.c.email == user.email)
    user_record = await database.fetch_one(query)

    if not user_record:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user.password, user_record["password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")

    return {
        "message": "Login successful",
        "user_id": user_record["user_id"],
        "username": user_record["username"],
        "email": user_record["email"],
        "bank_name": user_record["bank_name"]
    }