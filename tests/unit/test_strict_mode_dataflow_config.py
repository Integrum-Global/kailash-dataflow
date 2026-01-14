"""
Unit tests for DataFlow global strict mode configuration.

Tests DataFlow class strict_mode and strict_level parameters, ensuring:
1. Global strict mode configuration works correctly
2. Per-model override via __dataflow__ dict works
3. Precedence rules are followed: __dataflow__ > decorator > global
4. Backward compatibility (default strict=False)
5. StrictLevel enum works (RELAXED, MODERATE, AGGRESSIVE)
"""

import pytest
from dataflow import DataFlow
from dataflow.decorators import ValidationMode, model
from dataflow.exceptions import ModelValidationError
from dataflow.validators.strict_mode_validator import StrictLevel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


@pytest.fixture
def memory_db():
    """Create in-memory SQLite database for testing."""
    return DataFlow(":memory:")


@pytest.fixture
def base():
    """Create SQLAlchemy declarative base."""
    return declarative_base()


# ==============================================================================
# Test 1: Global strict_mode Parameter in DataFlow.__init__()
# ==============================================================================


def test_dataflow_init_accepts_strict_mode_parameter():
    """Test that DataFlow.__init__() accepts strict_mode parameter."""
    # Should not raise error
    db = DataFlow(":memory:", strict_mode=True)
    assert hasattr(db, "strict_mode")
    assert db.strict_mode is True


def test_dataflow_init_accepts_strict_mode_false():
    """Test that DataFlow.__init__() accepts strict_mode=False."""
    db = DataFlow(":memory:", strict_mode=False)
    assert hasattr(db, "strict_mode")
    assert db.strict_mode is False


def test_dataflow_init_strict_mode_defaults_to_false():
    """Test that strict_mode defaults to False (backward compatible)."""
    db = DataFlow(":memory:")
    assert hasattr(db, "strict_mode")
    assert db.strict_mode is False


# ==============================================================================
# Test 2: strict_mode Stored in DataFlow Instance
# ==============================================================================


def test_dataflow_stores_strict_mode_value():
    """Test that DataFlow instance stores strict_mode value."""
    db_strict = DataFlow(":memory:", strict_mode=True)
    db_warn = DataFlow(":memory:", strict_mode=False)

    assert db_strict.strict_mode is True
    assert db_warn.strict_mode is False


def test_dataflow_strict_mode_accessible():
    """Test that strict_mode is accessible from DataFlow instance."""
    db = DataFlow(":memory:", strict_mode=True)

    # Should be accessible
    assert db.strict_mode is True
    assert isinstance(db.strict_mode, bool)


# ==============================================================================
# Test 3: Per-Model Override Works Correctly
# ==============================================================================


def test_per_model_override_via_dataflow_dict(memory_db, base):
    """Test that __dataflow__['strict'] overrides global strict_mode."""
    # Global strict_mode=False
    memory_db.strict_mode = False

    # Model with __dataflow__={'strict': True} should fail validation
    with pytest.raises(ModelValidationError):

        @model(strict=False)  # Decorator says False
        class User(base):
            __tablename__ = "users_override_1"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name

            __dataflow__ = {"strict": True}  # This should win!


def test_per_model_override_allows_opt_out(memory_db, base):
    """Test that __dataflow__['strict']=False allows opt-out from global strict."""
    # Global strict_mode=True
    memory_db.strict_mode = True

    # Model with __dataflow__={'strict': False} should NOT raise
    try:

        @model  # Should inherit global strict_mode
        class User(base):
            __tablename__ = "users_override_2"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name

            __dataflow__ = {"strict": False}  # Opt out

        # If we get here, opt-out worked
        assert True
    except ModelValidationError:
        pytest.fail("__dataflow__['strict']=False should override global strict_mode")


# ==============================================================================
# Test 4: Precedence Rules (__dataflow__ > decorator > global)
# ==============================================================================


def test_precedence_dataflow_dict_beats_decorator():
    """Test that __dataflow__['strict'] overrides decorator parameter."""
    # This test should raise because __dataflow__['strict']=True wins over decorator strict=False

    base_local = declarative_base()

    with pytest.raises(ModelValidationError):

        @model(strict=False)  # Decorator says False
        class User(base_local):
            __tablename__ = "users_precedence_1"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name

            __dataflow__ = {"strict": True}  # This should win!


