# DataFlow TDD Performance Optimization Guide

Comprehensive guide to achieving consistent <100ms test execution times with DataFlow's TDD infrastructure. This guide covers all optimization techniques, best practices, and troubleshooting for maximum test performance.

## 🎯 Performance Targets

| Test Category | Target Time | Description |
|---------------|-------------|-------------|
| Simple CRUD | <50ms | Single model operations |
| Complex Workflows | <100ms | Multi-model scenarios |
| Bulk Operations | <200ms | 100+ record operations |
| Schema Operations | <30ms | With caching enabled |
| Concurrent Tests | <100ms | Per-user operations |

## 🚀 Quick Start

### 1. Enable TDD Mode and Optimization

```python
import os

# Enable TDD mode and performance optimization
os.environ["DATAFLOW_TDD_MODE"] = "true"
os.environ["DATAFLOW_PERFORMANCE_OPTIMIZATION"] = "true"
```

### 2. Use Enhanced TDD Fixtures

```python
import pytest
from dataflow.testing.enhanced_tdd_fixtures import enhanced_tdd_context

@pytest.mark.asyncio
async def test_fast_operation(enhanced_tdd_context):
    context = enhanced_tdd_context

    # All optimizations are automatically enabled:
    # - Preheated connection pools
    # - Schema caching
    # - Parallel execution support
    # - Performance monitoring
    # - Memory optimization

    # Your test code here - executes in <100ms
```

### 3. Validate Performance

```python
from dataflow.testing.enhanced_tdd_fixtures import comprehensive_tdd_benchmark

@pytest.mark.asyncio
async def test_with_benchmarking(comprehensive_tdd_benchmark):
    benchmark_context = comprehensive_tdd_benchmark

    # Perform test operations
    # Performance is automatically tracked

    # Validate target achievement
    assert benchmark_context.validate_performance_target()

    # Get detailed performance report
    report = benchmark_context.get_comprehensive_report()
    print(f"Target achieved: {report['target_achieved']}")
```

## 🔧 Optimization Techniques

### Connection Pool Optimization

The enhanced TDD infrastructure uses preheated connection pools to eliminate cold start delays.

#### Features:
- **Session-level pools**: Reused across test runs
- **Connection preheating**: Eliminates cold start delays
- **Pool size optimization**: Configured for test patterns
- **Health monitoring**: Automatic connection validation

#### Usage:

```python
from dataflow.testing.enhanced_tdd_fixtures import preheated_dataflow

@pytest.mark.asyncio
async def test_with_preheated_pool(preheated_dataflow):
    df, pool_stats = preheated_dataflow

    # Connection acquisition is <5ms
    # Pool is preheated and ready

    @df.model
    class User:
        name: str
        email: str

    # Database operations are immediate
    result = await df.User.create({
        "name": "Fast User",
        "email": "fast@example.com"
    })
```

#### Configuration:

```python
from dataflow.testing.performance_optimization import get_pool_manager

async def configure_custom_pool():
    pool_manager = get_pool_manager()

    pool = await pool_manager.create_optimized_pool(
        pool_id="custom_test_pool",
        connection_string="postgresql://...",
        min_size=2,      # Minimum connections
        max_size=10,     # Maximum connections
        preheat=True     # Enable preheating
    )

    # Get performance statistics
    stats = pool_manager.get_pool_statistics("custom_test_pool")
    print(f"Pool preheated: {stats['preheated']}")
    print(f"Average acquisition time: {stats['avg_acquisition_time_ms']:.2f}ms")
```

### Schema Caching

Schema caching eliminates repeated DDL operations by pre-creating and caching table definitions.

#### Features:
- **Pre-created schemas**: Defined in session setup
- **Cached DDL**: Avoids repeated table creation
- **Lazy loading**: Models loaded only when needed
- **Version management**: Automatic cache invalidation

#### Usage:

