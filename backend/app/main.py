from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.db.database import engine, Base, AsyncSessionLocal

from backend.app.api.endpoints import router as api_router

from contextlib import asynccontextmanager

from urllib.parse import unquote
from backend.app.models.models import VitalArticle
from backend.app.services.wiki_service import wiki_service
from sqlalchemy import func
from sqlalchemy.future import select

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Populate Vital Articles if empty
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(func.count(VitalArticle.id)))
        count = result.scalar()
        if count == 0:
            existing_titles = set()
            for level in [3, 4]:
                print(f"Fetching level-{level} vital articles... this may take a moment.")
                titles = await wiki_service.get_vital_article_titles(level)
                print(f"DEBUG: Wikipedia returned {len(titles)} titles for level {level}")
                if titles:
                    batch_size = 500
                    added_count = 0
                    for i in range(0, len(titles), batch_size):
                        batch = titles[i:i+batch_size]
                        new_articles = []
                        for title in batch:
                            decoded_title = unquote(title).replace("_", " ")
                            if decoded_title not in existing_titles:
                                new_articles.append(VitalArticle(title=decoded_title, level=level))
                                existing_titles.add(decoded_title)
                        
                        if new_articles:
                            db.add_all(new_articles)
                            try:
                                await db.commit()
                                added_count += len(new_articles)
                                print(f"Seeded batch {i//batch_size + 1} ({added_count} total so far for level {level})")
                            except Exception as e:
                                print(f"Error seeding batch: {e}")
                                await db.rollback()
                    print(f"Successfully cached {added_count} level-{level} articles.")
        else:
            print(f"Database already seeded with {count} vital articles.")
    yield
    # Shutdown: Clean up if needed

app = FastAPI(title="Wikipedia Racer API", lifespan=lifespan)

app.include_router(api_router, prefix="/api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Wikipedia Racer API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
