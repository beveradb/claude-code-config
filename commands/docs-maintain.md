---
description: Periodic documentation maintenance and organization check
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Documentation Maintenance Check

Perform periodic maintenance on project documentation to keep it organized and current.

## When to Use

- Periodically (weekly/monthly) to keep docs healthy
- After major milestones
- When docs feel disorganized or stale

## Instructions

### 1. Check Documentation Structure

Look for common doc locations and verify organization:

```bash
# Check what docs exist
ls -la docs/ 2>/dev/null || echo "No docs/ directory"
ls -la *.md 2>/dev/null
ls -la .claude/ 2>/dev/null
```

Recommended structure:
```
docs/
├── README.md              # Current status + navigation
├── ARCHITECTURE.md        # System design
├── DEVELOPMENT.md         # Dev setup, testing, deployment
├── API.md                 # API reference (if applicable)
├── LESSONS-LEARNED.md     # Accumulated wisdom
└── archive/               # Historical docs (YYYY-MM-DD-topic.md)

CLAUDE.md                  # Project instructions for AI agents
README.md                  # Project overview
```

Report any files that don't fit or are misplaced.

### 2. Freshness Check

- Read status sections - are they current?
- Check recent git commits - do they suggest docs need updates?
- Look for information that contradicts current code
- Identify stale TODOs or outdated references

```bash
# Recent commits to understand current state
git log --oneline -20

# When were docs last updated?
git log --oneline -1 -- docs/ 2>/dev/null
git log --oneline -1 -- "*.md" 2>/dev/null
```

### 3. Archive Organization

If docs/archive/ exists:
- Verify files use YYYY-MM-DD prefix
- Check for docs that should be archived (completed features, old plans)
- Remove truly obsolete content (empty files, duplicates)

### 4. Cross-Reference Check

- Verify CLAUDE.md points to correct doc locations
- Check that docs reference each other correctly
- Test internal links if possible
- Ensure no references to deleted files

### 5. Content Quality

Flag potential issues:
- Docs over 500 lines (may need splitting)
- Duplicate information across docs
- Sections that seem outdated
- Missing sections that should exist

### 6. Take Action

Based on findings:
1. **Fix structural issues** - Move/rename misplaced files
2. **Update stale content** - Refresh outdated information
3. **Archive completed work** - Move old docs to archive/
4. **Remove obsolete content** - Delete truly unnecessary files

### 7. Report Findings

Provide a maintenance report:

```
## Documentation Maintenance Report - YYYY-MM-DD

### Issues Found
- [List issues discovered]

### Actions Taken
- [List fixes made]

### Recommendations
- [Suggestions for future attention]

### Health Check
- [ ] Structure: OK / Needs attention
- [ ] Freshness: OK / Some stale content
- [ ] Archive: OK / Needs cleanup
- [ ] Cross-refs: OK / Broken links found
- [ ] Quality: OK / Large files flagged
```

## Guidelines

- Make minimal, focused changes
- Don't reorganize everything at once
- Preserve git history (move files with git mv)
- When in doubt, ask before deleting
