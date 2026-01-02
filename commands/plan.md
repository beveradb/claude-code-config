---
description: Create implementation plan for a feature (use after /new-worktree)
allowed-tools: Read, Glob, Grep, Write, Bash, Task
---

# Plan Command

Create a detailed implementation plan for a feature or task.

**Argument (optional):** Feature name or description: $ARGUMENTS

## Prerequisites

- You should be in a dedicated worktree for this work (created via `/new-worktree`)
- If not, suggest the user run `/new-worktree <description>` first

## Instructions

### 1. Understand the Context

First, check for project documentation:
- Read `CLAUDE.md` if it exists (project instructions)
- Read `docs/README.md` if it exists (current status)
- Check for existing patterns in the codebase

### 2. Clarify Requirements

If $ARGUMENTS is provided, use it as the feature description.
If not, ask the user what they want to plan.

### 3. Research the Codebase

- Search for similar implementations or patterns
- Identify files that will need changes
- Understand the project structure and conventions
- Check for existing tests to understand testing patterns

### 4. Create the Plan

Write the plan to `.claude/plans/<feature-name>.plan.md`

Use this format:
```markdown
# Plan: <Feature Name>

**Created:** YYYY-MM-DD
**Branch:** <current branch name>
**Status:** Draft

## Overview
Brief description of what we're building and why.

## Requirements
- [ ] Functional requirement 1
- [ ] Functional requirement 2
- [ ] Non-functional requirements (performance, security, etc.)

## Technical Approach
How we'll implement this, including:
- Architecture decisions
- Key dependencies
- Trade-offs considered

## Implementation Steps
1. [ ] Step 1 - description
2. [ ] Step 2 - description
3. [ ] Step 3 - description
(Detailed, checkable steps)

## Files to Create/Modify
| File | Action | Description |
|------|--------|-------------|
| path/to/file.py | Create/Modify | What changes |

## Testing Strategy
- Unit tests for: ...
- Integration tests for: ...
- Manual testing: ...

## Open Questions
- [ ] Question 1
- [ ] Question 2

## Rollback Plan
How to undo if something goes wrong.
```

### 5. Review with User

After writing the plan, summarize:
- What will be built
- Key implementation steps
- Any open questions that need answers

Suggest next steps:
- Answer open questions
- Run `/implement` when ready to start coding

## Tips

- Break large features into smaller, mergeable chunks
- Consider backwards compatibility
- Plan for testing from the start
- Note any dependencies on external services or APIs
