from fastapi import FastAPI, UploadFile, File, Depends, Query
from sqlalchemy.orm import Session
import shutil
import os
from database import SessionLocal, engine, Base
from fastapi import FastAPI, Depends
import crud, models, schema

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import auth
from fastapi import Response, Request, HTTPException
import os
from fastapi.responses import StreamingResponse
from fastapi.responses import FileResponse



app = FastAPI()

# Create tables
Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import JWTError, jwt
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@app.post("/register/", response_model=schema.UserResponse)
def register(user: schema.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.post("/login/", response_model=schema.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# Ensure videos folder exists
os.makedirs("videos", exist_ok=True)

@app.post("/upload-video/")
async def upload_video(title: str, description: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Ensure dummy user exists
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        user = models.User(
            username="laxman",
            email="laxman@strategicerp.com",
            password="ghpmgjklsdfjsguhiyft"
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
def add_comment(comment: schema.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.create_comment(db, comment)

@app.get("/comments/{video_id}", response_model=list[schema.CommentResponse])
def list_comments(video_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_comments_by_video(db, video_id)

@app.post("/reactions/", response_model=schema.ReactionResponse)
def react(reaction: schema.ReactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.add_or_update_reaction(db, reaction)

@app.get("/reactions/{video_id}", response_model=schema.ReactionCountResponse)
def reaction_count(video_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_reaction_count(db, video_id)

@app.get("/videos/", response_model=list[schema.VideoResponse])
def list_videos(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_videos(db, skip=skip, limit=limit)

@app.get("/search-videos/", response_model=list[schema.VideoResponse])
def search_videos(query: str = Query(..., min_length=1), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.search_videos(db, query)



@app.get("/videos/stream/{video_id}")
def stream_video(video_id: int, request: Request, db: Session = Depends(get_db)):
    # Fetch video info from DB
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    file_path = video.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    
    def get_chunk(start: int = 0, end: int = None):
        with open(file_path, "rb") as f:
            f.seek(start)
            remaining = (end - start + 1) if end is not None else file_size - start
            while remaining > 0:
                chunk_size = min(2048*2048, remaining)  # 1MB chunks
                data = f.read(chunk_size)
                if not data:
                    break
                yield data
                remaining -= len(data)

    if range_header:
        # Parse Range header: "bytes=start-end"
        bytes_range = range_header.replace("bytes=", "").split("-")
        start = int(bytes_range[0])
        end = int(bytes_range[1]) if len(bytes_range) > 1 and bytes_range[1] else file_size - 1
        content_length = end - start + 1

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
            "Cache-Control": "no-cache"
        }
        return StreamingResponse(get_chunk(start, end), status_code=206, headers=headers)
    
    # If no Range header, return full video
    headers = {
        "Content-Length": str(file_size),
        "Content-Type": "video/mp4",
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-cache"
    }
    return StreamingResponse(get_chunk(), headers=headers)


@app.get("/videos/full/{video_id}")
def get_full_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(models.Video).filter(models.Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video.file_path, media_type="video/mp4")
