from pydantic import BaseModel
from datetime import datetime

# User
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    class Config:
        orm_mode = True

# Auth
class Token(BaseModel):
    access_token: str
    token_type: str

class CommentCreate(BaseModel):
    video_id: int
    user_id: int
    text: str

class CommentResponse(BaseModel):
    id: int
    video_id: int
    user_id: int
    text: str
    timestamp: datetime

    class Config:
        orm_mode = True


class ReactionCreate(BaseModel):
    video_id: int
    user_id: int
    type: str  # 'like' or 'dislike'

class ReactionResponse(BaseModel):
    id: int
    video_id: int
    user_id: int
    type: str
    timestamp: datetime

    class Config:
        orm_mode = True

class ReactionCountResponse(BaseModel):
    likes: int
    dislikes: int

class VideoResponse(BaseModel):
    id: int
    title: str
    description: str
    file_path: str
    uploaded_by: int
    upload_date: datetime

    class Config:
        orm_mode = True

