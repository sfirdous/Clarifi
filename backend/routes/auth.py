from fastapi import APIRouter,HTTPException
from backend.schemas.user_schema import UserCreate
from backend.models import users
from backend.database import database
import uuid
import hashlib

router = APIRouter()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
async def register_user(user: UserCreate):
    print("Register API called")
    print("Received data:", user.dict())
    
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user.password)
    
    query = users.insert().values(
        user_id = user_id,
        username = user.username,
        email = user.email,
        password = hashed_pw,
        bank_name = user.bank_name,
    )
    
    try:
        await database.execute(query)
        return {"message" : "User registered successfully","user_id" : user_id}
    except Exception as e:
        print("Registration error:", e)
        raise HTTPException(status_code = 400,detail="Username or Email may already exists.")