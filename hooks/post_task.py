#!/usr/bin/env python3
"""
OpenClaw post-task hook for OrgClaw Skill.

This file is called by OpenClaw when a task completes.
Location: ~/.openclaw/skills/orgclaw/hooks/post_task.py
"""

import os
import sys
from pathlib import Path

# Add orgclaw to Python path
SKILL_DIR = Path(__file__).parent.parent  # hooks/ -> orgclaw/
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))


def on_task_complete(task_result: dict) -> dict:
    """
    OpenClaw Hook: Called when an Agent task completes.
    
    Args:
        task_result: OpenClaw task result containing:
            - id: Task ID
            - description: Task description
            - repo_path: Repository path
            - commit_hash: Git commit hash (if any)
            - files_changed: List of changed files
            - lines_added: Number of lines added
            - lines_removed: Number of lines removed
            - success: Whether task succeeded
    
    Returns:
        Updated task result with orgclaw metadata
    """
    # Only process successful tasks
    if not task_result.get("success", True):
        return task_result
    
    try:
        from orgclaw.auto_extract import on_task_complete as orgclaw_extract
        
        # Convert OpenClaw format to OrgClaw format
        orgclaw_task_info = {
            "task_id": task_result.get("id", "unknown"),
            "description": task_result.get("description", ""),
            "repo_path": task_result.get("repo_path", "."),
            "commit_hash": task_result.get("commit_hash"),
            "files_changed": task_result.get("files_changed", []),
            "lines_added": task_result.get("lines_added", 0),
            "lines_removed": task_result.get("lines_removed", 0),
        }
        
        # Auto-extract experience
        result = orgclaw_extract(orgclaw_task_info)
        
        if result:
            # Add orgclaw metadata to task result
            task_result["orgclaw"] = {
                "extracted": result.get("extracted", False),
                "stored": result.get("stored", False),
                "quality_score": result.get("quality_score", 0),
                "category": result.get("category"),
                "filepath": result.get("filepath"),
            }
            
            # Print summary for user
            if result.get("stored"):
                print(f"\n💡 [OrgClaw] Experience automatically captured!")
                print(f"   Quality: {result['quality_score']:.2f}")
                print(f"   Category: {result.get('category', 'unknown')}")
                print(f"   Run 'orgclaw stats' to view your knowledge base.")
        
    except ImportError as e:
        # OrgClaw not properly installed
        # Fail silently to not break OpenClaw
        pass
    except Exception as e:
        # Log error but don't fail the task
        print(f"[OrgClaw] Warning: Auto-extraction failed: {e}", file=sys.stderr)
    
    return task_result


# For testing: python3 post_task.py
if __name__ == "__main__":
    # Simulate a task result
    test_task = {
        "id": "test-task-hook-001",
        "description": "Fixed memory leak in user cache by implementing proper cleanup with context managers",
        "repo_path": ".",
        "commit_hash": "abc123",
        "files_changed": ["app/cache.py"],
        "lines_added": 15,
        "lines_removed": 5,
        "success": True,
    }
    
    print("Testing OrgClaw Hook...")
    print(f"Input: {test_task['description'][:50]}...")
    
    result = on_task_complete(test_task)
    
    if result.get("orgclaw"):
        print(f"\n✅ Hook test successful!")
        print(f"OrgClaw metadata: {result['orgclaw']}")
    else:
        print("\n⚠️  No OrgClaw metadata (may need to check installation)")
