# CI/CD Stub Detection & NO MOCKING Enforcement Guide

## Overview

This guide documents the automated enforcement system for preventing stub implementations and ensuring the NO MOCKING policy is followed in integration and E2E tests.

## Automated Checks

All pull requests automatically run three critical checks:

### 1. Stub Detection (`detect_stubs.sh`)

**Purpose**: Prevent stub/placeholder implementations from being merged into production code.

**What it detects**:
- `STUB implementation` comments
- `return.*simulated` patterns
- `mock.*data.*return` patterns
- `placeholder.*implementation` comments
- `TODO.*implement` patterns
- `raise NotImplementedError` with stub context
- `pass # stub` patterns
- Empty return stubs: `return {} # stub`, `return [] # stub`, `return None # stub`

**Exclusions**:
- Test files (`tests/`, `test_*.py`, `*_test.py`)
- Documentation (`docs/`)
- Examples (`examples/`)
- Cache directories (`__pycache__`, `.pytest_cache`)

**Exit codes**:
- `0`: No stubs found (PASS)
- `1`: Stubs detected (FAIL)

**Usage**:
```bash
# Run stub detection
./scripts/detect_stubs.sh

# With verbose output
./scripts/detect_stubs.sh --verbose
```

**Example output**:
```
=== Stub Detection Script ===
Scanning: /path/to/src

✗ STUB IMPLEMENTATIONS DETECTED

The following stub implementations were found in production code:

src/dataflow/feature.py:123:    # STUB implementation
src/dataflow/module.py:45:    return {}  # stub

Action Required:
1. Replace stub implementations with real code
2. If this is intentional, add to STUB_IMPLEMENTATIONS_REGISTRY.md
3. Remove stub patterns from production code

Total patterns matched: 2
```

### 2. Stub Registry Validation (`validate_stub_registry.sh`)

**Purpose**: Ensure `STUB_IMPLEMENTATIONS_REGISTRY.md` is synchronized with actual code.

**What it validates**:
- All stubs listed in registry exist in code
- All stubs in code are documented in registry
- Registry has proper format and required sections
- File paths in registry are valid

**Registry format**:
```markdown
# Stub Implementations Registry

## Active Stubs

### Stub: FeatureName
- **File**: `src/module/file.py`
- **Line**: 123-145
- **Function/Class**: `ClassName.method_name`
- **Reason**: Waiting for dependency X
- **Planned Completion**: 2025-02-01
- **Tracking Issue**: #456

## Completed Stubs
<!-- Audit trail of completed stubs -->
```

**Exit codes**:
- `0`: Registry valid and synchronized (PASS)
- `1`: Validation errors found (FAIL)

**Usage**:
```bash
# Validate stub registry
./scripts/validate_stub_registry.sh
```

**Auto-creation**: If registry doesn't exist, script creates template automatically.

### 3. NO MOCKING Enforcement (`enforce_no_mocking.sh`)

**Purpose**: Enforce strict NO MOCKING policy in Tier 2 (integration) and Tier 3 (e2e) tests.

**What it detects**:
- `from unittest.mock import`
- `from unittest import mock`
- `import unittest.mock`
- `import mock`
- `from mock import`
- `@patch`, `@mock.patch`
- `Mock()`, `MagicMock()`, `AsyncMock()`
- `patch.object`, `patch.dict`
- `pytest-mock` usage
- `mocker.patch`, `mocker.Mock`

**Scope**:
- **Tier 1 (unit tests)**: Mocking allowed (informational check only)
- **Tier 2 (integration tests)**: NO MOCKING - violations cause failure
- **Tier 3 (e2e tests)**: NO MOCKING - violations cause failure

**Exit codes**:
- `0`: No violations (PASS)
- `1`: Mocking detected in Tier 2/3 (FAIL)

**Usage**:
```bash
# Enforce NO MOCKING policy
./scripts/enforce_no_mocking.sh

# With verbose output
./scripts/enforce_no_mocking.sh --verbose
```

