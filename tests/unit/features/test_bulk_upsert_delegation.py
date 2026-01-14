"""
Unit tests for BulkOperations.bulk_upsert delegation to BulkUpsertNode.

Tests the delegation layer without database operations - focuses on:
- Parameter mapping and transformation
- Tenant context application
- Error handling and response format
- Conflict resolution strategy mapping
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dataflow import DataFlow
from dataflow.core.config import DatabaseConfig, DataFlowConfig, SecurityConfig


class TestBulkUpsertDelegation:
    """Unit tests for bulk_upsert delegation logic."""

    @pytest.fixture
    def mock_dataflow(self):
        """Create a mock DataFlow instance with necessary configuration."""
        # Create real config objects
        config = DataFlowConfig(
            database=DatabaseConfig(
                url="postgresql://test:test@localhost:5432/test_db",
                pool_size=10,
                max_overflow=20,
            ),
            security=SecurityConfig(
                multi_tenant=False,
            ),
            environment="test",
        )

        # Create DataFlow instance with mock methods
        df = MagicMock(spec=DataFlow)
        df.config = config
        df._tenant_context = None
        df._detect_database_type = MagicMock(return_value="postgresql")
        df._class_name_to_table_name = MagicMock(return_value="test_users")

        return df

    @pytest.mark.asyncio
    async def test_bulk_upsert_empty_data_returns_zero_counts(self, mock_dataflow):
        """Test that bulk_upsert with empty data returns zero counts without calling node."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        result = await bulk_ops.bulk_upsert(
            model_name="User",
            data=[],  # Empty list
            conflict_resolution="update",
            batch_size=1000,
        )

        # Verify response format
        assert result["success"] is True
        assert result["records_processed"] == 0
        assert result["inserted"] == 0
        assert result["updated"] == 0
        assert result["batch_size"] == 1000

    @pytest.mark.asyncio
    async def test_bulk_upsert_none_data_returns_error(self, mock_dataflow):
        """Test that bulk_upsert with None data returns error."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        result = await bulk_ops.bulk_upsert(
            model_name="User",
            data=None,  # None data
            conflict_resolution="update",
        )

        # Verify error response
        assert result["success"] is False
        assert "error" in result
        assert "cannot be none" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_bulk_upsert_tenant_context_applied(self, mock_dataflow):
        """Test that tenant context is applied when multi-tenant is enabled."""
        from dataflow.features.bulk import BulkOperations

        # Enable multi-tenant mode
        mock_dataflow.config.security.multi_tenant = True
        mock_dataflow._tenant_context = {"tenant_id": "tenant_123"}

        bulk_ops = BulkOperations(mock_dataflow)

        # Mock BulkUpsertNode
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 2,
                    "inserted": 1,
                    "updated": 1,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[
                    {"email": "test1@example.com", "name": "Test 1"},
                    {"email": "test2@example.com", "name": "Test 2"},
                ],
                conflict_resolution="update",
            )

            # Verify node was created with tenant context
            MockNode.assert_called_once()
            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["multi_tenant"] is True
            assert call_kwargs["tenant_id"] == "tenant_123"

            # Verify node.async_run was called with tenant_id
            mock_node_instance.async_run.assert_called_once()
            run_kwargs = mock_node_instance.async_run.call_args.kwargs
            assert run_kwargs["tenant_id"] == "tenant_123"

    @pytest.mark.asyncio
    async def test_bulk_upsert_delegates_to_node(self, mock_dataflow):
        """Test that bulk_upsert delegates correctly to BulkUpsertNode."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Mock BulkUpsertNode
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 5,
                    "inserted": 3,
                    "updated": 2,
                    "duplicates_removed": 1,
                    "performance_metrics": {
                        "execution_time_seconds": 0.5,
                        "records_per_second": 10.0,
                    },
                }
            )
            MockNode.return_value = mock_node_instance

            test_data = [
                {"email": f"user{i}@example.com", "name": f"User {i}"} for i in range(5)
            ]

            result = await bulk_ops.bulk_upsert(
                model_name="User",
                data=test_data,
                conflict_resolution="update",
                batch_size=100,
                conflict_columns=["email"],
                return_records=False,
            )

            # Verify BulkUpsertNode was created with correct parameters
            MockNode.assert_called_once()
            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["table_name"] == "test_users"
            assert call_kwargs["database_type"] == "postgresql"
            assert call_kwargs["batch_size"] == 100
            assert call_kwargs["merge_strategy"] == "update"
            assert call_kwargs["conflict_columns"] == ["email"]
            assert "connection_string" in call_kwargs

            # Verify async_run was called with data
            mock_node_instance.async_run.assert_called_once()
            run_kwargs = mock_node_instance.async_run.call_args.kwargs
            assert run_kwargs["data"] == test_data
            assert run_kwargs["return_records"] is False

            # Verify result transformation
            assert result["success"] is True
            assert result["records_processed"] == 5
            assert result["inserted"] == 3
            assert result["updated"] == 2

    @pytest.mark.asyncio
    async def test_bulk_upsert_conflict_resolution_mapping(self, mock_dataflow):
        """Test conflict_resolution parameter mapping (skip->ignore, update->update)."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Mock BulkUpsertNode
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 1,
                    "inserted": 0,
                    "updated": 0,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            # Test 'skip' -> 'ignore' mapping
            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="skip",
            )

            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["merge_strategy"] == "ignore"

            # Reset mock
            MockNode.reset_mock()
            mock_node_instance.async_run.reset_mock()

            # Test 'update' -> 'update' mapping
            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["merge_strategy"] == "update"

    @pytest.mark.asyncio
    async def test_bulk_upsert_response_format_matches_api(self, mock_dataflow):
        """Test that response format matches expected BulkOperations API."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Mock BulkUpsertNode with complete response
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 10,
                    "inserted": 6,
                    "updated": 4,
                    "duplicates_removed": 2,
                    "upserted_records": [
                        {"id": 1, "email": "user1@example.com", "name": "User 1"},
                        {"id": 2, "email": "user2@example.com", "name": "User 2"},
                    ],
                    "performance_metrics": {
                        "execution_time_seconds": 1.5,
                        "records_per_second": 6.67,
                        "batch_count": 1,
                    },
                }
            )
            MockNode.return_value = mock_node_instance

            result = await bulk_ops.bulk_upsert(
                model_name="User",
                data=[
                    {"email": f"user{i}@example.com", "name": f"User {i}"}
                    for i in range(10)
                ],
                conflict_resolution="update",
                return_records=True,
            )

            # Verify required fields
            assert "success" in result
            assert "records_processed" in result
            assert "inserted" in result
            assert "updated" in result
            assert "duplicates_removed" in result
            assert "conflict_resolution" in result
            assert "batch_size" in result
            assert "performance_metrics" in result

            # Verify values
            assert result["success"] is True
            assert result["records_processed"] == 10
            assert result["inserted"] == 6
            assert result["updated"] == 4
            assert result["duplicates_removed"] == 2
            assert result["conflict_resolution"] == "update"

            # Verify optional records field
            assert "records" in result
            assert len(result["records"]) == 2

    @pytest.mark.asyncio
    async def test_bulk_upsert_error_handling_returns_proper_format(
        self, mock_dataflow
    ):
        """Test that errors from BulkUpsertNode are properly formatted."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Test 1: Node returns error response
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={"success": False, "error": "Database connection failed"}
            )
            MockNode.return_value = mock_node_instance

            result = await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            assert result["success"] is False
            assert "error" in result
            assert "Database connection failed" in result["error"]
            assert result["records_processed"] == 0

        # Test 2: Node raises exception
        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                side_effect=Exception("Unexpected database error")
            )
            MockNode.return_value = mock_node_instance

            result = await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            assert result["success"] is False
            assert "error" in result
            assert "Unexpected database error" in result["error"]
            assert result["records_processed"] == 0

    @pytest.mark.asyncio
    async def test_bulk_upsert_optional_parameters_passed_correctly(
        self, mock_dataflow
    ):
        """Test that optional parameters are passed correctly to BulkUpsertNode."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 1,
                    "inserted": 1,
                    "updated": 0,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
                batch_size=500,
                conflict_columns=["email", "tenant_id"],
                return_records=True,
                auto_timestamps=False,
                version_control=True,
            )

            # Verify all optional parameters were passed
            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["batch_size"] == 500
            assert call_kwargs["conflict_columns"] == ["email", "tenant_id"]
            assert call_kwargs["auto_timestamps"] is False
            assert call_kwargs["version_control"] is True

            run_kwargs = mock_node_instance.async_run.call_args.kwargs
            assert run_kwargs["return_records"] is True

    @pytest.mark.asyncio
    async def test_bulk_upsert_database_type_detection(self, mock_dataflow):
        """Test that database type is correctly detected and passed to node."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Test PostgreSQL detection
        mock_dataflow._detect_database_type.return_value = "postgresql"

        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 1,
                    "inserted": 1,
                    "updated": 0,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["database_type"] == "postgresql"

        # Test with different database type
        mock_dataflow._detect_database_type.return_value = "mysql"

        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 1,
                    "inserted": 1,
                    "updated": 0,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            await bulk_ops.bulk_upsert(
                model_name="User",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["database_type"] == "mysql"

    @pytest.mark.asyncio
    async def test_bulk_upsert_table_name_conversion(self, mock_dataflow):
        """Test that model name is correctly converted to table name."""
        from dataflow.features.bulk import BulkOperations

        bulk_ops = BulkOperations(mock_dataflow)

        # Mock table name conversion
        mock_dataflow._class_name_to_table_name.return_value = "converted_table_name"

        with patch("dataflow.nodes.bulk_upsert.BulkUpsertNode") as MockNode:
            mock_node_instance = AsyncMock()
            mock_node_instance.async_run = AsyncMock(
                return_value={
                    "success": True,
                    "rows_affected": 1,
                    "inserted": 1,
                    "updated": 0,
                    "duplicates_removed": 0,
                    "performance_metrics": {},
                }
            )
            MockNode.return_value = mock_node_instance

            await bulk_ops.bulk_upsert(
                model_name="SomeModelName",
                data=[{"email": "test@example.com", "name": "Test"}],
                conflict_resolution="update",
            )

            # Verify _class_name_to_table_name was called
            mock_dataflow._class_name_to_table_name.assert_called_once_with(
                "SomeModelName"
            )

            # Verify correct table name was passed to node
            call_kwargs = MockNode.call_args.kwargs
            assert call_kwargs["table_name"] == "converted_table_name"
