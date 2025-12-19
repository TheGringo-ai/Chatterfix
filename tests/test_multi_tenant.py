"""
Tests for Multi-Tenant Organization Isolation

Verifies that:
1. Users can only access data from their own organization
2. Cross-organization access attempts are rejected with 403
3. Unauthenticated requests are rejected with 401
4. Organization_id is always required for data operations
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

from app.core.multi_tenant import (
    get_organization_id,
    require_organization_id,
    validate_organization_access,
    get_org_id_from_request,
    is_demo_organization,
    is_system_organization,
    DEMO_ORGANIZATION_ID,
    SYSTEM_ORGANIZATION_ID,
)
from app.models.user import User


# ==========================================
# TEST FIXTURES
# ==========================================


@pytest.fixture
def user_org_a():
    """User belonging to organization A"""
    return User(
        uid="user_001",
        email="user1@example.com",
        role="technician",
        organization_id="org_a",
        organization_name="Organization A",
    )


@pytest.fixture
def user_org_b():
    """User belonging to organization B"""
    return User(
        uid="user_002",
        email="user2@example.com",
        role="technician",
        organization_id="org_b",
        organization_name="Organization B",
    )


@pytest.fixture
def user_no_org():
    """User without organization assignment"""
    return User(
        uid="user_003",
        email="user3@example.com",
        role="technician",
        organization_id=None,
        organization_name=None,
    )


@pytest.fixture
def mock_request():
    """Mock FastAPI request object"""
    request = MagicMock()
    request.state = MagicMock()
    request.query_params = {}
    request.headers = {}
    return request


# ==========================================
# get_organization_id() TESTS
# ==========================================


class TestGetOrganizationId:
    """Tests for the get_organization_id function"""

    def test_returns_user_org_when_authenticated(self, user_org_a):
        """Authenticated user should get their organization_id"""
        result = get_organization_id(user_org_a, None)
        assert result == "org_a"

    def test_returns_user_org_ignores_explicit_when_matching(self, user_org_a):
        """When explicit org matches user's org, return the org"""
        result = get_organization_id(user_org_a, "org_a")
        assert result == "org_a"

    def test_returns_none_when_cross_org_attempt(self, user_org_a):
        """Cross-org access attempt should return None (not user's org)"""
        result = get_organization_id(user_org_a, "org_b")
        assert result is None

    def test_returns_explicit_when_no_user(self):
        """When no user, should use explicit org_id"""
        result = get_organization_id(None, "org_explicit")
        assert result == "org_explicit"

    def test_returns_explicit_when_user_has_no_org(self, user_no_org):
        """When user has no org, should use explicit org_id"""
        result = get_organization_id(user_no_org, "org_explicit")
        assert result == "org_explicit"

    def test_returns_none_when_nothing_provided(self):
        """When no user and no explicit org, return None"""
        result = get_organization_id(None, None)
        assert result is None

    def test_rejects_explicit_when_not_allowed(self, user_no_org):
        """When allow_explicit=False and no user org, return None"""
        result = get_organization_id(user_no_org, "org_explicit", allow_explicit=False)
        assert result is None


# ==========================================
# require_organization_id() TESTS
# ==========================================


class TestRequireOrganizationId:
    """Tests for the require_organization_id function"""

    def test_returns_user_org_when_authenticated(self, user_org_a):
        """Authenticated user should get their organization_id"""
        result = require_organization_id(user_org_a, None)
        assert result == "org_a"

    def test_raises_403_on_cross_org_attempt(self, user_org_a):
        """Cross-org access attempt should raise 403 Forbidden"""
        with pytest.raises(HTTPException) as exc_info:
            require_organization_id(user_org_a, "org_b")

        assert exc_info.value.status_code == 403
        assert "another organization" in exc_info.value.detail.lower()

    def test_returns_explicit_when_no_user(self):
        """When no user, should use explicit org_id with warning"""
        result = require_organization_id(None, "org_explicit")
        assert result == "org_explicit"

    def test_raises_401_when_no_user_no_org(self):
        """When no user and no explicit org, raise 401"""
        with pytest.raises(HTTPException) as exc_info:
            require_organization_id(None, None)

        assert exc_info.value.status_code == 401
        assert "authentication" in exc_info.value.detail.lower()

    def test_raises_400_when_user_has_no_org(self, user_no_org):
        """When user is authenticated but has no org, raise 400"""
        with pytest.raises(HTTPException) as exc_info:
            require_organization_id(user_no_org, None)

        assert exc_info.value.status_code == 400
        assert "organization" in exc_info.value.detail.lower()

    def test_accepts_matching_explicit_org(self, user_org_a):
        """When explicit org matches user's org, accept it"""
        result = require_organization_id(user_org_a, "org_a")
        assert result == "org_a"


