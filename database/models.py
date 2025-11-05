from sqlalchemy import BigInteger, Column, DateTime, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    flows: Mapped[list["FlowRecord"]] = relationship("FlowRecord", back_populates="user", cascade="all, delete-orphan")
    sprints: Mapped[list["SprintRecord"]] = relationship("SprintRecord", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"

class FlowRecord(Base):
    __tablename__ = 'flow_records'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship("User", back_populates="flows")

    def __repr__(self):
        return f"<FlowRecord(id={self.id}, user_id={self.user_id}, duration={self.duration_minutes})>"

class SprintRecord(Base):
    __tablename__ = 'sprint_records'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('users.telegram_id'))
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship("User", back_populates="sprints")

    def __repr__(self):
        return f"<SprintRecord(id={self.id}, user_id={self.user_id}, duration={self.duration_minutes})>"
