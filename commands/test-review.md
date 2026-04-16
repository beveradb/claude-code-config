---
description: Assess and fix automated testing gaps for current changes
allowed-tools: Read, Glob, Grep, Edit, Write, Bash
---

# Test Review

Assess the automated testing approach for changes in the current worktree/branch, then **automatically implement improvements** to address any gaps found.

**Goal:** Ensure tests are thorough, meaningful, and complete with:
- 70%+ unit test coverage
- Appropriate test types (integration, e2e, smoke, contract, mutation) where applicable
- Confidence in correctness and maintainability

**This command takes action.** After identifying gaps, it proceeds to write missing tests and improve existing ones. It does not stop at just reporting findings.

## When to Use

- After implementing a feature, before `/docs-review`
- When you want to ensure test quality before shipping
- As part of the `/shipit` workflow

**What happens:** This command analyzes your changes, identifies testing gaps, and then automatically writes/improves tests to address them. You can run it and walk away - it will both assess AND fix.

## Instructions

### Step 1: Understand Testing Context

First, look for testing guidelines and documentation:

```bash
# Check for testing documentation
for f in TESTING.md docs/TESTING.md test/README.md tests/README.md; do
  if [ -f "$f" ]; then
    echo "Found: $f"
  fi
done

# Check for test configuration
ls -la jest.config.* vitest.config.* pytest.ini pyproject.toml setup.cfg .coveragerc coverage.* 2>/dev/null | grep -v "No such"
```

If testing documentation exists, **read it thoroughly** to understand:
- Project-specific testing conventions
- Coverage requirements and targets
- Test categories and when to use each
- Required test fixtures or setup

### Step 2: Analyze Current Changes

Identify what was changed in this branch:

```bash
# Get branch info
BRANCH=$(git branch --show-current)
echo "Branch: $BRANCH"

# List changed files
git diff --name-only main..HEAD 2>/dev/null || git diff --name-only HEAD~10..HEAD

# Categorize changes
echo "\n=== Source files changed ==="
git diff --name-only main..HEAD 2>/dev/null | grep -vE '(test|spec|__test__|\.test\.|\.spec\.)' | grep -E '\.(ts|tsx|js|jsx|py|go|rs|java|rb)$' || echo "None"

echo "\n=== Test files changed ==="
git diff --name-only main..HEAD 2>/dev/null | grep -E '(test|spec|__test__|\.test\.|\.spec\.)' || echo "None"
```

### Step 3: Assess Test Coverage

Check current coverage if available:

```bash
# Try to find coverage reports
for f in coverage/lcov-report/index.html coverage/index.html htmlcov/index.html coverage.xml .coverage; do
  if [ -f "$f" ]; then
    echo "Found coverage report: $f"
  fi
done

# Check for coverage in CI config
grep -r "coverage" .github/workflows/*.yml 2>/dev/null | head -5 || echo "No coverage in CI"
```

If no coverage data exists, recommend running:
- **Node.js:** `npm test -- --coverage`
- **Python:** `pytest --cov=. --cov-report=html`
- **Go:** `go test -cover ./...`

### Step 4: Inventory Existing Tests

Map out the current testing landscape:

```bash
# Count test files by type
echo "=== Test file inventory ==="
echo "Unit tests:"
find . -name "*.test.*" -o -name "*_test.*" -o -name "test_*.py" 2>/dev/null | grep -v node_modules | grep -v __pycache__ | wc -l

echo "Integration tests:"
find . -path "*/integration/*" -o -path "*/tests/integration/*" 2>/dev/null | grep -v node_modules | wc -l

echo "E2E tests:"
find . -path "*/e2e/*" -o -path "*/tests/e2e/*" -o -name "*.e2e.*" 2>/dev/null | grep -v node_modules | wc -l

echo "Snapshot tests:"
find . -name "__snapshots__" -type d 2>/dev/null | wc -l
```

### Step 5: Critical Assessment

For each changed source file, evaluate:

#### Unit Tests (Target: 70%+ coverage)
- [ ] Does each public function/method have corresponding unit tests?
- [ ] Are edge cases covered (null, empty, boundary values)?
- [ ] Are error paths tested (exceptions, error returns)?
- [ ] Are tests isolated (no external dependencies)?
- [ ] Do tests verify behavior, not implementation details?

#### Caller-Callee Contract Tests (CRITICAL — easy to miss)

When function A calls function B with data (dict, object, args), check:
- [ ] Do tests verify A actually produces the inputs B expects?
- [ ] Or do tests only test B in isolation with hand-crafted "ideal" inputs?

**How to spot this gap:** For each new helper/utility function, find its callers. If the test for the helper
builds its own input dict (e.g., `transcription_result={"lyrics_dir": path}`), check whether the real caller
actually includes that key. If the caller's return value is an implicit dict (not a TypedDict/dataclass), this
is a HIGH RISK gap — flag it as P0.

**Especially dangerous with non-fatal code:** If the function is wrapped in try/except (designed to never crash),
a test that only checks "didn't raise" provides zero signal. A broken input will silently do nothing, and the
test will still pass. Always assert on the *positive outcome* (metadata was stored, value was computed), not
just the absence of exceptions.

Example of a gap that shipped in production:
```python
# Test passes — but transcribe_lyrics() never includes "lyrics_dir"!
def test_stores_ids(tmp_path):
    _store_metadata(result={"lyrics_dir": str(tmp_path)}, ...)  # hand-crafted
    assert data["task_id"] == "abc"  # ✅ passes, ❌ useless

# The missing contract test:
def test_caller_provides_lyrics_dir():
    result = transcribe_lyrics(...)
    assert "lyrics_dir" in result  # Would have caught the bug
```

