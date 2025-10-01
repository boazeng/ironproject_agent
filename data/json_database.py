"""
JSON Database module for Iron Drawing data storage
"""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

class IronDrawingJSONDatabase:
    """Simple JSON-based database for storing iron drawing analysis results"""

    def __init__(self, db_path: str = "data/iron_drawing_db.json"):
        self.db_path = db_path
        self.data = self._load_database()

    def _load_database(self) -> Dict:
        """Load existing database or create new one"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, 'r') as f:
                    return json.load(f)
            except:
                return {"drawings": {}, "analysis": {}, "metadata": {}}
        return {"drawings": {}, "analysis": {}, "metadata": {}}

    def save(self):
        """Save database to file"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, 'w') as f:
            json.dump(self.data, f, indent=2)

    def add_drawing(self, drawing_id: str, data: Dict) -> bool:
        """Add a drawing to the database"""
        self.data["drawings"][drawing_id] = {
            **data,
            "timestamp": datetime.now().isoformat()
        }
        self.save()
        return True

    def get_drawing(self, drawing_id: str) -> Optional[Dict]:
        """Get a drawing from the database"""
        return self.data["drawings"].get(drawing_id)

    def add_analysis(self, analysis_id: str, data: Dict) -> bool:
        """Add analysis results to the database"""
        self.data["analysis"][analysis_id] = {
            **data,
            "timestamp": datetime.now().isoformat()
        }
        self.save()
        return True

    def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis results from the database"""
        return self.data["analysis"].get(analysis_id)

    def list_drawings(self) -> List[str]:
        """List all drawing IDs in the database"""
        return list(self.data["drawings"].keys())

    def list_analyses(self) -> List[str]:
        """List all analysis IDs in the database"""
        return list(self.data["analysis"].keys())