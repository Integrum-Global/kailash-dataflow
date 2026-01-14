"""
Unit tests for strict mode model validation.

Tests the strict mode validation feature that enforces best practices
at model registration time.

Test Coverage:
- STRICT-001: Primary key must be named 'id'
- STRICT-002: No conflicts with auto-managed fields
- STRICT-007: Field naming conventions
- Global strict mode configuration
- Per-model strict mode override
- Precedence rules (__dataflow__ > decorator > global)
- Backward compatibility
- Error message quality
"""

import pytest
from dataflow import DataFlow
from dataflow.decorators import ValidationMode
from dataflow.exceptions import ModelValidationError
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import declarative_base

# ==============================================================================
# Test Fixtures
# ==============================================================================


@pytest.fixture
def base():
    """Create fresh declarative_base for each test to avoid table conflicts."""
    return declarative_base()


@pytest.fixture
def memory_db():
    """Create in-memory SQLite database for testing."""
    return DataFlow(":memory:")


@pytest.fixture
def strict_memory_db():
    """Create in-memory SQLite database with global strict mode."""
    return DataFlow(":memory:", strict_mode=True)


# ==============================================================================
# STRICT-001: Primary Key Validation
# ==============================================================================


def test_strict_mode_enforces_id_primary_key(strict_memory_db, base):
    """Test that strict mode requires primary key to be named 'id'."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)
            name = Column(String)

    # Verify error code and message
    error = exc_info.value
    assert any(
        "STRICT-001" in str(e) for e in error.errors
    ), "Expected STRICT-001 error code"
    assert "primary key" in str(error).lower()
    assert "id" in str(error).lower()


def test_strict_mode_allows_id_primary_key(strict_memory_db, base):
    """Test that strict mode allows primary key named 'id'."""

    # Should not raise
    @strict_memory_db.model(strict=True)
    class User(base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        name = Column(String)

    assert User is not None


def test_strict_mode_blocks_missing_primary_key(strict_memory_db, base):
    """Test that strict mode blocks models without primary key."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            name = Column(String)

    error = exc_info.value
    assert any(
        "STRICT-001" in str(e) for e in error.errors
    ), "Expected STRICT-001 error code"
    assert "primary key" in str(error).lower()


def test_warn_mode_allows_non_id_primary_key(memory_db, base):
    """Test that WARN mode allows primary key with non-'id' name (backward compatible)."""

    # Should not raise, only warn
    @memory_db.model  # Default: validation=WARN
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)
        name = Column(String)

    assert User is not None


# ==============================================================================
# STRICT-002: Auto-Managed Field Conflicts
# ==============================================================================


def test_strict_mode_blocks_created_at_conflict(strict_memory_db, base):
    """Test that strict mode blocks user-defined 'created_at' field."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            id = Column(String, primary_key=True)
            name = Column(String)
            created_at = Column(DateTime)  # Conflicts with auto-managed field

    error = exc_info.value
    assert any(
        "STRICT-002" in str(e) for e in error.errors
    ), "Expected STRICT-002 error code"
    assert "created_at" in str(error).lower()
    assert "auto" in str(error).lower()


def test_strict_mode_blocks_updated_at_conflict(strict_memory_db, base):
    """Test that strict mode blocks user-defined 'updated_at' field."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            id = Column(String, primary_key=True)
            name = Column(String)
            updated_at = Column(DateTime)  # Conflicts with auto-managed field

    error = exc_info.value
    assert any(
        "STRICT-002" in str(e) for e in error.errors
    ), "Expected STRICT-002 error code"
    assert "updated_at" in str(error).lower()


