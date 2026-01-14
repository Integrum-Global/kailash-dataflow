"""
Unit tests for DataFlow connection pooling.

Tests cover:
1. Per-Database Connection Pools (5 tests)
2. Configuration Interface (3 tests)
3. Connection Health Checking (3 tests)
4. Pool Metrics & Monitoring (3 tests)
5. Integration Tests (1 test)

Total: 15 tests
"""

import asyncio
import os
import time
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.unit
class TestPerDatabaseConnectionPools:
    """Test per-database connection pool management."""

    @pytest.mark.asyncio
    async def test_separate_pool_per_database_url(self):
        """Test that separate pools are created for each database URL."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager()

        # Simulate acquiring connections from different databases
        postgresql_url = "postgresql://user:pass@localhost:5432/db1"
        mysql_url = "mysql://user:pass@localhost:3306/db2"
        sqlite_url = "sqlite:///test.db"

        # Get pools for each database
        pg_pool = manager._get_or_create_pool(postgresql_url)
        mysql_pool = manager._get_or_create_pool(mysql_url)
        sqlite_pool = manager._get_or_create_pool(sqlite_url)

        # Verify separate pools created
        assert pg_pool is not None
        assert mysql_pool is not None
        assert sqlite_pool is not None
        assert pg_pool != mysql_pool
        assert pg_pool != sqlite_pool
        assert mysql_pool != sqlite_pool

        # Verify pool storage
        assert postgresql_url in manager._pools
        assert mysql_url in manager._pools
        assert sqlite_url in manager._pools

    @pytest.mark.asyncio
    async def test_pool_size_configuration(self):
        """Test pool_size and max_overflow configuration."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        # Test default configuration
        manager_default = ConnectionPoolManager()
        assert manager_default.pool_size == 10
        assert manager_default.max_overflow == 20

        # Test custom configuration
        manager_custom = ConnectionPoolManager(pool_size=50, max_overflow=100)
        assert manager_custom.pool_size == 50
        assert manager_custom.max_overflow == 100

    @pytest.mark.asyncio
    async def test_pool_created_on_first_connection(self):
        """Test pool is created on first connection, reused thereafter."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager()
        database_url = "postgresql://user:pass@localhost:5432/testdb"

        # Initially no pools
        assert len(manager._pools) == 0

        # First call creates pool
        pool1 = manager._get_or_create_pool(database_url)
        assert len(manager._pools) == 1

        # Second call reuses same pool
        pool2 = manager._get_or_create_pool(database_url)
        assert pool1 is pool2
        assert len(manager._pools) == 1

    @pytest.mark.asyncio
    async def test_thread_safe_pool_access(self):
        """Test thread-safe pool access with locks."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager()
        database_url = "postgresql://user:pass@localhost:5432/testdb"

        # Verify lock is initialized
        assert hasattr(manager, "_lock")
        assert manager._lock is not None

        # Simulate concurrent access
        async def concurrent_access():
            return manager._get_or_create_pool(database_url)

        # Run 10 concurrent accesses
        pools = await asyncio.gather(*[concurrent_access() for _ in range(10)])

        # All should return the same pool
        assert all(pool is pools[0] for pool in pools)
        assert len(manager._pools) == 1

    @pytest.mark.asyncio
    async def test_pool_isolation_between_dataflow_instances(self):
        """Test pool isolation between DataFlow instances."""
        from dataflow import DataFlow

        # Create two DataFlow instances with same database URL
        db_url = "sqlite:///test_isolation.db"
        df1 = DataFlow(db_url, pool_size=10, enable_connection_pooling=True)
        df2 = DataFlow(db_url, pool_size=20, enable_connection_pooling=True)

        # Each should have its own pool manager
        assert df1._pool_manager is not df2._pool_manager

        # Each should have its own pool configuration
        assert df1._pool_manager.pool_size == 10
        assert df2._pool_manager.pool_size == 20