```python
from dataflow.testing.enhanced_tdd_fixtures import cached_schema_models

@pytest.mark.asyncio
async def test_with_cached_schemas(cached_schema_models):
    User, Product, Order, cache_stats = cached_schema_models

    # Models are immediately available (cached)
    # No DDL overhead - operations complete in <10ms

    # Cache statistics
    print(f"Cached schemas: {cache_stats['cached_schemas']}")
    print(f"Cache hit rate: {cache_stats['cache_hit_rate']}")
```

#### Manual Cache Management:

```python
from dataflow.testing.performance_optimization import get_schema_cache

def manage_schema_cache():
    cache = get_schema_cache()

    # Cache a schema
    cache.cache_schema("user_schema", {
        "users": "CREATE TABLE users (id SERIAL PRIMARY KEY, name VARCHAR(255))"
    })

    # Check if cached
    if cache.is_schema_cached("user_schema"):
        print("Schema is cached and ready")

    # Get cache statistics
    stats = cache.get_cache_statistics()
    print(f"Total cached schemas: {stats['cached_schemas']}")
```

### Parallel Execution Support

Thread-safe parallel execution with proper isolation and resource management.

#### Features:
- **Database-level isolation**: SERIALIZABLE transactions
- **Resource allocation**: Deadlock prevention
- **Thread safety**: All managers are thread-safe
- **Connection pool management**: Handles high concurrency

#### Usage:

```python
from dataflow.testing.enhanced_tdd_fixtures import parallel_test_execution

@pytest.mark.asyncio
async def test_parallel_safe(parallel_test_execution):
    context, isolation_id, resource_manager = parallel_test_execution

    # Allocate database resource
    if resource_manager.allocate("user_table"):
        # Perform database operations
        # Guaranteed isolation from other parallel tests

        # Release resource when done
        resource_manager.release("user_table")
```

#### Concurrent Test Execution:

```python
import concurrent.futures
import asyncio

async def run_parallel_tests():
    """Example of running tests in parallel."""

    async def individual_test(test_id: int):
        # Each test gets its own isolation
        async with parallel_test_execution() as (context, isolation_id, resource_manager):
            # Test operations here
            await asyncio.sleep(0.01)  # Simulated work
            return f"test_{test_id}_completed"

    # Run 10 tests in parallel
    tasks = [individual_test(i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    # All tests complete successfully with isolation
    assert len(results) == 10
```

### Performance Monitoring

Real-time performance tracking with regression detection and alerting.

#### Features:
- **Real-time tracking**: Performance monitored during execution
- **Regression detection**: Automatic performance degradation alerts
- **Trend analysis**: Historical performance patterns
- **Alerting**: Configurable performance thresholds

#### Usage:

```python
from dataflow.testing.enhanced_tdd_fixtures import performance_monitored_test

@pytest.mark.asyncio
async def test_with_monitoring(performance_monitored_test):
    monitor, metrics_collector, alert_handler = performance_monitored_test

    # Monitor specific operations
    with metrics_collector.measure("database_operation"):
        # Perform database operation
        await asyncio.sleep(0.05)  # 50ms operation

    # Check for performance alerts
    alerts = alert_handler.get_alerts()
    if alerts:
        print(f"Performance alerts: {len(alerts)}")

    # Get performance report
    report = monitor.get_performance_report()
    print(f"Average execution time: {report['operations']['database_operation']['avg_duration_ms']:.2f}ms")
```

#### Custom Performance Monitoring:

```python
from dataflow.testing.performance_optimization import get_performance_monitor, PerformanceMetrics

def custom_performance_tracking():
    monitor = get_performance_monitor()

    # Create custom metrics
    metrics = PerformanceMetrics(
        operation_id="custom_operation",
        operation_type="database_query",
        duration_ms=45.0,
        connection_reused=True,
        schema_cached=True
    )

    # Record metrics
    monitor.record_metrics(metrics)

    # Add custom alert handler
    def custom_alert_handler(alert_data):
        print(f"Performance regression detected: {alert_data['degradation_percent']:.1f}% slower")

    monitor.add_alert_callback(custom_alert_handler)
```

