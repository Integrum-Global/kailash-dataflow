"""
Unit Tests for PostgreSQL Native ARRAY Type Support (DataFlow)

Testing Strategy:
- Tier 1 (Unit): Fast (<1s), isolated, NO external dependencies
- Feature flag parsing from __dataflow__
- Type mapping detection for List[str], List[int], List[float]
- SQL type generation for TEXT[], INTEGER[], REAL[]
- Cross-database validation errors

CRITICAL: These tests are written FIRST before implementation!
DO NOT modify tests to fit code - fix code to pass tests!
"""

from typing import List, Optional

import pytest

# Import the schema parsing components
from dataflow.core.schema import FieldMeta, FieldType, ModelMeta, SchemaParser


class TestArrayTypeDetection:
    """Test detection of List types and their element types."""

    def test_list_str_detected_as_array(self):
        """List[str] annotation detected as ARRAY type."""

        class TestModel:
            tags: List[str]

        meta = SchemaParser.parse_model(TestModel)

        assert "tags" in meta.fields
        field = meta.fields["tags"]
        assert field.type == FieldType.ARRAY
        assert field.array_type == FieldType.STRING

    def test_list_int_detected_as_array(self):
        """List[int] annotation detected as ARRAY type."""

        class TestModel:
            scores: List[int]

        meta = SchemaParser.parse_model(TestModel)

        assert "scores" in meta.fields
        field = meta.fields["scores"]
        assert field.type == FieldType.ARRAY
        assert field.array_type == FieldType.INTEGER

    def test_list_float_detected_as_array(self):
        """List[float] annotation detected as ARRAY type."""

        class TestModel:
            ratings: List[float]

        meta = SchemaParser.parse_model(TestModel)

        assert "ratings" in meta.fields
        field = meta.fields["ratings"]
        assert field.type == FieldType.ARRAY
        assert field.array_type == FieldType.FLOAT

    def test_optional_list_detected_correctly(self):
        """Optional[List[str]] detected as nullable array."""

        class TestModel:
            optional_tags: Optional[List[str]]

        meta = SchemaParser.parse_model(TestModel)

        assert "optional_tags" in meta.fields
        field = meta.fields["optional_tags"]
        assert field.type == FieldType.ARRAY
        assert field.array_type == FieldType.STRING
        assert field.nullable is True

    def test_list_without_type_defaults_to_string(self):
        """List without element type defaults to List[str]."""

        class TestModel:
            generic_list: List

        meta = SchemaParser.parse_model(TestModel)

        assert "generic_list" in meta.fields
        field = meta.fields["generic_list"]
        assert field.type == FieldType.ARRAY
        assert field.array_type == FieldType.STRING  # Default to string


class TestFeatureFlagParsing:
    """Test parsing of use_native_arrays feature flag."""

    def test_feature_flag_enabled(self):
        """__dataflow__ with use_native_arrays=True is parsed correctly."""

        class TestModel:
            tags: List[str]

            __dataflow__ = {"use_native_arrays": True}

        meta = SchemaParser.parse_model(TestModel)

        assert "use_native_arrays" in meta.options
        assert meta.options["use_native_arrays"] is True

    def test_feature_flag_disabled(self):
        """__dataflow__ with use_native_arrays=False is parsed correctly."""

        class TestModel:
            tags: List[str]

            __dataflow__ = {"use_native_arrays": False}

        meta = SchemaParser.parse_model(TestModel)

        assert "use_native_arrays" in meta.options
        assert meta.options["use_native_arrays"] is False

    def test_feature_flag_missing_defaults_false(self):
        """Missing use_native_arrays flag defaults to False."""

        class TestModel:
            tags: List[str]

        meta = SchemaParser.parse_model(TestModel)

        # Default behavior: use_native_arrays not in options or False
        assert meta.options.get("use_native_arrays", False) is False

    def test_feature_flag_with_other_options(self):
        """use_native_arrays works alongside other __dataflow__ options."""

        class TestModel:
            tags: List[str]

            __dataflow__ = {"use_native_arrays": True, "tablename": "custom_table"}

        meta = SchemaParser.parse_model(TestModel)

        assert meta.options["use_native_arrays"] is True
        assert meta.options["tablename"] == "custom_table"


