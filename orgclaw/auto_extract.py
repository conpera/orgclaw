"""Automatic experience extraction hooks."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from orgclaw.analyzer.extractor import ExperienceExtractor
from orgclaw.analyzer.quality_scorer import ExperienceScorer


class AutoExtractor:
    """Automatically extract experience from Agent tasks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("auto_extract", True)
        self.threshold = self.config.get("quality_threshold", 0.4)
        self.min_lines = self.config.get("min_lines_changed", 5)
        self.personal_dir = Path(self.config.get("personal_dir", "~/.orgclaw/personal")).expanduser()
        
        self.extractor = ExperienceExtractor()
        self.scorer = ExperienceScorer()
        
        # Ensure personal directory exists
        self.personal_dir.mkdir(parents=True, exist_ok=True)
    
    def on_task_complete(self, task_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Hook called when an Agent task completes.
        
        Args:
            task_info: {
                "task_id": str,
                "description": str,
                "repo_path": str,
                "commit_hash": Optional[str],
                "files_changed": List[str],
                "lines_added": int,
                "lines_removed": int,
            }
        
        Returns:
            Extraction result or None if skipped
        """
        if not self.enabled:
            return None
        
        # Skip if too small
        total_lines = task_info.get("lines_added", 0) + task_info.get("lines_removed", 0)
        if total_lines < self.min_lines:
            return None
        
        # Skip if no description
        description = task_info.get("description", "").strip()
        if not description or len(description) < 10:
            return None
        
        # Extract experience
        experience = self.extractor.extract_from_task(
            task_id=task_info["task_id"],
            task_description=description,
            commit_hash=task_info.get("commit_hash"),
        )
        
        if not experience:
            return None
        
        # Score
        score = self.scorer.score(experience)
        experience.quality_score = score.overall
        experience.created_at = datetime.utcnow().isoformat()
        
        result = {
            "task_id": task_info["task_id"],
            "extracted": True,
            "quality_score": score.overall,
            "category": experience.category,
            "stored": False,
        }
        
        # Auto-save if quality is good enough
        if score.overall >= self.threshold:
            filepath = self._save_experience(experience)
            result["stored"] = True
            result["filepath"] = str(filepath)
            result["message"] = f"✅ Experience auto-saved (quality: {score.overall:.2f})"
        else:
            suggestions = self.scorer.get_improvement_suggestions(experience)
            result["message"] = f"⚠️ Quality {score.overall:.2f} < {self.threshold}"
            if suggestions:
                result["suggestions"] = suggestions[:2]  # Limit suggestions
        
        # Console output
        if self.config.get("notifications", {}).get("console", True):
            self._print_result(result, experience)
        
        return result
    
    def _save_experience(self, experience) -> Path:
        """Save experience to personal directory."""
        import json
        from dataclasses import asdict
        
        filename = f"{experience.id}-{experience.category}.json"
        filepath = self.personal_dir / filename
        
        # Convert to dict
        data = asdict(experience)
        
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        return filepath
    
    def _print_result(self, result: Dict, experience):
        """Print result to console."""
        print(f"\n[OrgClaw] {result['message']}")
        if result.get("stored"):
            print(f"  📄 Title: {experience.title}")
            print(f"  🏷️  Category: {experience.category}")
            print(f"  📊 Quality: {experience.quality_score:.2f}")
            if experience.lessons_learned:
                print(f"  💡 Lessons: {len(experience.lessons_learned)}")
            print(f"  💾 Saved to: {result.get('filepath', 'personal dir')}")
    
    def on_git_commit(self, repo_path: str, commit_hash: str) -> Optional[Dict[str, Any]]:
        """Hook called after git commit."""
        if not self.enabled:
            return None
        
        try:
            # Get commit message
            msg_result = subprocess.run(
                ["git", "-C", repo_path, "log", "-1", "--pretty=%B", commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get stats
            stat_result = subprocess.run(
                ["git", "-C", repo_path, "show", "--stat", "--format=", commit_hash],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse lines changed
            lines_added = 0
            lines_removed = 0
            for line in stat_result.stdout.split("\n"):
                if "insertion" in line or "deletion" in line:
                    parts = line.split(",")
                    for part in parts:
                        if "insertion" in part:
                            lines_added = int(part.strip().split()[0])
                        elif "deletion" in part:
                            lines_removed = int(part.strip().split()[0])
            
            task_info = {
                "task_id": commit_hash[:8],
                "description": msg_result.stdout.strip(),
                "repo_path": repo_path,
                "commit_hash": commit_hash,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
            }
            
            return self.on_task_complete(task_info)
            
        except (subprocess.CalledProcessError, ValueError):
            return None


# Singleton
_auto_extractor: Optional[AutoExtractor] = None

def get_auto_extractor(config: Optional[Dict[str, Any]] = None) -> AutoExtractor:
    """Get or create auto-extractor singleton."""
    global _auto_extractor
    if _auto_extractor is None:
        _auto_extractor = AutoExtractor(config)
    return _auto_extractor


def on_task_complete(task_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Global hook function for OpenClaw to call."""
    extractor = get_auto_extractor()
    return extractor.on_task_complete(task_info)


def configure(config: Dict[str, Any]):
    """Configure auto-extractor."""
    global _auto_extractor
    _auto_extractor = AutoExtractor(config)