### Memory Optimization

Efficient memory management to prevent leaks and optimize resource usage.

#### Features:
- **Connection reuse**: No memory leaks from connections
- **Efficient cleanup**: Proper resource disposal
- **Garbage collection**: Optimized for long test suites
- **Memory monitoring**: Track usage and detect leaks

#### Usage:

```python
from dataflow.testing.enhanced_tdd_fixtures import memory_optimized_test

@pytest.mark.asyncio
async def test_memory_efficient(memory_optimized_test):
    optimizer, tracker, cleanup_manager = memory_optimized_test

    # Track objects for cleanup
    large_object = [i for i in range(100000)]
    tracker.track(large_object, "test_data")

    # Perform memory-intensive operations
    # Memory usage is automatically monitored

    # Check for memory leaks
    if tracker.check_leak_threshold(5.0):  # 5MB threshold
        print("Potential memory leak detected")

    # Force cleanup if needed
    cleanup_manager.force_cleanup()
```

## 📊 Performance Benchmarking

### Real-World Benchmarks

Use the comprehensive benchmark suite to validate performance in realistic scenarios:

```python
from dataflow.testing.enhanced_tdd_fixtures import comprehensive_tdd_benchmark

@pytest.mark.asyncio
async def test_real_world_scenario(comprehensive_tdd_benchmark):
    benchmark_context = comprehensive_tdd_benchmark

    # Complex e-commerce workflow
    # 1. User registration
    # 2. Product catalog browsing
    # 3. Shopping cart operations
    # 4. Order processing
    # 5. Payment handling

    # All operations complete within 100ms target
    assert benchmark_context.validate_performance_target()

    # Get detailed performance breakdown
    report = benchmark_context.get_comprehensive_report()
    print(f"Performance Summary:")
    print(f"- Setup time: {report['recorded_metrics']['setup_time']['value']:.2f}ms")
    print(f"- Total time: {report['total_execution_time_ms']:.2f}ms")
    print(f"- Target achieved: {report['target_achieved']}")
```

### Regression Testing

Implement automated regression detection:

```python
from dataflow.testing.performance_optimization import RegressionTestSuite

def test_performance_regression():
    suite = RegressionTestSuite()

    def test_operation():
        import time
        time.sleep(0.03)  # 30ms operation
        return "completed"

    # Establish baseline
    result = suite.run_regression_test(
        "test_operation",
        test_operation,
        establish_baseline=True
    )

    assert result.target_achieved

    # Subsequent runs check for regression
    result2 = suite.run_regression_test("test_operation", test_operation)

    if result2.is_regression:
        print(f"Performance regression detected: {result2.regression_factor:.2f}x slower")

    # Get comprehensive report
    report = suite.get_regression_report()
    print(f"Regression rate: {report['performance_summary']['regression_rate']:.1f}%")
```

## 🛠 Troubleshooting

### Common Performance Issues

#### Issue: Tests exceeding 100ms target

**Symptoms:**
- Tests consistently take >100ms
- Performance warnings in logs
- Regression detection alerts

**Solutions:**

1. **Enable all optimizations:**
```python
# Ensure all optimization flags are set
os.environ["DATAFLOW_TDD_MODE"] = "true"
os.environ["DATAFLOW_PERFORMANCE_OPTIMIZATION"] = "true"
```

2. **Use enhanced fixtures:**
```python
# Replace basic fixtures with enhanced ones
@pytest.mark.asyncio
async def test_slow_operation(enhanced_tdd_context):  # Instead of basic context
    # Test operations
```

3. **Check connection pool status:**
```python
from dataflow.testing.performance_optimization import get_pool_manager

pool_manager = get_pool_manager()
stats = pool_manager.get_pool_statistics("test_pool")

if not stats.get("preheated"):
    print("Pool not preheated - connection acquisition will be slow")
```

