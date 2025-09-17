from pydantic import BaseModel
from datetime import datetime

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