# ==========================================
# validate_organization_access() TESTS
# ==========================================


class TestValidateOrganizationAccess:
    """Tests for the validate_organization_access function"""

    def test_allows_access_to_own_org_resource(self, user_org_a):
        """User should access resources from their own org"""
        result = validate_organization_access(user_org_a, "org_a")
        assert result is True

    def test_denies_access_to_other_org_resource(self, user_org_a):
        """User should NOT access resources from other org"""
        with pytest.raises(HTTPException) as exc_info:
            validate_organization_access(user_org_a, "org_b")

        assert exc_info.value.status_code == 403
        assert "another organization" in exc_info.value.detail.lower()

    def test_denies_access_when_user_has_no_org(self, user_no_org):
        """User without org should not access any org resource"""
        with pytest.raises(HTTPException) as exc_info:
            validate_organization_access(user_no_org, "org_a")

        assert exc_info.value.status_code == 403


# ==========================================
# get_org_id_from_request() TESTS
# ==========================================


class TestGetOrgIdFromRequest:
    """Tests for extracting org_id from request"""

    def test_extracts_from_request_state(self, mock_request):
        """Should extract org_id from request state"""
        mock_request.state.organization_id = "org_from_state"
        result = get_org_id_from_request(mock_request)
        assert result == "org_from_state"

    def test_extracts_from_query_param_org_id(self, mock_request):
        """Should extract org_id from query parameter"""
        del mock_request.state.organization_id
        mock_request.query_params = {"organization_id": "org_from_query"}
        result = get_org_id_from_request(mock_request)
        assert result == "org_from_query"

    def test_extracts_from_query_param_org_id_short(self, mock_request):
        """Should extract org_id from short query parameter"""
        del mock_request.state.organization_id
        mock_request.query_params = {"org_id": "org_from_short_query"}
        result = get_org_id_from_request(mock_request)
        assert result == "org_from_short_query"

    def test_extracts_from_header(self, mock_request):
        """Should extract org_id from X-Organization-ID header"""
        del mock_request.state.organization_id
        mock_request.query_params = {}
        mock_request.headers = {"X-Organization-ID": "org_from_header"}
        result = get_org_id_from_request(mock_request)
        assert result == "org_from_header"

    def test_returns_none_when_not_found(self, mock_request):
        """Should return None when org_id not found anywhere"""
        del mock_request.state.organization_id
        mock_request.query_params = {}
        mock_request.headers = {}
        result = get_org_id_from_request(mock_request)
        assert result is None


# ==========================================
# UTILITY FUNCTION TESTS
# ==========================================


class TestUtilityFunctions:
    """Tests for utility functions"""

    def test_is_demo_organization_exact_match(self):
        """Should identify demo_org as demo"""
        assert is_demo_organization(DEMO_ORGANIZATION_ID) is True

    def test_is_demo_organization_prefix_match(self):
        """Should identify demo_ prefixed orgs as demo"""
        assert is_demo_organization("demo_12345") is True

    def test_is_demo_organization_false_for_regular(self):
        """Should NOT identify regular orgs as demo"""
        assert is_demo_organization("org_production") is False

    def test_is_system_organization(self):
        """Should identify system org"""
        assert is_system_organization(SYSTEM_ORGANIZATION_ID) is True
        assert is_system_organization("org_regular") is False


# ==========================================
# INTEGRATION TESTS WITH MOCKED FIRESTORE
# ==========================================


