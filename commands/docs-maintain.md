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
├── sessions/YYYY-Qn/      # Session records (YYYY-MM-DD-topic.md)
├── designs/YYYY-Qn/       # Design & spec docs
├── plans/YYYY-Qn/         # Implementation plans
└── archive/               # Legacy flat store — migrate into the folders above

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

### 3. Archive Organization & Reorg

Large flat `docs/archive/` folders become unwieldy (GitHub struggles to render
them). Migrate them into the typed, quarter-bucketed layout:
`docs/{sessions,designs,plans}/<YYYY-Qn>/`.

**This is report-first: print the full proposed move plan and ask for
confirmation before executing.** It is meant to be safe to run unattended
against large repos.

For each file in `docs/archive/*.md`:

1. **Classify by filename heuristic:**
   - matches `*plan*` → `docs/plans/`
   - matches `*design*` or `*spec*` → `docs/designs/`
   - matches `*handoff*`, `*session*`, `*report*`, `*findings*`, or
     `*investigation*` → `docs/sessions/`
   - otherwise → **flag for manual classification** (do not guess; leave in place).
2. **Determine the quarter bucket** from the `YYYY-MM-DD` filename prefix
   (`Q = ((month - 1) // 3) + 1`). If a file has no date prefix, fall back to its
   git first-commit date, then mtime; if still undated (e.g. a stable reference
   doc like `capital-tier-strategy.md`), **leave it in place and flag it**.
3. **Move with git to preserve history:**
   ```bash
   mkdir -p "docs/<type>/<YYYY-Qn>"
   git mv "docs/archive/<file>.md" "docs/<type>/<YYYY-Qn>/<file>.md"
   ```
4. After moving, **check for references** to the old paths across the repo
   (`grep -rn "docs/archive/<file>" .`) and update any that break.

Also: verify remaining files use the `YYYY-MM-DD` prefix, remove truly obsolete
content (empty files, exact duplicates), and flag any single folder that has
grown large enough to warrant a finer split.

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

### 6. LESSONS-LEARNED.md Size Management

The `LESSONS-LEARNED.md` file is read by `/new-worktree` to provide context to new sessions. It must stay under ~500 lines (~15K tokens) to fit in context windows.

**Check size:**
```bash
wc -l docs/LESSONS-LEARNED.md 2>/dev/null || echo "No LESSONS-LEARNED.md"
```

**If over 400 lines, perform archival:**

1. **Read the full file** to understand the content structure and identify lessons by date/topic

2. **Identify archival candidates:**
   - Lessons older than 2-3 months
   - Lessons specific to completed/shipped features
   - Lessons that are very detailed but can be summarized
   - Keep: Recent lessons, foundational patterns, frequently-referenced wisdom

3. **Create archive file:**
   - Path: `docs/archive/YYYY-MM-DD-lessons-learned-archive.md`
   - Include full content of archived lessons
   - Add header explaining this is an archive

4. **Update main LESSONS-LEARNED.md:**
   - Remove archived content
   - Add a "Summary of Archived Lessons" section near the top (after any intro)
   - Format as brief bullet points (1-2 sentences each)
   - Include reference: `> Full details: docs/archive/YYYY-MM-DD-lessons-learned-archive.md`

**Example summary format:**
```markdown
## Summary of Archived Lessons

> Full details: [docs/archive/2025-01-09-lessons-learned-archive.md](archive/2025-01-09-lessons-learned-archive.md)

Key takeaways from older lessons:
- **Topic A**: Brief 1-sentence summary of the lesson
- **Topic B**: Brief 1-sentence summary of the lesson
- **Topic C**: Brief 1-sentence summary of the lesson
```

**Target outcome:**
- Main file: Under 400 lines, recent + summarized older lessons
- Archive: Complete historical record for deep dives
- Future sessions get key lessons without context overflow

### 7. Take Action

Based on findings:
1. **Fix structural issues** - Move/rename misplaced files
2. **Update stale content** - Refresh outdated information
3. **Archive completed work** - Move old docs to archive/
4. **Remove obsolete content** - Delete truly unnecessary files
5. **Archive old lessons** - If LESSONS-LEARNED.md is too large, archive older content

### 8. Report Findings

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
- [ ] Lessons-Learned: OK / Archived older content / Needs archival
```

## Guidelines

- Make minimal, focused changes
- Don't reorganize everything at once
- Preserve git history (move files with git mv)
- When in doubt, ask before deleting