**Example output**:
```
=== NO MOCKING Policy Enforcement ===

Checking Tier 2 (Integration) tests...
Scanning 45 integration test files...
  ✗ Found 3 mocking violations

Checking Tier 3 (E2E) tests...
Scanning 12 e2e test files...
  ✓ No mocking violations in e2e tests

Checking Tier 1 (Unit) tests (informational only)...
  ℹ Unit tests with mocking: 23 (allowed)

=== Enforcement Summary ===

Tier 2 (Integration) violations: 3
Tier 3 (E2E) violations: 0
Total violations: 3

✗ NO MOCKING POLICY VIOLATION DETECTED

Violations found:
=== Tier 2 (Integration): tests/integration/test_feature.py ===
15:from unittest.mock import patch
23:@patch('module.function')

Action Required:
1. Remove all mock/stub usage from Tier 2 (integration) tests
2. Remove all mock/stub usage from Tier 3 (e2e) tests
3. Use real infrastructure (Docker services) for testing
4. Refer to testing strategy: sdk-users/3-development/testing/

NO MOCKING in Tiers 2-3 is MANDATORY
```

## GitHub Actions Workflow

### Workflow File: `.github/workflows/stub-check.yml`

**Triggers**:
- Pull requests to `main` or `develop`
- Pushes to `main` or `develop`

**Jobs**:

1. **stub-detection**: Runs `detect_stubs.sh`
2. **stub-registry-validation**: Runs `validate_stub_registry.sh`
3. **no-mocking-enforcement**: Runs `enforce_no_mocking.sh`
4. **comprehensive-check**: Generates summary report
5. **pr-comment**: Comments on PR with results (if failures)

**Artifacts**:
All jobs upload artifacts on failure:
- Detection logs
- Violation reports
- Registry validation results

**Permissions**:
- `pull-requests: write` for PR comments

### CI Status Badges

Add to README:
```markdown
![Stub Detection](https://github.com/org/repo/workflows/Stub%20Detection%20and%20NO%20MOCKING%20Enforcement/badge.svg)
```

## Local Development Workflow

### Pre-commit Hook (Recommended)

Create `.git/hooks/pre-commit`:
```bash
#!/bin/bash

echo "Running stub detection..."
./scripts/detect_stubs.sh || exit 1

echo "Validating stub registry..."
./scripts/validate_stub_registry.sh || exit 1

echo "Enforcing NO MOCKING policy..."
./scripts/enforce_no_mocking.sh || exit 1

echo "All checks passed!"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### Pre-push Checks

Create `.git/hooks/pre-push`:
```bash
#!/bin/bash

echo "Running comprehensive checks before push..."

# Run all checks
./scripts/detect_stubs.sh --verbose
STUB_CHECK=$?

./scripts/validate_stub_registry.sh
REGISTRY_CHECK=$?

./scripts/enforce_no_mocking.sh --verbose
MOCKING_CHECK=$?

# Report results
if [ $STUB_CHECK -ne 0 ] || [ $REGISTRY_CHECK -ne 0 ] || [ $MOCKING_CHECK -ne 0 ]; then
    echo ""
    echo "❌ Pre-push checks failed!"
    echo "   Stub check: $STUB_CHECK"
    echo "   Registry check: $REGISTRY_CHECK"
    echo "   Mocking check: $MOCKING_CHECK"
    exit 1
fi

echo "✓ All pre-push checks passed!"
```

### Manual Checks

```bash
# Run all checks
./scripts/detect_stubs.sh && \
./scripts/validate_stub_registry.sh && \
./scripts/enforce_no_mocking.sh

# Run specific check
./scripts/detect_stubs.sh --verbose
```

## Best Practices

### 1. Avoiding Stub Implementations

**DO**:
- Implement real functionality from the start
- Use feature flags for incomplete features
- Break work into smaller, fully-implemented increments

**DON'T**:
- Add stub implementations expecting to "fix later"
- Use placeholder return values
- Leave `NotImplementedError` in production code

### 2. Managing Intentional Stubs

If a stub is absolutely necessary:

1. **Document thoroughly** in `STUB_IMPLEMENTATIONS_REGISTRY.md`
2. **Include justification** - why is this stub needed?
3. **Set completion date** - when will it be implemented?
4. **Create tracking issue** - link to GitHub issue
5. **Review regularly** - update or remove stale entries

### 3. NO MOCKING in Integration/E2E Tests

**Why NO MOCKING?**
- Mocks hide real integration failures
- Real infrastructure validates actual behavior
- Configuration errors are caught
- Production confidence increases

**Use real infrastructure**:
```python
# ❌ WRONG - Mocking database
@patch('database.connect')
def test_integration(mock_db):
    mock_db.return_value = fake_connection

