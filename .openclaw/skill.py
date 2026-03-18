"""OpenClaw Skill integration for Claw Engine."""

import os
from typing import Any, Dict, Optional

from orgclaw.engine.analyzer.extractor import ExperienceExtractor
from orgclaw.engine.analyzer.quality_scorer import ExperienceScorer
from orgclaw.engine.storage.vector_store import KnowledgeStore


class ClawSkill:
    """OpenClaw Skill for experience collection and retrieval."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Claw Skill.
        
        Args:
            config: Skill configuration
        """
        self.config = config or {}
        
        # Initialize components
        self.extractor = ExperienceExtractor()
        self.scorer = ExperienceScorer()
        self.store = KnowledgeStore()
        
        # Configuration
        self.auto_extract = self.config.get("auto_extract", True)
        self.quality_threshold = self.config.get("quality_threshold", 0.75)
        self.repo_path = self.config.get("repo_path", os.getcwd())
    
    def on_task_complete(self, task_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Hook called when an Agent task completes.
        
        Args:
            task_result: Task execution result
            
        Returns:
            Processing result or None
        """
        if not self.auto_extract:
            return None
        
        task_id = task_result.get("task_id")
        description = task_result.get("description", "")
        commit_hash = task_result.get("commit_hash")
        
        if not task_id or not description:
            return None
        
        # Extract experience
        experience = self.extractor.extract_from_task(
            task_id=task_id,
            task_description=description,
            commit_hash=commit_hash,
        )
        
        if not experience:
            return None
        
        # Score the experience
        score = self.scorer.score(experience)
        experience.quality_score = score.overall
        
        # Store if quality is good enough
        if score.overall >= self.quality_threshold:
            doc_id = self.store.add_experience(experience)
            
            return {
                "experience_id": experience.id,
                "quality_score": score.overall,
                "stored": True,
                "doc_id": doc_id,
            }
        else:
            # Return suggestions for improvement
            suggestions = self.scorer.get_improvement_suggestions(experience)
            return {
                "experience_id": experience.id,
                "quality_score": score.overall,
                "stored": False,
                "suggestions": suggestions,
            }
    
    def on_agent_spawn(self, spawn_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called before spawning an Agent.
        
        Args:
            spawn_context: Context for spawning agent
            
        Returns:
            Enriched context with relevant experiences
        """
        task_description = spawn_context.get("description", "")
        repo_path = spawn_context.get("repo_path", self.repo_path)
        
        # Query relevant experiences
        relevant = self.store.query(
            query_text=task_description,
            n_results=5,
            min_quality=0.6,
        )
        
        if relevant:
            spawn_context["relevant_experiences"] = [
                {
                    "id": exp.id,
                    "title": exp.title,
                    "category": exp.category,
                    "lessons": exp.lessons_learned,
                    "scenarios": exp.applicable_scenarios,
                }
                for exp in relevant
            ]
        
        return spawn_context
    
    def query_knowledge(
        self,
        query: str,
        category: Optional[str] = None,
        n_results: int = 5,
    ) -> list:
        """Query the knowledge base.
        
        Args:
            query: Query text
            category: Optional category filter
            n_results: Number of results
            
        Returns:
            List of matching experiences
        """
        experiences = self.store.query(
            query_text=query,
            n_results=n_results,
            category=category,
        )
        
        return [
            {
                "id": exp.id,
                "title": exp.title,
                "category": exp.category,
                "description": exp.description,
                "lessons": exp.lessons_learned,
                "quality_score": exp.quality_score,
            }
            for exp in experiences
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base.
        
        Returns:
            Statistics dictionary
        """
        all_exp = self.store.list_all()
        
        categories = {}
        for exp in all_exp:
            categories[exp.category] = categories.get(exp.category, 0) + 1
        
        avg_quality = sum(e.quality_score for e in all_exp) / len(all_exp) if all_exp else 0
        
        return {
            "total_experiences": len(all_exp),
            "categories": categories,
            "average_quality": round(avg_quality, 2),
        }