class TestPostgreSQLNativeArrayTypeMapping:
    """Test PostgreSQL-specific SQL type generation for native arrays."""

    def test_list_str_maps_to_text_array_postgresql(self):
        """List[str] with feature flag maps to TEXT[] on PostgreSQL."""
        field = FieldMeta(
            name="tags",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.STRING,
        )

        # PostgreSQL with native arrays
        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=True)
        assert sql_type == "TEXT[]"

    def test_list_int_maps_to_integer_array_postgresql(self):
        """List[int] with feature flag maps to INTEGER[] on PostgreSQL."""
        field = FieldMeta(
            name="scores",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.INTEGER,
        )

        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=True)
        assert sql_type == "INTEGER[]"

    def test_list_float_maps_to_real_array_postgresql(self):
        """List[float] with feature flag maps to REAL[] on PostgreSQL."""
        field = FieldMeta(
            name="ratings",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.FLOAT,
        )

        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=True)
        assert sql_type == "REAL[]"

    def test_list_without_flag_maps_to_jsonb_postgresql(self):
        """List without feature flag maps to JSONB (backward compatible)."""
        field = FieldMeta(
            name="tags", type=FieldType.ARRAY, python_type=list, array_type=None
        )

        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=False)
        assert sql_type == "JSONB"  # Backward compatible default


class TestCrossDatabaseBehavior:
    """Test behavior on different databases with native arrays."""

    def test_mysql_rejects_native_arrays(self):
        """MySQL with use_native_arrays raises validation error."""
        field = FieldMeta(
            name="tags",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.STRING,
        )

        # MySQL doesn't support native arrays
        with pytest.raises(
            ValueError, match="Native arrays only supported on PostgreSQL"
        ):
            field.get_sql_type(dialect="mysql", use_native_arrays=True)

    def test_sqlite_rejects_native_arrays(self):
        """SQLite with use_native_arrays raises validation error."""
        field = FieldMeta(
            name="tags",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.STRING,
        )

        # SQLite doesn't support native arrays
        with pytest.raises(
            ValueError, match="Native arrays only supported on PostgreSQL"
        ):
            field.get_sql_type(dialect="sqlite", use_native_arrays=True)

    def test_mysql_list_without_flag_maps_to_json(self):
        """MySQL List fields map to JSON (backward compatible)."""
        field = FieldMeta(
            name="tags",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.STRING,
        )

        sql_type = field.get_sql_type(dialect="mysql", use_native_arrays=False)
        assert sql_type == "JSON"

    def test_sqlite_list_without_flag_maps_to_text(self):
        """SQLite List fields map to TEXT (backward compatible)."""
        field = FieldMeta(
            name="tags",
            type=FieldType.ARRAY,
            python_type=list,
            array_type=FieldType.STRING,
        )

        sql_type = field.get_sql_type(dialect="sqlite", use_native_arrays=False)
        assert sql_type == "TEXT"