# ✅ CORRECT - Real database
async def test_integration(test_suite):
    async with test_suite.get_connection() as conn:
        result = await conn.execute(...)
```

**Test environment setup**:
```bash
# Start test infrastructure
./tests/utils/test-env up

# Verify services ready
./tests/utils/test-env status

# Run integration tests
pytest tests/integration/
```

### 4. Handling False Positives

If a pattern is incorrectly flagged:

**Stub detection**:
- Add to exclusion list in script
- Refactor code to avoid flagged patterns
- Document in registry if legitimately needed

**NO MOCKING enforcement**:
- Move mocking to Tier 1 (unit tests)
- Use real infrastructure instead
- Refactor to eliminate need for mocking

## Troubleshooting

### Script Permissions

If scripts aren't executable:
```bash
chmod +x scripts/detect_stubs.sh
chmod +x scripts/validate_stub_registry.sh
chmod +x scripts/enforce_no_mocking.sh
```

### CI Failures

**Stub detection failing**:
1. Review detected stubs in CI output
2. Replace with real implementations
3. Or document in registry with justification

**Registry validation failing**:
1. Check file paths are correct
2. Verify stubs actually exist
3. Update registry to match code

**NO MOCKING enforcement failing**:
1. Review violations in CI output
2. Remove mocking from integration/e2e tests
3. Use IntegrationTestSuite for real infrastructure

### Local vs CI Differences

If checks pass locally but fail in CI:
1. Ensure scripts are committed and executable
2. Verify file paths are consistent
3. Check for platform-specific patterns (Windows vs Unix)

## Configuration

### Customizing Stub Patterns

Edit `scripts/detect_stubs.sh`:
```bash
declare -a STUB_PATTERNS=(
    "STUB implementation"
    "your custom pattern"
    # Add more patterns
)
```

### Customizing Exclusions

Edit exclusion lists in scripts:
```bash
declare -a EXCLUDE_PATTERNS=(
    "*/tests/*"
    "*/custom_exclude/*"
    # Add more exclusions
)
```

### Adjusting Mock Patterns

Edit `scripts/enforce_no_mocking.sh`:
```bash
declare -a MOCK_PATTERNS=(
    "from unittest.mock import"
    "your custom mock pattern"
    # Add more patterns
)
```

## Metrics and Reporting

### CI Summary

GitHub Actions generates a summary in the PR:
- ✅/❌ Status for each check
- Violation counts
- Action items
- Policy reminders

### Artifact Storage

Failed checks upload artifacts:
- `stub-detection-results`
- `stub-registry-validation-results`
- `no-mocking-enforcement-results`

Retention: 30 days

### Metrics to Track

Monitor over time:
- Stub detection failures per PR
- Registry entries added/removed
- NO MOCKING violations
- Time to fix violations

## References

### Documentation
- Testing Strategy: `sdk-users/3-development/testing/regression-testing-strategy.md`
- Test Organization: `sdk-users/3-development/testing/test-organization-policy.md`
- Production Testing: `sdk-users/3-development/12-testing-production-quality.md`

### Scripts
- Stub Detection: `scripts/detect_stubs.sh`
- Registry Validation: `scripts/validate_stub_registry.sh`
- NO MOCKING Enforcement: `scripts/enforce_no_mocking.sh`

### CI/CD
- GitHub Workflow: `.github/workflows/stub-check.yml`
- Test README: `tests/README.md`

## Support

For questions or issues:
1. Check this guide first
2. Review script output for specific errors
3. Consult testing documentation
4. Create GitHub issue if needed
