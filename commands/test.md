---
description: Run tests and report results
allowed-tools: Read, Glob, Grep, Bash
---

# Test Command

Run the project's test suite and report results.

**Argument (optional):** Specific test path or filter: $ARGUMENTS

## Instructions

### 1. Detect Project Type and Test Runner

Check for common test configurations:

```bash
# Check what's available
ls -la Makefile package.json pyproject.toml Cargo.toml go.mod 2>/dev/null | head -20
```

### 2. Run Tests

Based on project type, run the appropriate commands:

**If Makefile exists with test target:**
```bash
make test
```

**If package.json (Node.js/TypeScript):**
```bash
npm test
# or for specific tests
npm test -- $ARGUMENTS
```

**If pyproject.toml or setup.py (Python):**
```bash
# Try pytest first
pytest $ARGUMENTS
# Or if using poetry
poetry run pytest $ARGUMENTS
```

**If Cargo.toml (Rust):**
```bash
cargo test $ARGUMENTS
```

**If go.mod (Go):**
```bash
go test ./... $ARGUMENTS
```

### 3. Run Linting (if available)

Also check code quality:

**Makefile:**
```bash
make lint 2>/dev/null || echo "No lint target"
```

**Node.js:**
```bash
npm run lint 2>/dev/null || echo "No lint script"
```

**Python:**
```bash
ruff check . 2>/dev/null || flake8 . 2>/dev/null || echo "No linter configured"
```

### 4. Report Results

Provide a clear summary:

```
## Test Results

### Tests
- Status: ✅ PASSED / ❌ FAILED
- Total: X tests
- Passed: X
- Failed: X
- Skipped: X
- Coverage: X% (if available)

### Linting
- Status: ✅ CLEAN / ❌ ISSUES FOUND
- Issues: [list if any]

### Failed Tests (if any)
1. test_name - Brief failure reason
2. ...

### Recommendations
- [Any suggestions for fixing failures]
```

### 5. If Tests Fail

When tests fail:
1. Identify the root cause
2. Check if it's a test issue or code issue
3. Suggest specific fixes
4. Offer to fix if straightforward

## Tips

- Run tests before committing
- Run tests after pulling changes
- If tests are slow, mention which subset to run for quick feedback
- Check for flaky tests (tests that sometimes pass, sometimes fail)
