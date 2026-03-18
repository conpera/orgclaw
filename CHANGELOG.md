# CHANGELOG

## [0.1.0] - 2026-03-18

### Added
- Initial release of OrgClaw
- Organization knowledge federation system
- Experience extraction from Agent tasks
- Quality scoring system (completeness, specificity, actionability, reusability)
- Vector-based semantic knowledge storage using ChromaDB
- OpenClaw Skill integration with lifecycle hooks
- CLI tool for experience management
- Support for git diff analysis
- Pattern detection (bug_fix, refactor, optimization, feature)
- Multi-level knowledge: Personal → Team → Organization → Community

### Features
- `orgclaw extract` - Extract experience from completed tasks
- `orgclaw search` - Semantic search of knowledge base
- `orgclaw stats` - View knowledge base statistics
- `orgclaw add` - Add experience from JSON file

### Integration
- OpenClaw `on_task_complete` hook for automatic extraction
- OpenClaw `on_agent_spawn` hook for context enrichment
- Configurable quality threshold for automatic storage
