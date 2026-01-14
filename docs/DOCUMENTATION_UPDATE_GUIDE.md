# DataFlow Documentation Update Guide

**Date**: 2025-11-07
**Based On**: DATAFLOW_IMPROVEMENTS_COMPARISON.md
**Purpose**: Systematic guide for updating all DataFlow documentation to reflect Phase 1A/1B improvements

---

## Table of Contents

1. [Overview](#overview)
2. [Documentation Files to Update](#documentation-files-to-update)
3. [Update Instructions by File](#update-instructions-by-file)
4. [New Sections to Add](#new-sections-to-add)
5. [Examples to Replace/Update](#examples-to-replaceupdate)
6. [Validation Checklist](#validation-checklist)

---

## Overview

### What Changed (Phase 1A/1B Complete)

**Phase 1A: ErrorEnhancer (Week 1-3)** ✅
- ErrorEnhancer with 60+ methods (756 lines)
- YAML error catalog with 50+ patterns
- DF-XXX error codes with solutions
- 70-80% reduction in debugging time

**Phase 1B: Developer Tools (Week 4-6)** ✅
- Inspector with 30+ methods (3,540 lines)
- 5 CLI commands (analyze, debug, generate, perf, validate)
- Schema cache (91-99% performance improvement)
- 80-90% reduction in workflow debugging time

**Critical Bug Fix** ✅
- AsyncLocalRuntime transaction bug (SDK-CORE-2025-001)
- 23% → 100% test pass rate
- Production-ready for async workflows

### Impact on Documentation

**All documentation must now**:
1. Reference ErrorEnhancer for error handling
2. Show Inspector usage for debugging
3. Include CLI command examples
4. Update performance metrics (schema cache)
5. Remove workarounds that are now fixed
6. Add before/after comparisons for clarity

---

## Documentation Files to Update

### 1. Agent Framework Documentation
**File**: `.claude/agents/frameworks/dataflow-specialist.md`
**Priority**: **CRITICAL** (used by AI agents)
**Estimated Time**: 3-4 hours

### 2. Skills Documentation
**File**: `.claude/skills/02-dataflow.md`
**Priority**: **HIGH** (used for skill invocation)
**Estimated Time**: 2-3 hours

### 3. SDK Users Documentation
**Directory**: `sdk-users/apps/dataflow/`
**Priority**: **HIGH** (user-facing docs)
**Files to Update**:
- `sdk-users/apps/dataflow/README.md`
- `sdk-users/apps/dataflow/guides/error-handling.md` (NEW - create this)
- `sdk-users/apps/dataflow/guides/inspector-debugging-guide.md` (already exists)
- `sdk-users/apps/dataflow/guides/cli-commands.md` (NEW - create this)
- `sdk-users/apps/dataflow/guides/performance-optimization.md` (NEW - create this)
- `sdk-users/apps/dataflow/troubleshooting/common-errors.md`
**Estimated Time**: 6-8 hours

### 4. CLAUDE.md (Project Instructions)
**File**: `apps/kailash-dataflow/CLAUDE.md`
**Priority**: **MEDIUM** (internal reference)
**Estimated Time**: 1-2 hours

### 5. Main README
**File**: `apps/kailash-dataflow/README.md`
**Priority**: **LOW** (high-level overview)
**Estimated Time**: 1 hour

---

## Update Instructions by File

### 1. `.claude/agents/frameworks/dataflow-specialist.md`

**Current State**: Pre-Phase 1A/1B documentation
**Target State**: Include all Phase 1A/1B improvements

#### Section 1: Add ErrorEnhancer Section

**Location**: After "DataFlow Framework Guide" header, before "Core Capabilities"

```markdown
## 🚨 Error Handling with ErrorEnhancer (NEW in v0.4.7+)

DataFlow includes **ErrorEnhancer** to transform Python exceptions into rich, actionable error messages with solutions.

**Key Features**:
- **DF-XXX Error Codes**: Standardized error codes for quick lookup
- **Context-Aware Messages**: What, why, and how to fix
- **Multiple Solutions**: 3-5 possible fixes with code examples
- **Performance Modes**: FULL (development), MINIMAL (staging), DISABLED (production)
- **Pattern Caching**: 90%+ cache hit rate for repeated errors

**Example Enhanced Error**:
```python
# Code that triggers error
workflow.add_node("UserCreateNode", "create", {
    "name": "Alice"  # Missing 'id' field
})

# Enhanced error output
DF-101: Missing Required Parameter

Error: Field 'id' is required for CREATE operations

Context:
- Node: UserCreateNode
- Operation: CREATE
- Model: User
- Missing Parameter: id

Causes:
1. Missing 'id' field in data dictionary
2. Typo in field name (e.g., 'user_id' instead of 'id')
3. Data structure doesn't match model schema

Solutions:
1. Add 'id' field to your data:
   data = {"id": "user-123", "name": "Alice"}

2. Check model definition for required fields
3. Use Inspector to validate workflow structure

Documentation: https://docs.kailash.dev/dataflow/errors/DF-101
```

**Performance Modes**:
```python
from dataflow import DataFlow

# Development: Full error enhancement (default)
db = DataFlow(url, error_enhancement_mode="FULL")

# Staging: Minimal overhead
db = DataFlow(url, error_enhancement_mode="MINIMAL")

# Production: Disabled for performance
db = DataFlow(url, error_enhancement_mode="DISABLED")
```

**Common Error Codes**:
- **DF-101**: Missing Required Parameter → Add missing field to data dictionary
- **DF-201**: Connection Type Mismatch → Check parameter types in connections
- **DF-301**: Migration Failed → Review schema changes and constraints
- **DF-401**: Database URL Invalid → Verify connection string format
- **DF-501**: Event Loop Closed → Use AsyncLocalRuntime in async contexts
- **DF-601**: Primary Key Missing → Ensure model has 'id' field
- **DF-701**: Node Not Found → Check node name spelling and case
- **DF-801**: Workflow Build Failed → Validate all connections before .build()

**File Reference**: `src/dataflow/core/error_enhancer.py:1-756` (60+ methods)
```

#### Section 2: Add Inspector Section

**Location**: After ErrorEnhancer section

```markdown
## 🔍 Inspector - Workflow Introspection (NEW in v0.4.7+)

DataFlow includes **Inspector** for debugging and analyzing workflow structure before execution.

**Key Features**:
- **Connection Analysis**: List connections, find broken connections, trace chains
- **Parameter Tracing**: Trace parameters back to source, track transformations
- **Workflow Validation**: Validate connections and detect circular dependencies
- **Visual Inspection**: Rich formatted output for debugging
- **30+ Methods**: Comprehensive introspection API

**Basic Usage**:
```python
from dataflow.platform.inspector import Inspector
from kailash.workflow.builder import WorkflowBuilder

workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {"id": "user-123", "name": "Alice"})
workflow.add_node("UserReadNode", "read", {"id": "user-123"})
workflow.add_connection("create", "id", "read", "id")

# Inspect workflow structure
inspector = Inspector(workflow)

# List all connections
connections = inspector.connections()
print(f"Found {len(connections)} connections")

# Trace parameter back to source
trace = inspector.trace_parameter("read", "id")
print(trace.show())  # Shows: create.id → read.id

# Validate connections
validation = inspector.validate_connections()
if not validation["is_valid"]:
    print(f"Found {len(validation['errors'])} connection errors")
```

**Common Debugging Scenarios**:

**Scenario 1: Missing Data Parameter**
```python
# Problem: Parameter 'id' is None in node 'read'
inspector = Inspector(workflow)
trace = inspector.trace_parameter("read", "id")

# Inspector shows:
# create.id (source) → read.id (destination)
# Value: "user-123" (confirmed data flow)
# If value is None, Inspector shows where connection breaks
```

**Scenario 2: Broken Connection**
```python
# Problem: Connection not working as expected
inspector = Inspector(workflow)
broken = inspector.find_broken_connections()

# Shows all connections with type mismatches or missing sources
for conn in broken:
    print(f"Broken: {conn['source']} → {conn['target']}")
    print(f"Reason: {conn['error']}")
```

**Scenario 3: Circular Dependency**
```python
# Problem: Workflow hangs due to circular dependency
inspector = Inspector(workflow)
cycles = inspector.detect_cycles()

if cycles:
    print(f"Found {len(cycles)} circular dependencies:")
    for cycle in cycles:
        print(f"  Cycle: {' → '.join(cycle)}")
```

**File Reference**: `src/dataflow/platform/inspector.py:1-3540` (30+ methods)

**Quick Reference Guide**: `sdk-users/apps/dataflow/guides/inspector-debugging-guide.md` (12+ scenarios)
```

#### Section 3: Add CLI Commands Section

**Location**: After Inspector section

```markdown
## 🔧 CLI Commands (NEW in v0.4.7+)

DataFlow includes 5 CLI commands for workflow analysis, debugging, and generation.

**Available Commands**:
1. **analyze**: Analyze workflow structure and dependencies
2. **debug**: Debug workflow issues with detailed diagnostics
3. **generate**: Generate node code from models
4. **perf**: Performance analysis and profiling
5. **validate**: Validate workflow structure before execution

**Command 1: Analyze**
```bash
# Analyze workflow structure
dataflow analyze my_workflow.py

# Output:
# Workflow Analysis Report
# - Nodes: 15
# - Connections: 23
# - Cycles: 0
# - Validation: PASSED
# - Estimated Runtime: ~2.5s
```

**Command 2: Debug**
```bash
# Debug workflow with detailed diagnostics
dataflow debug my_workflow.py --node "user_create"

# Output:
# Node Debug Report: user_create
# - Type: UserCreateNode
# - Parameters: id, name, email
# - Connections: 3 outgoing, 0 incoming
# - Validation: PASSED
# - Potential Issues: None
```

**Command 3: Generate**
```bash
# Generate node code from model
dataflow generate User --output nodes/

# Generates:
# - nodes/user_create_node.py
# - nodes/user_read_node.py
# - nodes/user_update_node.py
# - nodes/user_delete_node.py
# - nodes/user_list_node.py
```

**Command 4: Perf**
```bash
# Analyze workflow performance
dataflow perf my_workflow.py --profile

# Output:
# Performance Analysis Report
# - Total Runtime: 1.8s
# - Node Timings:
#   - user_create: 0.5s (28%)
#   - user_read: 0.3s (17%)
#   - email_send: 1.0s (55%)
# - Bottlenecks: email_send (optimize email API calls)
```

**Command 5: Validate**
```bash
# Validate workflow before execution
dataflow validate my_workflow.py --strict

# Output:
# Workflow Validation Report
# - Structure: PASSED
# - Connections: PASSED (23 connections)
# - Parameters: PASSED (all required parameters present)
# - Types: PASSED (all type constraints satisfied)
# - Cycles: PASSED (no circular dependencies)
# - Overall: PASSED ✓
```

**File Reference**: `src/dataflow/cli/*.py` (5 command files)
```

#### Section 4: Update Performance Section

**Location**: Replace existing "📊 Performance Considerations" section

```markdown
## 📊 Performance Considerations

**Schema Cache (NEW in v0.4.7+)**:
- **First Operation**: ~1500ms (cache miss with migration check)
- **Subsequent Operations**: ~1ms (cache hit) - **99% faster!**
- **Memory Overhead**: <1KB per cached table
- **Thread Safety**: RLock-protected concurrent access
- **Configuration**:
  ```python
  db = DataFlow(
      url,
      schema_cache_enabled=True,      # Enable cache (default)
      schema_cache_ttl=300,            # TTL in seconds (None = no expiration)
      schema_cache_max_size=10000,    # Max cached tables
      schema_cache_validation=False,  # Schema checksum validation
  )
  ```

**Multi-Operation Workflows**:
```python
# Before Schema Cache:
# Operation 1: 1500ms (migration check)
# Operation 2: 1500ms (migration check)
# Operation 3: 1500ms (migration check)
# Total: 4500ms

# After Schema Cache:
# Operation 1: 1500ms (cache miss)
# Operation 2: 1ms (cache hit)
# Operation 3: 1ms (cache hit)
# Total: 1502ms (99% faster!)
```

**Cache Management**:
```python
# Clear all cache entries
db._schema_cache.clear()

# Clear specific table cache
db._schema_cache.clear_table("User", database_url)

# Get cache performance metrics
metrics = db._schema_cache.get_metrics()
print(f"Hits: {metrics['hits']}")
print(f"Misses: {metrics['misses']}")
print(f"Hit rate: {metrics['hit_rate']:.2%}")
```

**CRUD Operations**:
- Instance creation: ~700ms per DataFlow instance
- First operation (cache miss): ~1500ms with migration checks
- Subsequent operations (cache hit): ~1ms (99% faster)
- Memory overhead: ~20MB per instance with models + <1KB per cached table

**Real-World Impact**:
- **FastAPI Apps**: No slowdown from migration checks on every request
- **ETL Pipelines**: 10x throughput increase for batch operations
- **Background Jobs**: Reliable high-volume processing
- **Multi-Step Workflows**: 91-99% performance improvement
```

#### Section 5: Update Debugging Tips Section

**Location**: Replace existing "🔍 Debugging Tips" section

```markdown
## 🔍 Debugging Tips (Updated for v0.4.7+)

**Use Inspector for Pre-Execution Debugging** (NEW):
```python
from dataflow.platform.inspector import Inspector

# Inspect workflow before execution
inspector = Inspector(workflow)

# List all connections
connections = inspector.connections()
print(f"Total connections: {len(connections)}")

# Trace parameter back to source
trace = inspector.trace_parameter("process", "user_id")
print(trace.show())  # Shows full parameter lineage

# Validate connections
validation = inspector.validate_connections()
if not validation["is_valid"]:
    for error in validation["errors"]:
        print(f"Connection Error: {error}")
```

**Use CLI Commands for Analysis** (NEW):
```bash
# Analyze workflow structure
dataflow analyze my_workflow.py

# Debug specific node
dataflow debug my_workflow.py --node "user_create"

# Validate before execution
dataflow validate my_workflow.py --strict
```

**Enhanced Error Messages** (NEW):
```python
# Errors now include DF-XXX codes, causes, and solutions
try:
    results, _ = runtime.execute(workflow.build())
except Exception as e:
    # Enhanced error with:
    # - Error code (DF-XXX)
    # - Context (node, operation, model)
    # - 3-5 possible causes
    # - 3-5 solutions with code examples
    # - Documentation link
    print(str(e))
```

**Check Node-Instance Coupling** (Existing):
```python
node = db._nodes["UserCreateNode"]()
print(f"Bound to: {node.dataflow_instance}")
print(f"Correct: {node.dataflow_instance is db}")
```

**Verify String ID Preservation** (Existing):
```python
results = runtime.execute(workflow.build())
print(f"ID type: {type(results['create_user']['id'])}")
print(f"ID value: {results['create_user']['id']}")
```

**Performance Profiling** (NEW):
```bash
# Profile workflow performance
dataflow perf my_workflow.py --profile

# Identify bottlenecks and optimization opportunities
```
```

#### Section 6: Add Troubleshooting Section

**Location**: Add new section before "⚠️ Critical Rules"

```markdown
## 🐛 Common Issues & Fixes (NEW in v0.4.7+)

### Issue 1: "DF-101: Missing Required Parameter"

**Problem**: Field 'id' is required for CREATE operations

**Causes**:
1. Missing 'id' field in data dictionary
2. Typo in field name (e.g., 'user_id' instead of 'id')
3. Data structure doesn't match model schema

**Solutions**:
```python
# ❌ WRONG: Missing 'id' field
workflow.add_node("UserCreateNode", "create", {
    "name": "Alice"  # Missing 'id'
})

# ✅ CORRECT: Include 'id' field
workflow.add_node("UserCreateNode", "create", {
    "id": "user-123",  # Primary key required
    "name": "Alice"
})
```

**Quick Fix**: Use Inspector to check model definition
```python
inspector = Inspector(workflow)
model_info = inspector.model("User")
print(f"Required fields: {model_info['required_fields']}")
```

---

### Issue 2: "DF-501: Event Loop is Closed"

**Problem**: AsyncLocalRuntime used in wrong context

**Causes**:
1. Using AsyncLocalRuntime in sync context
2. pytest-asyncio event loop lifecycle mismatch
3. Connection pool bound to closed event loop

**Solutions**:
```python
# ❌ WRONG: AsyncLocalRuntime in sync context
from kailash.runtime import AsyncLocalRuntime

runtime = AsyncLocalRuntime()
results, _ = runtime.execute(workflow.build())  # Sync call on async runtime

# ✅ CORRECT: Use LocalRuntime for sync contexts
from kailash.runtime import LocalRuntime

runtime = LocalRuntime()
results, _ = runtime.execute(workflow.build())

# ✅ OR: Use AsyncLocalRuntime properly in async context
from kailash.runtime import AsyncLocalRuntime

runtime = AsyncLocalRuntime()
results, _ = await runtime.execute_workflow_async(workflow.build(), inputs={})
```

**Quick Fix**: Use `get_runtime()` for automatic selection
```python
from kailash.runtime import get_runtime

runtime = get_runtime()  # Automatically selects correct runtime
```

---

### Issue 3: "Schema cache not improving performance"

**Problem**: First operation slow, subsequent operations also slow

**Causes**:
1. Cache disabled in configuration
2. TTL too short (cache expiring too quickly)
3. Creating new DataFlow instances for each operation

**Solutions**:
```python
# ❌ WRONG: Cache disabled
db = DataFlow(url, schema_cache_enabled=False)

# ✅ CORRECT: Cache enabled (default)
db = DataFlow(url, schema_cache_enabled=True)

# ❌ WRONG: New instance for each operation (cache not reused)
for i in range(100):
    db = DataFlow(url)  # New instance = new cache
    workflow.add_node("UserCreateNode", "create", {...})
    ...

# ✅ CORRECT: Reuse same instance (cache reused)
db = DataFlow(url)  # Single instance
for i in range(100):
    workflow = WorkflowBuilder()
    workflow.add_node("UserCreateNode", "create", {...})
    ...  # 99% faster after first operation!
```

**Quick Fix**: Check cache metrics
```python
metrics = db._schema_cache.get_metrics()
print(f"Cache hit rate: {metrics['hit_rate']:.2%}")  # Should be >90% after warmup
```

---

### Issue 4: "Workflow validation errors"

**Problem**: Connections broken or parameters missing

**Causes**:
1. Typo in node ID or parameter name
2. Connection to non-existent output parameter
3. Type mismatch between connected parameters

**Solutions**:
```python
# Use Inspector to diagnose
inspector = Inspector(workflow)

# Check for broken connections
broken = inspector.find_broken_connections()
for conn in broken:
    print(f"Broken: {conn['source']} → {conn['target']}")
    print(f"Reason: {conn['error']}")

# Validate before execution
validation = inspector.validate_connections()
if not validation["is_valid"]:
    print("Validation errors:")
    for error in validation["errors"]:
        print(f"  - {error}")
```

**Quick Fix**: Use CLI validate command
```bash
dataflow validate my_workflow.py --strict
```
```

### 2. `.claude/skills/02-dataflow.md`

**Current State**: Basic DataFlow skill description
**Target State**: Include Phase 1A/1B tools and patterns

#### Update Skill Description

**Replace Current Description With**:
```markdown
# 02-dataflow

## Description
Kailash DataFlow - zero-config database framework with automatic model-to-node generation, enhanced error handling, and comprehensive debugging tools. Use when asking about 'database operations', 'DataFlow', 'database models', 'CRUD operations', 'bulk operations', 'database queries', 'database migrations', 'multi-tenancy', 'multi-instance', 'database transactions', 'PostgreSQL', 'MySQL', 'SQLite', 'MongoDB', 'pgvector', 'vector search', 'document database', 'RAG', 'semantic search', 'existing database', 'database performance', 'database deployment', 'database testing', 'TDD with databases', '**error handling**', '**debugging workflows**', '**Inspector**', '**CLI commands**', or '**performance optimization**'.

**NEW in v0.4.7+ (Phase 1A/1B)**:
- **ErrorEnhancer**: Transform Python exceptions into actionable DF-XXX error codes with solutions (70-80% faster debugging)
- **Inspector**: 30+ methods for workflow introspection and pre-execution validation (80-90% faster workflow debugging)
- **CLI Commands**: 5 commands (analyze, debug, generate, perf, validate) for development productivity
- **Schema Cache**: 91-99% performance improvement for multi-operation workflows (<1ms after first operation)
- **Bug Fixes**: AsyncLocalRuntime transaction leak resolved (23% → 100% test pass rate)

DataFlow is NOT an ORM - it generates 11 workflow nodes per SQL model, 8 nodes for MongoDB, and 3 nodes for vector operations. (project)
```

#### Add New Skill Invocation Examples

**Add After Description**:
```markdown
## Common Use Cases

**Error Debugging** (NEW - Phase 1A):
- User asks: "How do I fix DF-101 error?"
- User asks: "Why am I getting 'Missing Required Parameter' error?"
- User asks: "How can I get better error messages in DataFlow?"
→ Invoke skill to explain ErrorEnhancer and DF-XXX error codes

**Workflow Debugging** (NEW - Phase 1B):
- User asks: "How do I debug my workflow before running it?"
- User asks: "How can I trace where a parameter comes from?"
- User asks: "How do I find broken connections in my workflow?"
→ Invoke skill to explain Inspector and its 30+ methods

**CLI Usage** (NEW - Phase 1B):
- User asks: "How do I analyze my workflow structure?"
- User asks: "How can I validate my workflow before execution?"
- User asks: "How do I profile my workflow performance?"
→ Invoke skill to explain CLI commands (analyze, debug, validate, perf, generate)

**Performance Optimization** (NEW - Phase 1B):
- User asks: "Why is my workflow slow?"
- User asks: "How can I make my DataFlow operations faster?"
- User asks: "What is schema cache and how do I use it?"
→ Invoke skill to explain schema cache and performance optimizations

**Traditional Database Operations** (Existing):
- User asks: "How do I create/read/update/delete records?"
- User asks: "How do I perform bulk operations?"
- User asks: "How do I query with filters?"
→ Invoke skill for standard CRUD operations
```

### 3. `sdk-users/apps/dataflow/guides/` (Create New Guides)

**Priority**: **HIGH** - These are entirely new files

#### New File 1: `error-handling.md`

**Location**: `sdk-users/apps/dataflow/guides/error-handling.md`

Create comprehensive guide covering:
1. ErrorEnhancer overview
2. Error code reference (DF-1XX through DF-8XX)
3. Performance modes (FULL, MINIMAL, DISABLED)
4. Common error scenarios with solutions
5. Integration with Inspector for error diagnosis
6. Error catalog customization

**Structure**:
```markdown
# DataFlow Error Handling Guide

## Table of Contents
1. ErrorEnhancer Overview
2. Error Code Reference
3. Performance Modes
4. Common Error Scenarios
5. Integration with Inspector
6. Error Catalog Customization

## 1. ErrorEnhancer Overview
[Content from DATAFLOW_IMPROVEMENTS_COMPARISON.md Section 2.1]

## 2. Error Code Reference

### DF-1XX: Parameter Errors
- DF-101: Missing Required Parameter
- DF-102: Parameter Type Mismatch
- DF-103: Parameter Validation Failed
- ...

### DF-2XX: Connection Errors
- DF-201: Connection Type Mismatch
- DF-202: Circular Connection Detected
- ...

### DF-3XX: Migration Errors
...

### DF-4XX: Configuration Errors
...

### DF-5XX: Runtime Errors
...

### DF-6XX: Model Errors
...

### DF-7XX: Node Errors
...

### DF-8XX: Workflow Errors
...

## 3. Performance Modes
[Examples for FULL, MINIMAL, DISABLED modes]

## 4. Common Error Scenarios
[20+ scenarios with before/after examples]

## 5. Integration with Inspector
[How to use Inspector to diagnose errors]

## 6. Error Catalog Customization
[How to extend error_catalog.yaml]
```

**Content Source**: Extract from `DATAFLOW_IMPROVEMENTS_COMPARISON.md` Section 2.1 and Section 3.1

---

#### New File 2: `cli-commands.md`

**Location**: `sdk-users/apps/dataflow/guides/cli-commands.md`

Create comprehensive CLI guide covering:
1. Installation and setup
2. Command reference (analyze, debug, generate, perf, validate)
3. Common workflows with CLI
4. Integration with CI/CD pipelines
5. Advanced usage patterns

**Structure**:
```markdown
# DataFlow CLI Commands Guide

## Table of Contents
1. Installation and Setup
2. Command Reference
3. Common Workflows
4. CI/CD Integration
5. Advanced Usage

## 1. Installation and Setup
```bash
# CLI is included in DataFlow v0.4.7+
pip install kailash-dataflow>=0.4.7

# Verify installation
dataflow --version
```

## 2. Command Reference

### analyze
[Full documentation with examples]

### debug
[Full documentation with examples]

### generate
[Full documentation with examples]

### perf
[Full documentation with examples]

### validate
[Full documentation with examples]

## 3. Common Workflows
[Step-by-step CLI workflows for common tasks]

## 4. CI/CD Integration
```yaml
# GitHub Actions example
- name: Validate DataFlow Workflows
  run: dataflow validate workflows/ --strict
```

## 5. Advanced Usage
[Advanced patterns and tips]
```

**Content Source**: Extract from `.claude/agents/frameworks/dataflow-specialist.md` CLI Commands section

---

#### New File 3: `performance-optimization.md`

**Location**: `sdk-users/apps/dataflow/guides/performance-optimization.md`

Create comprehensive performance guide covering:
1. Schema cache overview and configuration
2. Multi-operation workflow optimization
3. FastAPI/Flask integration patterns
4. ETL pipeline optimization
5. Performance profiling with CLI
6. Benchmarking and metrics

**Structure**:
```markdown
# DataFlow Performance Optimization Guide

## Table of Contents
1. Schema Cache Overview
2. Multi-Operation Workflows
3. FastAPI/Flask Integration
4. ETL Pipeline Optimization
5. Performance Profiling
6. Benchmarking and Metrics

## 1. Schema Cache Overview

### What is Schema Cache?
[Explanation with before/after metrics]

### Configuration
```python
db = DataFlow(
    url,
    schema_cache_enabled=True,
    schema_cache_ttl=300,
    schema_cache_max_size=10000,
)
```

### Performance Metrics
- First operation: ~1500ms (cache miss)
- Subsequent operations: ~1ms (cache hit)
- Improvement: 91-99% faster

## 2. Multi-Operation Workflows
[Examples showing 4500ms → 1502ms improvement]

## 3. FastAPI/Flask Integration
```python
from fastapi import FastAPI
from dataflow import DataFlow

# Create single DataFlow instance
db = DataFlow("postgresql://...")

@app.post("/users")
async def create_user(user_data: dict):
    # Reuses schema cache from db instance
    workflow = WorkflowBuilder()
    ...
    # Fast: ~1ms after first request (cache hit)
```

## 4. ETL Pipeline Optimization
[Batch processing examples with 10x throughput increase]

## 5. Performance Profiling
```bash
dataflow perf my_workflow.py --profile
```

## 6. Benchmarking and Metrics
[Cache metrics, hit rates, benchmarking methodology]
```

**Content Source**: Extract from `DATAFLOW_IMPROVEMENTS_COMPARISON.md` Section 4 (Performance Metrics)

---

### 4. `sdk-users/apps/dataflow/troubleshooting/common-errors.md`

**Current State**: May exist with basic errors
**Target State**: Comprehensive DF-XXX error code reference

#### Update Structure

**Replace/Expand with**:
```markdown
# DataFlow Common Errors and Solutions

## Table of Contents
1. Parameter Errors (DF-1XX)
2. Connection Errors (DF-2XX)
3. Migration Errors (DF-3XX)
4. Configuration Errors (DF-4XX)
5. Runtime Errors (DF-5XX)
6. Model Errors (DF-6XX)
7. Node Errors (DF-7XX)
8. Workflow Errors (DF-8XX)

---

## 1. Parameter Errors (DF-1XX)

### DF-101: Missing Required Parameter

**Error Message**:
```
DF-101: Missing Required Parameter

Error: Field 'id' is required for CREATE operations
```

**Causes**:
1. Missing 'id' field in data dictionary
2. Typo in field name (e.g., 'user_id' instead of 'id')
3. Data structure doesn't match model schema
4. Using UPDATE pattern on CREATE node (common mistake)

**Solutions**:
```python
# ❌ WRONG: Missing 'id' field
workflow.add_node("UserCreateNode", "create", {
    "name": "Alice"  # Missing 'id'
})

# ✅ CORRECT: Include 'id' field
workflow.add_node("UserCreateNode", "create", {
    "id": "user-123",
    "name": "Alice",
    "email": "alice@example.com"
})
```

**Quick Fix**:
1. Check model definition for required fields
2. Use Inspector to validate workflow: `inspector.model("User")`
3. Review error message for missing parameter name

**Documentation**: See `guides/error-handling.md#df-101`

---

### DF-102: Parameter Type Mismatch
[Similar structure for each error code]

---

## 2. Connection Errors (DF-2XX)
[Full documentation for DF-2XX errors]

## 3. Migration Errors (DF-3XX)
[Full documentation for DF-3XX errors]

## 4. Configuration Errors (DF-4XX)
[Full documentation for DF-4XX errors]

## 5. Runtime Errors (DF-5XX)

### DF-501: Event Loop is Closed

**Error Message**:
```
DF-501: Event Loop is Closed

Error: RuntimeError: Event loop is closed
```

**Causes**:
1. Using AsyncLocalRuntime in sync context
2. pytest-asyncio event loop lifecycle mismatch
3. Connection pool bound to closed event loop
4. Mixing sync and async runtimes incorrectly

**Solutions**:
```python
# ❌ WRONG: AsyncLocalRuntime in sync context
from kailash.runtime import AsyncLocalRuntime

runtime = AsyncLocalRuntime()
results, _ = runtime.execute(workflow.build())  # Sync call on async runtime!

# ✅ CORRECT: Use LocalRuntime for sync contexts
from kailash.runtime import LocalRuntime

runtime = LocalRuntime()
results, _ = runtime.execute(workflow.build())

# ✅ OR: Use AsyncLocalRuntime properly in async context
from kailash.runtime import AsyncLocalRuntime

async def main():
    runtime = AsyncLocalRuntime()
    results, _ = await runtime.execute_workflow_async(workflow.build(), inputs={})
```

**Quick Fix**:
1. Use `get_runtime()` for automatic runtime selection
2. Check if you're in async context (inside `async def`)
3. For pytest, ensure `cleanup_dataflow_connection_pools` fixture is active

**Documentation**: See `guides/asynclocalruntime-guide.md`

---

## 6. Model Errors (DF-6XX)
[Full documentation for DF-6XX errors]

## 7. Node Errors (DF-7XX)
[Full documentation for DF-7XX errors]

## 8. Workflow Errors (DF-8XX)
[Full documentation for DF-8XX errors]
```

**Content Source**: Extract from `DATAFLOW_IMPROVEMENTS_COMPARISON.md` Section 2.1 and `src/dataflow/core/error_catalog.yaml`

---

### 5. `apps/kailash-dataflow/CLAUDE.md`

**Current State**: Project instructions with basic patterns
**Target State**: Include Phase 1A/1B tools in critical patterns

#### Update Critical Patterns Section

**Add New Subsection After "Essential Pattern (All Frameworks)"**:

```markdown
### Debugging & Error Handling Patterns (v0.4.7+)

**ErrorEnhancer** - Get actionable error messages with solutions:
```python
from dataflow import DataFlow

# Development: Full error enhancement (default)
db = DataFlow(url, error_enhancement_mode="FULL")

# Staging: Minimal overhead
db = DataFlow(url, error_enhancement_mode="MINIMAL")

# Production: Disabled for performance
db = DataFlow(url, error_enhancement_mode="DISABLED")

try:
    results, _ = runtime.execute(workflow.build())
except Exception as e:
    # Error includes:
    # - DF-XXX error code
    # - Context (node, operation, model)
    # - 3-5 possible causes
    # - 3-5 solutions with code examples
    # - Documentation link
    print(str(e))
```

**Inspector** - Debug workflows before execution:
```python
from dataflow.platform.inspector import Inspector

inspector = Inspector(workflow)

# List all connections
connections = inspector.connections()

# Trace parameter back to source
trace = inspector.trace_parameter("process", "user_id")
print(trace.show())

# Validate connections
validation = inspector.validate_connections()
if not validation["is_valid"]:
    for error in validation["errors"]:
        print(f"Connection Error: {error}")
```

**CLI Commands** - Analyze and validate workflows:
```bash
# Analyze workflow structure
dataflow analyze my_workflow.py

# Debug specific node
dataflow debug my_workflow.py --node "user_create"

# Validate before execution
dataflow validate my_workflow.py --strict

# Profile performance
dataflow perf my_workflow.py --profile

# Generate node code from models
dataflow generate User --output nodes/
```

**Schema Cache** - Optimize multi-operation workflows:
```python
from dataflow import DataFlow

# Enable schema cache (default)
db = DataFlow(url, schema_cache_enabled=True)

# First operation: ~1500ms (cache miss)
# Subsequent operations: ~1ms (cache hit) - 99% faster!

# Get cache metrics
metrics = db._schema_cache.get_metrics()
print(f"Cache hit rate: {metrics['hit_rate']:.2%}")
```
```

#### Update "⚠️ Critical Rules" Section

**Add These Rules**:
```markdown
## ⚠️ Critical Rules
- ALWAYS: `runtime.execute(workflow.build())`
- NEVER: `workflow.execute(runtime)`
- String-based nodes: `workflow.add_node("NodeName", "id", {})`
- Real infrastructure: NO MOCKING in Tiers 2-3 tests
- **NEW**: Use Inspector to validate workflows before execution
- **NEW**: Use CLI commands (`dataflow validate`) in CI/CD pipelines
- **NEW**: Enable schema cache for multi-operation workflows (default in v0.4.7+)
- **NEW**: Use ErrorEnhancer in development (error_enhancement_mode="FULL")
- **Docker/FastAPI**: Use `AsyncLocalRuntime()` or `WorkflowAPI()` (defaults to async)
- **CLI/Scripts**: Use `LocalRuntime()` for synchronous execution
```

---

### 6. `apps/kailash-dataflow/README.md`

**Current State**: High-level overview
**Target State**: Mention Phase 1A/1B improvements

#### Update Features Section

**Add Subsection**:
```markdown
## ✨ Recent Improvements (v0.4.7+)

### Developer Experience Enhancements

**ErrorEnhancer** - 70-80% faster debugging:
- DF-XXX error codes with solutions
- Context-aware error messages
- 3-5 possible causes and fixes per error
- 50+ error patterns in YAML catalog

**Inspector** - 80-90% faster workflow debugging:
- 30+ inspection methods for workflow introspection
- Connection tracing and validation
- Parameter lineage tracking
- Pre-execution error detection

**CLI Commands** - 5 productivity commands:
- `analyze`: Workflow structure analysis
- `debug`: Detailed node diagnostics
- `generate`: Auto-generate node code
- `perf`: Performance profiling
- `validate`: Pre-execution validation

**Schema Cache** - 91-99% performance improvement:
- <1ms operations after first (was ~1500ms)
- Thread-safe concurrent access
- <1KB memory overhead per table
- Automatic for multi-operation workflows

**Bug Fixes**:
- AsyncLocalRuntime transaction leak resolved
- 23% → 100% test pass rate
- Production-ready for async workflows
```

---

## New Sections to Add

### 1. Error Code Reference Page

**Location**: `sdk-users/apps/dataflow/reference/error-codes.md`

Create comprehensive error code reference:
```markdown
# DataFlow Error Code Reference

## Quick Lookup

| Code | Category | Description | Quick Fix |
|------|----------|-------------|-----------|
| DF-101 | Parameter | Missing Required Parameter | Add missing field to data |
| DF-102 | Parameter | Parameter Type Mismatch | Check parameter type |
| DF-201 | Connection | Connection Type Mismatch | Verify connection types |
| DF-301 | Migration | Migration Failed | Review schema changes |
| DF-401 | Configuration | Database URL Invalid | Fix connection string |
| DF-501 | Runtime | Event Loop Closed | Use correct runtime type |
| DF-601 | Model | Primary Key Missing | Add 'id' field to model |
| DF-701 | Node | Node Not Found | Check node name spelling |
| DF-801 | Workflow | Workflow Build Failed | Validate all connections |

## Detailed Reference

[Full documentation for each error code with:
- Error message format
- Common causes (3-5)
- Solutions with code examples (3-5)
- Quick fixes
- Related error codes
- Documentation links]
```

### 2. Inspector API Reference

**Location**: `sdk-users/apps/dataflow/reference/inspector-api.md`

Create comprehensive Inspector API reference:
```markdown
# Inspector API Reference

## Overview
The Inspector class provides 30+ methods for workflow introspection, validation, and debugging.

## Basic Methods

### `workflow()`
Returns the workflow object being inspected.

### `connections()`
List all connections in the workflow.

**Returns**: List of connection dictionaries

**Example**:
```python
inspector = Inspector(workflow)
connections = inspector.connections()
for conn in connections:
    print(f"{conn['source']} → {conn['target']}")
```

## Connection Methods

### `trace_parameter(node_id, param_name)`
Trace a parameter back to its source.

### `find_broken_connections()`
Find all broken connections in the workflow.

### `validate_connections()`
Validate all connections for type safety.

## [Continue for all 30+ methods]
```

### 3. CLI Command Reference

**Location**: `sdk-users/apps/dataflow/reference/cli-reference.md`

Create comprehensive CLI reference:
```markdown
# DataFlow CLI Command Reference

## Command: analyze

**Usage**: `dataflow analyze [OPTIONS] WORKFLOW_FILE`

**Description**: Analyze workflow structure and dependencies

**Options**:
- `--format TEXT`: Output format (text, json, yaml) [default: text]
- `--verbose`: Show detailed analysis
- `--output FILE`: Write output to file

**Examples**:
```bash
# Basic analysis
dataflow analyze my_workflow.py

# JSON output
dataflow analyze my_workflow.py --format json

# Save to file
dataflow analyze my_workflow.py --output analysis.txt
```

**Output**:
```
Workflow Analysis Report
- Nodes: 15
- Connections: 23
- Cycles: 0
- Validation: PASSED
- Estimated Runtime: ~2.5s
```

## [Continue for all 5 commands]
```

---

## Examples to Replace/Update

### 1. Error Handling Examples

**Replace All Generic Exception Handling With ErrorEnhancer Examples**:

**Before (Generic)**:
```python
try:
    results, _ = runtime.execute(workflow.build())
except Exception as e:
    print(f"Error: {e}")
```

**After (Enhanced)**:
```python
from dataflow import DataFlow

# Enable error enhancement (default in v0.4.7+)
db = DataFlow(url, error_enhancement_mode="FULL")

try:
    results, _ = runtime.execute(workflow.build())
except Exception as e:
    # Error includes:
    # - DF-XXX error code
    # - Context (node, operation, model)
    # - 3-5 possible causes
    # - 3-5 solutions with code examples
    # - Documentation link
    print(str(e))

    # Or extract structured error info
    if hasattr(e, 'error_code'):
        print(f"Error Code: {e.error_code}")
        print(f"Solutions: {e.solutions}")
```

### 2. Debugging Examples

**Replace All Print Debugging With Inspector Examples**:

**Before (Print Debugging)**:
```python
# Print debugging workflow
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {...})
workflow.add_node("UserReadNode", "read", {...})
workflow.add_connection("create", "id", "read", "id")

print(f"Nodes: {len(workflow._node_instances)}")
print(f"Connections: {len(workflow._connections)}")

# Try to find why parameter is None
results, _ = runtime.execute(workflow.build())
print(f"User ID from create: {results.get('create', {}).get('id')}")
print(f"User ID in read: {results.get('read', {}).get('id')}")
```

**After (Inspector)**:
```python
from dataflow.platform.inspector import Inspector

# Use Inspector to debug workflow
workflow = WorkflowBuilder()
workflow.add_node("UserCreateNode", "create", {...})
workflow.add_node("UserReadNode", "read", {...})
workflow.add_connection("create", "id", "read", "id")

inspector = Inspector(workflow)

# Analyze structure
print(f"Nodes: {len(inspector.nodes())}")
print(f"Connections: {len(inspector.connections())}")

# Trace parameter
trace = inspector.trace_parameter("read", "id")
print(trace.show())  # Shows: create.id → read.id with values

# Validate before execution
validation = inspector.validate_connections()
if not validation["is_valid"]:
    print("Errors found before execution:")
    for error in validation["errors"]:
        print(f"  - {error}")
else:
    results, _ = runtime.execute(workflow.build())
```

### 3. Performance Examples

**Add Schema Cache Examples to All Multi-Operation Workflows**:

**Before (No Cache Context)**:
```python
from dataflow import DataFlow
from kailash.runtime import LocalRuntime

db = DataFlow("postgresql://...")

# Multiple operations
for user_data in user_list:
    workflow = WorkflowBuilder()
    workflow.add_node("UserCreateNode", "create", user_data)
    runtime = LocalRuntime()
    results, _ = runtime.execute(workflow.build())
```

**After (With Cache Context)**:
```python
from dataflow import DataFlow
from kailash.runtime import LocalRuntime

# Schema cache enabled by default in v0.4.7+
db = DataFlow("postgresql://...")

# First operation: ~1500ms (cache miss)
# Subsequent operations: ~1ms (cache hit) - 99% faster!

for user_data in user_list:
    workflow = WorkflowBuilder()
    workflow.add_node("UserCreateNode", "create", user_data)
    runtime = LocalRuntime()
    results, _ = runtime.execute(workflow.build())
    # Fast after first iteration: ~1ms (cache hit)

# Check cache performance
metrics = db._schema_cache.get_metrics()
print(f"Cache hit rate: {metrics['hit_rate']:.2%}")  # Should be >90%
```

---

## Validation Checklist

### Before Updating Documentation

- [ ] Read `DATAFLOW_IMPROVEMENTS_COMPARISON.md` thoroughly
- [ ] Understand all Phase 1A/1B improvements
- [ ] Review file:line references in comparison document
- [ ] Check existing documentation structure
- [ ] Identify sections that need updating vs. new sections

### During Documentation Update

- [ ] Update `.claude/agents/frameworks/dataflow-specialist.md` (3-4 hours)
  - [ ] Add ErrorEnhancer section
  - [ ] Add Inspector section
  - [ ] Add CLI Commands section
  - [ ] Update Performance section
  - [ ] Update Debugging Tips section
  - [ ] Add Troubleshooting section

- [ ] Update `.claude/skills/02-dataflow.md` (2-3 hours)
  - [ ] Update skill description
  - [ ] Add new use cases
  - [ ] Add invocation examples

- [ ] Create new guides in `sdk-users/apps/dataflow/guides/` (6-8 hours)
  - [ ] Create `error-handling.md`
  - [ ] Create `cli-commands.md`
  - [ ] Create `performance-optimization.md`
  - [ ] Update `inspector-debugging-guide.md` (if exists)

- [ ] Update `sdk-users/apps/dataflow/troubleshooting/common-errors.md` (2-3 hours)
  - [ ] Add DF-1XX error codes
  - [ ] Add DF-2XX error codes
  - [ ] Add DF-3XX error codes
  - [ ] Add DF-4XX error codes
  - [ ] Add DF-5XX error codes
  - [ ] Add DF-6XX error codes
  - [ ] Add DF-7XX error codes
  - [ ] Add DF-8XX error codes

- [ ] Create new reference pages (3-4 hours)
  - [ ] Create `reference/error-codes.md`
  - [ ] Create `reference/inspector-api.md`
  - [ ] Create `reference/cli-reference.md`

- [ ] Update `apps/kailash-dataflow/CLAUDE.md` (1-2 hours)
  - [ ] Add debugging patterns
  - [ ] Update critical rules

- [ ] Update `apps/kailash-dataflow/README.md` (1 hour)
  - [ ] Add v0.4.7+ improvements section

### After Documentation Update

- [ ] **Validate all code examples** - Run every code example to ensure it works
- [ ] **Check all file:line references** - Verify file paths and line numbers are correct
- [ ] **Cross-reference links** - Ensure all documentation links work
- [ ] **Consistency check** - Ensure terminology is consistent across all files
- [ ] **Completeness check** - Verify all Phase 1A/1B features are documented
- [ ] **Review with team** - Have someone review the updated documentation
- [ ] **Test with Claude** - Ensure `.claude/` files work with Claude Code
- [ ] **User testing** - Have a developer follow the guides to verify clarity

### Documentation Quality Metrics

**Target Metrics**:
- [ ] 100% of Phase 1A/1B features documented
- [ ] 100% of code examples tested and working
- [ ] 100% of error codes documented (DF-1XX through DF-8XX)
- [ ] 100% of Inspector methods documented (30+ methods)
- [ ] 100% of CLI commands documented (5 commands)
- [ ] 0 broken internal links
- [ ] 0 incorrect file:line references
- [ ] <5 minutes to find solution for any common error (using docs)

---

## Estimated Total Time

**Documentation Update Effort**:
- `.claude/agents/frameworks/dataflow-specialist.md`: 3-4 hours
- `.claude/skills/02-dataflow.md`: 2-3 hours
- `sdk-users/apps/dataflow/guides/`: 6-8 hours (3 new guides)
- `sdk-users/apps/dataflow/troubleshooting/`: 2-3 hours
- `sdk-users/apps/dataflow/reference/`: 3-4 hours (3 new references)
- `apps/kailash-dataflow/CLAUDE.md`: 1-2 hours
- `apps/kailash-dataflow/README.md`: 1 hour
- **Validation and testing**: 4-6 hours

**Total**: 22-31 hours (3-4 business days)

---

## Next Steps

1. **Create a GitHub Issue** - Track documentation update work
2. **Prioritize files** - Start with `.claude/` files (most critical for AI agents)
3. **Work in branches** - Create branch per major documentation section
4. **Test incrementally** - Validate examples as you write them
5. **Review with team** - Get feedback before finalizing
6. **Deploy gradually** - Roll out updated docs section by section

---

## References

- **Comparison Document**: `docs/DATAFLOW_IMPROVEMENTS_COMPARISON.md`
- **Stock Take**: `todos/STOCK-TAKE-2025-11-07.md`
- **Bug Fix Verification**: `reports/issues/ASYNCLOCALRUNTIME_FIX_VERIFICATION_FINAL.md`
- **ErrorEnhancer Source**: `src/dataflow/core/error_enhancer.py:1-756`
- **Inspector Source**: `src/dataflow/platform/inspector.py:1-3540`
- **CLI Commands Source**: `src/dataflow/cli/*.py`
- **Schema Cache Source**: `src/dataflow/core/schema_cache.py`

---

**Document Status**: Ready for execution
**Last Updated**: 2025-11-07
**Maintained By**: DataFlow Team
