from datetime import datetime

from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    bio: str | None
    avatar_url: str | None
    cover_url: str | None
    city: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    city: str | None = None


class VenueCreate(BaseModel):
    name: str
    description: str | None = None
    city: str
    address: str
    phone: str | None = None
    min_price: int | None = None
    max_price: int | None = None
    has_vip: bool = False


class VenuePublic(VenueCreate):
    id: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str
    capacity: int
    hourly_price: int
    is_private: bool = False


class RoomPublic(RoomCreate):
    id: int
    venue_id: int

    class Config:
        from_attributes = True


class BookingCreate(BaseModel):
    room_id: int
    start_time: datetime
    end_time: datetime


class BookingPublic(BaseModel):
    id: int
    user_id: int
    room_id: int
    start_time: datetime
    end_time: datetime
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class FavoritePublic(BaseModel):
    id: int
    venue_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    content: str


class PostPublic(BaseModel):
    id: int
    author_id: int
    content: str
    created_at: datetime
    likes_count: int

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str


class CommentPublic(BaseModel):
    id: int
    post_id: int
    author_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True
