# app/models.py
from sqlalchemy import (Column, Integer, String, BigInteger, ForeignKey,
                        DateTime, func)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String)
    language = Column(String(2), default='ru')
    level_id = Column(Integer, ForeignKey('levels.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    direction = Column(String(10)) # e.g., 'ru-en'

    level = relationship("Level")
    topic = relationship("Topic")
    
    def __repr__(self):
        return f"<User(id={self.id}, tg_id={self.tg_id})>"

class Level(Base):
    __tablename__ = 'levels'
    id = Column(Integer, primary_key=True)
    name_ru = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False) # 'A1', 'B2'
    sort_order = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Level(id={self.id}, code='{self.code}')>"

class Topic(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    name_ru = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    description = Column(String)

    def __repr__(self):
        return f"<Topic(id={self.id}, name_ru='{self.name_ru}')>"

class Phrase(Base):
    __tablename__ = 'phrases'
    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey('topics.id'), nullable=False)
    level_id = Column(Integer, ForeignKey('levels.id'), nullable=False)
    text_en = Column(String, nullable=False)
    text_ru = Column(String, nullable=False)
    text_uz = Column(String, nullable=False)

    topic = relationship("Topic")
    level = relationship("Level")
    
    def __repr__(self):
        return f"<Phrase(id={self.id}, text_en='{self.text_en[:20]}...')>"

class UserProgress(Base):
    __tablename__ = 'user_progress'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    phrase_id = Column(Integer, ForeignKey('phrases.id'), nullable=False)
    score = Column(Integer)
    attempts = Column(Integer, default=0)
    last_attempt = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User")
    phrase = relationship("Phrase")