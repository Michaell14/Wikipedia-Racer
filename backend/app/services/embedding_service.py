from sentence_transformers import SentenceTransformer, util
import torch
import numpy as np
import asyncio
from typing import List, Optional
from backend.app.services.cache_service import cache_service
from sqlalchemy.ext.asyncio import AsyncSession

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
    
    async def get_embedding(self, text: str, db: Optional[AsyncSession] = None) -> np.ndarray:
        if db:
            cached = await cache_service.get_cached_embedding(db, text)
            if cached is not None:
                return cached
        
        # Compute embedding (this is CPU/GPU bound)
        embedding = self.model.encode(text, convert_to_tensor=True)
        embedding_np = embedding.cpu().numpy()
        
        # We don't cache here anymore to avoid session concurrency issues
        return embedding_np
    
    async def compute_similarities(self, target_text: str, candidate_texts: List[str], db: Optional[AsyncSession] = None):
        if not candidate_texts:
            return []
        
        # 1. Get target embedding
        target_embedding = await self.get_embedding(target_text, db)
        target_tensor = torch.from_numpy(target_embedding)
        
        # 2. Get candidate embeddings (parallel read from cache/model)
        candidate_embeddings = await asyncio.gather(
            *[self.get_embedding(text, db) for text in candidate_texts]
        )
        
        # 3. Cache any new embeddings (sequential write to avoid session issues)
        if db:
            for text, emb_np in zip(candidate_texts, candidate_embeddings):
                # cache_service.cache_embedding handles existence check
                await cache_service.cache_embedding(db, text, emb_np)
            
        candidate_tensors = torch.from_numpy(np.array(candidate_embeddings))
        
        cosine_scores = util.cos_sim(target_tensor, candidate_tensors)[0]
        
        results = []
        for text, score in zip(candidate_texts, cosine_scores):
            results.append({"text": text, "score": float(score)})
            
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

embedding_service = EmbeddingService()
