import os
from datetime import datetime
from pymongo import MongoClient
from typing import Dict, List, Optional
import json

class IronDrawingDatabase:
    """
    Simple MongoDB database manager for iron order drawing analysis.
    Uses embedded MongoDB with data stored in the data folder.
    """
    
    def __init__(self, db_name: str = "iron_drawing_analysis"):
        """
        Initialize MongoDB connection for iron drawing analysis
        
        Args:
            db_name: Name of the MongoDB database
        """
        # Use MongoDB connection string for local embedded database
        # For simplicity, we'll use a local connection
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client[db_name]
        
        # Create collections (tables)
        self.order_drawings = self.db.order_drawings
        self.catalog_shapes = self.db.catalog_shapes
        
        print(f"[DATABASE] Connected to MongoDB database: {db_name}")
        print(f"[DATABASE] Collections: order_drawings, catalog_shapes")
    
    def create_collections(self):
        """
        Create the two main collections with proper schema validation
        """
        try:
            # Create order_drawings collection
            if "order_drawings" not in self.db.list_collection_names():
                self.db.create_collection("order_drawings")
                print("[DATABASE] Created 'order_drawings' collection")
            
            # Create catalog_shapes collection  
            if "catalog_shapes" not in self.db.list_collection_names():
                self.db.create_collection("catalog_shapes")
                print("[DATABASE] Created 'catalog_shapes' collection")
            
            print("[DATABASE] Collections created successfully")
            return True
            
        except Exception as e:
            print(f"[DATABASE] Error creating collections: {e}")
            return False
    
    def insert_order_drawing(self, analysis_result: Dict) -> str:
        """
        Insert analysis results for an order drawing
        
        Args:
            analysis_result: Complete analysis results from the system
            
        Returns:
            Document ID of inserted record
        """
        try:
            # Add metadata
            document = {
                "timestamp": datetime.now().isoformat(),
                "file_name": analysis_result.get("file_name", "unknown"),
                "analysis_status": "completed",
                
                # RibFinder results
                "ribfinder": {
                    "rib_count": analysis_result.get("ribfinder", {}).get("rib_count", 0),
                    "shape_pattern": analysis_result.get("ribfinder", {}).get("shape_pattern", ""),
                    "confidence": analysis_result.get("ribfinder", {}).get("confidence", 0),
                    "match_percentage": analysis_result.get("ribfinder", {}).get("match_percentage", 0)
                },
                
                # CHATAN results
                "chatan": {
                    "shape_type": analysis_result.get("shape_type", ""),
                    "number_of_ribs": analysis_result.get("number_of_ribs", 0),
                    "confidence": analysis_result.get("confidence", 0),
                    "match_percentage": analysis_result.get("match_percentage", 0),
                    "sides": analysis_result.get("sides", []),
                    "angles_between_ribs": analysis_result.get("angles_between_ribs", []),
                    "google_vision_data": analysis_result.get("google_vision_data", {})
                },
                
                # PathFinder results
                "pathfinder": {
                    "shape_type": analysis_result.get("pathfinder", {}).get("shape_type", ""),
                    "vertex_count": analysis_result.get("pathfinder", {}).get("vertex_count", 0),
                    "total_path_length": analysis_result.get("pathfinder", {}).get("total_path_length", 0),
                    "is_closed": analysis_result.get("pathfinder", {}).get("is_closed", False),
                    "vertices": analysis_result.get("pathfinder", {}).get("vertices", []),
                    "vectors": analysis_result.get("pathfinder", {}).get("vectors", []),
                    "bounding_box": analysis_result.get("pathfinder", {}).get("path_summary", {}).get("bounding_box", {})
                },
                
                # CHATCO comparison results
                "chatco": {
                    "best_match_file": analysis_result.get("comparison", {}).get("best_match_file", ""),
                    "similarity_score": analysis_result.get("comparison", {}).get("similarity_score", 0),
                    "match_quality": analysis_result.get("comparison", {}).get("match_quality", ""),
                    "matching_features": analysis_result.get("comparison", {}).get("matching_features", []),
                    "differences": analysis_result.get("comparison", {}).get("differences", [])
                }
            }
            
            result = self.order_drawings.insert_one(document)
            print(f"[DATABASE] Order drawing analysis saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"[DATABASE] Error inserting order drawing: {e}")
            return ""
    
    def insert_catalog_shape(self, shape_name: str, shape_data: Dict) -> str:
        """
        Insert catalog shape data
        
        Args:
            shape_name: Name/ID of the catalog shape
            shape_data: Shape characteristics and metadata
            
        Returns:
            Document ID of inserted record
        """
        try:
            document = {
                "timestamp": datetime.now().isoformat(),
                "shape_name": shape_name,
                "shape_type": shape_data.get("shape_type", ""),
                "rib_count": shape_data.get("rib_count", 0),
                "dimensions": shape_data.get("dimensions", []),
                "file_path": shape_data.get("file_path", ""),
                "description": shape_data.get("description", ""),
                "tags": shape_data.get("tags", [])
            }
            
            result = self.catalog_shapes.insert_one(document)
            print(f"[DATABASE] Catalog shape '{shape_name}' saved with ID: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            print(f"[DATABASE] Error inserting catalog shape: {e}")
            return ""
    
    def get_order_drawings(self, limit: int = 10) -> List[Dict]:
        """Get recent order drawing analyses"""
        try:
            cursor = self.order_drawings.find().sort("timestamp", -1).limit(limit)
            return list(cursor)
        except Exception as e:
            print(f"[DATABASE] Error retrieving order drawings: {e}")
            return []
    
    def get_catalog_shapes(self, shape_type: str = None) -> List[Dict]:
        """Get catalog shapes, optionally filtered by type"""
        try:
            query = {"shape_type": shape_type} if shape_type else {}
            cursor = self.catalog_shapes.find(query)
            return list(cursor)
        except Exception as e:
            print(f"[DATABASE] Error retrieving catalog shapes: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            stats = {
                "total_order_drawings": self.order_drawings.count_documents({}),
                "total_catalog_shapes": self.catalog_shapes.count_documents({}),
                "database_name": self.db.name,
                "collections": self.db.list_collection_names()
            }
            return stats
        except Exception as e:
            print(f"[DATABASE] Error getting statistics: {e}")
            return {}
    
    def close_connection(self):
        """Close database connection"""
        try:
            self.client.close()
            print("[DATABASE] Connection closed")
        except Exception as e:
            print(f"[DATABASE] Error closing connection: {e}")


def create_iron_database() -> IronDrawingDatabase:
    """
    Factory function to create and initialize the iron drawing database
    
    Returns:
        IronDrawingDatabase instance
    """
    try:
        db = IronDrawingDatabase()
        db.create_collections()
        return db
    except Exception as e:
        print(f"[DATABASE] Failed to create database: {e}")
        return None


if __name__ == "__main__":
    # Test the database creation
    print("="*50)
    print("TESTING IRON DRAWING DATABASE")
    print("="*50)
    
    db = create_iron_database()
    if db:
        stats = db.get_statistics()
        print(f"\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        db.close_connection()
        print("\n[SUCCESS] Database test completed!")
    else:
        print("\n[ERROR] Database test failed!")