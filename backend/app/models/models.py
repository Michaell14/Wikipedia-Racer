from sqlalchemy import Column, Integer, String, JSON, Float, LargeBinary
from backend.app.db.database import Base

class CachedPage(Base):
    __tablename__ = "cached_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    links = Column(JSON)  # List of link titles

class CachedEmbedding(Base):
    __tablename__ = "cached_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, unique=True, index=True)
    embedding = Column(LargeBinary)  # Serialized numpy array

class VitalArticle(Base):
    __tablename__ = "vital_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, unique=True, index=True)
    level = Column(Integer, index=True) # 3 for Target, 4 for Start
