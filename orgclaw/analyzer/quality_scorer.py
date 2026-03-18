"""Quality scoring for extracted experiences."""

from dataclasses import dataclass
from typing import List

from orgclaw.analyzer.extractor import Experience


@dataclass
class ScoreBreakdown:
    """Detailed scoring breakdown."""
    completeness: float  # 0-1
    specificity: float   # 0-1
    actionability: float # 0-1
    reusability: float   # 0-1
    overall: float       # 0-1


class ExperienceScorer:
    """Scores the quality of extracted experiences."""
    
    def __init__(self):
        self.weights = {
            "completeness": 0.25,
            "specificity": 0.25,
            "actionability": 0.25,
            "reusability": 0.25,
        }
    
    def score(self, experience: Experience) -> ScoreBreakdown:
        """Calculate quality score for an experience.
        
        Returns:
            ScoreBreakdown with detailed scores
        """
        completeness = self._score_completeness(experience)
        specificity = self._score_specificity(experience)
        actionability = self._score_actionability(experience)
        reusability = self._score_reusability(experience)
        
        overall = (
            completeness * self.weights["completeness"] +
            specificity * self.weights["specificity"] +
            actionability * self.weights["actionability"] +
            reusability * self.weights["reusability"]
        )
        
        return ScoreBreakdown(
            completeness=completeness,
            specificity=specificity,
            actionability=actionability,
            reusability=reusability,
            overall=overall,
        )
    
    def _score_completeness(self, exp: Experience) -> float:
        """Score based on how complete the experience is."""
        score = 0.0
        
        # Has description
        if exp.description and len(exp.description) > 50:
            score += 0.2
        
        # Has solution steps
        if len(exp.solution_steps) >= 2:
            score += 0.2
        
        # Has lessons learned
        if len(exp.lessons_learned) > 0:
            score += 0.2
        
        # Has applicable scenarios
        if len(exp.applicable_scenarios) > 0:
            score += 0.2
        
        # Has code changes (if applicable)
        if exp.code_changes:
            score += 0.2
        
        return min(score, 1.0)
    
    def _score_specificity(self, exp: Experience) -> float:
        """Score based on how specific the experience is."""
        score = 0.0
        
        # Description has specific details
        desc = exp.description.lower()
        specific_terms = ["error", "exception", "function", "method", "class", "file"]
        matches = sum(1 for term in specific_terms if term in desc)
        score += min(matches / 3, 0.4)
        
        # Has concrete code changes
        if exp.code_changes:
            avg_complexity = sum(c.complexity_score for c in exp.code_changes) / len(exp.code_changes)
            score += min(avg_complexity / 10, 0.3)
        
        # Specific category (not "general")
        if exp.category != "general":
            score += 0.3
        
        return min(score, 1.0)
    
    def _score_actionability(self, exp: Experience) -> float:
        """Score based on how actionable the experience is."""
        score = 0.0
        
        # Has clear steps
        if len(exp.solution_steps) >= 3:
            score += 0.4
        elif len(exp.solution_steps) >= 1:
            score += 0.2
        
        # Steps are concrete (contain verbs)
        action_verbs = ["add", "remove", "fix", "update", "create", "delete", "refactor"]
        for step in exp.solution_steps:
            if any(verb in step.lower() for verb in action_verbs):
                score += 0.1
                break
        
        # Has lessons that guide future actions
        if len(exp.lessons_learned) >= 2:
            score += 0.3
        elif len(exp.lessons_learned) >= 1:
            score += 0.15
        
        return min(score, 1.0)
    
    def _score_reusability(self, exp: Experience) -> float:
        """Score based on how reusable the experience is."""
        score = 0.0
        
        # Multiple applicable scenarios
        if len(exp.applicable_scenarios) >= 3:
            score += 0.3
        elif len(exp.applicable_scenarios) >= 1:
            score += 0.15
        
        # Not too specific to one file/location
        if exp.code_changes:
            unique_dirs = set()
            for change in exp.code_changes:
                parts = change.file_path.split('/')
                if len(parts) > 1:
                    unique_dirs.add(parts[0])
            
            if len(unique_dirs) > 1:
                score += 0.3  # Applies to multiple directories
            else:
                score += 0.15
        
        # General patterns in solution steps
        general_patterns = ["always", "never", "consider", "typically", "usually"]
        for step in exp.solution_steps:
            if any(pattern in step.lower() for pattern in general_patterns):
                score += 0.2
                break
        
        # Category is reusable
        reusable_categories = ["bug_fix", "refactor", "optimization"]
        if exp.category in reusable_categories:
            score += 0.2
        
        return min(score, 1.0)
    
    def should_promote_to_pattern(self, exp: Experience, threshold: float = 0.75) -> bool:
        """Determine if experience should be promoted to verified pattern.
        
        Args:
            exp: Experience to evaluate
            threshold: Minimum score to promote
            
        Returns:
            True if should be promoted
        """
        score = self.score(exp)
        return score.overall >= threshold
    
    def get_improvement_suggestions(self, exp: Experience) -> List[str]:
        """Get suggestions for improving the experience."""
        score = self.score(exp)
        suggestions = []
        
        if score.completeness < 0.6:
            suggestions.append("Add more details: solution steps, lessons learned, or applicable scenarios")
        
        if score.specificity < 0.6:
            suggestions.append("Include more specific technical terms, function names, or file paths")
        
        if score.actionability < 0.6:
            suggestions.append("Make solution steps more concrete with clear actions")
        
        if score.reusability < 0.6:
            suggestions.append("Identify more scenarios where this experience applies")
        
        return suggestions