def test_precedence_dataflow_dict_beats_global():
    """Test that __dataflow__['strict'] overrides global strict_mode."""
    db = DataFlow(":memory:", strict_mode=False)  # Global says False
    base_local = declarative_base()

    with pytest.raises(ModelValidationError):

        @model  # Should read from global (False), but __dataflow__ wins
        class User(base_local):
            __tablename__ = "users_precedence_2"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name

            __dataflow__ = {"strict": True}  # This should win!


def test_precedence_decorator_beats_global():
    """Test that decorator strict=True overrides global strict_mode=False."""
    db = DataFlow(":memory:", strict_mode=False)  # Global says False
    base_local = declarative_base()

    with pytest.raises(ModelValidationError):

        @model(strict=True)  # Decorator says True
        class User(base_local):
            __tablename__ = "users_precedence_3"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name


def test_precedence_global_is_fallback():
    """Test that global strict_mode is used when no override exists."""
    db = DataFlow(":memory:", strict_mode=True)  # Global says True
    base_local = declarative_base()

    # Model with no __dataflow__ and no decorator parameter should use global
    with pytest.raises(ModelValidationError):

        @model  # No strict parameter
        class User(base_local):
            __tablename__ = "users_precedence_4"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            # No __dataflow__ dict


# ==============================================================================
# Test 5: Default is False (Backward Compatible)
# ==============================================================================


def test_default_strict_mode_is_false():
    """Test that default strict_mode is False (backward compatible)."""
    db = DataFlow(":memory:")
    assert db.strict_mode is False


def test_default_allows_non_id_primary_key():
    """Test that default mode (strict=False) allows non-id primary keys."""
    db = DataFlow(":memory:")  # strict_mode=False by default
    base_local = declarative_base()

    # Should not raise (only warning in WARN mode)
    try:

        @model  # Uses default WARN mode
        class User(base_local):
            __tablename__ = "users_default"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            name: str = Column(String)

        # Success - WARN mode allows this
        assert True
    except ModelValidationError:
        pytest.fail("Default mode should be WARN, not STRICT")


# ==============================================================================
# Test 6: Validation Propagates to Model Registration
# ==============================================================================


def test_global_strict_mode_propagates_to_models():
    """Test that global strict_mode propagates to model validation."""
    db = DataFlow(":memory:", strict_mode=True)
    base_local = declarative_base()

    # Model should fail validation due to global strict_mode
    with pytest.raises(ModelValidationError):

        @model  # Should read from global strict_mode
        class User(base_local):
            __tablename__ = "users_propagate"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name


def test_global_strict_false_allows_models():
    """Test that global strict_mode=False allows models to register."""
    db = DataFlow(":memory:", strict_mode=False)
    base_local = declarative_base()

    # Model should register successfully (WARN mode)
    try:

        @model
        class User(base_local):
            __tablename__ = "users_allow"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            name: str = Column(String)

        assert True
    except ModelValidationError:
        pytest.fail("strict_mode=False should allow model registration")


# ==============================================================================
# Test 7: strict_level Parameter (RELAXED, MODERATE, AGGRESSIVE)
# ==============================================================================


def test_dataflow_init_accepts_strict_level_parameter():
    """Test that DataFlow.__init__() accepts strict_level parameter."""
    db = DataFlow(":memory:", strict_mode=True, strict_level=StrictLevel.RELAXED)
    assert hasattr(db, "strict_level")
    assert db.strict_level == StrictLevel.RELAXED


def test_strict_level_defaults_to_moderate():
    """Test that strict_level defaults to MODERATE."""
    db = DataFlow(":memory:", strict_mode=True)
    assert hasattr(db, "strict_level")
    assert db.strict_level == StrictLevel.MODERATE


def test_strict_level_relaxed():
    """Test that StrictLevel.RELAXED works."""
    db = DataFlow(":memory:", strict_mode=True, strict_level=StrictLevel.RELAXED)
    assert db.strict_level == StrictLevel.RELAXED


def test_strict_level_moderate():
    """Test that StrictLevel.MODERATE works."""
    db = DataFlow(":memory:", strict_mode=True, strict_level=StrictLevel.MODERATE)
    assert db.strict_level == StrictLevel.MODERATE


def test_strict_level_aggressive():
    """Test that StrictLevel.AGGRESSIVE works."""
    db = DataFlow(":memory:", strict_mode=True, strict_level=StrictLevel.AGGRESSIVE)
    assert db.strict_level == StrictLevel.AGGRESSIVE


