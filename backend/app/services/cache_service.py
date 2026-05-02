import numpy as np
import io
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.models import CachedPage, CachedEmbedding
from typing import List, Optional

class CacheService:
    async def get_cached_links(self, db: AsyncSession, title: str) -> Optional[List[str]]:
        result = await db.execute(select(CachedPage).where(CachedPage.title == title))
        cached_page = result.scalars().first()
        return cached_page.links if cached_page else None

    async def cache_links(self, db: AsyncSession, title: str, links: List[str]):
        # Check if already exists to avoid unique constraint violation
        existing = await self.get_cached_links(db, title)
        if existing is not None:
            return
        new_page = CachedPage(title=title, links=links)
        db.add(new_page)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

    async def get_cached_embedding(self, db: AsyncSession, text: str) -> Optional[np.ndarray]:
        result = await db.execute(select(CachedEmbedding).where(CachedEmbedding.text == text))
        cached_embedding = result.scalars().first()
        if cached_embedding:
            return np.load(io.BytesIO(cached_embedding.embedding))
        return None

    async def cache_embedding(self, db: AsyncSession, text: str, embedding: np.ndarray):
        # Check if already exists
        existing = await self.get_cached_embedding(db, text)
        if existing is not None:
            return
        buffer = io.BytesIO()
        np.save(buffer, embedding)
        new_embedding = CachedEmbedding(text=text, embedding=buffer.getvalue())
        db.add(new_embedding)
        try:
            await db.commit()
        except Exception:
            await db.rollback()

cache_service = CacheService()
