import asyncio
import heapq
from typing import List, Set, Tuple
from backend.app.services.wiki_service import wiki_service
from backend.app.services.embedding_service import embedding_service
from backend.app.services.cache_service import cache_service
from backend.app.db.database import AsyncSessionLocal

class BotEngine:
    def __init__(self, session_id: str, start_page: str, target_page: str, game_manager):
        self.session_id = session_id
        self.start_page = start_page
        self.target_page = target_page
        self.game_manager = game_manager
        self.visited: Set[str] = set()
        # Priority Queue: (-similarity_score, path_to_node)
        self.pq: List[Tuple[float, List[str]]] = []
        self.max_hops = 30
        self.is_running = True

    async def run(self):
        session = self.game_manager.get_session(self.session_id)
        if not session:
            return

        # Initialize with start page
        heapq.heappush(self.pq, (0.0, [self.start_page]))
        
        while self.pq and self.is_running and session.status == "playing":
            # 1. Pop the next best path
            score, path = heapq.heappop(self.pq)
            current_page = path[-1]
            
            if current_page in self.visited:
                continue

            # 2. Handicap: Flat delay
            await session.broadcast({"type": "BOT_THINKING", "current_page": current_page})
            await asyncio.sleep(session.bot_delay)
            
            # 3. Check session status again after sleep
            if not self.is_running or session.status != "playing":
                break

            # 4. Perform the move
            self.visited.add(current_page)
            session.bot_current_path = path
            await session.broadcast({
                "type": "BOT_MOVED",
                "path": path,
                "current_page": current_page
            })
            
            if current_page.lower() == self.target_page.lower():
                # Bot wins!
                if session.status == "playing":
                    session.status = "finished"
                    session.winner = "bot"
                    await session.broadcast({
                        "type": "RACE_OVER",
                        "winner": "bot",
                        "path": path
                    })
                break
            
            if len(path) >= self.max_hops:
                # Restart logic
                await session.broadcast({"type": "BOT_RESTARTED", "reason": "Max hops reached"})
                self.visited.clear()
                self.pq = []
                heapq.heappush(self.pq, (0.0, [self.start_page]))
                continue

            # Fetch links
            async with AsyncSessionLocal() as db:
                links = await cache_service.get_cached_links(db, current_page)
                if links is None:
                    links = await wiki_service.get_links(current_page)
                    await cache_service.cache_links(db, current_page, links)
                
                if not links:
                    continue
                
                # Filter out visited
                unvisited_links = [l for l in links if l not in self.visited]
                if not unvisited_links:
                    continue
                
                # Compute similarities
                similarities = await embedding_service.compute_similarities(self.target_page, unvisited_links, db)
                
                # Push to PQ (top N to avoid exploding the PQ too much, but best-first usually stays manageable)
                for item in similarities[:10]: # Take top 10 most similar links to explore
                    new_path = path + [item["text"]]
                    heapq.heappush(self.pq, (-item["score"], new_path))
            
        if not self.pq and session.status == "playing":
             await session.broadcast({"type": "RACE_OVER", "winner": "human", "reason": "Bot gave up (no more links)"})
             session.status = "finished"
             session.winner = "human"

    def stop(self):
        self.is_running = False
