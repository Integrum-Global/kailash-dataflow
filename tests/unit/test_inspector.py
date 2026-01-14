"""
Test-First Development for Inspector API

This test suite is written BEFORE implementation to ensure proper TDD methodology.
All tests should FAIL initially (RED phase), then pass after implementation (GREEN phase).

Test Coverage:
- Connection Analysis (connections, connection_chain, connection_graph, validate_connections, find_broken_connections)
- Parameter Tracing (trace_parameter, parameter_flow, find_parameter_source, parameter_dependencies, parameter_consumers)
- Node Analysis (node_dependencies, node_dependents, execution_order, node_schema, compare_nodes)
- Workflow Analysis (workflow_summary, workflow_metrics, workflow_validation_report)
- Integration with DataFlow workflows
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

# ============================================================================
# Test Group 1: Connection Analysis (Critical Foundation)
# ============================================================================


class TestConnectionAnalysis:
    """Test connection analysis methods."""

    @pytest.fixture
    def sample_workflow(self):
        """Create a sample workflow with various connection patterns."""
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "create_user",
            {"code": "result = {'id': 'user-1', 'record': {'name': 'Alice'}}"},
        )
        workflow.add_node(
            "PythonCodeNode",
            "update_user",
            {"code": "result = {'success': True, 'updated': filter}"},
        )
        workflow.add_node(
            "PythonCodeNode", "read_user", {"code": "result = {'user': filter}"}
        )

        # Direct connection
        workflow.add_connection("create_user", "id", "update_user", "filter.id")
        # Dot notation
        workflow.add_connection(
            "create_user", "record.name", "read_user", "filter.name"
        )
        # Simple connection
        workflow.add_connection("update_user", "success", "read_user", "should_read")

        return workflow

    @pytest.fixture
    def inspector_with_workflow(self, sample_workflow):
        """Create Inspector instance with sample workflow."""
        from dataflow.platform.inspector import Inspector

        # Create a mock DataFlow instance
        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        mock_db = MockDataFlow()
        inspector = Inspector(mock_db)
        inspector.workflow_obj = sample_workflow.build()
        return inspector

    def test_connections_all(self, inspector_with_workflow):
        """Should list all connections in workflow."""
        from dataflow.platform.inspector import ConnectionInfo

        inspector = inspector_with_workflow
        connections = inspector.connections()

        assert isinstance(connections, list)
        assert len(connections) == 3, "Should have 3 connections"
        assert all(isinstance(c, ConnectionInfo) for c in connections)

        # Verify connection details
        conn1 = connections[0]
        assert conn1.source_node == "create_user"
        assert conn1.target_node == "update_user"
        assert conn1.source_param == "id"
        assert conn1.target_param == "filter.id"

    def test_connections_for_node(self, inspector_with_workflow):
        """Should list connections for specific node."""
        from dataflow.platform.inspector import ConnectionInfo

        inspector = inspector_with_workflow
        connections = inspector.connections(node_id="create_user")

        assert isinstance(connections, list)
        assert len(connections) == 2, "create_user has 2 outgoing connections"
        assert all(c.source_node == "create_user" for c in connections)

    def test_connection_chain(self, inspector_with_workflow):
        """Should trace connection path between two nodes."""
        from dataflow.platform.inspector import ConnectionInfo

        inspector = inspector_with_workflow
        chain = inspector.connection_chain(from_node="create_user", to_node="read_user")

        assert isinstance(chain, list)
        assert len(chain) >= 1, "Should have at least one path"

        # Verify chain starts and ends correctly
        assert chain[0].source_node == "create_user"
        assert chain[-1].target_node == "read_user"

    def test_connection_graph(self, inspector_with_workflow):
        """Should get full workflow connection graph."""
        inspector = inspector_with_workflow
        graph = inspector.connection_graph()

        assert isinstance(graph, dict)
        assert "create_user" in graph
        assert "update_user" in graph
        assert "read_user" in graph

        # Verify adjacency relationships
        assert "update_user" in graph["create_user"]
        assert "read_user" in graph["create_user"]

    def test_validate_connections(self, inspector_with_workflow):
        """Should validate all connections."""
        inspector = inspector_with_workflow
        is_valid, issues = inspector.validate_connections()

        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)

        # Valid workflow should pass
        assert is_valid is True
        assert len(issues) == 0

    def test_find_broken_connections(self, sample_workflow):
        """Should identify broken connections."""
        from dataflow.platform.inspector import ConnectionInfo, Inspector

        from kailash.workflow.builder import WorkflowBuilder

        # Create workflow with broken connection
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "create_user", {"code": "result = {'id': 'user-1'}"}
        )
        workflow.add_node(
            "PythonCodeNode", "read_user", {"code": "result = {'user': filter}"}
        )

        # Add connection with missing source output
        workflow.add_connection(
            "create_user", "nonexistent_field", "read_user", "filter.name"
        )

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        broken = inspector.find_broken_connections()

        assert isinstance(broken, list)
        assert len(broken) > 0, "Should find broken connection"
        assert all(isinstance(c, ConnectionInfo) for c in broken)
        assert broken[0].is_valid is False
        assert len(broken[0].validation_issues) > 0


# ============================================================================
# Test Group 2: Parameter Tracing (Critical for Debugging)
# ============================================================================


class TestParameterTracing:
    """Test parameter tracing methods."""

    @pytest.fixture
    def complex_workflow(self):
        """Create workflow with parameter flow chains."""
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "input", {"code": "result = {'value': 10}"})
        workflow.add_node(
            "PythonCodeNode", "processor", {"code": "result = {'result': data * 2}"}
        )
        workflow.add_node(
            "PythonCodeNode", "transformer", {"code": "result = {'output': input + 5}"}
        )
        workflow.add_node(
            "PythonCodeNode", "output", {"code": "result = {'final': result}"}
        )

        # Create parameter flow chain
        workflow.add_connection("input", "value", "processor", "data")
        workflow.add_connection("processor", "result", "transformer", "input")
        workflow.add_connection("transformer", "output", "output", "result")

        return workflow

    @pytest.fixture
    def inspector_with_complex_workflow(self, complex_workflow):
        """Create Inspector with complex workflow."""
        from dataflow.platform.inspector import Inspector

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = complex_workflow.build()
        return inspector

    def test_trace_parameter(self, inspector_with_complex_workflow):
        """Should trace parameter back to source."""
        from dataflow.platform.inspector import ParameterTrace

        inspector = inspector_with_complex_workflow
        trace = inspector.trace_parameter(node_id="output", parameter_name="result")

        assert isinstance(trace, ParameterTrace)
        assert trace.parameter_name == "result"
        assert trace.destination_node == "output"
        assert trace.destination_param == "result"
        assert trace.source_node == "input"
        assert len(trace.transformations) >= 2  # processor -> transformer -> output

    def test_parameter_flow(self, inspector_with_complex_workflow):
        """Should show how parameter flows through workflow."""
        from dataflow.platform.inspector import ParameterTrace

        inspector = inspector_with_complex_workflow
        flows = inspector.parameter_flow(from_node="input", parameter="value")

        assert isinstance(flows, list)
        assert len(flows) > 0
        assert all(isinstance(f, ParameterTrace) for f in flows)

        # Should show full chain: input -> processor -> transformer -> output
        assert len(flows) >= 3

    def test_find_parameter_source(self, inspector_with_complex_workflow):
        """Should find where parameter originates."""
        inspector = inspector_with_complex_workflow
        source = inspector.find_parameter_source(node_id="output", parameter="result")

        assert source is not None
        assert source == "input"

    def test_parameter_dependencies(self, inspector_with_complex_workflow):
        """Should list all parameters node depends on."""
        inspector = inspector_with_complex_workflow
        deps = inspector.parameter_dependencies(node_id="output")

        assert isinstance(deps, dict)
        assert "result" in deps
        assert deps["result"] == "transformer"  # Direct dependency

    def test_parameter_consumers(self, inspector_with_complex_workflow):
        """Should list nodes consuming output parameter."""
        inspector = inspector_with_complex_workflow
        consumers = inspector.parameter_consumers(node_id="input", output_param="value")

        assert isinstance(consumers, list)
        assert "processor" in consumers

    def test_parameter_trace_with_dot_notation(self):
        """Should handle dot notation in parameter tracing."""
        from dataflow.platform.inspector import Inspector, ParameterTrace

        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "create_user",
            {
                "code": "result = {'record': {'name': 'Alice', 'email': 'alice@example.com'}}"
            },
        )
        workflow.add_node(
            "PythonCodeNode", "read_user", {"code": "result = {'user': filter}"}
        )

        # Dot notation connection
        workflow.add_connection(
            "create_user", "record.name", "read_user", "filter.name"
        )

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        trace = inspector.trace_parameter(
            node_id="read_user", parameter_name="filter.name"
        )

        assert isinstance(trace, ParameterTrace)
        assert trace.source_param == "record.name"
        assert trace.destination_param == "filter.name"


# ============================================================================
# Test Group 3: Node Analysis
# ============================================================================


class TestNodeAnalysis:
    """Test node analysis methods."""

    @pytest.fixture
    def dag_workflow(self):
        """Create DAG workflow for dependency analysis."""
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "input", {"code": "result = {'data': [1, 2, 3]}"}
        )
        workflow.add_node(
            "PythonCodeNode", "proc_a", {"code": "result = {'result': sum(input)}"}
        )
        workflow.add_node(
            "PythonCodeNode", "proc_b", {"code": "result = {'result': len(input)}"}
        )
        workflow.add_node(
            "PythonCodeNode",
            "merger",
            {"code": "result = {'output': input_a + input_b}"},
        )
        workflow.add_node(
            "PythonCodeNode", "output", {"code": "result = {'final': result}"}
        )

        # Create dependency graph
        workflow.add_connection("input", "data", "proc_a", "input")
        workflow.add_connection("input", "data", "proc_b", "input")
        workflow.add_connection("proc_a", "result", "merger", "input_a")
        workflow.add_connection("proc_b", "result", "merger", "input_b")
        workflow.add_connection("merger", "output", "output", "result")

        return workflow

    @pytest.fixture
    def inspector_with_dag(self, dag_workflow):
        """Create Inspector with DAG workflow."""
        from dataflow.platform.inspector import Inspector

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = dag_workflow.build()
        return inspector

    def test_node_dependencies(self, inspector_with_dag):
        """Should list all nodes this node depends on."""
        inspector = inspector_with_dag
        deps = inspector.node_dependencies(node_id="merger")

        assert isinstance(deps, list)
        assert "proc_a" in deps
        assert "proc_b" in deps
        assert len(deps) == 2

    def test_node_dependents(self, inspector_with_dag):
        """Should list all nodes that depend on this node."""
        inspector = inspector_with_dag
        dependents = inspector.node_dependents(node_id="input")

        assert isinstance(dependents, list)
        assert "proc_a" in dependents
        assert "proc_b" in dependents

    def test_execution_order(self, inspector_with_dag):
        """Should get workflow execution order (topological sort)."""
        inspector = inspector_with_dag
        order = inspector.execution_order()

        assert isinstance(order, list)
        assert len(order) == 5

        # Verify topological order
        assert order.index("input") < order.index("proc_a")
        assert order.index("input") < order.index("proc_b")
        assert order.index("proc_a") < order.index("merger")
        assert order.index("proc_b") < order.index("merger")
        assert order.index("merger") < order.index("output")

    def test_node_schema(self, inspector_with_dag):
        """Should get input/output schema for node."""
        inspector = inspector_with_dag
        schema = inspector.node_schema(node_id="merger")

        assert isinstance(schema, dict)
        assert "inputs" in schema
        assert "outputs" in schema

        # Verify schema structure
        assert "input_a" in schema["inputs"]
        assert "input_b" in schema["inputs"]
        assert "output" in schema["outputs"]

    def test_compare_nodes(self, inspector_with_dag):
        """Should compare two nodes and show differences."""
        inspector = inspector_with_dag
        comparison = inspector.compare_nodes(node_id1="proc_a", node_id2="proc_b")

        assert isinstance(comparison, dict)
        assert "node1" in comparison
        assert "node2" in comparison
        assert "differences" in comparison

        # Should have node details
        assert comparison["node1"]["node_id"] == "proc_a"
        assert comparison["node2"]["node_id"] == "proc_b"


# ============================================================================
# Test Group 4: Workflow Analysis
# ============================================================================


class TestWorkflowAnalysis:
    """Test workflow analysis methods."""

    @pytest.fixture
    def full_workflow(self):
        """Create comprehensive workflow for analysis."""
        from kailash.workflow.builder import WorkflowBuilder

        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "input", {"code": "result = {'value': 10}"})
        workflow.add_node(
            "PythonCodeNode",
            "validator",
            {"code": "result = {'valid_data': data if data > 0 else 0}"},
        )
        workflow.add_node(
            "PythonCodeNode", "processor", {"code": "result = {'result': data * 2}"}
        )
        workflow.add_node(
            "PythonCodeNode",
            "storage",
            {"code": "result = {'success': True, 'stored': record}"},
        )
        workflow.add_node(
            "PythonCodeNode", "output", {"code": "result = {'final': result}"}
        )

        # Create connections
        workflow.add_connection("input", "value", "validator", "data")
        workflow.add_connection("validator", "valid_data", "processor", "data")
        workflow.add_connection("processor", "result", "storage", "record")
        workflow.add_connection("storage", "success", "output", "result")

        return workflow

    @pytest.fixture
    def inspector_with_full_workflow(self, full_workflow):
        """Create Inspector with full workflow."""
        from dataflow.platform.inspector import Inspector

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = full_workflow.build()
        return inspector

    def test_workflow_summary(self, inspector_with_full_workflow):
        """Should get high-level workflow overview."""
        inspector = inspector_with_full_workflow
        summary = inspector.workflow_summary()

        assert isinstance(summary, dict)
        assert "node_count" in summary
        assert "connection_count" in summary
        assert "nodes" in summary
        assert "entry_points" in summary
        assert "exit_points" in summary

        # Verify counts
        assert summary["node_count"] == 5
        assert summary["connection_count"] == 4
        assert "input" in summary["entry_points"]
        assert "output" in summary["exit_points"]

    def test_workflow_metrics(self, inspector_with_full_workflow):
        """Should get workflow statistics."""
        inspector = inspector_with_full_workflow
        metrics = inspector.workflow_metrics()

        assert isinstance(metrics, dict)
        assert "node_count" in metrics
        assert "connection_count" in metrics
        assert "depth" in metrics
        assert "complexity" in metrics

        # Verify metric values
        assert metrics["node_count"] == 5
        assert metrics["connection_count"] == 4
        assert metrics["depth"] >= 4  # Longest path

    def test_workflow_validation_report(self, inspector_with_full_workflow):
        """Should provide comprehensive workflow validation."""
        inspector = inspector_with_full_workflow
        report = inspector.workflow_validation_report()

        assert isinstance(report, dict)
        assert "is_valid" in report
        assert "errors" in report
        assert "warnings" in report
        assert "suggestions" in report

        # Valid workflow should pass
        assert report["is_valid"] is True
        assert len(report["errors"]) == 0


# ============================================================================
# Test Group 5: Integration with DataFlow
# ============================================================================


class TestInspectorIntegration:
    """Test Inspector integration with real DataFlow workflows."""

    def test_inspector_with_dataflow_workflow(self, memory_dataflow):
        """Should inspect DataFlow-generated workflow."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        db = memory_dataflow

        @db.model
        class User:
            id: str
            name: str
            email: str

        # Create workflow with DataFlow nodes
        workflow = WorkflowBuilder()
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"id": "user-1", "name": "Alice", "email": "alice@example.com"},
        )
        workflow.add_node("UserReadNode", "read_user", {"filter": {}})
        workflow.add_connection("create_user", "id", "read_user", "filter.id")

        inspector = Inspector(db)
        inspector.workflow_obj = workflow.build()

        # Test connection analysis
        connections = inspector.connections()
        assert len(connections) == 1
        assert connections[0].source_node == "create_user"
        assert connections[0].target_node == "read_user"

    def test_inspector_parameter_tracing_real_workflow(self, memory_dataflow):
        """Should trace parameters in real DataFlow workflow."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        db = memory_dataflow

        @db.model
        class Product:
            id: str
            name: str
            price: float

        workflow = WorkflowBuilder()
        workflow.add_node(
            "ProductCreateNode",
            "create_product",
            {"id": "prod-1", "name": "Widget", "price": 19.99},
        )
        workflow.add_node(
            "ProductUpdateNode",
            "update_product",
            {"filter": {}, "fields": {"price": 29.99}},
        )
        workflow.add_connection("create_product", "id", "update_product", "filter.id")

        inspector = Inspector(db)
        inspector.workflow_obj = workflow.build()

        # Trace parameter source
        source = inspector.find_parameter_source("update_product", "filter.id")
        assert source == "create_product"

    def test_inspector_connection_validation_catches_errors(self):
        """Should catch connection validation errors."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "node_a", {"code": "result = {'output': 'test'}"}
        )
        workflow.add_node(
            "PythonCodeNode", "node_b", {"code": "result = {'result': input}"}
        )

        # Invalid connection (missing output)
        workflow.add_connection("node_a", "missing_output", "node_b", "input")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        is_valid, issues = inspector.validate_connections()
        assert is_valid is False
        assert len(issues) > 0

    def test_inspector_execution_order_matches_runtime(self):
        """Should produce execution order matching runtime behavior."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "a", {"code": "result = {'out': 1}"})
        workflow.add_node(
            "PythonCodeNode", "b", {"code": "result = {'out': in_val + 1}"}
        )
        workflow.add_node(
            "PythonCodeNode", "c", {"code": "result = {'final': in_val + 1}"}
        )

        workflow.add_connection("a", "out", "b", "in_val")
        workflow.add_connection("b", "out", "c", "in_val")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        order = inspector.execution_order()
        assert order == ["a", "b", "c"]

    def test_inspector_with_cyclic_workflow(self):
        """Should handle cyclic workflows gracefully."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "a",
            {"code": "result = {'out': in_val + 1 if 'in_val' in locals() else 0}"},
        )
        workflow.add_node(
            "PythonCodeNode", "b", {"code": "result = {'out': in_val + 1}"}
        )
        workflow.add_node(
            "PythonCodeNode", "c", {"code": "result = {'out': in_val + 1}"}
        )

        # Create cycle: a -> b -> c -> a
        workflow.add_connection("a", "out", "b", "in_val")
        workflow.add_connection("b", "out", "c", "in_val")
        workflow.add_connection("c", "out", "a", "in_val")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should detect cycle
        report = inspector.workflow_validation_report()
        assert "cycle" in str(report).lower() or not report["is_valid"]

    def test_inspector_with_complex_multipath_workflow(self):
        """Should handle workflows with multiple execution paths."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Create workflow with multiple paths
        workflow = WorkflowBuilder()

        # Entry point
        workflow.add_node("PythonCodeNode", "input", {"code": "result = {'data': 100}"})

        # Path 1: Processing chain
        workflow.add_node(
            "PythonCodeNode", "process_a", {"code": "result = {'value': data * 2}"}
        )
        workflow.add_node(
            "PythonCodeNode", "process_b", {"code": "result = {'value': data / 2}"}
        )

        # Path 2: Validation chain
        workflow.add_node(
            "PythonCodeNode", "validate_a", {"code": "result = {'valid': data > 0}"}
        )
        workflow.add_node(
            "PythonCodeNode", "validate_b", {"code": "result = {'valid': data < 1000}"}
        )

        # Merger
        workflow.add_node(
            "PythonCodeNode",
            "merger",
            {"code": "result = {'output': val1 and val2 and proc1 and proc2}"},
        )

        # Connect multiple paths
        workflow.add_connection("input", "data", "process_a", "data")
        workflow.add_connection("input", "data", "process_b", "data")
        workflow.add_connection("input", "data", "validate_a", "data")
        workflow.add_connection("input", "data", "validate_b", "data")
        workflow.add_connection("process_a", "value", "merger", "proc1")
        workflow.add_connection("process_b", "value", "merger", "proc2")
        workflow.add_connection("validate_a", "valid", "merger", "val1")
        workflow.add_connection("validate_b", "valid", "merger", "val2")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Verify workflow metrics
        metrics = inspector.workflow_metrics()
        assert metrics["node_count"] == 6
        assert metrics["connection_count"] == 8

        # Verify execution order is valid (respects dependencies)
        order = inspector.execution_order()
        assert len(order) == 6
        assert order.index("input") < order.index("process_a")
        assert order.index("input") < order.index("process_b")
        assert order.index("input") < order.index("validate_a")
        assert order.index("input") < order.index("validate_b")
        assert order.index("process_a") < order.index("merger")
        assert order.index("process_b") < order.index("merger")
        assert order.index("validate_a") < order.index("merger")
        assert order.index("validate_b") < order.index("merger")


# ============================================================================
# Test Group 6: Basic Inspector Methods
# ============================================================================


class TestBasicInspectorMethods:
    """Test the 4 basic Inspector methods."""

    @pytest.fixture
    def inspector_with_dataflow(self, memory_dataflow):
        """Create Inspector with real DataFlow instance."""
        from dataflow.platform.inspector import Inspector

        db = memory_dataflow

        @db.model
        class User:
            id: str
            name: str
            email: str

        @db.model
        class Product:
            id: str
            name: str
            price: float

        inspector = Inspector(db)
        return inspector, db

    def test_model_method(self, inspector_with_dataflow):
        """Should return model information."""
        from dataflow.platform.inspector import ModelInfo

        inspector, db = inspector_with_dataflow

        model_info = inspector.model("User")

        assert isinstance(model_info, ModelInfo)
        assert model_info.name == "User"
        assert "id" in model_info.schema
        assert "name" in model_info.schema
        assert "email" in model_info.schema

    def test_model_method_nonexistent(self, inspector_with_dataflow):
        """Should handle nonexistent model."""
        inspector, db = inspector_with_dataflow

        model_info = inspector.model("NonexistentModel")

        # Should return None for nonexistent model
        assert model_info is None

    def test_node_method(self, inspector_with_dataflow):
        """Should return node information."""
        from dataflow.platform.inspector import NodeInfo

        inspector, db = inspector_with_dataflow
        from kailash.workflow.builder import WorkflowBuilder

        # Create workflow with nodes
        workflow = WorkflowBuilder()
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"id": "user-1", "name": "Alice", "email": "alice@example.com"},
        )
        workflow.add_node("UserReadNode", "read_user", {"filter": {}})
        workflow.add_connection("create_user", "id", "read_user", "filter.id")

        inspector.workflow_obj = workflow.build()

        node_info = inspector.node("create_user")

        assert isinstance(node_info, NodeInfo)
        assert node_info.node_id == "create_user"
        assert node_info.node_type == "UserCreateNode"

    def test_instance_method(self, inspector_with_dataflow):
        """Should return DataFlow instance information."""
        from dataflow.platform.inspector import InstanceInfo

        inspector, db = inspector_with_dataflow

        instance_info = inspector.instance()

        assert isinstance(instance_info, InstanceInfo)
        assert instance_info.database_url is not None
        assert "User" in instance_info.models
        assert "Product" in instance_info.models

    def test_workflow_method(self, inspector_with_dataflow):
        """Should return workflow information."""
        from dataflow.platform.inspector import WorkflowInfo

        inspector, db = inspector_with_dataflow
        from kailash.workflow.builder import WorkflowBuilder

        # Create workflow
        workflow = WorkflowBuilder()
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {"id": "user-1", "name": "Alice", "email": "alice@example.com"},
        )
        workflow.add_node("UserReadNode", "read_user", {"filter": {}})
        workflow.add_connection("create_user", "id", "read_user", "filter.id")

        inspector.workflow_obj = workflow.build()

        workflow_info = inspector.workflow()

        assert isinstance(workflow_info, WorkflowInfo)
        assert len(workflow_info.nodes) == 2
        assert len(workflow_info.connections) == 1


# ============================================================================
# Test Group 7: Error Handling and Edge Cases
# ============================================================================


class TestInspectorErrorHandling:
    """Test Inspector error handling and edge cases."""

    def test_validate_connections_missing_workflow(self):
        """Should raise error when workflow_obj not set."""
        from dataflow.platform.inspector import Inspector

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())

        # Should raise error when workflow_obj not set
        with pytest.raises(ValueError, match="No workflow attached"):
            inspector.validate_connections()

    def test_trace_parameter_missing_workflow(self):
        """Should raise error when workflow_obj not set."""
        from dataflow.platform.inspector import Inspector

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        inspector = Inspector(MockDataFlow())

        # Should raise error when workflow_obj not set
        with pytest.raises(ValueError, match="No workflow attached"):
            inspector.trace_parameter("node_id", "param")

    def test_empty_workflow(self):
        """Should handle empty workflow gracefully."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Empty workflow should return empty results
        connections = inspector.connections()
        assert len(connections) == 0

        summary = inspector.workflow_summary()
        assert summary["node_count"] == 0
        assert summary["connection_count"] == 0

    def test_single_node_workflow(self):
        """Should handle single-node workflow."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "single", {"code": "result = {'output': 'test'}"}
        )

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Single node workflow
        summary = inspector.workflow_summary()
        assert summary["node_count"] == 1
        assert summary["connection_count"] == 0

        order = inspector.execution_order()
        assert len(order) == 1
        assert order[0] == "single"

    def test_disconnected_nodes(self):
        """Should handle workflow with disconnected nodes."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "node_a", {"code": "result = {'output': 'a'}"}
        )
        workflow.add_node(
            "PythonCodeNode", "node_b", {"code": "result = {'output': 'b'}"}
        )
        # No connections - disconnected nodes

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should handle disconnected nodes
        summary = inspector.workflow_summary()
        assert summary["node_count"] == 2
        assert summary["connection_count"] == 0

        # Both nodes should be entry and exit points
        assert len(summary["entry_points"]) == 2
        assert len(summary["exit_points"]) == 2

    def test_node_dependencies_nonexistent_node(self):
        """Should handle nonexistent node ID."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "node_a", {"code": "result = {'output': 'a'}"}
        )

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should return empty list for nonexistent node
        deps = inspector.node_dependencies("nonexistent_node")
        assert isinstance(deps, list)
        assert len(deps) == 0

    def test_complex_dot_notation_parameter_tracing(self):
        """Should trace parameters with complex dot notation."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "source",
            {"code": "result = {'nested': {'deep': {'value': 123}}}"},
        )
        workflow.add_node(
            "PythonCodeNode", "target", {"code": "result = {'output': data}"}
        )
        workflow.add_connection("source", "nested.deep.value", "target", "data")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should trace complex dot notation
        source = inspector.find_parameter_source("target", "data")
        assert source == "source"