class TestFirestoreOrgScoping:
    """Tests for Firestore organization scoping"""

    @pytest.mark.asyncio
    async def test_get_org_document_returns_none_for_wrong_org(self):
        """get_org_document should return None for documents from other orgs"""
        from app.core.firestore_db import FirestoreManager

        manager = FirestoreManager()

        # Mock the get_document method
        with patch.object(manager, 'get_document', new_callable=AsyncMock) as mock_get:
            # Document belongs to org_b
            mock_get.return_value = {
                "id": "doc_123",
                "organization_id": "org_b",
                "data": "test"
            }

            # Try to access from org_a - should return None
            result = await manager.get_org_document("test_collection", "doc_123", "org_a")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_org_document_returns_document_for_correct_org(self):
        """get_org_document should return document for correct org"""
        from app.core.firestore_db import FirestoreManager

        manager = FirestoreManager()

        with patch.object(manager, 'get_document', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "id": "doc_123",
                "organization_id": "org_a",
                "data": "test"
            }

            result = await manager.get_org_document("test_collection", "doc_123", "org_a")
            assert result is not None
            assert result["organization_id"] == "org_a"

    @pytest.mark.asyncio
    async def test_update_org_document_fails_for_wrong_org(self):
        """update_org_document should return False for documents from other orgs"""
        from app.core.firestore_db import FirestoreManager

        manager = FirestoreManager()

        with patch.object(manager, 'get_document', new_callable=AsyncMock) as mock_get:
            # Document belongs to org_b
            mock_get.return_value = {
                "id": "doc_123",
                "organization_id": "org_b"
            }

            # Try to update from org_a - should return False (access denied)
            result = await manager.update_org_document(
                "test_collection", "doc_123", {"data": "new"}, "org_a"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_create_org_document_includes_org_id(self):
        """create_org_document should always include organization_id"""
        from app.core.firestore_db import FirestoreManager

        manager = FirestoreManager()

        with patch.object(manager, 'create_document', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = "new_doc_id"

            await manager.create_org_document(
                "test_collection",
                {"title": "Test"},
                "org_a"
            )

            # Verify organization_id was added to the data
            call_args = mock_create.call_args
            created_data = call_args[0][1]
            assert created_data["organization_id"] == "org_a"


# ==========================================
# API ENDPOINT TESTS
# ==========================================


class TestPMAutomationEndpoints:
    """Tests for PM Automation API endpoint org isolation"""

    @pytest.mark.asyncio
    async def test_meter_reading_requires_org(self):
        """POST /api/pm/meter-reading should require organization"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        # Request without org_id should fail
        response = client.post(
            "/api/pm/meter-reading",
            json={
                "meter_id": "meter_001",
                "new_value": 5.0
            }
        )

        # Should require auth or org_id
        assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_generate_schedule_requires_org(self):
        """POST /api/pm/generate-schedule should require organization"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        response = client.post(
            "/api/pm/generate-schedule",
            json={}
        )

        assert response.status_code in [400, 401, 422]

    @pytest.mark.asyncio
    async def test_overview_requires_org(self):
        """GET /api/pm/overview should require organization"""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)

        response = client.get("/api/pm/overview")

        assert response.status_code in [400, 401]


# ==========================================
# SECURITY TESTS
# ==========================================


class TestSecurityBoundaries:
    """Tests for security boundaries between organizations"""

    def test_user_cannot_switch_orgs_via_parameter(self, user_org_a):
        """Authenticated user cannot switch orgs via explicit parameter"""
        # User tries to specify different org
        with pytest.raises(HTTPException) as exc_info:
            require_organization_id(user_org_a, "org_malicious")

        assert exc_info.value.status_code == 403

    def test_none_values_dont_bypass_checks(self):
        """Empty strings and None values shouldn't bypass checks"""
        result = get_organization_id(None, "")
        assert result is None or result == ""

        result = get_organization_id(None, None)
        assert result is None

    def test_org_id_is_not_empty_string_after_require(self, user_org_a):
        """require_organization_id should never return empty string"""
        result = require_organization_id(user_org_a, None)
        assert result is not None
        assert result != ""
        assert len(result) > 0
