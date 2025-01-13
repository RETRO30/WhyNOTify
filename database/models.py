from database.database import Base
from sqlalchemy import Column, Enum, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import enum

class AccountStatus(enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    BANNED = "banned"

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(100), nullable=False)
    telegram_session = Column(Text, nullable=True)
    password = Column(String(100), nullable=True)
    status = Column(Enum(AccountStatus), nullable=False, default=AccountStatus.PENDING)
    proxy = relationship("Proxy", uselist=False, back_populates="account")
    
    def __repr__(self):
        return f"Account({self.phone_number})"
    
    def __str__(self):
        return f"Account({self.phone_number})"
    
    
class Proxy(Base):
    id = Column(Integer, primary_key=True)
    scheme = Column(String(100), nullable=False)
    hostname = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    account = relationship("Account", uselist=False, back_populates="proxy")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    channel_id = Column(String(100), nullable=False)
    
    def __str__(self):
        return f"Channel(channel_id={self.channel_id})"
    
    