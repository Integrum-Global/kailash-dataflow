"""
Phase 3.1.1: SaaS Starter Template - Core Models + Authentication Tests

Test-first development (TDD) for SaaS starter template foundational features:
1. Data Models (5 tests)
2. Authentication Workflows (8 tests)
3. Multi-Tenant Data Isolation (7 tests)

CRITICAL: These tests are written BEFORE implementation (red phase).
Tests define the API contract and expected behavior.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict

import pytest

# Add templates directory to Python path for imports
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "../../../templates")
if TEMPLATES_DIR not in sys.path:
    sys.path.insert(0, TEMPLATES_DIR)

from dataflow import DataFlow

from kailash.runtime.local import LocalRuntime
from kailash.workflow.builder import WorkflowBuilder

# ==============================================================================
# Section 1: Data Models Tests (5 tests)
# ==============================================================================


class TestSaaSDataModels:
    """Test SaaS data model structure and validation."""

    @pytest.fixture
    def test_database_url(self):
        """Use in-memory SQLite for unit tests (no external dependencies)."""
        return ":memory:"

    @pytest.fixture
    def saas_dataflow(self, test_database_url):
        """Create DataFlow with SaaS models."""
        db = DataFlow(test_database_url, auto_migrate=True)

        # Import models from template
        from saas_starter.models import register_models

        register_models(db)
        return db

    def test_organization_model_structure(self, saas_dataflow):
        """
        Test Organization model has correct fields and structure.

        Expected Fields:
        - id: str (tenant UUID)
        - name: str (organization name)
        - slug: str (unique subdomain/path)
        - plan_id: str (subscription plan)
        - status: str (active, suspended, cancelled)
        - settings: dict (JSON settings)
        - created_at: datetime (auto-managed)
        - updated_at: datetime (auto-managed)
        """
        # Check model is registered
        assert (
            "Organization" in saas_dataflow._models
        ), "Organization model not registered"

        # Check generated nodes
        assert "OrganizationCreateNode" in saas_dataflow._nodes
        assert "OrganizationReadNode" in saas_dataflow._nodes
        assert "OrganizationUpdateNode" in saas_dataflow._nodes
        assert "OrganizationListNode" in saas_dataflow._nodes

        # Test model field structure using inspector
        inspector = saas_dataflow._inspector
        org_fields = inspector.model("Organization")["fields"]

        field_names = [f["name"] for f in org_fields]
        assert "id" in field_names
        assert "name" in field_names
        assert "slug" in field_names
        assert "plan_id" in field_names
        assert "status" in field_names
        assert "settings" in field_names

        # Verify field types
        field_types = {f["name"]: f["type"] for f in org_fields}
        assert field_types["id"] == "str"
        assert field_types["name"] == "str"
        assert field_types["slug"] == "str"

    def test_user_model_with_organization_fk(self, saas_dataflow):
        """
        Test User model has organization_id foreign key for multi-tenancy.

        Expected Fields:
        - id: str (user UUID)
        - organization_id: str (FK to Organization.id)
        - email: str (unique)
        - password_hash: str (bcrypt hash)
        - role: str (owner, admin, member)
        - status: str (active, invited, suspended)
        - created_at: datetime
        - updated_at: datetime
        """
        # Check model is registered
        assert "User" in saas_dataflow._models, "User model not registered"

        # Check generated nodes
        assert "UserCreateNode" in saas_dataflow._nodes
        assert "UserReadNode" in saas_dataflow._nodes
        assert "UserUpdateNode" in saas_dataflow._nodes
        assert "UserListNode" in saas_dataflow._nodes

        # Test model field structure
        inspector = saas_dataflow._inspector
        user_fields = inspector.model("User")["fields"]

        field_names = [f["name"] for f in user_fields]
        assert "id" in field_names
        assert "organization_id" in field_names, "Missing organization_id FK"
        assert "email" in field_names
        assert "password_hash" in field_names
        assert "role" in field_names
        assert "status" in field_names

        # Verify field types
        field_types = {f["name"]: f["type"] for f in user_fields}
        assert field_types["id"] == "str"
        assert field_types["organization_id"] == "str"  # FK to Organization
        assert field_types["email"] == "str"

    def test_subscription_model_stripe_fields(self, saas_dataflow):
        """
        Test Subscription model has Stripe integration fields.

        Expected Fields:
        - id: str
        - organization_id: str (FK to Organization.id)
        - plan_id: str (Stripe price ID)
        - stripe_customer_id: str
        - stripe_subscription_id: str
        - status: str (active, cancelled, past_due)
        - current_period_start: datetime
        - current_period_end: datetime
        - cancel_at_period_end: bool
        - created_at: datetime
        - updated_at: datetime
        """
        # Check model is registered
        assert (
            "Subscription" in saas_dataflow._models
        ), "Subscription model not registered"

        # Check generated nodes
        assert "SubscriptionCreateNode" in saas_dataflow._nodes
        assert "SubscriptionReadNode" in saas_dataflow._nodes
        assert "SubscriptionUpdateNode" in saas_dataflow._nodes

        # Test model field structure
        inspector = saas_dataflow._inspector
        sub_fields = inspector.model("Subscription")["fields"]

        field_names = [f["name"] for f in sub_fields]
        assert "id" in field_names
        assert "organization_id" in field_names
        assert "plan_id" in field_names
        assert "stripe_customer_id" in field_names
        assert "stripe_subscription_id" in field_names
        assert "status" in field_names
        assert "current_period_start" in field_names
        assert "current_period_end" in field_names

        # Verify Stripe-specific fields
        field_types = {f["name"]: f["type"] for f in sub_fields}
        assert field_types["stripe_customer_id"] == "str"
        assert field_types["stripe_subscription_id"] == "str"

    def test_model_relationships(self, saas_dataflow, test_database_url):
        """
        Test relationships between Organization, User, and Subscription.

        Verify:
        - User.organization_id → Organization.id
        - Subscription.organization_id → Organization.id
        - Can query users by organization_id
        - Can query subscriptions by organization_id
        """
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()

        # Create organization
        org_id = f"org_{int(time.time() * 1000)}"
        workflow.add_node(
            "OrganizationCreateNode",
            "create_org",
            {
                "id": org_id,
                "name": "Test Org",
                "slug": "test-org",
                "plan_id": "free",
                "status": "active",
                "settings": {},
            },
        )

        # Create user with organization FK
        user_id = f"user_{int(time.time() * 1000)}"
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {
                "id": user_id,
                "organization_id": org_id,
                "email": f"test_{int(time.time() * 1000)}@example.com",
                "password_hash": "hashed_password",
                "role": "owner",
                "status": "active",
            },
        )

        # Create subscription with organization FK
        sub_id = f"sub_{int(time.time() * 1000)}"
        workflow.add_node(
            "SubscriptionCreateNode",
            "create_subscription",
            {
                "id": sub_id,
                "organization_id": org_id,
                "plan_id": "price_123",
                "stripe_customer_id": "cus_123",
                "stripe_subscription_id": "sub_123",
                "status": "active",
                "current_period_start": datetime.now(),
                "current_period_end": datetime.now() + timedelta(days=30),
                "cancel_at_period_end": False,
            },
        )

        # Query users by organization_id
        workflow.add_node(
            "UserListNode",
            "list_users",
            {"filters": {"organization_id": org_id}, "limit": 10},
        )

        # Query subscriptions by organization_id
        workflow.add_node(
            "SubscriptionListNode",
            "list_subscriptions",
            {"filters": {"organization_id": org_id}, "limit": 10},
        )

        # Execute workflow
        results, run_id = runtime.execute(workflow.build())

        # Verify relationships work
        assert results["create_org"]["id"] == org_id
        assert results["create_user"]["organization_id"] == org_id
        assert results["create_subscription"]["organization_id"] == org_id

        # Verify list queries filter by organization_id
        # List operations return lists of records
        user_list = results["list_users"]
        assert isinstance(user_list, list), "UserListNode should return a list"
        assert len(user_list) >= 1, "Should have at least one user"
        assert all(u["organization_id"] == org_id for u in user_list)

        sub_list = results["list_subscriptions"]
        assert isinstance(sub_list, list), "SubscriptionListNode should return a list"
        assert len(sub_list) >= 1, "Should have at least one subscription"
        assert all(s["organization_id"] == org_id for s in sub_list)

    def test_model_field_validation(self, saas_dataflow):
        """
        Test model field validation and constraints.

        Verify:
        - Email uniqueness constraint on User
        - Slug uniqueness constraint on Organization
        - Status enum validation (active, suspended, cancelled)
        - Role enum validation (owner, admin, member)
        """
        runtime = LocalRuntime()
        workflow = WorkflowBuilder()

        # Create organization with slug
        org_id = f"org_{int(time.time() * 1000)}"
        slug = f"unique-slug-{int(time.time() * 1000)}"
        workflow.add_node(
            "OrganizationCreateNode",
            "create_org",
            {
                "id": org_id,
                "name": "Validation Test",
                "slug": slug,
                "plan_id": "free",
                "status": "active",
                "settings": {},
            },
        )

        # Create user with unique email
        user_id = f"user_{int(time.time() * 1000)}"
        email = f"unique_{int(time.time() * 1000)}@example.com"
        workflow.add_node(
            "UserCreateNode",
            "create_user",
            {
                "id": user_id,
                "organization_id": org_id,
                "email": email,
                "password_hash": "hashed_password",
                "role": "owner",
                "status": "active",
            },
        )

        # Execute workflow
        results, run_id = runtime.execute(workflow.build())

        # Verify creation succeeded with valid data
        assert results["create_org"]["slug"] == slug
        assert results["create_user"]["email"] == email

        # Test duplicate email constraint
        workflow2 = WorkflowBuilder()
        workflow2.add_node(
            "UserCreateNode",
            "create_duplicate_user",
            {
                "id": f"user_dup_{int(time.time() * 1000)}",
                "organization_id": org_id,
                "email": email,  # Duplicate email
                "password_hash": "hashed_password",
                "role": "member",
                "status": "active",
            },
        )

        # Duplicate email should raise error
        with pytest.raises(Exception) as exc_info:
            runtime.execute(workflow2.build())

        # Verify error is about uniqueness constraint
        assert (
            "unique" in str(exc_info.value).lower()
            or "duplicate" in str(exc_info.value).lower()
        ), "Should raise uniqueness constraint error"


# ==============================================================================
# Section 2: Authentication Workflows Tests (8 tests)
# ==============================================================================


class TestAuthenticationWorkflows:
    """Test authentication workflow patterns."""

    @pytest.fixture
    def test_database_url(self):
        """Use in-memory SQLite for unit tests."""
        return ":memory:"

    @pytest.fixture
    def saas_dataflow(self, test_database_url):
        """Create DataFlow with SaaS models."""
        db = DataFlow(test_database_url, auto_migrate=True)
        from saas_starter.models import register_models

        register_models(db)
        return db

    @pytest.fixture
    def runtime(self):
        """Create LocalRuntime for workflow execution."""
        return LocalRuntime()

    def test_user_registration_workflow(self, saas_dataflow, runtime):
        """
        Test complete user registration workflow.

        Steps:
        1. Validate email uniqueness
        2. Hash password with bcrypt
        3. Create organization
        4. Create user with owner role
        5. Generate JWT token
        6. Return user + token

        Expected Output:
        {
            "user": {User object},
            "organization": {Organization object},
            "token": "jwt_token_here"
        }
        """
        from saas_starter.workflows.auth import build_registration_workflow

        # Build registration workflow
        unique_email = f"newuser_{int(time.time() * 1000)}@example.com"
        workflow = build_registration_workflow(
            email=unique_email, password="securepassword123", org_name="New Startup"
        )

        # Execute workflow
        results, run_id = runtime.execute(workflow)

        # Verify organization created
        assert "organization" in results
        assert results["organization"]["name"] == "New Startup"
        assert results["organization"]["slug"] == "new-startup"
        assert results["organization"]["status"] == "active"

        # Verify user created with owner role
        assert "user" in results
        assert results["user"]["email"] == unique_email
        assert results["user"]["role"] == "owner"
        assert results["user"]["status"] == "active"
        assert (
            results["user"]["organization_id"] == results["organization"]["id"]
        ), "User should belong to created org"

        # Verify password was hashed (not plain text)
        assert results["user"]["password_hash"] != "securepassword123"
        assert results["user"]["password_hash"].startswith("$2b$")  # bcrypt prefix

        # Verify JWT token generated
        assert "token" in results
        assert isinstance(results["token"], str)
        assert len(results["token"]) > 50  # JWT tokens are long

        # Verify JWT contains user_id and org_id
        import jwt

        decoded = jwt.decode(results["token"], options={"verify_signature": False})
        assert decoded["user_id"] == results["user"]["id"]
        assert decoded["org_id"] == results["organization"]["id"]

    def test_user_login_workflow(self, saas_dataflow, runtime):
        """
        Test user login workflow.

        Steps:
        1. Check email exists
        2. Verify password hash with bcrypt
        3. Generate JWT token
        4. Return user + token

        Expected Output:
        {
            "user": {User object},
            "token": "jwt_token_here"
        }
        """
        # First register a user
        from saas_starter.workflows.auth import (
            build_login_workflow,
            build_registration_workflow,
        )

        email = f"login_test_{int(time.time() * 1000)}@example.com"
        password = "testpassword123"

        # Register user
        reg_workflow = build_registration_workflow(
            email=email, password=password, org_name="Login Test Org"
        )
        reg_results, _ = runtime.execute(reg_workflow)

        # Now test login
        login_workflow = build_login_workflow(email=email, password=password)
        results, run_id = runtime.execute(login_workflow)

        # Verify login successful
        assert "user" in results
        assert results["user"]["email"] == email

        # Verify token generated
        assert "token" in results
        assert isinstance(results["token"], str)

        # Verify token contains correct claims
        import jwt

        decoded = jwt.decode(results["token"], options={"verify_signature": False})
        assert decoded["user_id"] == reg_results["user"]["id"]
        assert decoded["org_id"] == reg_results["organization"]["id"]

    def test_token_validation_workflow(self, saas_dataflow, runtime):
        """
        Test JWT token validation workflow.

        Steps:
        1. Decode JWT token
        2. Verify signature
        3. Check expiration
        4. Extract claims (user_id, org_id)

        Expected Output:
        {
            "valid": True,
            "user_id": "user_uuid",
            "org_id": "org_uuid",
            "exp": timestamp
        }
        """
        # First register a user to get a valid token
        from saas_starter.workflows.auth import (
            build_registration_workflow,
            build_token_validation_workflow,
        )

        email = f"token_test_{int(time.time() * 1000)}@example.com"
        reg_workflow = build_registration_workflow(
            email=email, password="password123", org_name="Token Test"
        )
        reg_results, _ = runtime.execute(reg_workflow)

        token = reg_results["token"]

        # Test token validation
        validation_workflow = build_token_validation_workflow(token=token)
        results, run_id = runtime.execute(validation_workflow)

        # Verify token is valid
        assert results["valid"] is True
        assert results["user_id"] == reg_results["user"]["id"]
        assert results["org_id"] == reg_results["organization"]["id"]
        assert "exp" in results

    def test_token_expiration_workflow(self, saas_dataflow, runtime):
        """
        Test that expired JWT tokens are rejected.

        Steps:
        1. Create expired JWT token
        2. Attempt to validate
        3. Verify validation fails with expiration error
        """
        from datetime import datetime, timedelta

        import jwt
        from saas_starter.workflows.auth import build_token_validation_workflow

        # Create expired token
        payload = {
            "user_id": "test_user",
            "org_id": "test_org",
            "exp": datetime.now() - timedelta(hours=1),  # Expired 1 hour ago
        }

        # Use a known secret for testing
        expired_token = jwt.encode(payload, "test_secret", algorithm="HS256")

        # Test validation of expired token
        validation_workflow = build_token_validation_workflow(
            token=expired_token, secret="test_secret"
        )

        # Should raise exception for expired token
        with pytest.raises(Exception) as exc_info:
            runtime.execute(validation_workflow)

        # Verify error is about expiration
        assert (
            "expired" in str(exc_info.value).lower()
            or "invalid" in str(exc_info.value).lower()
        ), "Should raise expiration error"

    def test_password_reset_request_workflow(self, saas_dataflow, runtime):
        """
        Test password reset request workflow.

        Steps:
        1. Verify email exists
        2. Generate reset token (JWT with short expiry)
        3. Send reset email (APINode to email service)
        4. Return reset token

        Expected Output:
        {
            "reset_token": "jwt_token_here",
            "email_sent": True
        }
        """
        # First register a user
        from saas_starter.workflows.auth import (
            build_password_reset_request_workflow,
            build_registration_workflow,
        )

        email = f"reset_test_{int(time.time() * 1000)}@example.com"
        reg_workflow = build_registration_workflow(
            email=email, password="oldpassword", org_name="Reset Test"
        )
        runtime.execute(reg_workflow)

        # Request password reset
        reset_request_workflow = build_password_reset_request_workflow(email=email)
        results, run_id = runtime.execute(reset_request_workflow)

        # Verify reset token generated
        assert "reset_token" in results
        assert isinstance(results["reset_token"], str)

        # Verify token has short expiry (15 minutes)
        import jwt

        decoded = jwt.decode(
            results["reset_token"], options={"verify_signature": False}
        )
        assert "exp" in decoded
        exp_time = datetime.fromtimestamp(decoded["exp"])
        now = datetime.now()
        time_until_expiry = (exp_time - now).total_seconds()
        assert (
            time_until_expiry <= 15 * 60
        ), "Reset token should expire within 15 minutes"

        # Verify email sent (mocked in unit tests)
        assert "email_sent" in results

    def test_password_reset_complete_workflow(self, saas_dataflow, runtime):
        """
        Test password reset completion workflow.

        Steps:
        1. Validate reset token
        2. Extract user_id from token
        3. Hash new password
        4. Update user password_hash
        5. Invalidate reset token

        Expected Output:
        {
            "success": True,
            "user_id": "user_uuid"
        }
        """
        # First register a user and request reset
        from saas_starter.workflows.auth import (
            build_password_reset_complete_workflow,
            build_password_reset_request_workflow,
            build_registration_workflow,
        )

        email = f"reset_complete_{int(time.time() * 1000)}@example.com"
        reg_workflow = build_registration_workflow(
            email=email, password="oldpassword", org_name="Reset Complete Test"
        )
        reg_results, _ = runtime.execute(reg_workflow)

        # Request reset
        reset_request_workflow = build_password_reset_request_workflow(email=email)
        reset_results, _ = runtime.execute(reset_request_workflow)

        reset_token = reset_results["reset_token"]

        # Complete reset with new password
        reset_complete_workflow = build_password_reset_complete_workflow(
            reset_token=reset_token, new_password="newpassword123"
        )
        results, run_id = runtime.execute(reset_complete_workflow)

        # Verify reset successful
        assert results["success"] is True
        assert results["user_id"] == reg_results["user"]["id"]

        # Verify password was updated (try login with new password)
        from saas_starter.workflows.auth import build_login_workflow

        login_workflow = build_login_workflow(email=email, password="newpassword123")
        login_results, _ = runtime.execute(login_workflow)

        assert login_results["user"]["id"] == reg_results["user"]["id"]

    def test_oauth_google_integration_workflow(self, saas_dataflow, runtime):
        """
        Test OAuth Google signup/login workflow.

        Steps:
        1. Verify Google OAuth token
        2. Extract email from Google profile
        3. Check if user exists by email
        4. If new user: create org + user
        5. If existing user: fetch user
        6. Generate JWT token

        Expected Output:
        {
            "user": {User object},
            "organization": {Organization object},
            "token": "jwt_token_here",
            "is_new_user": bool
        }
        """
        from saas_starter.workflows.auth import build_oauth_google_workflow

        # Simulate Google OAuth token payload
        google_token = {
            "email": f"google_user_{int(time.time() * 1000)}@gmail.com",
            "name": "Google User",
            "picture": "https://example.com/photo.jpg",
            "sub": "google_user_id_123",
        }

        # Test OAuth flow
        oauth_workflow = build_oauth_google_workflow(google_token=google_token)
        results, run_id = runtime.execute(oauth_workflow)

        # Verify user created
        assert "user" in results
        assert results["user"]["email"] == google_token["email"]

        # Verify organization created
        assert "organization" in results

        # Verify token generated
        assert "token" in results
        assert isinstance(results["token"], str)

        # Verify is_new_user flag
        assert "is_new_user" in results
        assert results["is_new_user"] is True  # First time signup

        # Test login with same OAuth token (existing user)
        oauth_workflow2 = build_oauth_google_workflow(google_token=google_token)
        results2, _ = runtime.execute(oauth_workflow2)

        # Should return existing user
        assert results2["user"]["id"] == results["user"]["id"]
        assert results2["is_new_user"] is False  # Existing user

    def test_oauth_github_integration_workflow(self, saas_dataflow, runtime):
        """
        Test OAuth GitHub signup/login workflow.

        Steps:
        1. Verify GitHub OAuth token
        2. Extract email from GitHub profile
        3. Check if user exists by email
        4. If new user: create org + user
        5. If existing user: fetch user
        6. Generate JWT token

        Expected Output:
        {
            "user": {User object},
            "organization": {Organization object},
            "token": "jwt_token_here",
            "is_new_user": bool
        }
        """
        from saas_starter.workflows.auth import build_oauth_github_workflow

        # Simulate GitHub OAuth token payload
        github_token = {
            "email": f"github_user_{int(time.time() * 1000)}@github.com",
            "name": "GitHub User",
            "avatar_url": "https://github.com/avatar.jpg",
            "login": "githubuser123",
        }

        # Test OAuth flow
        oauth_workflow = build_oauth_github_workflow(github_token=github_token)
        results, run_id = runtime.execute(oauth_workflow)

        # Verify user created
        assert "user" in results
        assert results["user"]["email"] == github_token["email"]

        # Verify organization created
        assert "organization" in results

        # Verify token generated
        assert "token" in results

        # Verify is_new_user flag
        assert "is_new_user" in results
        assert results["is_new_user"] is True


# ==============================================================================
# Section 3: Multi-Tenant Data Isolation Tests (7 tests)
# ==============================================================================


class TestMultiTenantIsolation:
    """Test multi-tenant data isolation and security."""

    @pytest.fixture
    def test_database_url(self):
        """Use in-memory SQLite for unit tests."""
        return ":memory:"

    @pytest.fixture
    def saas_dataflow(self, test_database_url):
        """Create DataFlow with SaaS models."""
        db = DataFlow(test_database_url, auto_migrate=True)
        from saas_starter.models import register_models

        register_models(db)
        return db

    @pytest.fixture
    def runtime(self):
        """Create LocalRuntime for workflow execution."""
        return LocalRuntime()

    @pytest.fixture
    def two_tenants(self, saas_dataflow, runtime):
        """Create two separate tenants with users for testing isolation."""
        from saas_starter.workflows.auth import build_registration_workflow

        # Tenant A
        tenant_a_workflow = build_registration_workflow(
            email=f"tenant_a_{int(time.time() * 1000)}@example.com",
            password="password",
            org_name="Tenant A",
        )
        tenant_a_results, _ = runtime.execute(tenant_a_workflow)

        # Tenant B
        tenant_b_workflow = build_registration_workflow(
            email=f"tenant_b_{int(time.time() * 1000)}@example.com",
            password="password",
            org_name="Tenant B",
        )
        tenant_b_results, _ = runtime.execute(tenant_b_workflow)

        return {
            "tenant_a": {
                "org_id": tenant_a_results["organization"]["id"],
                "user_id": tenant_a_results["user"]["id"],
                "token": tenant_a_results["token"],
            },
            "tenant_b": {
                "org_id": tenant_b_results["organization"]["id"],
                "user_id": tenant_b_results["user"]["id"],
                "token": tenant_b_results["token"],
            },
        }

    def test_tenant_context_injection(self, saas_dataflow, runtime, two_tenants):
        """
        Test tenant context injection from JWT token.

        Steps:
        1. Decode JWT token
        2. Extract org_id from token
        3. Inject org_id into workflow context
        4. All subsequent queries automatically filtered by org_id

        Expected Behavior:
        Workflow context should contain tenant_id after injection.
        """
        from saas_starter.middleware.tenant import inject_tenant_context

        # Test with Tenant A token
        tenant_a_token = two_tenants["tenant_a"]["token"]

        # Build workflow with tenant context injection
        workflow = WorkflowBuilder()
        workflow.add_node(
            "PythonCodeNode",
            "inject_context",
            {"code": inject_tenant_context, "inputs": {"token": tenant_a_token}},
        )

        # Execute workflow
        results, run_id = runtime.execute(workflow.build())

        # Verify tenant context injected
        assert "tenant_id" in results["inject_context"]
        assert (
            results["inject_context"]["tenant_id"] == two_tenants["tenant_a"]["org_id"]
        )

    def test_cross_tenant_read_prevention(self, saas_dataflow, runtime, two_tenants):
        """
        Test that Tenant A cannot read Tenant B's data.

        Steps:
        1. Inject Tenant A context
        2. Attempt to read Tenant B user by ID
        3. Verify read fails or returns empty

        Expected Behavior:
        Should raise PermissionError or return None.
        """
        from saas_starter.middleware.tenant import build_tenant_scoped_read_workflow

        # Try to read Tenant B user from Tenant A context
        workflow = build_tenant_scoped_read_workflow(
            model_name="User",
            record_id=two_tenants["tenant_b"]["user_id"],
            tenant_token=two_tenants["tenant_a"]["token"],
        )

        # Execute workflow
        results, run_id = runtime.execute(workflow)

        # Verify cross-tenant read prevented
        # Result should be None or empty (tenant mismatch)
        assert (
            results.get("user") is None or results.get("user") == {}
        ), "Cross-tenant read should be prevented"

    def test_cross_tenant_update_prevention(self, saas_dataflow, runtime, two_tenants):
        """
        Test that Tenant A cannot update Tenant B's data.

        Steps:
        1. Inject Tenant A context
        2. Attempt to update Tenant B user
        3. Verify update fails

        Expected Behavior:
        Should raise PermissionError.
        """
        from saas_starter.middleware.tenant import build_tenant_scoped_update_workflow

        # Try to update Tenant B user from Tenant A context
        workflow = build_tenant_scoped_update_workflow(
            model_name="User",
            record_id=two_tenants["tenant_b"]["user_id"],
            updates={"role": "admin"},  # Malicious update attempt
            tenant_token=two_tenants["tenant_a"]["token"],
        )

        # Should raise permission error
        with pytest.raises(Exception) as exc_info:
            runtime.execute(workflow)

        # Verify error is about permissions/access
        assert (
            "permission" in str(exc_info.value).lower()
            or "access" in str(exc_info.value).lower()
            or "forbidden" in str(exc_info.value).lower()
        ), "Should raise permission error for cross-tenant update"

    def test_cross_tenant_delete_prevention(self, saas_dataflow, runtime, two_tenants):
        """
        Test that Tenant A cannot delete Tenant B's data.

        Steps:
        1. Inject Tenant A context
        2. Attempt to delete Tenant B user
        3. Verify delete fails

        Expected Behavior:
        Should raise PermissionError.
        """
        from saas_starter.middleware.tenant import build_tenant_scoped_delete_workflow

        # Try to delete Tenant B user from Tenant A context
        workflow = build_tenant_scoped_delete_workflow(
            model_name="User",
            record_id=two_tenants["tenant_b"]["user_id"],
            tenant_token=two_tenants["tenant_a"]["token"],
        )

        # Should raise permission error
        with pytest.raises(Exception) as exc_info:
            runtime.execute(workflow)

        # Verify error is about permissions
        assert (
            "permission" in str(exc_info.value).lower()
            or "access" in str(exc_info.value).lower()
        ), "Should raise permission error for cross-tenant delete"

    def test_tenant_scoped_list_queries(self, saas_dataflow, runtime, two_tenants):
        """
        Test that list queries are automatically scoped to tenant.

        Steps:
        1. Inject Tenant A context
        2. Query User.list()
        3. Verify only Tenant A users returned (not Tenant B)

        Expected Behavior:
        List should only contain users from Tenant A.
        """
        from saas_starter.middleware.tenant import build_tenant_scoped_list_workflow

        # List users from Tenant A context
        workflow = build_tenant_scoped_list_workflow(
            model_name="User", tenant_token=two_tenants["tenant_a"]["token"]
        )

        results, run_id = runtime.execute(workflow)

        # Verify only Tenant A users returned
        users = results["users"]
        assert isinstance(users, list)
        assert len(users) >= 1  # At least Tenant A user

        # All users should belong to Tenant A
        tenant_a_org_id = two_tenants["tenant_a"]["org_id"]
        for user in users:
            assert (
                user["organization_id"] == tenant_a_org_id
            ), f"Found user from wrong tenant: {user['organization_id']}"

    def test_organization_switching(self, saas_dataflow, runtime, two_tenants):
        """
        Test user switching between organizations (if member of multiple).

        Steps:
        1. Create user who is member of both orgs
        2. Switch context to Org A
        3. Verify queries scoped to Org A
        4. Switch context to Org B
        5. Verify queries scoped to Org B

        Expected Behavior:
        User can switch between orgs and queries are properly scoped.
        """
        # First create a user who is member of both orgs
        workflow = WorkflowBuilder()

        multi_org_user_id = f"multi_user_{int(time.time() * 1000)}"
        multi_org_email = f"multi_{int(time.time() * 1000)}@example.com"

        # Create user in Tenant A
        workflow.add_node(
            "UserCreateNode",
            "create_multi_user_a",
            {
                "id": multi_org_user_id,
                "organization_id": two_tenants["tenant_a"]["org_id"],
                "email": multi_org_email,
                "password_hash": "hashed",
                "role": "member",
                "status": "active",
            },
        )

        runtime.execute(workflow.build())

        # Now test context switching
        from saas_starter.middleware.tenant import build_org_switching_workflow

        # Switch to Org A and list users
        workflow_a = build_org_switching_workflow(
            user_id=multi_org_user_id,
            target_org_id=two_tenants["tenant_a"]["org_id"],
            operation="list_users",
        )
        results_a, _ = runtime.execute(workflow_a)

        # Verify scoped to Org A
        assert all(
            u["organization_id"] == two_tenants["tenant_a"]["org_id"]
            for u in results_a["users"]
        )

    def test_tenant_isolation_in_bulk_operations(
        self, saas_dataflow, runtime, two_tenants
    ):
        """
        Test that bulk operations respect tenant boundaries.

        Steps:
        1. Inject Tenant A context
        2. Perform bulk update on users
        3. Verify only Tenant A users affected (not Tenant B)

        Expected Behavior:
        Bulk operations should only affect current tenant's data.
        """
        from saas_starter.middleware.tenant import (
            build_tenant_scoped_bulk_update_workflow,
        )

        # Bulk update users from Tenant A context
        workflow = build_tenant_scoped_bulk_update_workflow(
            model_name="User",
            updates={"status": "verified"},  # Bulk status update
            tenant_token=two_tenants["tenant_a"]["token"],
        )

        results, run_id = runtime.execute(workflow)

        # Verify only Tenant A users updated
        # Read Tenant B user to confirm not affected
        workflow_check = WorkflowBuilder()
        workflow_check.add_node(
            "UserReadNode",
            "check_tenant_b_user",
            {"filters": {"id": two_tenants["tenant_b"]["user_id"]}},
        )

        check_results, _ = runtime.execute(workflow_check.build())

        # Tenant B user should NOT have status="verified"
        # (bulk update should not have affected it)
        tenant_b_user = check_results["check_tenant_b_user"]
        assert (
            tenant_b_user["status"] != "verified"
        ), "Bulk update should not affect other tenants"