#### Integration Tests (where applicable)
- [ ] Are module interactions tested?
- [ ] Are database operations tested with test fixtures?
- [ ] Are external service integrations mocked appropriately?
- [ ] Are API endpoints tested end-to-end within the service?

#### E2E Tests (for user-facing changes)
- [ ] Are critical user flows covered?
- [ ] Are happy paths tested?
- [ ] Are error states tested (validation, failures)?
- [ ] Do tests run against realistic configurations?

#### Contract Tests (for APIs/services)
- [ ] Are API request/response schemas validated?
- [ ] Are breaking changes detected?
- [ ] Are consumers' expectations verified?

#### Smoke Tests (for deployments)
- [ ] Is there a quick health check test?
- [ ] Are critical paths tested post-deploy?

#### Mutation Testing (for critical code)
- [ ] Has mutation testing been considered for critical logic?
- [ ] Are tests actually catching bugs, not just covering lines?

### Step 6: Identify Gaps

Create a specific list of missing tests:

```
## Test Gaps Identified

### Missing Unit Tests
1. `src/payment/processor.ts` - No tests for `refundTransaction()`
2. `src/auth/validator.py` - Edge cases for expired tokens not covered

### Missing Integration Tests
1. Database transaction rollback scenarios
2. Cache invalidation on update

### Missing E2E Tests
1. Complete checkout flow
2. Error recovery in multi-step wizard

### Coverage Below Target
- Current: 45%
- Target: 70%
- Files needing attention: [list]
```

### Step 7: Prioritize Recommendations

Rank test additions by impact:

**P0 - Must Have (blocks shipping):**
- Tests for new public APIs
- Tests for security-critical code
- Tests for payment/financial logic

**P1 - Should Have (quality gate):**
- Unit tests to reach 70% coverage
- Integration tests for new database operations
- Error handling tests

**P2 - Nice to Have (future improvement):**
- Mutation testing for complex algorithms
- Performance regression tests
- Additional edge cases

### Step 8: Implement Test Improvements

**Automatically proceed to add/improve tests based on your findings.**

For each identified gap (starting with P0, then P1):

1. **Write the missing tests** following existing test patterns in the codebase
2. **Run tests** after each addition to verify they pass
3. **Continue until** all P0 and P1 gaps are addressed
4. **Update coverage** and verify improvement

Do NOT stop at just reporting gaps. The purpose of this command is to ensure tests are complete before shipping, which means fixing issues not just identifying them.

### Step 9: Report

Provide a comprehensive assessment:

```
## Test Review Summary

### Testing Documentation
- [ ] TESTING.md exists: Yes/No
- [ ] Coverage targets defined: Yes/No (Target: X%)
- [ ] Test categories documented: Yes/No

### Coverage Assessment
- **Current coverage:** X%
- **Target coverage:** 70%+
- **Gap:** X percentage points

### Test Type Inventory
| Type | Count | Status |
|------|-------|--------|
| Unit | X | ✅ Adequate / ⚠️ Needs work |
| Integration | X | ✅ / ⚠️ / ❌ Missing |
| E2E | X | ✅ / ⚠️ / ❌ N/A |
| Contract | X | ✅ / ⚠️ / ❌ N/A |
| Smoke | X | ✅ / ⚠️ / ❌ N/A |

### Changes Analyzed
- Source files changed: X
- Test files changed: X
- Test-to-source ratio: X:1

### Gaps Identified
**Critical (P0):**
- [list or "None"]

**Important (P1):**
- [list or "None"]

**Optional (P2):**
- [list or "None"]

### Actions Taken
1. [Test file added/modified]
2. [Test file added/modified]
3. [etc.]

### Remaining Items (P2 - deferred)
- [Optional improvements not implemented]

### Verdict
- [ ] ✅ **Ready to ship** - Tests are thorough and meaningful
- [ ] ⚠️ **Needs attention** - Add P0/P1 tests before shipping
- [ ] ❌ **Significant gaps** - Major test additions required
```

## Guidelines

- **Take action, don't just report** - Implement P0 and P1 test improvements before finishing
- **Be critical but constructive** - The goal is better tests, not perfection
- **Focus on changed code** - Don't boil the ocean; assess what's new
- **Consider risk** - Payment, auth, and data integrity need more testing
- **Respect project conventions** - Follow existing test patterns
- **Pragmatic over dogmatic** - 70% coverage is a guide, not a hard rule
- **Defer P2 items** - Optional improvements can be skipped; focus on what matters for shipping

## Test Quality Checklist

Good tests should be:
- **Fast** - Unit tests run in milliseconds
- **Isolated** - No dependencies between tests
- **Repeatable** - Same result every time
- **Self-validating** - Pass or fail, no manual inspection
- **Timely** - Written alongside the code

Tests should NOT:
- Test implementation details (private methods, internal state)
- Have excessive mocking that makes them brittle
- Be flaky (sometimes pass, sometimes fail)
- Require manual setup or external services (for unit tests)

## Related Commands

| Command | Purpose |
|---------|---------|
| `/test` | Run tests and report results |
| `/docs-review` | Review documentation after test review |
| `/coderabbit` | Code review after tests pass |
| `/shipit` | Run all remaining steps |
