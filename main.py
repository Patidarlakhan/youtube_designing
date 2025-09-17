from fastapi import FastAPI, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
import shutil
import os
from database import SessionLocal, engine, Base
from fastapi import FastAPI, Depends
import crud, models, schema

app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure videos folder exists
os.makedirs("videos", exist_ok=True)

@app.post("/upload-video/")
async def upload_video(title: str, description: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Ensure dummy user exists
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        user = models.User(
            username="Default User",
            email="default@example.com",
            password="hashed_dummy_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Save file
    os.makedirs("videos", exist_ok=True)
    file_location = f"videos/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Insert video
    new_video = models.Video(
        title=title,
        description=description,
        file_path=file_location,
        uploaded_by=user.id
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    print(f"New Video created with ID: {new_video.id}")
    return {"info": f"Video '{title}' uploaded successfully", "id": new_video.id, "file_path": file_location}

@app.post("/comments/", response_model=schema.CommentResponse)
def add_comment(comment: schema.CommentCreate, db: Session = Depends(get_db)):
    return crud.create_comment(db, comment)

@app.get("/comments/{video_id}", response_model=list[schema.CommentResponse])
def list_comments(video_id: int, db: Session = Depends(get_db)):
    return crud.get_comments_by_video(db, video_id)

@app.post("/reactions/", response_model=schema.ReactionResponse)
def react(reaction: schema.ReactionCreate, db: Session = Depends(get_db)):
    return crud.add_or_update_reaction(db, reaction)

@app.get("/reactions/{video_id}", response_model=schema.ReactionCountResponse)
def reaction_count(video_id: int, db: Session = Depends(get_db)):
    return crud.get_reaction_count(db, video_id)

@app.get("/videos/", response_model=list[schema.VideoResponse])
def list_videos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return crud.get_videos(db, skip=skip, limit=limit)

@app.get("/search-videos/", response_model=list[schema.VideoResponse])
def search_videos(query: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    return crud.search_videos(db, query)