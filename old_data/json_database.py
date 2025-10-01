import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import uuid

class IronDrawingJSONDatabase:
    """
    Simple JSON file-based database for iron order drawing analysis.
    Stores data in JSON files in the data folder - much simpler than MongoDB.
    """
    
    def __init__(self, data_folder: str = "."):
        """
        Initialize JSON database with two main data files
        
        Args:
            data_folder: Folder to store JSON database files
        """
        self.data_folder = data_folder
        self.order_drawings_file = os.path.join(data_folder, "order_drawings.json")
        self.catalog_shapes_file = os.path.join(data_folder, "catalog_shapes.json")
        
        # Create data folder if it doesn't exist
        os.makedirs(data_folder, exist_ok=True)
        
        # Initialize JSON files if they don't exist
        self._initialize_database_files()
        
        print(f"[DATABASE] JSON Database initialized in: {data_folder}")
        print(f"[DATABASE] Files: order_drawings.json, catalog_shapes.json")
    
    def _initialize_database_files(self):
        """Create initial JSON database files if they don't exist"""
        try:
            # Initialize order_drawings.json
            if not os.path.exists(self.order_drawings_file):
                initial_data = {
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "description": "Iron order drawing analysis results",
                        "total_records": 0
                    },
                    "drawings": []
                }
                with open(self.order_drawings_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=2, ensure_ascii=False)
                print("[DATABASE] Created order_drawings.json")
            
            # Initialize catalog_shapes.json
            if not os.path.exists(self.catalog_shapes_file):
                initial_data = {
                    "metadata": {
                        "created": datetime.now().isoformat(),
                        "description": "Catalog shape definitions and characteristics",
                        "total_records": 0
                    },
                    "shapes": []
                }
                with open(self.catalog_shapes_file, 'w', encoding='utf-8') as f:
                    json.dump(initial_data, f, indent=2, ensure_ascii=False)
                print("[DATABASE] Created catalog_shapes.json")
                
        except Exception as e:
            print(f"[DATABASE] Error initializing database files: {e}")
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[DATABASE] Error loading {file_path}: {e}")
            return {}
    
    def _save_json_file(self, file_path: str, data: Dict):
        """Save JSON data to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DATABASE] Error saving {file_path}: {e}")
    
    def _get_shape_explanation(self, shape_type: str, rib_count: int) -> str:
        """
        Determine shape explanation based on shape type and rib count
        
        Args:
            shape_type: Type of shape (U-shape, L-shape, etc.)
            rib_count: Number of ribs
            
        Returns:
            Explanation string for the shape
        """
        shape_type_lower = shape_type.lower()
        
        if rib_count == 1:
            return "a. Straight rib"
        elif rib_count == 2:
            if "l" in shape_type_lower:
                return "b. L rib with rotation"
            else:
                return "b. L rib with rotation"
        elif rib_count == 3:
            if "u" in shape_type_lower:
                # Check if sides are equal or different (would need additional analysis)
                return "d. U rib with different side rib length with rotation"
            else:
                return "c. Rib with equal side rib with rotation"
        else:
            # Complex shape with more than 3 ribs
            return f"Complex shape with {rib_count} ribs"
    
    def insert_order_drawing(self, order_number: str, file_name: str, analysis_result: Dict = None) -> str:
        """
        Insert analysis results for an order drawing with structured format
        
        Args:
            order_number: Order number/ID for the drawing
            file_name: Name of the analyzed drawing file
            analysis_result: Complete analysis results from the system (optional)
            
        Returns:
            Record ID of inserted document
        """
        try:
            # Load existing data
            data = self._load_json_file(self.order_drawings_file)
            if not data:
                return ""
            
            # Extract data from analysis results if provided
            if analysis_result:
                # Get number of ribs
                rib_count = analysis_result.get("ribfinder", {}).get("rib_count", 0)
                
                # Determine if all ribs are straight
                all_straight = True  # Default assumption
                
                # Determine shape explanation
                shape_type = analysis_result.get("shape_type", "")
                shape_explanation = self._get_shape_explanation(shape_type, rib_count)
                
                # Extract path degrees (angles and lengths for each rib)
                path_degrees = []
                sides = analysis_result.get("sides", [])
                for i, side in enumerate(sides):
                    rib_info = {
                        "rib_number": i + 1,
                        "length": side.get("length", 0),
                        "degree_to_next": side.get("angle_to_next", 0) if i < len(sides) - 1 else None
                    }
                    path_degrees.append(rib_info)
                
                # Extract path vectors from PathFinder
                path_vectors = []
                vectors = analysis_result.get("pathfinder", {}).get("vectors", [])
                for vec in vectors:
                    vector_info = {
                        "rib_number": vec.get("rib_number", 0),
                        "dx": vec.get("vector", {}).get("dx", 0),
                        "dy": vec.get("vector", {}).get("dy", 0)
                    }
                    path_vectors.append(vector_info)
            else:
                # Default values if no analysis result provided
                rib_count = 0
                all_straight = None
                shape_explanation = ""
                path_degrees = []
                path_vectors = []
            
            # Extract catalog compatibility data
            catalog_compatibility = {
                "best_match_file": analysis_result.get("comparison", {}).get("best_match_file", ""),
                "similarity_score": analysis_result.get("comparison", {}).get("similarity_score", 0),
                "match_quality": analysis_result.get("comparison", {}).get("match_quality", ""),
                "is_compatible": analysis_result.get("comparison", {}).get("similarity_score", 0) >= 70,  # Consider 70% or higher as compatible
                "differences": analysis_result.get("comparison", {}).get("differences", [])
            }
            
            # Create new record with your exact structure
            record_id = str(uuid.uuid4())
            new_record = {
                "id": record_id,
                
                # 1. Order number
                "order_number": order_number,
                
                # 2. File name
                "file_name": file_name,
                
                # 3. Date
                "date": datetime.now().isoformat(),
                
                # 4. Number of ribs
                "number_of_ribs": rib_count,
                
                # 5. Straight rib (true/false)
                "straight_rib": all_straight,
                
                # 6. Explanation of the shape
                "shape_explanation": shape_explanation,
                
                # 7. Path degree (length and angle for each rib)
                "path_degrees": path_degrees,
                
                # 8. Path vectors (dx, dy for each rib)
                "path_vectors": path_vectors,
                
                # 9. Compatible catalog shape
                "compatible_catalog_shape": catalog_compatibility
            }
            
            # Add to data and update metadata
            data["drawings"].append(new_record)
            data["metadata"]["total_records"] = len(data["drawings"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            self._save_json_file(self.order_drawings_file, data)
            
            print(f"[DATABASE] Order drawing analysis saved with ID: {record_id}")
            return record_id
            
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
            Record ID of inserted document
        """
        try:
            # Load existing data
            data = self._load_json_file(self.catalog_shapes_file)
            if not data:
                return ""
            
            # Create new record
            record_id = str(uuid.uuid4())
            new_record = {
                "id": record_id,
                "timestamp": datetime.now().isoformat(),
                "shape_name": shape_name,
                "shape_type": shape_data.get("shape_type", ""),
                "rib_count": shape_data.get("rib_count", 0),
                "dimensions": shape_data.get("dimensions", []),
                "file_path": shape_data.get("file_path", ""),
                "description": shape_data.get("description", ""),
                "tags": shape_data.get("tags", [])
            }
            
            # Add to data and update metadata
            data["shapes"].append(new_record)
            data["metadata"]["total_records"] = len(data["shapes"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            self._save_json_file(self.catalog_shapes_file, data)
            
            print(f"[DATABASE] Catalog shape '{shape_name}' saved with ID: {record_id}")
            return record_id
            
        except Exception as e:
            print(f"[DATABASE] Error inserting catalog shape: {e}")
            return ""
    
    def get_order_drawings(self, limit: int = 10) -> List[Dict]:
        """Get recent order drawing analyses"""
        try:
            data = self._load_json_file(self.order_drawings_file)
            if not data or "drawings" not in data:
                return []
            
            # Sort by timestamp (newest first) and limit results
            drawings = sorted(data["drawings"], key=lambda x: x.get("timestamp", ""), reverse=True)
            return drawings[:limit]
            
        except Exception as e:
            print(f"[DATABASE] Error retrieving order drawings: {e}")
            return []
    
    def get_catalog_shapes(self, shape_type: str = None) -> List[Dict]:
        """Get catalog shapes, optionally filtered by type"""
        try:
            data = self._load_json_file(self.catalog_shapes_file)
            if not data or "shapes" not in data:
                return []
            
            shapes = data["shapes"]
            
            # Filter by shape type if specified
            if shape_type:
                shapes = [s for s in shapes if s.get("shape_type", "").lower() == shape_type.lower()]
            
            return shapes
            
        except Exception as e:
            print(f"[DATABASE] Error retrieving catalog shapes: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        try:
            order_data = self._load_json_file(self.order_drawings_file)
            catalog_data = self._load_json_file(self.catalog_shapes_file)
            
            stats = {
                "total_order_drawings": order_data.get("metadata", {}).get("total_records", 0),
                "total_catalog_shapes": catalog_data.get("metadata", {}).get("total_records", 0),
                "database_type": "JSON Files",
                "data_folder": self.data_folder,
                "files": ["order_drawings.json", "catalog_shapes.json"]
            }
            return stats
            
        except Exception as e:
            print(f"[DATABASE] Error getting statistics: {e}")
            return {}


def create_iron_database() -> IronDrawingJSONDatabase:
    """
    Factory function to create and initialize the iron drawing JSON database
    
    Returns:
        IronDrawingJSONDatabase instance
    """
    try:
        db = IronDrawingJSONDatabase()
        return db
    except Exception as e:
        print(f"[DATABASE] Failed to create database: {e}")
        return None


if __name__ == "__main__":
    # Test the database creation
    print("="*50)
    print("TESTING IRON DRAWING JSON DATABASE")
    print("="*50)
    
    db = create_iron_database()
    if db:
        stats = db.get_statistics()
        print(f"\nDatabase Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Test inserting a sample order drawing with new structure
        sample_analysis = {
            "ribfinder": {"rib_count": 3},
            "shape_type": "U-shape",
            "sides": [
                {"length": 50, "angle_to_next": 90},
                {"length": 110, "angle_to_next": 90},
                {"length": 50}
            ],
            "pathfinder": {
                "vectors": [
                    {"rib_number": 1, "vector": {"dx": 0, "dy": 50}},
                    {"rib_number": 2, "vector": {"dx": 110, "dy": 0}},
                    {"rib_number": 3, "vector": {"dx": 0, "dy": -50}}
                ]
            }
        }
        
        drawing_id = db.insert_order_drawing(
            order_number="ORD-2024-001",
            file_name="test_u_shape.png",
            analysis_result=sample_analysis
        )
        
        if drawing_id:
            print(f"\n[TEST] Sample order drawing inserted with ID: {drawing_id}")
            print("\nStored Structure:")
            
            # Load and display the inserted record
            drawings = db.get_order_drawings(limit=1)
            if drawings:
                latest = drawings[0]
                print(f"  1. Order Number: {latest.get('order_number')}")
                print(f"  2. File Name: {latest.get('file_name')}")
                print(f"  3. Date: {latest.get('date')}")
                print(f"  4. Number of Ribs: {latest.get('number_of_ribs')}")
                print(f"  5. Straight Rib: {latest.get('straight_rib')}")
                print(f"  6. Shape Explanation: {latest.get('shape_explanation')}")
                print(f"  7. Path Degrees:")
                for pd in latest.get('path_degrees', []):
                    print(f"     Rib {pd['rib_number']}: Length={pd['length']}cm, Degree to next={pd['degree_to_next']}°")
                print(f"  8. Path Vectors:")
                for pv in latest.get('path_vectors', []):
                    print(f"     Rib {pv['rib_number']}: dx={pv['dx']}, dy={pv['dy']}")
                
                # Display catalog compatibility
                catalog = latest.get('compatible_catalog_shape', {})
                if catalog:
                    print(f"  9. Compatible Catalog Shape:")
                    print(f"     Best Match: {catalog.get('best_match_file', 'None')}")
                    print(f"     Similarity: {catalog.get('similarity_score', 0)}%")
                    print(f"     Is Compatible: {catalog.get('is_compatible', False)}")
                    print(f"     Match Quality: {catalog.get('match_quality', 'N/A')}")
        
        # Get updated statistics
        updated_stats = db.get_statistics()
        print(f"\nUpdated Statistics:")
        print(f"  total_order_drawings: {updated_stats.get('total_order_drawings', 0)}")
        
        print("\n[SUCCESS] Database test completed!")
    else:
        print("\n[ERROR] Database test failed!")