"""OpenClaw Skill integration for OrgClaw."""

import os
from typing import Any, Dict, Optional

from orgclaw.analyzer.extractor import ExperienceExtractor
from orgclaw.analyzer.quality_scorer import ExperienceScorer
from orgclaw.storage.vector_store import KnowledgeStore
from orgclaw.patterns_client import PatternsClient, PatternEnricher


class OrgClawSkill:
    """OpenClaw Skill for experience collection and pattern retrieval."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the OrgClaw Skill.
        
        Args:
            config: Skill configuration
        """
        self.config = config or {}
        
        # Initialize components
        self.extractor = ExperienceExtractor()
        self.scorer = ExperienceScorer()
        self.store = KnowledgeStore()
        self.patterns_client = PatternsClient()
        self.pattern_enricher = PatternEnricher(self.patterns_client)
        
        # Configuration
        self.auto_extract = self.config.get("auto_extract", True)
        self.quality_threshold = self.config.get("quality_threshold", 0.75)
        self.repo_path = self.config.get("repo_path", os.getcwd())
        self.enable_patterns = self.config.get("enable_patterns", True)
    
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
        
        # Enrich with patterns
        result = {
            "experience_id": experience.id,
            "quality_score": score.overall,
            "score_breakdown": {
                "completeness": score.completeness,
                "specificity": score.specificity,
                "actionability": score.actionability,
                "reusability": score.reusability,
            }
        }
        
        # Add related patterns
        if self.enable_patterns:
            try:
                enriched = self.pattern_enricher.enrich_experience(experience)
                result["related_patterns"] = enriched.get("related_patterns", [])
            except Exception as e:
                # Don't fail if patterns can't be fetched
                result["patterns_error"] = str(e)
        
        # Store if quality is good enough
        if score.overall >= self.quality_threshold:
            doc_id = self.store.add_experience(experience)
            result["stored"] = True
            result["doc_id"] = doc_id
        else:
            # Return suggestions for improvement
            suggestions = self.scorer.get_improvement_suggestions(experience)
            result["stored"] = False
            result["suggestions"] = suggestions
        
        return result
    
    def on_agent_spawn(self, spawn_context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook called before spawning an Agent.
        
        Args:
            spawn_context: Context for spawning agent
            
        Returns:
            Enriched context with relevant experiences and patterns
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
        
        # Add relevant patterns
        if self.enable_patterns:
            try:
                # Search patterns by keywords in task description
                keywords = self._extract_keywords(task_description)
                patterns = []
                
                for keyword in keywords:
                    tag_patterns = self.patterns_client.search_by_tag(keyword)
                    patterns.extend(tag_patterns)
                
                # Deduplicate and limit
                seen = set()
                unique_patterns = []
                for p in patterns:
                    if p.id not in seen and len(unique_patterns) < 5:
                        seen.add(p.id)
                        unique_patterns.append(p)
                
                if unique_patterns:
                    spawn_context["relevant_patterns"] = [
                        {
                            "id": p.id,
                            "title": p.title,
                            "category": p.category,
                            "url": p.source_url,
                        }
                        for p in unique_patterns
                    ]
            except Exception:
                pass  # Fail silently
        
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
    
    def query_patterns(
        self,
        query: str,
        category: Optional[str] = None,
    ) -> list:
        """Query conpera-patterns.
        
        Args:
            query: Search query (tag or category)
            category: Pattern category filter
            
        Returns:
            List of matching patterns
        """
        if category:
            patterns = self.patterns_client.search_by_category(category)
        else:
            patterns = self.patterns_client.search_by_tag(query)
        
        return [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "status": p.status,
                "url": p.source_url,
            }
            for p in patterns
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
    
    def _extract_keywords(self, text: str) -> list:
        """Extract keywords from text."""
        keywords = []
        keyword_map = {
            "api": ["api", "rest", "http"],
            "testing": ["test", "pytest", "unit"],
            "deployment": ["deploy", "release", "ci/cd"],
            "error": ["error", "exception", "handling"],
            "database": ["database", "sql", "postgres"],
            "microservice": ["microservice", "service", "distributed"],
            "architecture": ["architecture", "design", "pattern"],
        }
        
        text_lower = text.lower()
        for category, words in keyword_map.items():
            if any(word in text_lower for word in words):
                keywords.append(category)
        
        return keywords
