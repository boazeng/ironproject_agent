import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from data.json_database import IronDrawingJSONDatabase

class DataOutputAgent:
    """
    Agent responsible for organizing analysis results and storing them in the database.
    Takes raw analysis data from all agents and structures it according to database requirements.
    """
    
    def __init__(self, db_path: str = "data"):
        """
        Initialize the DataOutput agent
        
        Args:
            db_path: Path to the database folder
        """
        self.db_path = db_path
        self.db = None
        self._initialize_database()
        print("[DATAOUTPUT] Agent initialized - Database storage specialist")
    
    def _initialize_database(self):
        """Initialize database connection"""
        try:
            # Initialize the JSON database
            self.db = IronDrawingJSONDatabase(self.db_path)
            print("[DATAOUTPUT] Database connection established")
        except Exception as e:
            print(f"[DATAOUTPUT] Error initializing database: {e}")
    
    def process_and_store(self, order_number: str, file_name: str, analysis_results: Dict) -> Dict:
        """
        Main method to process analysis results and store in database
        
        Args:
            order_number: Order number for the drawing
            file_name: Name of the analyzed drawing file
            analysis_results: Complete analysis results from all agents
            
        Returns:
            Dictionary with storage status and organized data
        """
        try:
            print(f"[DATAOUTPUT] Processing results for Order: {order_number}, File: {file_name}")
            
            # Step 1: Extract and organize data
            organized_data = self._organize_data(analysis_results)
            print("[DATAOUTPUT] Data organized according to database structure")
            
            # Step 2: Validate data completeness
            validation_result = self._validate_data(organized_data)
            if not validation_result["valid"]:
                print(f"[DATAOUTPUT] Data validation failed: {validation_result['message']}")
                return {
                    "status": "validation_failed",
                    "message": validation_result["message"],
                    "data": organized_data
                }
            
            # Step 3: Store in database
            if self.db:
                record_id = self.db.insert_order_drawing(
                    order_number=order_number,
                    file_name=file_name,
                    analysis_result=analysis_results
                )
                
                if record_id:
                    print(f"[DATAOUTPUT] Data stored successfully with ID: {record_id}")
                    return {
                        "status": "success",
                        "record_id": record_id,
                        "order_number": order_number,
                        "file_name": file_name,
                        "data": organized_data,
                        "message": "Analysis results stored in database"
                    }
                else:
                    print("[DATAOUTPUT] Failed to store data in database")
                    return {
                        "status": "storage_failed",
                        "message": "Database storage failed",
                        "data": organized_data
                    }
            else:
                print("[DATAOUTPUT] No database connection")
                return {
                    "status": "no_database",
                    "message": "Database not initialized",
                    "data": organized_data
                }
                
        except Exception as e:
            print(f"[DATAOUTPUT] Error processing data: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {}
            }
    
    def _organize_data(self, analysis_results: Dict) -> Dict:
        """
        Organize raw analysis data into required database structure
        
        Args:
            analysis_results: Raw analysis results from all agents
            
        Returns:
            Organized data dictionary
        """
        try:
            # Extract data from different agents
            ribfinder_data = analysis_results.get("ribfinder", {})
            chatan_data = analysis_results
            pathfinder_data = analysis_results.get("pathfinder", {})
            chatco_data = analysis_results.get("comparison", {})
            
            # Get number of ribs
            rib_count = ribfinder_data.get("rib_count", 0)
            
            # Determine if all ribs are straight
            all_straight = self._determine_if_straight(pathfinder_data)
            
            # Get shape explanation
            shape_type = chatan_data.get("shape_type", "")
            shape_explanation = self._get_shape_explanation(shape_type, rib_count, chatan_data)
            
            # Extract path degrees (lengths and angles)
            path_degrees = self._extract_path_degrees(chatan_data)
            
            # Extract path vectors
            path_vectors = self._extract_path_vectors(pathfinder_data)
            
            # Extract catalog compatibility information
            catalog_compatibility = self._extract_catalog_compatibility(chatco_data)
            
            # Build organized structure
            organized = {
                "number_of_ribs": rib_count,
                "straight_rib": all_straight,
                "shape_explanation": shape_explanation,
                "path_degrees": path_degrees,
                "path_vectors": path_vectors,
                "compatible_catalog_shape": catalog_compatibility,
                
                # Additional metadata
                "confidence_scores": {
                    "ribfinder": ribfinder_data.get("confidence", 0),
                    "chatan": chatan_data.get("confidence", 0),
                    "match_percentage": chatan_data.get("match_percentage", 0)
                },
                "shape_type": shape_type
            }
            
            return organized
            
        except Exception as e:
            print(f"[DATAOUTPUT] Error organizing data: {e}")
            return {}
    
    def _determine_if_straight(self, pathfinder_data: Dict) -> bool:
        """
        Determine if all ribs are straight based on PathFinder data
        
        Args:
            pathfinder_data: PathFinder analysis results
            
        Returns:
            True if all ribs are straight, False otherwise
        """
        # For now, assume all ribs are straight if we have valid vectors
        # Could be enhanced with curvature detection
        vectors = pathfinder_data.get("vectors", [])
        return len(vectors) > 0
    
    def _get_shape_explanation(self, shape_type: str, rib_count: int, chatan_data: Dict) -> str:
        """
        Generate shape explanation based on shape characteristics
        
        Args:
            shape_type: Type of shape
            rib_count: Number of ribs
            chatan_data: CHATAN analysis data
            
        Returns:
            Shape explanation string
        """
        shape_type_lower = shape_type.lower()
        
        if rib_count == 1:
            return "a. Straight rib"
        elif rib_count == 2:
            return "b. L rib with rotation"
        elif rib_count == 3:
            if "u" in shape_type_lower:
                # Check if sides are equal or different
                sides = chatan_data.get("sides", [])
                if len(sides) >= 3:
                    first_length = sides[0].get("length", 0)
                    last_length = sides[-1].get("length", 0)
                    if abs(first_length - last_length) < 5:  # Within 5cm tolerance
                        return "c. Rib with equal side rib with rotation"
                    else:
                        return "d. U rib with different side rib length with rotation"
                return "d. U rib with different side rib length with rotation"
            else:
                return "c. Rib with equal side rib with rotation"
        else:
            return f"Complex shape with {rib_count} ribs"
    
    def _extract_path_degrees(self, chatan_data: Dict) -> List[Dict]:
        """
        Extract path degrees (length and angle for each rib)
        
        Args:
            chatan_data: CHATAN analysis data
            
        Returns:
            List of path degree dictionaries
        """
        path_degrees = []
        sides = chatan_data.get("sides", [])
        
        for i, side in enumerate(sides):
            rib_info = {
                "rib_number": i + 1,
                "length": side.get("length", 0),
                "degree_to_next": side.get("angle_to_next", 0) if i < len(sides) - 1 else None
            }
            path_degrees.append(rib_info)
        
        return path_degrees
    
    def _extract_path_vectors(self, pathfinder_data: Dict) -> List[Dict]:
        """
        Extract path vectors (dx, dy for each rib)
        
        Args:
            pathfinder_data: PathFinder analysis data
            
        Returns:
            List of path vector dictionaries
        """
        path_vectors = []
        vectors = pathfinder_data.get("vectors", [])
        
        for vec in vectors:
            vector_info = {
                "rib_number": vec.get("rib_number", 0),
                "dx": round(vec.get("vector", {}).get("dx", 0), 2),
                "dy": round(vec.get("vector", {}).get("dy", 0), 2)
            }
            path_vectors.append(vector_info)
        
        return path_vectors
    
    def _extract_catalog_compatibility(self, chatco_data: Dict) -> Dict:
        """
        Extract catalog compatibility information from CHATCO results
        
        Args:
            chatco_data: CHATCO comparison data
            
        Returns:
            Catalog compatibility dictionary
        """
        similarity_score = chatco_data.get("similarity_score", 0)
        
        catalog_compatibility = {
            "best_match_file": chatco_data.get("best_match_file", ""),
            "similarity_score": similarity_score,
            "match_quality": chatco_data.get("match_quality", ""),
            "is_compatible": similarity_score >= 70,  # 70% or higher considered compatible
            "differences": chatco_data.get("differences", []),
            "matching_features": chatco_data.get("matching_features", [])
        }
        
        return catalog_compatibility
    
    def _validate_data(self, organized_data: Dict) -> Dict:
        """
        Validate that organized data has all required fields
        
        Args:
            organized_data: Organized data dictionary
            
        Returns:
            Validation result dictionary
        """
        required_fields = [
            "number_of_ribs",
            "straight_rib",
            "shape_explanation",
            "path_degrees",
            "path_vectors",
            "compatible_catalog_shape"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in organized_data or organized_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }
        
        # Validate rib count matches data
        rib_count = organized_data["number_of_ribs"]
        path_degrees = organized_data["path_degrees"]
        path_vectors = organized_data["path_vectors"]
        
        if len(path_degrees) != rib_count:
            return {
                "valid": False,
                "message": f"Path degrees count ({len(path_degrees)}) doesn't match rib count ({rib_count})"
            }
        
        if len(path_vectors) != rib_count:
            return {
                "valid": False,
                "message": f"Path vectors count ({len(path_vectors)}) doesn't match rib count ({rib_count})"
            }
        
        return {"valid": True, "message": "Data validation successful"}
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        if self.db:
            return self.db.get_statistics()
        return {"error": "Database not initialized"}
    
    def get_recent_orders(self, limit: int = 10) -> List[Dict]:
        """Get recent order drawings from database"""
        if self.db:
            return self.db.get_order_drawings(limit)
        return []


