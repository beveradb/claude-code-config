---
description: Implement from an existing plan (use after /plan)
allowed-tools: Read, Glob, Grep, Edit, Write, Bash, Task
---

# Implement Command

Implement a feature based on an existing plan.

**Argument (optional):** Plan name or path: $ARGUMENTS

## Prerequisites

- You should have a plan created via `/plan`
- You should be in a dedicated worktree for this work

## Instructions

### 1. Find the Plan

If $ARGUMENTS is provided, look for a matching plan.
Otherwise, list available plans:
```bash
ls -la .claude/plans/*.plan.md 2>/dev/null || echo "No plans found"
```

If no plans exist, suggest running `/plan <feature>` first.

### 2. Read and Understand the Plan

- Read the plan file thoroughly
- Check if there are open questions that need resolving
- Understand the implementation steps and their order

### 3. Follow Implementation Steps

For each step in the plan:
1. Mark the step as "in progress" in your todo list
2. Implement the change
3. Write tests as you go (don't defer testing)
4. Commit frequently with meaningful messages
5. Mark the step complete

### 4. Implementation Checklist

Work through this checklist:

- [ ] Read and understand the plan fully
- [ ] Resolve any open questions before coding
- [ ] Implement core functionality first
- [ ] Add proper error handling
- [ ] Write unit tests (aim for good coverage)
- [ ] Write integration tests if applicable
- [ ] Update API documentation if API changed
- [ ] Update README/docs if user-facing changes
- [ ] Run full test suite: `make test` or project equivalent
- [ ] Run linting: `make lint` or project equivalent

### 5. Commit Strategy

Make atomic commits as you complete logical chunks:
```bash
git add -A
git commit -m "feat: brief description

- Detail 1
- Detail 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### 6. Update the Plan

As you work:
- Check off completed steps in the plan file
- Note any deviations or discoveries
- Update the plan status when done

### 7. When Complete

After implementation:
1. Run `/test` to verify everything passes
2. Run `/docs-review` to check if docs need updates
3. Suggest creating a PR if on a feature branch

## Output

Provide status updates as you work:
- Which step you're on
- Any issues encountered
- Tests passing/failing
- What's remaining

## Tips

- Don't skip tests - they catch bugs early
- Commit often - easier to revert if needed
- Ask if requirements are unclear - don't guess
- Keep changes focused on the plan scope