#### Issue: Memory leaks during test runs

**Symptoms:**
- Memory usage continuously increasing
- Test suite slows down over time
- Out of memory errors

**Solutions:**

1. **Enable memory optimization:**
```python
from dataflow.testing.enhanced_tdd_fixtures import memory_optimized_test

@pytest.mark.asyncio
async def test_with_memory_tracking(memory_optimized_test):
    optimizer, tracker, cleanup_manager = memory_optimized_test

    # Automatic memory tracking and cleanup
```

2. **Manual cleanup:**
```python
from dataflow.testing.performance_optimization import get_memory_optimizer

def test_with_manual_cleanup():
    optimizer = get_memory_optimizer()

    # Take initial snapshot
    optimizer.take_memory_snapshot("test_start")

    # Perform test operations

    # Force cleanup
    optimizer.optimize_memory()

    # Check memory delta
    final_snapshot = optimizer.take_memory_snapshot("test_end")
```

#### Issue: Parallel test conflicts

**Symptoms:**
- Random test failures in parallel execution
- Resource allocation errors
- Deadlock warnings

**Solutions:**

1. **Use parallel-safe fixtures:**
```python
from dataflow.testing.enhanced_tdd_fixtures import parallel_test_execution

@pytest.mark.asyncio
async def test_parallel_safe(parallel_test_execution):
    context, isolation_id, resource_manager = parallel_test_execution

    # Proper resource allocation
    if resource_manager.allocate("shared_resource"):
        # Safe to proceed
        pass
```

2. **Configure isolation levels:**
```python
from dataflow.testing.performance_optimization import get_parallel_manager

parallel_manager = get_parallel_manager()
parallel_manager.register_parallel_test(
    "test_id",
    threading.get_ident(),
    "SERIALIZABLE"  # Highest isolation
)
```

### Performance Diagnostics

#### Check Optimization Status

```python
from dataflow.testing.performance_optimization import is_optimization_enabled
from dataflow.testing.tdd_support import is_tdd_mode

def diagnose_performance():
    print(f"TDD Mode: {is_tdd_mode()}")
    print(f"Optimization Enabled: {is_optimization_enabled()}")

    if not is_tdd_mode():
        print("❌ Enable TDD mode: export DATAFLOW_TDD_MODE=true")

    if not is_optimization_enabled():
        print("❌ Enable optimization: export DATAFLOW_PERFORMANCE_OPTIMIZATION=true")
```

#### Get Performance Statistics

```python
def get_comprehensive_stats():
    from dataflow.testing.performance_optimization import (
        get_pool_manager, get_schema_cache, get_parallel_manager,
        get_performance_monitor, get_memory_optimizer
    )

    # Pool statistics
    pool_manager = get_pool_manager()
    pool_stats = pool_manager.get_pool_statistics("default")

    # Cache statistics
    cache = get_schema_cache()
    cache_stats = cache.get_cache_statistics()

    # Parallel execution statistics
    parallel_manager = get_parallel_manager()
    parallel_stats = parallel_manager.get_parallel_statistics()

    # Performance monitoring
    monitor = get_performance_monitor()
    perf_report = monitor.get_performance_report()

    # Memory usage
    memory_optimizer = get_memory_optimizer()
    memory_report = memory_optimizer.get_memory_report()

    return {
        "pool": pool_stats,
        "cache": cache_stats,
        "parallel": parallel_stats,
        "performance": perf_report,
        "memory": memory_report
    }

# Get and display stats
stats = get_comprehensive_stats()
for category, data in stats.items():
    print(f"{category.title()} Statistics: {data}")
```

## 📋 Best Practices

### 1. Test Organization

- **Use appropriate fixtures** for your test type
- **Group related tests** to benefit from shared setup
- **Minimize test isolation overhead** with enhanced fixtures

