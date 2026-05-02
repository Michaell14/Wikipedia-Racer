from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Response
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.database import get_db
from backend.app.services.wiki_service import wiki_service
from backend.app.services.game_manager import game_manager
from backend.app.services.bot_engine import BotEngine
from bs4 import BeautifulSoup
import asyncio
import re

from backend.app.models.models import VitalArticle
from sqlalchemy import func
from sqlalchemy.future import select

router = APIRouter()

@router.post("/race/new")
async def create_race(db: AsyncSession = Depends(get_db)):
    try:
        # 1. Pick Start from Level 4 (Broad but mostly recognizable)
        res_start = await db.execute(select(VitalArticle).where(VitalArticle.level == 4).order_by(func.random()).limit(1))
        start_article = res_start.scalars().first()
        start_page = start_article.title if start_article else "Philosophy"
        print(f"DEBUG: Selected start_page: {start_page} (from DB: {start_article is not None})")

        # 2. Pick Target from Level 3 (The ~1,000 most famous topics on Earth)
        res_target = await db.execute(select(VitalArticle).where(VitalArticle.level == 3).order_by(func.random()).limit(1))
        target_article = res_target.scalars().first()
        target_page = target_article.title if target_article else "Internet"
        print(f"DEBUG: Selected target_page: {target_page} (from DB: {target_article is not None})")
            
        # Ensure they are different
        if start_page == target_page:
            target_page = "History" # Quick escape
            
        session = game_manager.create_session(start_page, target_page)
        return {
            "id": session.id,
            "start_page": session.start_page,
            "target_page": session.target_page
        }
    except Exception as e:
        print(f"CRITICAL ERROR IN CREATE_RACE: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race/{session_id}")
async def get_race(session_id: str):
    session = game_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "id": session.id,
        "start_page": session.start_page,
        "target_page": session.target_page,
        "status": session.status,
        "winner": session.winner
    }

@router.get("/proxy/{session_id}/{page_title:path}")
async def proxy_wikipedia(session_id: str, page_title: str):
    session = game_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    html = await wiki_service.get_page_html(page_title)
    if not html:
        raise HTTPException(status_code=404, detail=f"Page not found: {page_title}")
    
    soup = BeautifulSoup(html, "html.parser")
    
    # In Action API 'parse', the title isn't in a <title> tag in the snippet.
    # But we can assume the title we requested or handled by redirects.
    # For now, let's just track based on the requested page_title.
    session.human_current_page = page_title.replace("_", " ")
    
    # Check win condition
    if session.human_current_page.lower() == session.target_page.lower():
        if session.status == "playing":
            session.status = "finished"
            session.winner = "human"
            await session.broadcast({
                "type": "RACE_OVER",
                "winner": "human",
                "current_page": session.human_current_page
            })

    # Rewrite links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        
        # 1. Handle absolute links
        if href.startswith("https://en.wikipedia.org/wiki/"):
            topic = href.replace("https://en.wikipedia.org/wiki/", "")
            a["href"] = f"/api/proxy/{session_id}/{topic}"
        # 2. Handle /wiki/ links
        elif href.startswith("/wiki/"):
            topic = href.replace("/wiki/", "")
            a["href"] = f"/api/proxy/{session_id}/{topic}"
        # 3. Handle ./ links (common in REST API but maybe Action API too)
        elif href.startswith("./"):
            topic = href.replace("./", "")
            a["href"] = f"/api/proxy/{session_id}/{topic}"
        # 4. Handle non-colon relative links (likely articles)
        elif not href.startswith("http") and not href.startswith("#") and ":" not in href:
            a["href"] = f"/api/proxy/{session_id}/{href}"
        
        # Security/Game filter: Block external links and namespaces
        if ":" in a["href"] and "/api/proxy/" in a["href"]:
            topic = a["href"].split("/")[-1]
            if re.match(r"^(File|Category|Wikipedia|Special|Talk|User|Template|Help|Portal|Draft|MediaWiki):", topic, re.I):
                a["href"] = "#"
        
        if not a["href"].startswith("/api/proxy/") and not a["href"].startswith("#"):
             a["target"] = "_blank"

    # Inject base styles to keep it readable
    style_tag = soup.new_tag("style")
    style_tag.string = """
        body { font-family: sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; }
        img { max-width: 100%; height: auto; }
        .mw-editsection, .navbox, .reflist, .printfooter, .asbox { display: none; }
        a { color: #0645ad; text-decoration: none; }
        a:hover { text-decoration: underline; }
    """
    
    # Wrap in a basic HTML structure if it's just a snippet
    full_html = f"<html><head></head><body>{soup.prettify()}</body></html>"
    new_soup = BeautifulSoup(full_html, "html.parser")
    new_soup.head.append(style_tag)

    return Response(content=new_soup.prettify(), media_type="text/html")

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    session = await game_manager.connect(session_id, websocket)
    if not session:
        await websocket.close(code=1008)
        return

    try:
        # Wait for start command
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "START_RACE":
                if session.status == "waiting":
                    session.bot_delay = data.get("botDelay", 5.0)
                    session.status = "playing"
                    await session.broadcast({"type": "GAME_START"})
                    
                    # Start bot
                    bot = BotEngine(session.id, session.start_page, session.target_page, game_manager)
                    session.bot_task = asyncio.create_task(bot.run())
            
            elif data.get("type") == "PING":
                await websocket.send_json({"type": "PONG"})

    except WebSocketDisconnect:
        game_manager.disconnect(session_id, websocket)