def test_strict_mode_blocks_created_by_conflict(strict_memory_db, base):
    """Test that strict mode blocks user-defined 'created_by' field."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            id = Column(String, primary_key=True)
            name = Column(String)
            created_by = Column(String)  # Conflicts with auto-managed field

    error = exc_info.value
    assert any(
        "STRICT-002" in str(e) for e in error.errors
    ), "Expected STRICT-002 error code"
    assert "created_by" in str(error).lower()


def test_strict_mode_blocks_updated_by_conflict(strict_memory_db, base):
    """Test that strict mode blocks user-defined 'updated_by' field."""
    with pytest.raises(ModelValidationError) as exc_info:

        @strict_memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            id = Column(String, primary_key=True)
            name = Column(String)
            updated_by = Column(String)  # Conflicts with auto-managed field

    error = exc_info.value
    assert any(
        "STRICT-002" in str(e) for e in error.errors
    ), "Expected STRICT-002 error code"
    assert "updated_by" in str(error).lower()


def test_warn_mode_allows_auto_managed_conflicts(memory_db, base):
    """Test that WARN mode allows auto-managed field conflicts (backward compatible)."""

    # Should not raise, only warn
    @memory_db.model  # Default: validation=WARN
    class User(base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        created_at = Column(DateTime)

    assert User is not None


# ==============================================================================
# STRICT-007: Field Naming Conventions
# ==============================================================================


def test_strict_mode_warns_about_camelcase(strict_memory_db, base):
    """Test that strict mode warns about camelCase field names (not error)."""

    # Should not raise error - naming is a warning, not critical
    @strict_memory_db.model(strict=True)
    class User(base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        userName = Column(String)  # camelCase - should warn

    assert User is not None


def test_strict_mode_warns_about_sql_reserved_words(strict_memory_db, base):
    """Test that strict mode warns about SQL reserved words (not error)."""

    # Should not raise error - naming is a warning, not critical
    @strict_memory_db.model(strict=True)
    class User(base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        order = Column(String)  # SQL reserved word - should warn

    assert User is not None


# ==============================================================================
# Global Strict Mode Configuration
# ==============================================================================


def test_global_strict_mode_enforces_all_models(strict_memory_db, base):
    """Test that global strict mode applies to all models by default."""
    # strict_memory_db has global strict_mode=True
    with pytest.raises(ModelValidationError):

        @strict_memory_db.model
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)  # Wrong PK name

    with pytest.raises(ModelValidationError):

        @strict_memory_db.model
        class Product(base):
            __tablename__ = "products"
            id = Column(String, primary_key=True)
            created_at = Column(DateTime)  # Auto-managed conflict


def test_global_strict_mode_disabled_by_default(memory_db, base):
    """Test that global strict mode is disabled by default (backward compatible)."""

    # memory_db has strict_mode=False (default)
    # Should not raise - only warns
    @memory_db.model
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

    assert User is not None


# ==============================================================================
# Per-Model Strict Mode Override
# ==============================================================================


def test_per_model_strict_overrides_global_off(memory_db, base):
    """Test that per-model strict=True overrides global strict=False."""
    # Global: strict_mode=False
    # Per-model: strict=True
    with pytest.raises(ModelValidationError):

        @memory_db.model(strict=True)
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)  # Should fail


def test_per_model_strict_off_overrides_global_on(strict_memory_db, base):
    """Test that per-model strict=False overrides global strict=True."""

    # Global: strict_mode=True
    # Per-model: strict=False
    # Should not raise
    @strict_memory_db.model(strict=False)
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)  # Should not fail

    assert User is not None


def test_dataflow_dict_strict_overrides_decorator(memory_db, base):
    """Test that __dataflow__ strict overrides decorator parameter."""
    # Decorator: strict=False
    # __dataflow__: strict=True
    # __dataflow__ should win
    with pytest.raises(ModelValidationError):

        @memory_db.model(strict=False)
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)

            __dataflow__ = {"strict": True}  # Highest precedence


def test_dataflow_dict_strict_overrides_global(strict_memory_db, base):
    """Test that __dataflow__ strict overrides global strict mode."""

    # Global: strict_mode=True
    # __dataflow__: strict=False
    # __dataflow__ should win
    @strict_memory_db.model
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

        __dataflow__ = {"strict": False}  # Highest precedence

    assert User is not None


# ==============================================================================
# Precedence Rules Testing
# ==============================================================================


def test_precedence_dataflow_dict_wins_over_all(base):
    """Test precedence: __dataflow__ dict > decorator > global."""
    # Global: strict_mode=True
    db = DataFlow(":memory:", strict_mode=True)

    # __dataflow__ = False should win
    @db.model(strict=True)
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

        __dataflow__ = {"strict": False}

    assert User is not None


def test_precedence_decorator_wins_over_global(base):
    """Test precedence: decorator > global."""
    # Global: strict_mode=True
    db = DataFlow(":memory:", strict_mode=True)

    # Decorator strict=False should win
    @db.model(strict=False)
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

    assert User is not None


def test_precedence_global_is_default(base):
    """Test precedence: global is used when no overrides."""
    # Global: strict_mode=True
    db = DataFlow(":memory:", strict_mode=True)

    # No overrides - global should apply
    with pytest.raises(ModelValidationError):

        @db.model
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)


# ==============================================================================
# Backward Compatibility
# ==============================================================================


def test_default_behavior_unchanged(base):
    """Test that default behavior is unchanged (backward compatible)."""
    # Default: strict_mode=False, validation=WARN
    db = DataFlow(":memory:")

    # Should not raise - only warns
    @db.model
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)
        created_at = Column(DateTime)

    assert User is not None


def test_existing_code_unaffected(base):
    """Test that existing code without strict mode is unaffected."""
    db = DataFlow(":memory:")

    # All these should work (backward compatible)
    @db.model
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

    @db.model
    class Product(base):
        __tablename__ = "products"
        product_id = Column(Integer, primary_key=True)
        created_at = Column(DateTime)

    @db.model
    class Order(base):
        __tablename__ = "orders"
        id = Column(String, primary_key=True)
        userName = Column(String)  # camelCase

    assert User is not None
    assert Product is not None
    assert Order is not None


# ==============================================================================
# Error Message Quality
# ==============================================================================


def test_error_message_includes_code(base):
    """Test that error messages include STRICT-XXX error codes."""
    db = DataFlow(":memory:", strict_mode=True)

    with pytest.raises(ModelValidationError) as exc_info:

        @db.model
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)

    error_msg = str(exc_info.value)
    assert "STRICT-001" in error_msg, "Error message should include error code"


def test_error_message_is_actionable(base):
    """Test that error messages provide actionable guidance."""
    db = DataFlow(":memory:", strict_mode=True)

    with pytest.raises(ModelValidationError) as exc_info:

        @db.model
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)

    error_msg = str(exc_info.value).lower()
    # Should mention what to do
    assert "id" in error_msg or "rename" in error_msg or "primary key" in error_msg


def test_error_message_includes_field_name(base):
    """Test that error messages include the problematic field name."""
    db = DataFlow(":memory:", strict_mode=True)

    with pytest.raises(ModelValidationError) as exc_info:

        @db.model
        class User(base):
            __tablename__ = "users"
            id = Column(String, primary_key=True)
            created_at = Column(DateTime)

    error_msg = str(exc_info.value)
    assert "created_at" in error_msg, "Error message should include field name"


def test_multiple_errors_reported(base):
    """Test that multiple errors are reported together."""
    db = DataFlow(":memory:", strict_mode=True)

    with pytest.raises(ModelValidationError) as exc_info:

        @db.model
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)  # STRICT-001
            created_at = Column(DateTime)  # STRICT-002
            updated_at = Column(DateTime)  # STRICT-002

    error = exc_info.value
    # Should have multiple errors
    assert len(error.errors) >= 2, "Should report multiple errors"


# ==============================================================================
# Edge Cases
# ==============================================================================


def test_strict_mode_with_validation_off(base):
    """Test that strict=True with validation=OFF still validates."""
    db = DataFlow(":memory:")

    # strict=True should enable validation even if ValidationMode.OFF
    with pytest.raises(ModelValidationError):

        @db.model(strict=True, validation=ValidationMode.OFF)
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)


def test_strict_mode_with_skip_validation(base):
    """Test that skip_validation=True disables strict mode."""
    db = DataFlow(":memory:", strict_mode=True)

    # skip_validation should override strict mode
    @db.model(skip_validation=True)
    class User(base):
        __tablename__ = "users"
        user_id = Column(Integer, primary_key=True)

    assert User is not None


def test_strict_mode_with_none_strict(base):
    """Test that strict=None falls back to global setting."""
    db = DataFlow(":memory:", strict_mode=True)

    # strict=None should use global setting (True)
    with pytest.raises(ModelValidationError):

        @db.model(strict=None)
        class User(base):
            __tablename__ = "users"
            user_id = Column(Integer, primary_key=True)


# ==============================================================================
# Integration Tests
# ==============================================================================


def test_strict_mode_with_valid_model(base):
    """Test that strict mode accepts valid models."""
    db = DataFlow(":memory:", strict_mode=True)

    @db.model
    class User(base):
        __tablename__ = "users"
        id = Column(String, primary_key=True)
        email = Column(String)
        name = Column(String)

    assert User is not None


def test_strict_mode_mixed_models(base):
    """Test that strict mode can be selectively applied to models."""
    db = DataFlow(":memory:", strict_mode=False)

    # This should pass (strict=False)
    @db.model(strict=False)
    class LegacyUser(base):
        __tablename__ = "legacy_users"
        user_id = Column(Integer, primary_key=True)

    # This should fail (strict=True)
    with pytest.raises(ModelValidationError):

        @db.model(strict=True)
        class NewUser(base):
            __tablename__ = "new_users"
            user_id = Column(Integer, primary_key=True)

    assert LegacyUser is not None