### 2. Performance Monitoring

- **Always monitor critical paths** with performance fixtures
- **Set up regression detection** for important workflows
- **Review performance reports** regularly

### 3. Resource Management

- **Use connection pooling** for database-heavy tests
- **Implement proper cleanup** in test teardown
- **Monitor memory usage** in long-running test suites

### 4. Parallel Execution

- **Design tests for parallel execution** from the start
- **Use proper resource allocation** to avoid conflicts
- **Test parallel scenarios** before deploying

### 5. Optimization Validation

- **Benchmark realistic scenarios** regularly
- **Validate optimization effectiveness** with metrics
- **Update baselines** as code evolves

## 🔍 Advanced Configuration

### Custom Optimization Configuration

```python
from dataflow.testing.performance_optimization import optimized_test_context

@pytest.mark.asyncio
async def test_custom_optimization():
    async with optimized_test_context(
        test_id="custom_test",
        enable_pooling=True,
        enable_caching=True,
        enable_parallel=False,  # Disable parallel for single-threaded test
        enable_monitoring=True,
        enable_memory_optimization=True
    ) as context:
        # Custom optimized test execution
        pass
```

### Environment-Specific Settings

```python
import os

# Development environment - maximum optimization
os.environ.update({
    "DATAFLOW_TDD_MODE": "true",
    "DATAFLOW_PERFORMANCE_OPTIMIZATION": "true",
    "DATAFLOW_POOL_SIZE": "5",
    "DATAFLOW_MAX_OVERFLOW": "10"
})

# CI environment - conservative settings
if os.getenv("CI"):
    os.environ.update({
        "DATAFLOW_POOL_SIZE": "2",
        "DATAFLOW_MAX_OVERFLOW": "3"
    })
```

## 📈 Performance Metrics

### Key Performance Indicators

| Metric | Target | Description |
|--------|--------|-------------|
| Test Execution Time | <100ms | Individual test duration |
| Connection Acquisition | <5ms | Pool connection time |
| Schema Operations | <10ms | DDL with caching |
| Memory Overhead | <2MB | Per test context |
| Parallel Success Rate | 100% | Concurrent test success |
| Cache Hit Rate | >90% | Schema cache effectiveness |

### Monitoring Dashboard

```python
def performance_dashboard():
    stats = get_comprehensive_stats()

    print("📊 DataFlow TDD Performance Dashboard")
    print("="*50)

    # Connection Pool Performance
    pool = stats.get("pool", {})
    print(f"🔌 Connection Pool:")
    print(f"   Preheated: {pool.get('preheated', False)}")
    print(f"   Avg Acquisition: {pool.get('avg_acquisition_time_ms', 0):.2f}ms")
    print(f"   Pool Size: {pool.get('size', 0)}/{pool.get('max_size', 0)}")

    # Cache Performance
    cache = stats.get("cache", {})
    print(f"💾 Schema Cache:")
    print(f"   Cached Schemas: {cache.get('cached_schemas', 0)}")
    print(f"   Hit Rate: {cache.get('cache_hit_rate', 0):.1f}%")

    # Performance Overview
    perf = stats.get("performance", {})
    if "operations" in perf:
        print(f"⚡ Performance:")
        for op_type, op_stats in perf["operations"].items():
            print(f"   {op_type}: {op_stats.get('avg_duration_ms', 0):.2f}ms avg")

    # Memory Usage
    memory = stats.get("memory", {})
    print(f"🧠 Memory:")
    print(f"   Current Usage: {memory.get('current_usage_mb', 0):.2f}MB")
    print(f"   Memory Delta: {memory.get('memory_delta_mb', 0):.2f}MB")

# Display dashboard
performance_dashboard()
```

---

This guide provides comprehensive coverage of DataFlow's TDD performance optimization features. For additional support or advanced configuration, refer to the source code in `/src/dataflow/testing/` or contact the development team.