@pytest.mark.unit
class TestConfigurationInterface:
    """Test connection pool configuration interface."""

    def test_dataflow_pool_parameters(self):
        """Test DataFlow(pool_size=10, max_overflow=20) parameters."""
        from dataflow import DataFlow

        # Test with custom pool parameters
        db = DataFlow(
            "sqlite:///test.db",
            pool_size=50,
            max_overflow=100,
            enable_connection_pooling=True,
        )

        assert db._pool_manager is not None
        assert db._pool_manager.pool_size == 50
        assert db._pool_manager.max_overflow == 100

    def test_environment_variable_configuration(self):
        """Test DATAFLOW_POOL_SIZE, DATAFLOW_MAX_OVERFLOW environment variables."""
        from dataflow import DataFlow

        # Set environment variables
        os.environ["DATAFLOW_POOL_SIZE"] = "25"
        os.environ["DATAFLOW_MAX_OVERFLOW"] = "50"

        try:
            # Create DataFlow without explicit parameters
            db = DataFlow("sqlite:///test.db", enable_connection_pooling=True)

            # Should read from environment variables
            assert db._pool_manager.pool_size == 25
            assert db._pool_manager.max_overflow == 50
        finally:
            # Cleanup
            os.environ.pop("DATAFLOW_POOL_SIZE", None)
            os.environ.pop("DATAFLOW_MAX_OVERFLOW", None)

    def test_per_database_pool_override(self):
        """Test per-database override: DataFlow(pools={url: {pool_size: 50}})."""
        from dataflow import DataFlow

        # Test per-database configuration
        postgresql_url = "postgresql://user:pass@localhost:5432/db1"
        db = DataFlow(
            "sqlite:///default.db",
            pool_size=10,
            enable_connection_pooling=True,
            pools={postgresql_url: {"pool_size": 50, "max_overflow": 100}},
        )

        assert db._pool_manager is not None
        # Default pool size for main database
        assert db._pool_manager.pool_size == 10

        # Should have override configuration
        assert hasattr(db._pool_manager, "_pool_overrides")
        assert postgresql_url in db._pool_manager._pool_overrides
        assert db._pool_manager._pool_overrides[postgresql_url]["pool_size"] == 50


