# Issue #1: Organization Layer Integration

**Status**: Open  
**Priority**: Low  
**Labels**: enhancement, future, organization

## Description

Organization layer (cross-team knowledge sharing) is currently handled separately via [conpera-patterns](https://github.com/conpera/conpera-patterns) repository. 

This issue tracks potential automatic integration between orgclaw's team layer and the organization-level pattern library.

## Current State

```
Personal (~/.orgclaw/personal/)
    ↓ submit
Team (~/.orgclaw/teams/<team>/approved/)
    ↓ (manual) PR to conpera-patterns
Organization (conpera-patterns repo)
```

Currently, promoting team experiences to organization level requires manual PR creation.

## Proposed Features

### Option 1: Auto-Submit High Quality Experiences

Automatically submit experiences with quality >= 0.8 to conpera-patterns:

```python
# In team_share.py
if experience['quality_score'] >= 0.8 and len(experience['votes']) >= 3:
    auto_create_pr_to_patterns(experience)
```

**Pros**: Fully automated  
**Cons**: May create noise in patterns repo

### Option 2: Curated Export

Team admin reviews and exports selected experiences:

```bash
orgclaw team export-for-patterns <team>
# Creates PR to conpera-patterns with selected experiences
```

**Pros**: Controlled quality  
**Cons**: Manual effort required

### Option 3: Organization Search

Allow searching across all teams in an organization:

```bash
orgclaw org search "memory leak" --org conpera
# Searches all teams: backend, frontend, devops, etc.
```

**Pros**: Easy discovery  
**Cons**: Requires org-level index

## Decision

**Deferred to v0.3.0**

Current workflow (manual PR to conpera-patterns) is sufficient for now.

## Related

- Repository: https://github.com/conpera/conpera-patterns
- Local patterns can be browsed via: `orgclaw patterns <query>`

## Acceptance Criteria

- [ ] Team experiences can be easily exported to conpera-patterns
- [ ] Either automated or well-documented manual workflow
- [ ] Quality threshold configurable
- [ ] PR template for pattern submission

---

**Note**: This is a low-priority feature. Current focus should be on:
1. Stabilizing personal layer
2. Testing team layer in production
3. Documentation

*Created: 2026-03-18*
