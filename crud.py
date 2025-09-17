from sqlalchemy.orm import Session
import models, schema

def create_comment(db: Session, comment: schema.CommentCreate):
    db_comment = models.Comment(
        video_id=comment.video_id,
        user_id=comment.user_id,
        text=comment.text
    )
    print(comment.text, comment.user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def get_comments_by_video(db: Session, video_id: int):
    return db.query(models.Comment).filter(models.Comment.video_id == video_id).all()
