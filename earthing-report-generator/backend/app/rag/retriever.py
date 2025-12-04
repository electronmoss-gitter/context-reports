"""
Retriever - Search historical reports and retrieve relevant context
"""
from typing import List, Dict, Optional
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore
import os

class Retriever:
    """
    Retrieve relevant context from historical reports based on project data
    """
    
    def __init__(self):
        """Initialize retriever with embedder and vector store"""
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        
        # Configuration
        self.top_k = int(os.getenv("TOP_K_RESULTS", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    def retrieve(
        self,
        query: str,
        project_metadata: Optional[Dict] = None,
        n_results: int = None,
        section_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: Search query (e.g., "touch potential calculations for 33kV substation")
            project_metadata: Optional project metadata for filtering
            n_results: Number of results to return (default: self.top_k)
            section_type: Optional filter by section type
            
        Returns:
            List of relevant chunks with similarity scores
        """
        if n_results is None:
            n_results = self.top_k
        
        # Generate query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Build metadata filter
        filter_metadata = {}
        if project_metadata:
            # Filter by matching project characteristics
            if "project_type" in project_metadata:
                filter_metadata["project_type"] = project_metadata["project_type"]
            if "voltage_level" in project_metadata:
                filter_metadata["voltage_level"] = project_metadata["voltage_level"]
        
        if section_type:
            filter_metadata["section_type"] = section_type
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=n_results * 2,  # Get more results to filter by threshold
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        # Filter by similarity threshold
        filtered_results = [
            r for r in results
            if r["similarity_score"] >= self.similarity_threshold
        ]
        
        # Take top n_results
        return filtered_results[:n_results]
    
    def retrieve_by_project_type(
        self,
        project_data: Dict,
        section_types: Optional[List[str]] = None
    ) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant examples for each section of the report
        
        Args:
            project_data: Project input data
            section_types: List of section types to retrieve (default: all major sections)
            
        Returns:
            Dict mapping section_type to list of relevant chunks
        """
        if section_types is None:
            section_types = [
                "executive_summary",
                "site_description",
                "soil_resistivity",
                "earthing_design",
                "calculations",
                "touch_step",
                "compliance",
                "recommendations"
            ]
        
        # Extract project characteristics for filtering
        project_metadata = {
            "project_type": project_data.get("project_type", "general"),
            "voltage_level": self._extract_voltage_level(project_data.get("voltage_level", ""))
        }
        
        results_by_section = {}
        
        for section_type in section_types:
            # Create section-specific query
            query = self._create_section_query(section_type, project_data)
            
            # Retrieve relevant chunks
            chunks = self.retrieve(
                query=query,
                project_metadata=project_metadata,
                section_type=section_type,
                n_results=3  # Get top 3 examples per section
            )
            
            results_by_section[section_type] = chunks
        
        return results_by_section
    
    def retrieve_similar_projects(
        self,
        project_data: Dict,
        n_results: int = 5
    ) -> List[Dict]:
        """
        Find similar complete projects based on characteristics
        
        Args:
            project_data: Project input data
            n_results: Number of similar projects to find
            
        Returns:
            List of similar project chunks
        """
        # Create query from project characteristics
        query_parts = []
        
        if "project_type" in project_data:
            query_parts.append(project_data["project_type"])
        if "voltage_level" in project_data:
            query_parts.append(f"{project_data['voltage_level']} voltage")
        if "fault_current_symmetrical" in project_data:
            query_parts.append(f"{project_data['fault_current_symmetrical']}kA fault current")
        
        query = " ".join(query_parts)
        
        # Retrieve with project metadata filter
        project_metadata = {
            "project_type": project_data.get("project_type", "general"),
            "voltage_level": self._extract_voltage_level(project_data.get("voltage_level", ""))
        }
        
        return self.retrieve(
            query=query,
            project_metadata=project_metadata,
            n_results=n_results
        )
    
    def _create_section_query(self, section_type: str, project_data: Dict) -> str:
        """Create a search query for a specific section"""
        voltage = project_data.get("voltage_level", "")
        project_type = project_data.get("project_type", "")
        
        queries = {
            "executive_summary": f"executive summary for {voltage} {project_type} earthing study",
            "site_description": f"site description {project_type} electrical installation",
            "soil_resistivity": f"soil resistivity measurements analysis Wenner method",
            "earthing_design": f"earthing grid design {voltage} earth electrode system",
            "calculations": f"earth resistance touch step potential calculations {voltage}",
            "touch_step": f"touch potential step potential safety analysis IEEE 80",
            "compliance": f"compliance AS/NZS 3000 IEEE 80 earthing standards",
            "recommendations": f"earthing system recommendations maintenance testing"
        }
        
        return queries.get(section_type, section_type)
    
    def _extract_voltage_level(self, voltage_str: str) -> str:
        """Extract voltage level category from voltage string"""
        if not voltage_str:
            return "unknown"
        
        # Extract numeric value
        import re
        match = re.search(r'(\d+)', voltage_str)
        if not match:
            return "unknown"
        
        voltage = int(match.group(1))
        
        if voltage <= 1:
            return "LV"
        elif voltage <= 66:
            return "HV"
        else:
            return "EHV"
    
    def is_ready(self) -> bool:
        """Check if retriever is ready (vector store has data)"""
        stats = self.vector_store.get_stats()
        return stats.get("total_chunks", 0) > 0


if __name__ == "__main__":
    # Test the retriever
    retriever = Retriever()
    
    # Test simple retrieval
    results = retriever.retrieve("soil resistivity measurement methods")
    print(f"Found {len(results)} results")
    for r in results:
        print(f"- Score: {r['similarity_score']:.3f}")
        print(f"  {r['text'][:100]}...")
    
    # Test project-based retrieval
    test_project = {
        "project_type": "substation",
        "voltage_level": "33kV",
        "fault_current_symmetrical": 25.0
    }
    
    section_results = retriever.retrieve_by_project_type(test_project)
    print(f"\nRetrieved examples for {len(section_results)} sections")
    for section, chunks in section_results.items():
        print(f"- {section}: {len(chunks)} chunks")