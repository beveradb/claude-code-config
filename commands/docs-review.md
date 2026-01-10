---
description: Review current session for documentation updates before merging PR
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Pre-Merge Documentation Review

Review the current work session to identify documentation updates needed before merging.

## When to Use

- Before creating a PR
- Before merging a PR
- After completing significant work in a worktree

## Instructions

### 1. Analyze Current Work

Determine what was done in this session:
```bash
# See what branch we're on
git branch --show-current

# See recent commits on this branch
git log --oneline main..HEAD 2>/dev/null || git log --oneline -10

# See what files changed
git diff --name-only main..HEAD 2>/dev/null || git diff --name-only HEAD~5..HEAD
```

### 2. Check Documentation Needs

For each category, determine if updates are needed:

**README / Status (docs/README.md or README.md):**
- Has the project status changed?
- Are there new features to document?
- Any new known issues?

**Architecture (docs/ARCHITECTURE.md):**
- Did the system design change?
- New components or services added?
- Changed data flows?

**Development Guide (docs/DEVELOPMENT.md):**
- New setup steps required?
- Changed development workflow?
- New dependencies?

**API Reference (docs/API.md):**
- New endpoints added?
- Changed request/response formats?
- Updated authentication?

**Lessons Learned (docs/LESSONS-LEARNED.md):**
- Encountered tricky bugs?
- Discovered non-obvious patterns?
- Found gotchas worth documenting?

**Project Instructions (CLAUDE.md):**
- New conventions established?
- Changed workflows?
- New commands or tools?

### 3. Create Archive Entry (if significant work)

For substantial completed features or investigations:

```bash
# Create archive doc with today's date
# docs/archive/YYYY-MM-DD-topic.md
```

Archive format:
```markdown
# Topic Name - YYYY-MM-DD

## Summary
What was done and why.

## Key Changes
- Change 1
- Change 2

## Decisions Made
- Decision and rationale

## Future Considerations
- Things to keep in mind
```

### 4. Make Updates

Apply necessary documentation changes:
- Keep updates concise and factual
- Focus on information useful for future work
- Don't duplicate what's obvious from code
- Use consistent formatting with existing docs

### 5. Report

Provide a summary:

```
## Documentation Review

### Updates Made
- [x] Updated docs/README.md - added new feature status
- [x] Added docs/archive/2024-01-15-auth-refactor.md
- [ ] No changes needed to ARCHITECTURE.md

### Updates Skipped (with reason)
- API.md - no API changes in this work

### Recommendations
- Consider updating X when Y is complete
```

## Guidelines

- **Make changes on the current branch** - not on main
- Keep docs DRY - don't repeat what's in code
- Write for future developers (including AI agents)
- Archive completed work, keep active docs current

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests before review |
| `/coderabbit` | Run CodeRabbit CLI review |
| `/pr` | Create PR after docs review |
| `/shipit` | Run all remaining steps and ship to prod |
