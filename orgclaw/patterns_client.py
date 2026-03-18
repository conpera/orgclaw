"""Integration with conpera-patterns knowledge base."""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import requests
import yaml


@dataclass
class Pattern:
    """A pattern from conpera-patterns."""
    id: str
    title: str
    category: str
    status: str
    tags: List[str]
    content: str
    source_url: str
    author: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None


class PatternsClient:
    """Client for accessing conpera-patterns knowledge base."""
    
    DEFAULT_BASE_URL = "https://raw.githubusercontent.com/conpera/conpera-patterns/main"
    
    def __init__(self, base_url: Optional[str] = None, local_path: Optional[str] = None):
        """Initialize patterns client.
        
        Args:
            base_url: GitHub raw URL for remote access
            local_path: Local path to patterns repo for offline access
        """
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.local_path = Path(local_path) if local_path else None
        self._cache: Dict[str, Pattern] = {}
    
    def get_pattern(self, pattern_path: str) -> Optional[Pattern]:
        """Fetch a specific pattern by path.
        
        Args:
            pattern_path: e.g., "patterns/coding/api-error-response.md"
            
        Returns:
            Pattern object or None
        """
        if pattern_path in self._cache:
            return self._cache[pattern_path]
        
        content = self._fetch_content(pattern_path)
        if not content:
            return None
        
        pattern = self._parse_pattern(content, pattern_path)
        if pattern:
            self._cache[pattern_path] = pattern
        
        return pattern
    
    def search_by_tag(self, tag: str) -> List[Pattern]:
        """Search patterns by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of matching patterns
        """
        all_patterns = self._list_all_patterns()
        results = []
        
        for pattern_path in all_patterns:
            pattern = self.get_pattern(pattern_path)
            if pattern and tag in pattern.tags:
                results.append(pattern)
        
        return results
    
    def search_by_category(self, category: str) -> List[Pattern]:
        """Get all patterns in a category.
        
        Args:
            category: e.g., "coding", "architecture", "testing", "deployment"
            
        Returns:
            List of patterns in category
        """
        all_patterns = self._list_all_patterns()
        results = []
        
        for pattern_path in all_patterns:
            if f"/patterns/{category}/" in pattern_path:
                pattern = self.get_pattern(pattern_path)
                if pattern:
                    results.append(pattern)
        
        return results
    
    def get_related_patterns(self, pattern: Pattern) -> List[Pattern]:
        """Find patterns related to given pattern.
        
        Args:
            pattern: Reference pattern
            
        Returns:
            List of related patterns
        """
        # Find by shared tags
        related = []
        for tag in pattern.tags:
            candidates = self.search_by_tag(tag)
            for candidate in candidates:
                if candidate.id != pattern.id and candidate not in related:
                    related.append(candidate)
        
        return related[:5]  # Return top 5
    
    def _fetch_content(self, path: str) -> Optional[str]:
        """Fetch content from remote or local."""
        if self.local_path and self.local_path.exists():
            # Local access
            file_path = self.local_path / path
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
        
        # Remote access via GitHub raw
        url = f"{self.base_url}/{path}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
        except Exception:
            pass
        
        return None
    
    def _parse_pattern(self, content: str, path: str) -> Optional[Pattern]:
        """Parse pattern markdown content."""
        try:
            # Extract YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                    
                    return Pattern(
                        id=frontmatter.get('id', ''),
                        title=self._extract_title(body) or frontmatter.get('id', ''),
                        category=frontmatter.get('category', ''),
                        status=frontmatter.get('status', 'draft'),
                        tags=frontmatter.get('tags', []),
                        content=body,
                        source_url=f"{self.base_url}/{path}",
                        author=frontmatter.get('author'),
                        created=frontmatter.get('created'),
                        updated=frontmatter.get('updated'),
                    )
        except Exception as e:
            print(f"Error parsing pattern {path}: {e}")
        
        return None
    
    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from markdown content."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return None
    
    def _list_all_patterns(self) -> List[str]:
        """List all available pattern paths."""
        # Known patterns (could be fetched from INDEX.md)
        return [
            "patterns/coding/api-error-response.md",
            "patterns/architecture/circuit-breaker.md",
            "patterns/testing/unit-testing.md",
            "patterns/testing/contract-testing.md",
            "patterns/deployment/feature-flag.md",
            "patterns/deployment/infrastructure-as-code.md",
        ]


class PatternEnricher:
    """Enrich experience with relevant patterns."""
    
    def __init__(self, client: Optional[PatternsClient] = None):
        self.client = client or PatternsClient()
    
    def enrich_experience(self, experience: "Experience") -> Dict[str, Any]:
        """Add relevant patterns to experience.
        
        Args:
            experience: Experience to enrich
            
        Returns:
            Enriched experience data
        """
        # Search patterns by category
        category_patterns = self.client.search_by_category(experience.category)
        
        # Search by keywords in description
        keyword_patterns = []
        keywords = self._extract_keywords(experience.description)
        for keyword in keywords:
            patterns = self.client.search_by_tag(keyword)
            keyword_patterns.extend(patterns)
        
        # Combine and deduplicate
        all_patterns = {p.id: p for p in category_patterns + keyword_patterns}
        
        return {
            "experience": experience,
            "related_patterns": [
                {
                    "id": p.id,
                    "title": p.title,
                    "category": p.category,
                    "status": p.status,
                    "url": p.source_url,
                }
                for p in all_patterns.values()
            ]
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        keywords = []
        keyword_map = {
            "api": ["api", "rest", "http"],
            "testing": ["test", "pytest", "unit"],
            "deployment": ["deploy", "release", "ci/cd"],
            "error": ["error", "exception", "handling"],
            "database": ["database", "sql", "postgres"],
            "microservice": ["microservice", "service", "distributed"],
        }
        
        text_lower = text.lower()
        for category, words in keyword_map.items():
            if any(word in text_lower for word in words):
                keywords.append(category)
        
        return keywords
