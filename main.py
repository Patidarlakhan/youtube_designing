from fastapi import FastAPI, UploadFile, File, Depends
from sqlalchemy.orm import Session
import shutil
import os
from database import SessionLocal, engine, Base
import models

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
    file_location = f"videos/{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Insert record into DB
    new_video = models.Video(
        title=title,
        description=description,
        file_path=file_location,
        uploaded_by=1  # For now, just use a dummy user id
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return {"info": f"Video '{title}' uploaded successfully", "file_path": file_location}