class TestCompleteModelWithArrays:
    """Test complete model parsing with array fields."""

    def test_model_with_multiple_array_types(self):
        """Model with multiple array types parses correctly."""

        class AgentMemory:
            id: str
            tags: List[str]
            scores: List[int]
            ratings: List[float]
            description: str

            __dataflow__ = {"use_native_arrays": True}

        meta = SchemaParser.parse_model(AgentMemory)

        # Check all fields parsed
        assert "id" in meta.fields
        assert "tags" in meta.fields
        assert "scores" in meta.fields
        assert "ratings" in meta.fields
        assert "description" in meta.fields

        # Check array types
        assert meta.fields["tags"].type == FieldType.ARRAY
        assert meta.fields["tags"].array_type == FieldType.STRING

        assert meta.fields["scores"].type == FieldType.ARRAY
        assert meta.fields["scores"].array_type == FieldType.INTEGER

        assert meta.fields["ratings"].type == FieldType.ARRAY
        assert meta.fields["ratings"].array_type == FieldType.FLOAT

        # Check non-array field
        assert meta.fields["description"].type == FieldType.STRING

        # Check feature flag
        assert meta.options["use_native_arrays"] is True

    def test_model_without_feature_flag_backward_compatible(self):
        """Model without feature flag uses backward compatible JSON storage."""

        class OldModel:
            id: str
            tags: List[str]

        meta = SchemaParser.parse_model(OldModel)

        # Array detected but no feature flag
        assert meta.fields["tags"].type == FieldType.ARRAY
        assert meta.options.get("use_native_arrays", False) is False

        # Should generate JSONB on PostgreSQL (backward compatible)
        field = meta.fields["tags"]
        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=False)
        assert sql_type == "JSONB"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_list_with_unsupported_element_type(self):
        """List with unsupported element type defaults to JSON."""

        class CustomType:
            value: str

        class TestModel:
            custom_list: List[CustomType]

        meta = SchemaParser.parse_model(TestModel)

        # Should detect as array but with JSON/unknown element type
        assert meta.fields["custom_list"].type == FieldType.ARRAY
        # Complex types default to JSON
        assert meta.fields["custom_list"].array_type == FieldType.JSON

    def test_nested_list_not_supported(self):
        """Nested List[List[str]] not supported, defaults to JSON."""

        class TestModel:
            nested: List[List[str]]

        meta = SchemaParser.parse_model(TestModel)

        # Nested lists default to JSON storage
        assert meta.fields["nested"].type == FieldType.ARRAY

    def test_array_field_with_default_value(self):
        """Array field with default value parses correctly."""

        class TestModel:
            tags: List[str] = []

        meta = SchemaParser.parse_model(TestModel)

        assert meta.fields["tags"].type == FieldType.ARRAY
        assert meta.fields["tags"].default == []

    def test_null_array_type_handling(self):
        """Null array type handled gracefully."""
        field = FieldMeta(
            name="tags", type=FieldType.ARRAY, python_type=list, array_type=None
        )

        # Should not crash, default to JSONB
        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=False)
        assert sql_type == "JSONB"


class TestSchemaGenerationSQL:
    """Test SQL schema generation with native arrays."""

    def test_create_table_with_array_columns_sql(self):
        """Generated CREATE TABLE SQL includes array columns correctly."""

        class TestModel:
            id: str
            tags: List[str]
            scores: List[int]

            __dataflow__ = {"use_native_arrays": True}

        meta = SchemaParser.parse_model(TestModel)

        # Expected SQL types for PostgreSQL with native arrays
        assert (
            meta.fields["tags"].get_sql_type(
                dialect="postgresql", use_native_arrays=True
            )
            == "TEXT[]"
        )
        assert (
            meta.fields["scores"].get_sql_type(
                dialect="postgresql", use_native_arrays=True
            )
            == "INTEGER[]"
        )

    def test_nullable_array_column_sql(self):
        """Nullable array columns generate correct SQL."""

        class TestModel:
            optional_tags: Optional[List[str]]

            __dataflow__ = {"use_native_arrays": True}

        meta = SchemaParser.parse_model(TestModel)

        field = meta.fields["optional_tags"]
        assert field.nullable is True
        assert (
            field.get_sql_type(dialect="postgresql", use_native_arrays=True) == "TEXT[]"
        )


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test that existing code continues to work without feature flag."""

    def test_existing_list_fields_unchanged(self):
        """Existing List fields without feature flag work as before."""

        class ExistingModel:
            tags: List[str]  # No feature flag

        meta = SchemaParser.parse_model(ExistingModel)

        # Detected as array
        assert meta.fields["tags"].type == FieldType.ARRAY

        # Without feature flag, maps to JSONB (backward compatible)
        field = meta.fields["tags"]
        sql_type = field.get_sql_type(dialect="postgresql", use_native_arrays=False)
        assert sql_type == "JSONB"

    def test_no_breaking_changes_to_existing_models(self):
        """Existing models without feature flag generate same schema."""

        class UserModel:
            id: str
            name: str
            roles: List[str]  # Existing field

        meta = SchemaParser.parse_model(UserModel)

        # Backward compatible: roles maps to JSONB
        assert (
            meta.fields["roles"].get_sql_type(
                dialect="postgresql", use_native_arrays=False
            )
            == "JSONB"
        )
