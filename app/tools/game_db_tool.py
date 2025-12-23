import json
import logging
import random
from pathlib import Path
from typing import List, Dict, Any
from crewai.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)

class GameDatabaseSearchTool(BaseTool):
    name: str = "Game Database Search Tool"
    description: str = """Search for generic game ideas and twists from the local database.
    Useful for finding inspiration for activity games.
    
    IMPORTANT: The database is in HEBREW. Use HEBREW keywords/phrases for best results!
    
    Args:
        query: Multiple HEBREW keywords separated by commas or spaces.
               Examples: 
               - 'קבוצה, תנועה, ריצה' (group, movement, running)
               - 'כדור מעגל' (ball circle)
               - 'היכרות חברים' (getting to know friends)
               - 'תחרות קבוצתית' (team competition)
               - 'משחק מחשבה' (thinking game)
               - 'random' for random ideas
               
               Good Hebrew keywords: משחק, קבוצה, תנועה, ריצה, כדור, מעגל, היכרות, 
               חברים, תחרות, צוות, שיתוף, חשיבה, זיכרון, מילים, שאלות
    Returns:
        JSON string with list of game ideas including title and description.
    """
    
    _games_data: List[Dict[str, Any]] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_db()

    def _load_db(self):
        try:
            # Simplified structure: look in data/ directory at project root
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "data/games_db.json"

            if db_path.exists():
                self._games_data = json.loads(db_path.read_text(encoding='utf-8'))
                logger.info(f"Loaded {len(self._games_data)} games from DB: {db_path}")
            else:
                logger.warning(f"Game DB not found at {db_path}")
                self._games_data = []
        except Exception as e:
            logger.error(f"Error loading game DB: {e}")
            self._games_data = []

    def _run(self, query: str) -> str:
        """
        Search the game database with multiple keywords support.
        """
        if not self._games_data:
            return json.dumps({"error": "Game database not loaded"}, ensure_ascii=False)

        query = str(query).strip().lower()
        
        # Handle random/empty queries
        if query in ["random", "", "none", "null", "אקראי"]:
            results = random.sample(self._games_data, min(5, len(self._games_data)))
            return json.dumps({
                "message": "Here are 5 random game ideas for inspiration:",
                "games": results
            }, ensure_ascii=False, indent=2)
        
        # Split query into multiple keywords (by comma, space, or Hebrew comma)
        separators = [',', '،', ' ', '\t']
        keywords = [query]
        for sep in separators:
            new_keywords = []
            for kw in keywords:
                new_keywords.extend(kw.split(sep))
            keywords = new_keywords
        
        # Clean and filter keywords (min 2 chars)
        keywords = [kw.strip().lower() for kw in keywords if len(kw.strip()) >= 2]
        
        if not keywords:
            # Fallback to random
            results = random.sample(self._games_data, min(5, len(self._games_data)))
            return json.dumps({
                "message": "No valid keywords provided. Here are random ideas:",
                "games": results
            }, ensure_ascii=False, indent=2)
        
        # Score-based search: games matching more keywords rank higher
        scored_results = []
        
        for game in self._games_data:
            title = game.get('title', '').lower()
            desc = game.get('description', '').lower()
            tags = " ".join(game.get('tags', [])).lower()
            searchable = f"{title} {desc} {tags}"
            
            # Count how many keywords match
            score = sum(1 for kw in keywords if kw in searchable)
            
            if score > 0:
                scored_results.append((score, game))
        
        # Sort by score (highest first) and take top 10
        scored_results.sort(key=lambda x: x[0], reverse=True)
        results = [game for score, game in scored_results[:10]]
        
        if not results:
            # Fallback if no results
            fallback_games = random.sample(self._games_data, min(5, len(self._games_data)))
            return json.dumps({
                "message": f"No games found for keywords: {keywords}. Here are random ideas instead:",
                "keywords_searched": keywords,
                "games": fallback_games
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "message": f"Found {len(results)} games matching keywords: {keywords}",
            "keywords_searched": keywords,
            "games": results
        }, ensure_ascii=False, indent=2)
