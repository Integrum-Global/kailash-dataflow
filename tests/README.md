# DataFlow Test Suite

## 🚨 CRITICAL: Test Location

**All DataFlow tests MUST be in this directory (`apps/kailash-dataflow/tests/`)**
- ✅ CORRECT: `apps/kailash-dataflow/tests/unit/test_models.py`
- ❌ WRONG: `tests/unit/dataflow/test_models.py` (This is for SDK core tests only!)

DataFlow is an application built using the Kailash SDK, not part of the SDK core. Therefore, all DataFlow-specific tests belong in the DataFlow app directory.

## Test Organization

```
apps/kailash-dataflow/tests/
├── unit/                    # Unit tests for DataFlow components
│   ├── dataflow/           # Core DataFlow functionality
│   └── nodes/              # Generated node tests
├── integration/            # Integration tests
│   ├── dataflow/          # Database integration tests
│   └── workflows/         # Workflow integration tests
├── e2e/                   # End-to-end tests
│   └── dataflow/         # Complete scenarios
├── conftest.py           # Shared fixtures for DataFlow tests
└── README.md            # This file
```

## Test Categories

### Unit Tests (`unit/`)
- Model registration and validation
- Node generation and parameters
- SQL generation and type mapping
- Configuration management
- Error handling

### Integration Tests (`integration/`)
- Database connection pooling
- Multi-database support
- Enterprise features (multi-tenancy, audit)
- Performance validation
- AsyncSQL integration

### End-to-End Tests (`e2e/`)
- Documentation examples validation
- Package installation experience
- Real application building
- Production readiness

## Running Tests

From the DataFlow app directory:
```bash
# Run all DataFlow tests
pytest apps/kailash-dataflow/tests/

# Run specific test tier
pytest apps/kailash-dataflow/tests/unit/
pytest apps/kailash-dataflow/tests/integration/
pytest apps/kailash-dataflow/tests/e2e/

# Run with coverage
pytest apps/kailash-dataflow/tests/ --cov=apps/kailash-dataflow/src/dataflow
```

## Test Guidelines

1. **Isolation**: DataFlow tests should not depend on SDK core tests
2. **Self-contained**: Each test should set up its own test data
3. **No external dependencies**: Tests should work with SQLite (default)
4. **Meaningful assertions**: Test actual functionality, not just existence
5. **Edge cases**: Include error conditions and boundary testing

## 🚨 NO MOCKING Policy & Stub Detection

### Automated Enforcement
All pull requests are automatically checked for:
1. **Stub implementations** in production code
2. **Stub registry** synchronization
3. **NO MOCKING** policy compliance in Tier 2/3 tests

### Running Local Checks

Before submitting a PR, run these checks locally:

```bash
# Check for stub implementations
./scripts/detect_stubs.sh

# Validate stub registry
./scripts/validate_stub_registry.sh

# Enforce NO MOCKING policy
./scripts/enforce_no_mocking.sh
```

### NO MOCKING Policy by Tier

**Tier 1 (Unit Tests)**: `tests/unit/`
- ✅ Mocking **allowed** for external services
- ✅ Use SQLite for database operations
- ✅ Mock complex dependencies

**Tier 2 (Integration Tests)**: `tests/integration/`
- ❌ **NO MOCKING** - ABSOLUTELY FORBIDDEN
- ✅ Use real Docker services (PostgreSQL on port 5434)
- ✅ Use IntegrationTestSuite fixture
- ❌ Never use `@patch`, `Mock()`, `MagicMock()`, `AsyncMock()`

**Tier 3 (E2E Tests)**: `tests/e2e/`
- ❌ **NO MOCKING** - ABSOLUTELY FORBIDDEN
- ✅ Use complete real infrastructure stack
- ✅ Use IntegrationTestSuite fixture
- ❌ Never use any mocking frameworks

### Stub Implementations

If you need to add a temporary stub implementation:

1. **Document in registry**: Add entry to `STUB_IMPLEMENTATIONS_REGISTRY.md`
2. **Include justification**: Explain why stub is necessary
3. **Set completion date**: Target date for real implementation
4. **Create tracking issue**: Link to GitHub issue

Example registry entry:
```markdown
### Stub: MyFeature
- **File**: `src/dataflow/feature.py`
- **Line**: 123-145
- **Function/Class**: `MyClass.my_method`
- **Reason**: Waiting for dependency X to be released
- **Planned Completion**: 2025-02-01
- **Tracking Issue**: #456
```

### Why NO MOCKING in Tiers 2-3?

1. **Real-world validation**: Mocks hide integration failures
2. **Production confidence**: Tests prove system works with real infrastructure
3. **Configuration validation**: Real services catch config errors
4. **True integration**: Component interactions are validated properly

### Common Violations

```python
# ❌ WRONG - Mocking in integration test
@pytest.mark.integration
@patch('dataflow.database.connect')
def test_database_operation(mock_connect):
    mock_connect.return_value = fake_connection

# ✅ CORRECT - Real infrastructure
@pytest.mark.integration
async def test_database_operation(test_suite):
    async with test_suite.get_connection() as conn:
        result = await conn.execute(...)
```

## Common Fixtures

See `conftest.py` for shared fixtures like:
- `dataflow_db`: Fresh DataFlow instance for each test
- `test_model`: Sample model for testing
- `mock_runtime`: Mocked LocalRuntime for unit tests **ONLY**
- `test_suite`: IntegrationTestSuite for integration/e2e tests