# ==============================================================================
# Test 8: Integration with Model Validation
# ==============================================================================


def test_strict_mode_enforces_primary_key_validation():
    """Test that strict_mode=True enforces primary key validation."""
    db = DataFlow(":memory:", strict_mode=True)
    base_local = declarative_base()

    # Should fail due to non-id primary key
    with pytest.raises(ModelValidationError) as exc_info:

        @model
        class User(base_local):
            __tablename__ = "users_pk_validation"
            __table_args__ = {"extend_existing": True}

            user_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            name: str = Column(String)

    # Check error message
    errors = exc_info.value.args[0]
    assert any("STRICT-001" in str(err) for err in errors)


def test_strict_mode_enforces_auto_managed_fields():
    """Test that strict_mode=True enforces auto-managed field validation."""
    db = DataFlow(":memory:", strict_mode=True)
    base_local = declarative_base()

    # Should fail due to created_at conflict
    with pytest.raises(ModelValidationError) as exc_info:

        @model
        class User(base_local):
            __tablename__ = "users_auto_managed"
            __table_args__ = {"extend_existing": True}

            id: int = Column(Integer, primary_key=True)
            created_at: str = Column(String)  # Conflicts with auto-managed field

    # Check error message
    errors = exc_info.value.args[0]
    assert any("STRICT-002" in str(err) for err in errors)


# ==============================================================================
# Test 9: Complex Scenarios
# ==============================================================================


def test_multiple_models_with_different_strict_settings():
    """Test that multiple models can have different strict settings."""
    db = DataFlow(":memory:", strict_mode=False)  # Global off
    base_local = declarative_base()

    # Model 1: Uses global (WARN mode) - should succeed
    try:

        @model
        class Product(base_local):
            __tablename__ = "products_multi"
            __table_args__ = {"extend_existing": True}

            product_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            name: str = Column(String)

        assert True
    except ModelValidationError:
        pytest.fail("Global strict=False should allow Product")

    # Model 2: Opts into strict mode - should fail
    with pytest.raises(ModelValidationError):

        @model(strict=True)
        class Order(base_local):
            __tablename__ = "orders_multi"
            __table_args__ = {"extend_existing": True}

            order_id: int = Column(Integer, primary_key=True)  # Wrong PK name
            total: int = Column(Integer)


def test_strict_mode_with_valid_model():
    """Test that strict_mode=True allows valid models."""
    db = DataFlow(":memory:", strict_mode=True)
    base_local = declarative_base()

    # Valid model should register successfully even in strict mode
    try:

        @model
        class User(base_local):
            __tablename__ = "users_valid"
            __table_args__ = {"extend_existing": True}

            id: int = Column(Integer, primary_key=True)  # Correct PK name
            name: str = Column(String)
            email: str = Column(String)

        assert True
    except ModelValidationError:
        pytest.fail("Valid model should register in strict mode")


def test_strict_mode_integration_end_to_end():
    """Test complete end-to-end flow of strict mode."""
    # 1. Create DataFlow with strict mode
    db = DataFlow(":memory:", strict_mode=True, strict_level=StrictLevel.MODERATE)

    # 2. Verify configuration
    assert db.strict_mode is True
    assert db.strict_level == StrictLevel.MODERATE

    base_local = declarative_base()

    # 3. Invalid model should fail
    with pytest.raises(ModelValidationError):

        @model
        class InvalidModel(base_local):
            __tablename__ = "invalid_model"
            __table_args__ = {"extend_existing": True}

            pk: int = Column(Integer, primary_key=True)  # Wrong PK name

    # 4. Valid model should succeed
    try:

        @model
        class ValidModel(base_local):
            __tablename__ = "valid_model"
            __table_args__ = {"extend_existing": True}

            id: int = Column(Integer, primary_key=True)  # Correct!
            name: str = Column(String)

        assert True
    except ModelValidationError:
        pytest.fail("Valid model should register")

    # 5. Override with __dataflow__ should work
    try:

        @model
        class OptOutModel(base_local):
            __tablename__ = "opt_out_model"
            __table_args__ = {"extend_existing": True}

            custom_id: int = Column(Integer, primary_key=True)  # Wrong, but opt-out

            __dataflow__ = {"strict": False}  # Opt out

        assert True
    except ModelValidationError:
        pytest.fail("__dataflow__ opt-out should work")