def create_dataoutput_agent(db_path: str = "data") -> DataOutputAgent:
    """
    Factory function to create a DataOutput agent
    
    Args:
        db_path: Path to the database folder
        
    Returns:
        DataOutputAgent instance
    """
    return DataOutputAgent(db_path)


if __name__ == "__main__":
    # Test the DataOutput agent
    print("="*50)
    print("TESTING DATAOUTPUT AGENT")
    print("="*50)
    
    # Create agent
    agent = create_dataoutput_agent()
    
    # Sample analysis results (simulating output from other agents)
    sample_results = {
        "ribfinder": {
            "rib_count": 3,
            "shape_pattern": "vertical-horizontal-vertical",
            "confidence": 100,
            "match_percentage": 100
        },
        "shape_type": "U-shape",
        "number_of_ribs": 3,
        "confidence": 100,
        "match_percentage": 100,
        "sides": [
            {"length": 50, "angle_to_next": 90, "description": "left vertical leg"},
            {"length": 110, "angle_to_next": 90, "description": "horizontal base"},
            {"length": 50, "angle_to_next": None, "description": "right vertical leg"}
        ],
        "pathfinder": {
            "shape_type": "U-shape",
            "vectors": [
                {"rib_number": 1, "vector": {"dx": 0, "dy": 50}},
                {"rib_number": 2, "vector": {"dx": 110, "dy": 0}},
                {"rib_number": 3, "vector": {"dx": 0, "dy": -50}}
            ]
        },
        "comparison": {
            "best_match_file": "shape_000.png",
            "similarity_score": 40,
            "match_quality": "POOR"
        }
    }
    
    # Process and store
    result = agent.process_and_store(
        order_number="TEST-ORDER-001",
        file_name="test_drawing.png",
        analysis_results=sample_results
    )
    
    print(f"\n[TEST] Storage Result: {result['status']}")
    if result['status'] == 'success':
        print(f"[TEST] Record ID: {result['record_id']}")
        print(f"\n[TEST] Organized Data Structure:")
        data = result['data']
        print(f"  Number of Ribs: {data['number_of_ribs']}")
        print(f"  Straight Rib: {data['straight_rib']}")
        print(f"  Shape Explanation: {data['shape_explanation']}")
        print(f"  Path Degrees: {len(data['path_degrees'])} ribs")
        print(f"  Path Vectors: {len(data['path_vectors'])} vectors")
    
    # Get statistics
    stats = agent.get_statistics()
    print(f"\n[TEST] Database Statistics:")
    print(f"  Total Order Drawings: {stats.get('total_order_drawings', 0)}")
    
    print("\n[SUCCESS] DataOutput agent test completed!")