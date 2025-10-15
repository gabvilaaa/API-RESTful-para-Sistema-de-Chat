from pydantic import BaseModel
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from database import Base
from datetime import datetime


class RoomMembers(Base):
    __tablename__ = "room_members"
    room_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, primary_key=True, index=True)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, unique=True, index=True)
    members = Column(Integer, index=True)
    is_private = Column(Boolean, index=True, default=False)

class RoomCreate(BaseModel):
    name:str
    description:str
    members:int
    is_private:bool = False

class RoomOut(BaseModel):
    id:int
    name:str
    description:str
    members:int
    is_private:bool

    class Config:
        orm_mode = True  # permite que o Pydantic leia objetos SQLAlchemy

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)  # ⚠️ usar hash em produção
    role = Column(String, index=True)

# Schema para receber dados (entrada)
class UserCreate(BaseModel):
    name: str
    username: str
    email: str
    password: str
    role: str

class UserAuth(BaseModel):
    emailUsername: str
    password:str


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    email: str
    password:str
    role: str

    class Config:
        orm_mode = True  # permite que o Pydantic leia objetos SQLAlchemy

class GroupMessagePayload(BaseModel):
    senderId: int
    content: str
    # O roomId é obtido do caminho da URL, então não é necessário aqui.

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MessageCreate(BaseModel):
    room_id:int
    sender_id:int
    receiver_id:int
    content:str
    created_at:datetime

class MessageOut(BaseModel):
    id:int
    room_id:int
    sender_id:int
    receiver_id:int
    content:str
    created_at:datetime

    class Config:
        orm_mode = True  # permite que o Pydantic leia objetos SQLAlchemy

