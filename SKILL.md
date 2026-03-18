# OrgClaw - OpenClaw Skill

**Name**: `orgclaw`  
**Version**: 0.1.0  
**Author**: Conpera Team  
**License**: MIT

## Description

Organization knowledge federation system for OpenClaw. Automatically extracts, scores, and stores reusable experiences from Agent tasks.

## Features

- **Auto-Extract**: Automatically capture experience on task completion
- **Quality Scoring**: 4-dimension quality assessment (completeness, specificity, actionability, reusability)
- **Smart Storage**: Save high-quality experiences to personal knowledge base
- **Pattern Linking**: Connect with conpera-patterns knowledge base
- **Semantic Search**: Vector-based experience retrieval

## Installation

### Method 1: One-line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/conpera/orgclaw/main/install.py | python3
```

### Method 2: OpenClaw CLI

```bash
openclaw skill install conpera/orgclaw
```

### Method 3: Manual

```bash
git clone https://github.com/conpera/orgclaw.git ~/.openclaw/skills/orgclaw
cd ~/.openclaw/skills/orgclaw
python3 install.py
```

## Configuration

Default configuration in `~/.openclaw/config.yaml`:

```yaml
skills:
  orgclaw:
    enabled: true
    auto_extract: true
    quality_threshold: 0.4
    min_lines_changed: 5
    personal_dir: ~/.orgclaw/personal
    enable_patterns: true
```

## Usage

### Automatic (Recommended)

Once installed, OrgClaw automatically extracts experience when OpenClaw tasks complete:

```
[OpenClaw] Task completed successfully!
[OrgClaw] ✅ Experience auto-saved (quality: 0.51)
  💾 Saved to: ~/.orgclaw/personal/exp-xxx.json
```

### Manual Commands

```bash
# View statistics
orgclaw stats

# Search experiences
orgclaw search "memory leak"

# Search patterns
orgclaw patterns "api" --category coding

# Manual extract
orgclaw extract task-001 --description "Fixed bug in..."
```

## How It Works

1. **Task Completion**: OpenClaw completes an Agent task
2. **Hook Trigger**: `post_task.py` is called automatically
3. **Experience Extraction**: Parse task description, detect patterns
4. **Quality Scoring**: Score on 4 dimensions (each 25% weight)
5. **Storage Decision**: Save if quality >= threshold (default 0.4)
6. **Pattern Linking**: Suggest related patterns from conpera-patterns

## Architecture

```
Agent Task
    ↓
OpenClaw Hook (post_task.py)
    ↓
ExperienceExtractor
    ├── Pattern Detection (bug_fix/refactor/feature/optimization)
    ├── Solution Extraction
    └── Lesson Generation
    ↓
ExperienceScorer
    ├── Completeness (25%)
    ├── Specificity (25%)
    ├── Actionability (25%)
    └── Reusability (25%)
    ↓
Decision Gate (quality >= 0.4?)
    ├── Yes → ~/.orgclaw/personal/
    └── No → Discard + Suggestions
```

## Data Flow

- **Input**: Task description, git diff, changed files
- **Process**: Extract → Score → Decide → Store
- **Output**: Structured experience JSON
- **Storage**: `~/.orgclaw/personal/*.json`

## File Locations

| Type | Path |
|------|------|
| Skill Code | `~/.openclaw/skills/orgclaw/` |
| Configuration | `~/.openclaw/config.yaml` |
| Personal Data | `~/.orgclaw/personal/` |
| Hook | `~/.openclaw/skills/orgclaw/hooks/post_task.py` |

## Integration

### With conpera-patterns

OrgClaw automatically links with [conpera-patterns](https://github.com/conpera/conpera-patterns):

- Extracted experiences suggest relevant patterns
- High-quality experiences can be promoted to patterns
- Bidirectional knowledge flow

### With OpenClaw

Required OpenClaw support:
- `post_task` hook system
- Task result metadata (description, commit, changes)

## Development

```bash
# Clone
git clone https://github.com/conpera/orgclaw.git
cd orgclaw

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Type check
mypy orgclaw/
```

## Troubleshooting

### Issue: Hook not called

**Solution**: Check if OpenClaw supports `post_task` hook. Use manual extraction:
```bash
orgclaw extract <task-id> --description "..."
```

### Issue: Import errors

**Solution**: Reinstall dependencies:
```bash
pip install -r ~/.openclaw/skills/orgclaw/requirements.txt --force-reinstall
```

### Issue: Permission denied

**Solution**: Use user installation:
```bash
python3 install.py --user
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Submit PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Roadmap

- [x] Auto-extract from tasks
- [x] Quality scoring
- [x] Pattern linking
- [ ] Web UI for browsing
- [ ] Team/organization sharing
- [ ] LLM-enhanced extraction
- [ ] Feedback learning

## License

MIT License - see [LICENSE](LICENSE)

## Links

- GitHub: https://github.com/conpera/orgclaw
- Patterns: https://github.com/conpera/conpera-patterns
- Issues: https://github.com/conpera/orgclaw/issues