# ============================================================================
# Test Group 8: Advanced Workflow Patterns
# ============================================================================


class TestAdvancedWorkflowPatterns:
    """Test Inspector with advanced workflow patterns."""

    def test_diamond_dependency_pattern(self):
        """Should handle diamond dependency pattern."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Diamond pattern: A -> B,C -> D
        workflow = WorkflowBuilder()
        workflow.add_node("PythonCodeNode", "a", {"code": "result = {'data': 100}"})
        workflow.add_node(
            "PythonCodeNode", "b", {"code": "result = {'result': data * 2}"}
        )
        workflow.add_node(
            "PythonCodeNode", "c", {"code": "result = {'result': data * 3}"}
        )
        workflow.add_node(
            "PythonCodeNode", "d", {"code": "result = {'final': b_res + c_res}"}
        )

        workflow.add_connection("a", "data", "b", "data")
        workflow.add_connection("a", "data", "c", "data")
        workflow.add_connection("b", "result", "d", "b_res")
        workflow.add_connection("c", "result", "d", "c_res")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Verify diamond pattern dependencies
        d_deps = inspector.node_dependencies("d")
        assert set(d_deps) == {"b", "c"}

        b_dependents = inspector.node_dependents("a")
        assert set(b_dependents) == {"b", "c"}

        # Verify execution order respects diamond
        order = inspector.execution_order()
        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    def test_fan_out_fan_in_pattern(self):
        """Should handle fan-out fan-in pattern."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Fan-out: 1 -> 3, Fan-in: 3 -> 1
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode", "source", {"code": "result = {'data': [1, 2, 3]}"}
        )
        workflow.add_node(
            "PythonCodeNode", "proc1", {"code": "result = {'r': data[0]}"}
        )
        workflow.add_node(
            "PythonCodeNode", "proc2", {"code": "result = {'r': data[1]}"}
        )
        workflow.add_node(
            "PythonCodeNode", "proc3", {"code": "result = {'r': data[2]}"}
        )
        workflow.add_node(
            "PythonCodeNode", "sink", {"code": "result = {'final': [r1, r2, r3]}"}
        )

        # Fan-out
        workflow.add_connection("source", "data", "proc1", "data")
        workflow.add_connection("source", "data", "proc2", "data")
        workflow.add_connection("source", "data", "proc3", "data")

        # Fan-in
        workflow.add_connection("proc1", "r", "sink", "r1")
        workflow.add_connection("proc2", "r", "sink", "r2")
        workflow.add_connection("proc3", "r", "sink", "r3")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Verify fan-out
        source_dependents = inspector.node_dependents("source")
        assert len(source_dependents) == 3
        assert set(source_dependents) == {"proc1", "proc2", "proc3"}

        # Verify fan-in
        sink_deps = inspector.node_dependencies("sink")
        assert len(sink_deps) == 3
        assert set(sink_deps) == {"proc1", "proc2", "proc3"}

        # Verify metrics
        metrics = inspector.workflow_metrics()
        assert metrics["node_count"] == 5
        assert metrics["connection_count"] == 6

    def test_long_chain_workflow(self):
        """Should handle long sequential chains."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Long chain: n1 -> n2 -> n3 -> ... -> n10
        workflow = WorkflowBuilder()
        chain_length = 10

        for i in range(chain_length):
            workflow.add_node(
                "PythonCodeNode",
                f"node_{i}",
                {
                    "code": f"result = {{'value': input_val + 1 if 'input_val' in locals() else {i}}}"
                },
            )

        for i in range(chain_length - 1):
            workflow.add_connection(f"node_{i}", "value", f"node_{i+1}", "input_val")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Verify chain length
        metrics = inspector.workflow_metrics()
        assert metrics["node_count"] == chain_length
        assert metrics["connection_count"] == chain_length - 1

        # Verify chain depth
        assert metrics["depth"] >= chain_length - 1

        # Verify execution order is sequential
        order = inspector.execution_order()
        for i in range(chain_length):
            assert order[i] == f"node_{i}"


# ============================================================================
# Test Group 9: Performance and Scalability
# ============================================================================


class TestInspectorPerformance:
    """Test Inspector performance with large workflows."""

    def test_large_workflow_metrics(self):
        """Should handle large workflows efficiently."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Create large workflow (50 nodes)
        workflow = WorkflowBuilder()
        num_nodes = 50

        for i in range(num_nodes):
            workflow.add_node(
                "PythonCodeNode", f"node_{i}", {"code": f"result = {{'value': {i}}}"}
            )

        # Create connections (each node connects to next)
        for i in range(num_nodes - 1):
            workflow.add_connection(f"node_{i}", "value", f"node_{i+1}", "input")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should calculate metrics efficiently
        metrics = inspector.workflow_metrics()
        assert metrics["node_count"] == num_nodes
        assert metrics["connection_count"] == num_nodes - 1

    def test_highly_connected_workflow(self):
        """Should handle workflows with many connections."""
        from dataflow.platform.inspector import Inspector

        from kailash.workflow.builder import WorkflowBuilder

        class MockDataFlow:
            def __init__(self):
                self._models = {}
                self.database_url = "sqlite:///:memory:"

        # Create highly connected workflow
        workflow = WorkflowBuilder()

        # Hub node
        workflow.add_node("PythonCodeNode", "hub", {"code": "result = {'data': 100}"})

        # 10 spoke nodes all connected to hub
        num_spokes = 10
        for i in range(num_spokes):
            workflow.add_node(
                "PythonCodeNode",
                f"spoke_{i}",
                {"code": f"result = {{'value': data * {i}}}"},
            )
            workflow.add_connection("hub", "data", f"spoke_{i}", "data")

        inspector = Inspector(MockDataFlow())
        inspector.workflow_obj = workflow.build()

        # Should handle many connections efficiently
        hub_dependents = inspector.node_dependents("hub")
        assert len(hub_dependents) == num_spokes

        connections = inspector.connections()
        assert len(connections) == num_spokes


# ============================================================================
# Run Tests to Verify They Fail (RED phase)
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
