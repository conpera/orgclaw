"""Vector storage for semantic knowledge retrieval."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from orgclaw.analyzer.extractor import Experience


class KnowledgeStore:
    """Stores and retrieves experiences using vector embeddings."""
    
    def __init__(self, persist_dir: Optional[str] = None):
        """Initialize the knowledge store.
        
        Args:
            persist_dir: Directory to persist vector database
        """
        if persist_dir is None:
            persist_dir = str(Path.home() / ".claw-engine" / "knowledge")
        
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB
        self.client = chromadb.Client(
            Settings(
                persist_directory=str(self.persist_dir),
                anonymized_telemetry=False,
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="experiences",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_experience(self, experience: Experience) -> str:
        """Add an experience to the store.
        
        Args:
            experience: Experience to store
            
        Returns:
            Document ID
        """
        # Generate ID from experience
        doc_id = self._generate_id(experience)
        
        # Prepare document
        document = self._experience_to_text(experience)
        metadata = {
            "id": experience.id,
            "category": experience.category,
            "title": experience.title,
            "quality_score": experience.quality_score,
            "source_task_id": experience.source_task_id or "",
            "json": json.dumps(asdict(experience)),
        }
        
        # Add to collection
        self.collection.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[metadata],
        )
        
        return doc_id
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        category: Optional[str] = None,
        min_quality: float = 0.0,
    ) -> List[Experience]:
        """Query experiences by semantic similarity.
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            category: Filter by category
            min_quality: Minimum quality score
            
        Returns:
            List of matching experiences
        """
        # Build where clause
        where = {}
        if category:
            where["category"] = category
        if min_quality > 0:
            where["quality_score"] = {"$gte": min_quality}
        
        # Query
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where if where else None,
        )
        
        # Convert to Experience objects
        experiences = []
        if results["metadatas"] and results["metadatas"][0]:
            for metadata in results["metadatas"][0]:
                exp = self._metadata_to_experience(metadata)
                if exp:
                    experiences.append(exp)
        
        return experiences
    
    def get_similar_experiences(
        self,
        experience: Experience,
        n_results: int = 3,
    ) -> List[Experience]:
        """Find experiences similar to the given one.
        
        Args:
            experience: Reference experience
            n_results: Number of similar experiences
            
        Returns:
            List of similar experiences
        """
        query = self._experience_to_text(experience)
        return self.query(query, n_results=n_results, category=experience.category)
    
    def delete_experience(self, experience_id: str) -> bool:
        """Delete an experience from the store.
        
        Args:
            experience_id: ID of experience to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            self.collection.delete(ids=[experience_id])
            return True
        except Exception:
            return False
    
    def list_all(self, category: Optional[str] = None) -> List[Experience]:
        """List all experiences.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of all experiences
        """
        where = {"category": category} if category else None
        
        results = self.collection.get(where=where)
        
        experiences = []
        if results["metadatas"]:
            for metadata in results["metadatas"]:
                exp = self._metadata_to_experience(metadata)
                if exp:
                    experiences.append(exp)
        
        return experiences
    
    def _generate_id(self, experience: Experience) -> str:
        """Generate unique ID for experience."""
        content = f"{experience.id}-{experience.title}-{experience.source_task_id}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _experience_to_text(self, experience: Experience) -> str:
        """Convert experience to searchable text."""
        parts = [
            f"Title: {experience.title}",
            f"Category: {experience.category}",
            f"Description: {experience.description}",
        ]
        
        if experience.solution_steps:
            parts.append("Solution Steps:")
            for step in experience.solution_steps:
                parts.append(f"- {step}")
        
        if experience.lessons_learned:
            parts.append("Lessons:")
            for lesson in experience.lessons_learned:
                parts.append(f"- {lesson}")
        
        if experience.applicable_scenarios:
            parts.append("Scenarios:")
            for scenario in experience.applicable_scenarios:
                parts.append(f"- {scenario}")
        
        return "\n".join(parts)
    
    def _metadata_to_experience(self, metadata: dict) -> Optional[Experience]:
        """Convert metadata back to Experience object."""
        try:
            from dataclasses import dataclass, field
            from typing import List, Dict, Any
            import json
            
            # Parse JSON representation
            json_str = metadata.get("json", "{}")
            data = json.loads(json_str)
            
            # Reconstruct CodeChange objects
            code_changes = []
            for cc_data in data.get("code_changes", []):
                from orgclaw.analyzer.extractor import CodeChange
                code_changes.append(CodeChange(**cc_data))
            
            # Reconstruct Experience
            from orgclaw.analyzer.extractor import Experience
            return Experience(
                id=data["id"],
                title=data["title"],
                description=data["description"],
                category=data["category"],
                context=data.get("context", {}),
                code_changes=code_changes,
                solution_steps=data.get("solution_steps", []),
                lessons_learned=data.get("lessons_learned", []),
                applicable_scenarios=data.get("applicable_scenarios", []),
                quality_score=data.get("quality_score", 0.0),
                source_task_id=data.get("source_task_id"),
                created_at=data.get("created_at"),
            )
        except Exception as e:
            print(f"Error converting metadata to experience: {e}")
            return None
