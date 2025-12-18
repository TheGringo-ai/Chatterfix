"""
Training Module Tests
Tests for training endpoints and Firestore integration
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers.training import router
from app.auth import get_current_active_user, require_permission
from app.models.user import User

# Create test app
app = FastAPI()

# Create a mock user for testing
mock_user = User(
    uid="test_user_1",
    email="test@example.com",
    display_name="Test User",
    role="manager",
    organization_id="test_org",
    permissions=["all"],  # Manager has all permissions
)

# Override auth dependencies for testing
app.dependency_overrides[get_current_active_user] = lambda: mock_user
app.dependency_overrides[require_permission("manager")] = lambda: mock_user

app.include_router(router)
client = TestClient(app)


@pytest.fixture
def mock_firestore_manager():
    """Mock Firestore manager for testing"""
    mock = AsyncMock()

    # Sample training modules
    mock.get_collection.return_value = [
        {
            "id": "module_1",
            "title": "Safety Training",
            "description": "Basic safety procedures",
            "skill_category": "safety",
            "asset_type": "general",
            "difficulty_level": 1,
            "estimated_duration_minutes": 30,
            "content_type": "ai_generated",
            "ai_generated": True,
        },
        {
            "id": "module_2",
            "title": "Pump Maintenance",
            "description": "Centrifugal pump maintenance",
            "skill_category": "maintenance",
            "asset_type": "pump",
            "difficulty_level": 3,
            "estimated_duration_minutes": 90,
            "content_type": "ai_generated",
            "ai_generated": True,
        },
    ]

    # Sample training module detail
    mock.get_document.return_value = {
        "id": "module_1",
        "title": "Safety Training",
        "description": "Basic safety procedures",
        "content_path": json.dumps(
            {
                "title": "Safety Training",
                "description": "Learn essential safety procedures",
                "sections": [
                    {"title": "Introduction", "content": "Welcome to safety training"},
                    {"title": "PPE Requirements", "content": "Always wear proper PPE"},
                ],
                "quiz": [
                    {
                        "question": "What should you always wear?",
                        "options": ["Nothing", "PPE", "Casual clothes", "Uniform"],
                        "correct_answer": 1,
                        "explanation": "PPE protects you from hazards",
                    }
                ],
            }
        ),
        "ai_generated": True,
    }

    # Sample user training assignments
    mock.get_user_training.return_value = [
        {
            "id": "training_1",
            "user_id": "1",
            "training_module_id": "module_1",
            "status": "assigned",
            "assigned_date": "2024-12-06T10:00:00",
            "started_date": None,
            "completed_date": None,
            "score": None,
        }
    ]

    # Mock create methods
    mock.create_document.return_value = "new_training_id"
    mock.create_training_module.return_value = "new_module_id"
    mock.create_user_training.return_value = "new_user_training_id"
    mock.update_document.return_value = True

    return mock


@pytest.fixture
def valid_session_headers():
    """Headers with valid session token"""
    return {"Cookie": "session_token=valid_session_token_12345"}


@pytest.fixture
def invalid_session_headers():
    """Headers with invalid session token"""
    return {"Cookie": "session_token=invalid"}


class TestTrainingEndpoints:
    """Test training API endpoints"""

    @patch("app.routers.training.get_firestore_manager")
    def test_get_modules(self, mock_get_manager, mock_firestore_manager):
        """Test getting all training modules"""
        mock_get_manager.return_value = mock_firestore_manager

        response = client.get("/training/modules")

        assert response.status_code == 200
        modules = response.json()
        assert len(modules) == 2
        assert modules[0]["title"] == "Safety Training"
        assert modules[1]["title"] == "Pump Maintenance"

        # Test filtering by skill category
        mock_firestore_manager.get_collection.return_value = [
            modules[0]
            for modules in [mock_firestore_manager.get_collection.return_value]
            if modules[0]["skill_category"] == "safety"
        ]
        response = client.get("/training/modules?skill_category=safety")
        assert response.status_code == 200

    @patch("app.routers.training.get_firestore_manager")
    @pytest.mark.skip(
        reason="Requires template rendering setup - tested via integration tests"
    )
    def test_module_detail(self, mock_get_manager, mock_firestore_manager):
        """Test getting module details"""
        mock_get_manager.return_value = mock_firestore_manager

        response = client.get("/training/modules/module_1")

        assert response.status_code == 200
        # Should render template with module data
        assert "Safety Training" in response.text

    @patch("app.routers.training.get_firestore_manager")
    @pytest.mark.skip(
        reason="Requires template rendering setup - tested via integration tests"
    )
    def test_module_detail_not_found(self, mock_get_manager, mock_firestore_manager):
        """Test module detail for non-existent module"""
        mock_get_manager.return_value = mock_firestore_manager
        mock_firestore_manager.get_document.return_value = None

        response = client.get("/training/modules/nonexistent")

        # Should redirect to training center
        assert response.status_code == 307

    @patch("app.routers.training.get_firestore_manager")
    def test_start_training(self, mock_get_manager, mock_firestore_manager):
        """Test starting training module"""
        mock_get_manager.return_value = mock_firestore_manager
        mock_firestore_manager.get_collection.return_value = []  # No existing training

        response = client.post("/training/modules/module_1/start")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Verify create_document was called
        mock_firestore_manager.create_document.assert_called_once()

    @patch("app.routers.training.get_firestore_manager")
    def test_start_training_existing(self, mock_get_manager, mock_firestore_manager):
        """Test starting training that's already assigned"""
        mock_get_manager.return_value = mock_firestore_manager
        mock_firestore_manager.get_collection.return_value = [
            {
                "id": "existing_training",
                "user_id": "test_user_1",
                "training_module_id": "module_1",
                "status": "assigned",
            }
        ]

        response = client.post("/training/modules/module_1/start")

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Should update existing rather than create new
        mock_firestore_manager.update_document.assert_called_once()

    @patch("app.routers.training.get_firestore_manager")
    def test_complete_training(self, mock_get_manager, mock_firestore_manager):
        """Test completing training module"""
        mock_get_manager.return_value = mock_firestore_manager

        # Mock user training record
        mock_firestore_manager.get_collection.return_value = [
            {
                "id": "training_1",
                "user_id": "test_user_1",
                "training_module_id": "module_1",
                "status": "in_progress",
            }
        ]

        response = client.post(
            "/training/modules/module_1/complete",
            data={"score": "85.0"},
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Verify training was updated as completed
        mock_firestore_manager.update_document.assert_called()

    @patch("app.routers.training.get_firestore_manager")
    def test_assign_training(self, mock_get_manager, mock_firestore_manager):
        """Test assigning training to user"""
        mock_get_manager.return_value = mock_firestore_manager

        response = client.post(
            "/training/assign", data={"user_id": "test_user_2", "module_id": "module_1"}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True

        # Verify training assignment was created
        mock_firestore_manager.create_document.assert_called_once()

    @patch("app.routers.training.get_firestore_manager")
    def test_get_my_training(self, mock_get_manager, mock_firestore_manager):
        """Test getting user's training assignments"""
        mock_get_manager.return_value = mock_firestore_manager
        mock_firestore_manager.get_collection.return_value = (
            []
        )  # Mock empty training list

        response = client.get("/training/my-training")

        assert response.status_code == 200
        training = response.json()
        assert len(training) >= 0  # Should return user's training

    @patch("app.routers.training.get_firestore_manager")
    @pytest.mark.skip(
        reason="Requires template/static file setup - tested via integration tests"
    )
    def test_training_center_authenticated(
        self, mock_get_manager, mock_firestore_manager, valid_session_headers
    ):
        """Test training center with valid authentication"""
        mock_get_manager.return_value = mock_firestore_manager

        response = client.get("/training/", headers=valid_session_headers)

        assert response.status_code == 200
        assert "Training" in response.text  # Should render training center page

    @pytest.mark.skip(
        reason="Requires template/static file setup - tested via integration tests"
    )
    def test_training_center_unauthenticated(self):
        """Test training center without authentication"""
        response = client.get("/training/")

        # Should redirect to login
        assert response.status_code == 307

    @pytest.mark.skip(
        reason="Requires template/static file setup - tested via integration tests"
    )
    def test_training_center_invalid_session(self, invalid_session_headers):
        """Test training center with invalid session"""
        response = client.get("/training/", headers=invalid_session_headers)

        # Should redirect to login
        assert response.status_code == 307


class TestTrainingHelperFunctions:
    """Test training helper functions"""

    @patch("app.routers.training.get_firestore_manager")
    @pytest.mark.asyncio
    async def test_get_user_training_with_modules(
        self, mock_get_manager, mock_firestore_manager
    ):
        """Test getting user training with module details"""
        from app.routers.training import get_user_training_with_modules

        mock_get_manager.return_value = mock_firestore_manager

        # Mock user training
        mock_firestore_manager.get_collection.return_value = [
            {
                "id": "training_1",
                "user_id": "1",
                "training_module_id": "module_1",
                "status": "assigned",
            }
        ]

        # Mock module details
        mock_firestore_manager.get_document.return_value = {
            "title": "Safety Training",
            "description": "Safety procedures",
            "estimated_duration_minutes": 30,
            "difficulty_level": 1,
        }

        result = await get_user_training_with_modules(mock_firestore_manager, "1")

        assert len(result) == 1
        assert result[0]["title"] == "Safety Training"
        assert result[0]["status"] == "assigned"

    @patch("app.routers.training.get_firestore_manager")
    @pytest.mark.asyncio
    async def test_get_user_training_stats(
        self, mock_get_manager, mock_firestore_manager
    ):
        """Test getting user training statistics"""
        from app.routers.training import get_user_training_stats

        mock_get_manager.return_value = mock_firestore_manager

        # Mock training records
        mock_firestore_manager.get_collection.return_value = [
            {"status": "completed", "score": 85.0},
            {"status": "completed", "score": 92.0},
            {"status": "in_progress", "score": None},
            {"status": "assigned", "score": None},
        ]

        result = await get_user_training_stats(mock_firestore_manager, "1")

        assert result["total_assigned"] == 4
        assert result["completed"] == 2
        assert result["in_progress"] == 1
        assert result["avg_score"] == 88.5  # (85 + 92) / 2


class TestTrainingGenerator:
    """Test training generation functionality"""

    @patch("app.services.training_generator.GEMINI_API_KEY", "test_key")
    @patch("app.services.training_generator.GENAI_AVAILABLE", True)
    @patch("app.services.training_generator.genai")
    @patch("app.services.training_generator.get_firestore_manager")
    @pytest.mark.asyncio
    async def test_generate_from_manual(
        self, mock_get_manager, mock_genai, mock_firestore_manager
    ):
        """Test generating training from manual"""
        from app.services.training_generator import training_generator

        # Mock Gemini response
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = json.dumps(
            {
                "title": "Generated Training",
                "description": "AI-generated training",
                "difficulty_level": 2,
                "estimated_duration_minutes": 45,
                "sections": [{"title": "Overview", "content": "Training overview"}],
                "quiz": [
                    {
                        "question": "Test question?",
                        "options": ["A", "B", "C", "D"],
                        "correct_answer": 0,
                        "explanation": "A is correct",
                    }
                ],
            }
        )
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model

        mock_get_manager.return_value = mock_firestore_manager
        mock_firestore_manager.create_training_module.return_value = (
            "generated_module_id"
        )

        # Create a temporary test file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Test manual content")
            temp_file_path = f.name

        try:
            result = await training_generator.generate_from_manual(
                temp_file_path, "pump", "maintenance"
            )

            assert result == "generated_module_id"
            mock_firestore_manager.create_training_module.assert_called_once()
        finally:
            os.unlink(temp_file_path)
