from sqlalchemy.orm import Session
import models, schema
from sqlalchemy import or_
import auth


def create_user(db: Session, user: schema.UserCreate):
    hashed_pw = auth.hash_password(user.password)
    db_user = models.User(username=user.username, email=user.email, password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


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

def add_or_update_reaction(db: Session, reaction: schema.ReactionCreate):
    existing = db.query(models.Reaction).filter(
        models.Reaction.video_id == reaction.video_id,
        models.Reaction.user_id == reaction.user_id
    ).first()

    if existing:
        existing.type = reaction.type
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_reaction = models.Reaction(
            video_id=reaction.video_id,
            user_id=reaction.user_id,
            type=reaction.type
        )
        db.add(new_reaction)
        db.commit()
        db.refresh(new_reaction)
        return new_reaction

def get_reaction_count(db: Session, video_id: int):
    likes = db.query(models.Reaction).filter(
        models.Reaction.video_id == video_id,
        models.Reaction.type == 'like'
    ).count()
    dislikes = db.query(models.Reaction).filter(
        models.Reaction.video_id == video_id,
        models.Reaction.type == 'dislike'
    ).count()
    return {"likes": likes, "dislikes": dislikes}

def get_videos(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Video).offset(skip).limit(limit).all()

def search_videos(db: Session, query: str):
    return db.query(models.Video).filter(
        or_(
            models.Video.title.ilike(f"%{query}%"),
            models.Video.description.ilike(f"%{query}%")
        )
    ).all()
