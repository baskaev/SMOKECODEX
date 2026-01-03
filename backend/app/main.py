from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password
from app.config import settings
from app.db import Base, engine
from app.deps import authenticate_user, get_current_user, get_db
from app.models import Booking, Comment, Favorite, Post, PostLike, Room, User, Venue
from app.schemas import (
    BookingCreate,
    BookingPublic,
    CommentCreate,
    CommentPublic,
    FavoritePublic,
    PostCreate,
    PostPublic,
    RoomCreate,
    RoomPublic,
    Token,
    UserCreate,
    UserPublic,
    UserUpdate,
    VenueCreate,
    VenuePublic,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="SmokeCodex Hookah Booking API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/auth/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token(subject=user.email)
    return Token(access_token=token)


@app.get("/users/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.patch("/users/me", response_model=UserPublic)
def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(current_user, key, value)
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/venues", response_model=VenuePublic, status_code=status.HTTP_201_CREATED)
def create_venue(
    payload: VenueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = Venue(owner_id=current_user.id, **payload.model_dump())
    db.add(venue)
    db.commit()
    db.refresh(venue)
    return venue


@app.get("/venues", response_model=list[VenuePublic])
def list_venues(
    db: Session = Depends(get_db),
    search: str | None = None,
    city: str | None = None,
    min_price: int | None = None,
    max_price: int | None = None,
    has_vip: bool | None = None,
):
    query = db.query(Venue)
    filters = []
    if search:
        like = f"%{search}%"
        filters.append(or_(Venue.name.ilike(like), Venue.description.ilike(like)))
    if city:
        filters.append(Venue.city.ilike(city))
    if min_price is not None:
        filters.append(or_(Venue.min_price.is_(None), Venue.min_price >= min_price))
    if max_price is not None:
        filters.append(or_(Venue.max_price.is_(None), Venue.max_price <= max_price))
    if has_vip is not None:
        filters.append(Venue.has_vip == has_vip)
    if filters:
        query = query.filter(and_(*filters))
    return query.order_by(Venue.created_at.desc()).all()


@app.get("/venues/{venue_id}", response_model=VenuePublic)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@app.post("/venues/{venue_id}/rooms", response_model=RoomPublic, status_code=status.HTTP_201_CREATED)
def create_room(
    venue_id: int,
    payload: RoomCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    if venue.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    room = Room(venue_id=venue_id, **payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@app.get("/venues/{venue_id}/rooms", response_model=list[RoomPublic])
def list_rooms(
    venue_id: int,
    db: Session = Depends(get_db),
    capacity: int | None = None,
    is_private: bool | None = None,
):
    query = db.query(Room).filter(Room.venue_id == venue_id)
    if capacity is not None:
        query = query.filter(Room.capacity >= capacity)
    if is_private is not None:
        query = query.filter(Room.is_private == is_private)
    return query.all()


@app.post("/bookings", response_model=BookingPublic, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(Room.id == payload.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    conflict = db.query(Booking).filter(
        Booking.room_id == payload.room_id,
        Booking.status == "active",
        Booking.end_time > payload.start_time,
        Booking.start_time < payload.end_time,
    ).first()
    if conflict:
        raise HTTPException(status_code=400, detail="Time slot already booked")
    booking = Booking(
        user_id=current_user.id,
        room_id=payload.room_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.get("/bookings", response_model=list[BookingPublic])
def list_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    status_filter: str | None = Query(default=None, alias="status"),
):
    query = db.query(Booking).filter(Booking.user_id == current_user.id)
    if status_filter:
        query = query.filter(Booking.status == status_filter)
    return query.order_by(Booking.start_time.desc()).all()


@app.delete("/bookings/{booking_id}", response_model=BookingPublic)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    booking.status = "cancelled"
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@app.post("/favorites/{venue_id}", response_model=FavoritePublic, status_code=status.HTTP_201_CREATED)
def add_favorite(
    venue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    existing = (
        db.query(Favorite)
        .filter(Favorite.venue_id == venue_id, Favorite.user_id == current_user.id)
        .first()
    )
    if existing:
        return existing
    favorite = Favorite(user_id=current_user.id, venue_id=venue_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@app.get("/favorites", response_model=list[VenuePublic])
def list_favorites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Venue)
        .join(Favorite, Favorite.venue_id == Venue.id)
        .filter(Favorite.user_id == current_user.id)
        .all()
    )


@app.delete("/favorites/{venue_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    venue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(Favorite)
        .filter(Favorite.venue_id == venue_id, Favorite.user_id == current_user.id)
        .first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()


@app.post("/posts", response_model=PostPublic, status_code=status.HTTP_201_CREATED)
def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = Post(author_id=current_user.id, content=payload.content)
    db.add(post)
    db.commit()
    db.refresh(post)
    return PostPublic(
        id=post.id,
        author_id=post.author_id,
        content=post.content,
        created_at=post.created_at,
        likes_count=0,
    )


@app.get("/users/{user_id}/posts", response_model=list[PostPublic])
def list_posts(user_id: int, db: Session = Depends(get_db)):
    posts = (
        db.query(Post, func.count(PostLike.id).label("likes_count"))
        .outerjoin(PostLike, PostLike.post_id == Post.id)
        .filter(Post.author_id == user_id)
        .group_by(Post.id)
        .order_by(Post.created_at.desc())
        .all()
    )
    return [
        PostPublic(
            id=post.id,
            author_id=post.author_id,
            content=post.content,
            created_at=post.created_at,
            likes_count=likes_count,
        )
        for post, likes_count in posts
    ]


@app.post("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    existing = (
        db.query(PostLike)
        .filter(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
        .first()
    )
    if existing:
        return
    like = PostLike(post_id=post_id, user_id=current_user.id)
    db.add(like)
    db.commit()


@app.post("/posts/{post_id}/comments", response_model=CommentPublic, status_code=status.HTTP_201_CREATED)
def add_comment(
    post_id: int,
    payload: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    comment = Comment(post_id=post_id, author_id=current_user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.get("/posts/{post_id}/comments", response_model=list[CommentPublic])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Comment)
        .filter(Comment.post_id == post_id)
        .order_by(Comment.created_at.asc())
        .all()
    )


@app.get("/")
async def root():
    return {
        "message": "SmokeCodex API running",
        "docs": "/docs",
        "frontend": settings.frontend_url,
    }


@app.on_event("startup")
def on_startup():
    print(
        f"API доступен: http://localhost:{settings.app_port} (Swagger: http://localhost:{settings.app_port}/docs)"
    )
    print(f"Фронтенд: {settings.frontend_url}")
