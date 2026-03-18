"""Vector storage for semantic knowledge retrieval."""

import hashlib
import json
import logging
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

# Optional dependency handling
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None
    logging.warning("ChromaDB not available. Vector storage disabled.")

from orgclaw.analyzer.extractor import Experience

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Stores and retrieves experiences using vector embeddings.
    
    Falls back to simple JSON storage if ChromaDB is not available.
    """
    
    def __init__(self, persist_dir: Optional[str] = None):
        """Initialize the knowledge store.
        
        Args:
            persist_dir: Directory to persist vector database
        """
        if persist_dir is None:
            persist_dir = str(Path.home() / ".orgclaw" / "vector_store")
        
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = None
        self.collection = None
        self._fallback_storage: List[dict] = []
        
        if CHROMADB_AVAILABLE:
            try:
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
                logger.info("ChromaDB initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize ChromaDB: {e}. Using fallback storage.")
                self.client = None
                self.collection = None
        else:
            logger.info("Using fallback JSON storage (ChromaDB not available)")
    
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
        
        if self.collection:
            # Use ChromaDB
            try:
                self.collection.add(
                    ids=[doc_id],
                    documents=[document],
                    metadatas=[metadata],
                )
            except Exception as e:
                logger.error(f"Failed to add to ChromaDB: {e}")
                # Fallback to JSON
                self._fallback_add(doc_id, metadata)
        else:
            # Fallback storage
            self._fallback_add(doc_id, metadata)
        
        return doc_id
    
    def _fallback_add(self, doc_id: str, metadata: dict):
        """Add to fallback JSON storage."""
        metadata['doc_id'] = doc_id
        self._fallback_storage.append(metadata)
        
        # Persist to file
        try:
            fallback_file = self.persist_dir / "experiences_fallback.json"
            with open(fallback_file, 'w') as f:
                json.dump(self._fallback_storage, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save fallback storage: {e}")
    
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
        if self.collection:
            return self._query_chromadb(query_text, n_results, category, min_quality)
        else:
            return self._query_fallback(query_text, n_results, category, min_quality)
    
    def _query_chromadb(self, query_text, n_results, category, min_quality) -> List[Experience]:
        """Query using ChromaDB."""
        try:
            # Build where clause
            where = {}
            if category:
                where["category"] = category
            if min_quality > 0:
                where["quality_score"] = {"$gte": min_quality}
            
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
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return self._query_fallback(query_text, n_results, category, min_quality)
    
    def _query_fallback(self, query_text, n_results, category, min_quality) -> List[Experience]:
        """Fallback query using simple keyword matching."""
        import re
        
        # Simple keyword matching
        query_words = set(re.findall(r'\w+', query_text.lower()))
        
        results = []
        for item in self._fallback_storage:
            # Check category filter
            if category and item.get('category') != category:
                continue
            
            # Check quality filter
            if item.get('quality_score', 0) < min_quality:
                continue
            
            # Simple text matching
            item_text = item.get('title', '') + ' ' + item.get('category', '')
            item_words = set(re.findall(r'\w+', item_text.lower()))
            
            # Calculate simple overlap score
            overlap = len(query_words & item_words)
            if overlap > 0:
                item['_match_score'] = overlap
                results.append(item)
        
        # Sort by match score and return top n
        results.sort(key=lambda x: x.get('_match_score', 0), reverse=True)
        
        experiences = []
        for item in results[:n_results]:
            exp = self._metadata_to_experience(item)
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
