"""OrgClaw - Organization knowledge federation system for OpenClaw."""

__version__ = "0.1.0"

from orgclaw.analyzer.extractor import ExperienceExtractor
from orgclaw.analyzer.quality_scorer import ExperienceScorer
from orgclaw.storage.vector_store import KnowledgeStore
from orgclaw.patterns_client import PatternsClient, PatternEnricher, Pattern
from orgclaw.auto_extract import AutoExtractor, on_task_complete, configure

__all__ = [
    "ExperienceExtractor",
    "KnowledgeStore", 
    "ExperienceScorer",
    "PatternsClient",
    "PatternEnricher",
    "Pattern",
    "AutoExtractor",
    "on_task_complete",
    "configure",
]
