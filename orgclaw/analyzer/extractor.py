"""Experience extraction from Agent task results."""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path

import git


@dataclass
class CodeChange:
    """Represents a code change in a task."""
    file_path: str
    change_type: str  # added, modified, deleted
    diff_content: str
    language: str
    complexity_score: float = 0.0


@dataclass
class Experience:
    """Extracted experience from a task."""
    id: str
    title: str
    description: str
    category: str  # bug_fix, feature, refactor, optimization
    context: Dict[str, Any] = field(default_factory=dict)
    code_changes: List[CodeChange] = field(default_factory=list)
    solution_steps: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    applicable_scenarios: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    source_task_id: Optional[str] = None
    created_at: Optional[str] = None


class ExperienceExtractor:
    """Extracts reusable experience from Agent task execution."""
    
    PATTERN_DETECTORS = {
        "bug_fix": r"fix|bug|error|exception|crash",
        "refactor": r"refactor|cleanup|extract|rename",
        "optimization": r"optimize|performance|speed|memory",
        "feature": r"feat|feature|add|implement",
    }
    
    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path) if repo_path else None
    
    def extract_from_task(
        self,
        task_id: str,
        task_description: str,
        commit_hash: Optional[str] = None
    ) -> Optional[Experience]:
        """Extract experience from a completed task.
        
        Args:
            task_id: Unique task identifier
            task_description: What the task was about
            commit_hash: Git commit hash if available
            
        Returns:
            Extracted Experience or None if extraction failed
        """
        # Determine category from description
        category = self._detect_category(task_description)
        
        # Get code changes
        code_changes = []
        if commit_hash and self.repo:
            code_changes = self._extract_code_changes(commit_hash)
        
        # Extract solution pattern
        solution_steps = self._extract_solution_steps(task_description)
        
        # Generate lessons learned
        lessons = self._generate_lessons(code_changes, category)
        
        # Build applicable scenarios
        scenarios = self._build_scenarios(category, code_changes)
        
        experience = Experience(
            id=f"exp-{task_id}",
            title=self._generate_title(task_description, category),
            description=task_description,
            category=category,
            context={
                "task_id": task_id,
                "commit_hash": commit_hash,
            },
            code_changes=code_changes,
            solution_steps=solution_steps,
            lessons_learned=lessons,
            applicable_scenarios=scenarios,
            source_task_id=task_id,
        )
        
        return experience
    
    def _detect_category(self, description: str) -> str:
        """Detect experience category from description."""
        description_lower = description.lower()
        
        for category, pattern in self.PATTERN_DETECTORS.items():
            if re.search(pattern, description_lower):
                return category
        
        return "general"
    
    def _extract_code_changes(self, commit_hash: str) -> List[CodeChange]:
        """Extract code changes from a git commit."""
        changes = []
        
        try:
            commit = self.repo.commit(commit_hash)
            
            for diff_item in commit.diff(commit.parents[0] if commit.parents else git.NULL_TREE):
                change_type = "modified"
                if diff_item.new_file:
                    change_type = "added"
                elif diff_item.deleted_file:
                    change_type = "deleted"
                
                # Detect language from file extension
                language = self._detect_language(diff_item.a_path or diff_item.b_path)
                
                change = CodeChange(
                    file_path=diff_item.a_path or diff_item.b_path,
                    change_type=change_type,
                    diff_content=diff_item.diff.decode('utf-8', errors='ignore') if diff_item.diff else "",
                    language=language,
                    complexity_score=self._calculate_complexity(diff_item),
                )
                changes.append(change)
                
        except Exception as e:
            print(f"Error extracting code changes: {e}")
        
        return changes
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file path."""
        extension_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".md": "markdown",
        }
        
        ext = Path(file_path).suffix.lower()
        return extension_map.get(ext, "unknown")
    
    def _calculate_complexity(self, diff_item) -> float:
        """Calculate complexity score of a change."""
        if not diff_item.diff:
            return 0.0
        
        diff_text = diff_item.diff.decode('utf-8', errors='ignore')
        
        # Simple heuristic: lines changed + nesting depth
        lines = diff_text.count('\n')
        nesting = diff_text.count('{') + diff_text.count('(')
        
        return min((lines + nesting * 0.5) / 10, 10.0)
    
    def _extract_solution_steps(self, description: str) -> List[str]:
        """Extract solution steps from task description."""
        # Look for numbered lists or step indicators
        steps = []
        
        # Match patterns like "1. Step one", "Step 1: Do something"
        step_patterns = [
            r'\d+\.\s*(.+?)(?=\n\d+\.|$)',
            r'Step\s+\d+:?\s*(.+?)(?=Step|$)',
        ]
        
        for pattern in step_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.DOTALL)
            steps.extend([s.strip() for s in matches if s.strip()])
        
        return steps if steps else ["Task completed successfully"]
    
    def _generate_lessons(self, code_changes: List[CodeChange], category: str) -> List[str]:
        """Generate lessons learned from changes."""
        lessons = []
        
        if category == "bug_fix":
            lessons.append("Always add regression tests for bug fixes")
        
        if any(c.language == "python" for c in code_changes):
            lessons.append("Follow PEP 8 style guidelines")
        
        if len(code_changes) > 5:
            lessons.append("Consider breaking large changes into smaller PRs")
        
        return lessons
    
    def _build_scenarios(self, category: str, code_changes: List[CodeChange]) -> List[str]:
        """Build applicable scenarios for this experience."""
        scenarios = []
        
        languages = {c.language for c in code_changes}
        
        if category == "bug_fix":
            scenarios.append("Similar error patterns in same codebase")
        elif category == "refactor":
            scenarios.append("Code cleanup and maintenance tasks")
        elif category == "optimization":
            scenarios.append("Performance improvement initiatives")
        
        for lang in languages:
            scenarios.append(f"{lang.capitalize()} projects")
        
        return scenarios
    
    def _generate_title(self, description: str, category: str) -> str:
        """Generate a concise title for the experience."""
        # Take first sentence or first 10 words
        first_part = description.split('.')[0] if '.' in description else description
        words = first_part.split()[:10]
        title = ' '.join(words)
        
        # Add category prefix
        return f"[{category.upper()}] {title}"