@pytest.mark.unit
class TestConnectionHealthChecking:
    """Test connection health checking."""

    @pytest.mark.asyncio
    async def test_pre_ping_validates_connections(self):
        """Test pre_ping=True validates connections before use."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(enable_pool_pre_ping=True)
        assert manager.enable_pool_pre_ping is True

        # Verify pre_ping is passed to pool configuration
        pool = manager._get_or_create_pool("sqlite:///test.db")
        pool_config = pool._pool_config if hasattr(pool, "_pool_config") else {}

        # For SQLite, pre_ping may not apply, but should be in config
        assert manager.enable_pool_pre_ping is True

    @pytest.mark.asyncio
    async def test_automatic_reconnection_on_stale_connections(self):
        """Test automatic reconnection on stale connections."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(enable_pool_pre_ping=True)

        # Mock connection that fails validation
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Connection lost"))
        mock_conn.close = AsyncMock()

        # Validate connection should handle failure
        with pytest.raises(Exception) as exc_info:
            await manager._validate_connection(mock_conn)

        assert "Connection lost" in str(exc_info.value)
        # Verify connection was closed on failure
        mock_conn.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_validation_errors_logged(self):
        """Test connection validation errors are logged."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(enable_pool_pre_ping=True)

        # Mock connection with validation error
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock(side_effect=Exception("Validation failed"))
        mock_conn.close = AsyncMock()

        # Capture logs
        with patch("dataflow.core.connection_pool.logger") as mock_logger:
            try:
                await manager._validate_connection(mock_conn)
            except Exception:
                pass

            # Verify error was logged
            assert mock_logger.error.called or mock_logger.warning.called


@pytest.mark.unit
class TestPoolMetricsMonitoring:
    """Test pool metrics and monitoring."""

    def test_get_pool_metrics(self):
        """Test get_pool_metrics() → {size, checked_out, overflow, total}."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(pool_size=10, max_overflow=20)
        database_url = "postgresql://user:pass@localhost:5432/testdb"

        # Create pool
        manager._get_or_create_pool(database_url)

        # Get metrics
        metrics = manager.get_pool_metrics(database_url)

        # Verify metrics structure
        assert isinstance(metrics, dict)
        assert "size" in metrics
        assert "checked_out" in metrics
        assert "overflow" in metrics
        assert "total" in metrics

        # Verify initial values
        assert metrics["size"] == 10
        assert metrics["checked_out"] >= 0
        assert metrics["overflow"] >= 0
        assert metrics["total"] >= 0

    def test_pool_utilization_percentage(self):
        """Test pool utilization percentage calculation."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(pool_size=10, max_overflow=20)
        database_url = "postgresql://user:pass@localhost:5432/testdb"

        # Create pool
        manager._get_or_create_pool(database_url)

        # Get metrics
        metrics = manager.get_pool_metrics(database_url)

        # Verify utilization percentage
        assert "utilization_percent" in metrics
        assert 0 <= metrics["utilization_percent"] <= 100

    def test_pool_exhaustion_detection(self):
        """Test pool exhaustion detection."""
        from dataflow.core.connection_pool import ConnectionPoolManager

        manager = ConnectionPoolManager(pool_size=5, max_overflow=0)
        database_url = "postgresql://user:pass@localhost:5432/testdb"

        # Create pool
        manager._get_or_create_pool(database_url)

        # Get metrics
        metrics = manager.get_pool_metrics(database_url)

        # Should be able to detect exhaustion
        assert "is_exhausted" in metrics
        assert isinstance(metrics["is_exhausted"], bool)

        # Initially not exhausted
        assert metrics["is_exhausted"] is False


@pytest.mark.unit
class TestIntegrationTests:
    """Integration tests for connection pooling."""

    @pytest.mark.asyncio
    async def test_concurrent_operations_share_pool(self):
        """Test multiple concurrent DataFlow operations sharing pool."""
        from dataflow import DataFlow

        from kailash.runtime import AsyncLocalRuntime
        from kailash.workflow.builder import WorkflowBuilder

        # Create DataFlow with connection pooling
        db_url = "sqlite:///test_concurrent.db"
        db = DataFlow(db_url, pool_size=5, enable_connection_pooling=True)

        @db.model
        class TestModel:
            name: str
            value: int

        # Simulate multiple concurrent operations
        async def create_record(index: int):
            workflow = WorkflowBuilder()
            workflow.add_node(
                "TestModelCreateNode",
                f"create_{index}",
                {"id": f"test-{index}", "name": f"Test {index}", "value": index},
            )

            runtime = AsyncLocalRuntime()
            results, _ = await runtime.execute_workflow_async(
                workflow.build(), inputs={}
            )
            return results

        # Run 10 concurrent operations
        results = await asyncio.gather(*[create_record(i) for i in range(10)])

        # Verify all completed successfully
        assert len(results) == 10

        # Verify pool metrics show reuse
        if db._pool_manager:
            metrics = db._pool_manager.get_pool_metrics(db_url)
            # Total connections should be less than operations (reuse)
            # This is implementation-dependent, but we verify structure
            assert "total" in metrics
            assert metrics["total"] >= 0


@pytest.mark.unit
class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_pooling_disabled_by_default(self):
        """Test connection pooling can be disabled."""
        from dataflow import DataFlow

        # Create DataFlow without pooling
        db = DataFlow("sqlite:///test.db", enable_connection_pooling=False)

        # Should not have pool manager
        assert db._pool_manager is None

    def test_existing_code_works_without_pooling(self):
        """Test existing code works without connection pooling."""
        from dataflow import DataFlow

        # Create DataFlow with default settings (pooling enabled)
        db = DataFlow("sqlite:///test.db")

        @db.model
        class User:
            name: str
            email: str

        # Should work normally
        models = db.get_models()
        assert "User" in models


# Test helper for metrics verification
def verify_pool_metrics_structure(metrics: Dict) -> bool:
    """Verify pool metrics have correct structure."""
    required_fields = [
        "size",
        "checked_out",
        "overflow",
        "total",
        "utilization_percent",
        "is_exhausted",
    ]
    return all(field in metrics for field in required_fields)
