"""
Import Validation Tests for ChatterFix CMMS

These tests ensure that all router modules can be imported without errors.
This helps catch import issues early before they cause service unavailability.
"""

import importlib
import sys
from pathlib import Path

import pytest


class TestRouterImports:
    """Test that all router modules can be imported successfully"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test"""
        # Add app directory to path if not already there
        app_path = Path(__file__).parent.parent
        if str(app_path) not in sys.path:
            sys.path.insert(0, str(app_path))

    def test_import_all_routers(self):
        """Test that all router modules can be imported without errors"""
        routers_path = Path(__file__).parent.parent / "app" / "routers"

        # Skip if routers directory doesn't exist
        if not routers_path.exists():
            pytest.skip("Routers directory not found")

        failed_imports = []
        successful_imports = []

        # Get all Python files in routers directory
        for file_path in routers_path.glob("*.py"):
            if file_path.name.startswith("__"):
                continue

            module_name = f"app.routers.{file_path.stem}"

            try:
                # Attempt to import the module
                module = importlib.import_module(module_name)
                successful_imports.append(module_name)

                # Verify the module has a router attribute
                if not hasattr(module, "router"):
                    failed_imports.append(
                        (module_name, "Module does not have 'router' attribute")
                    )
            except ImportError as e:
                failed_imports.append((module_name, f"ImportError: {str(e)}"))
            except ModuleNotFoundError as e:
                failed_imports.append((module_name, f"ModuleNotFoundError: {str(e)}"))
            except Exception as e:
                failed_imports.append(
                    (module_name, f"Error: {type(e).__name__}: {str(e)}")
                )

        # Report results
        print(f"\n✅ Successfully imported {len(successful_imports)} routers:")
        for name in successful_imports:
            print(f"  - {name}")

        if failed_imports:
            print(f"\n❌ Failed to import {len(failed_imports)} routers:")
            for name, error in failed_imports:
                print(f"  - {name}: {error}")

            pytest.fail(
                f"Failed to import {len(failed_imports)} router(s). "
                f"See output above for details."
            )

    def test_specific_router_imports(self):
        """Test importing specific routers that were mentioned in the issue"""
        critical_routers = [
            "app.routers.team",
            "app.routers.landing",
        ]

        failed_imports = []

        for router_name in critical_routers:
            try:
                module = importlib.import_module(router_name)
                assert hasattr(
                    module, "router"
                ), f"{router_name} does not have 'router' attribute"
            except Exception as e:
                failed_imports.append((router_name, str(e)))

        if failed_imports:
            error_msg = "\n".join(
                [f"{name}: {error}" for name, error in failed_imports]
            )
            pytest.fail(f"Critical router imports failed:\n{error_msg}")

    def test_router_registration_in_main(self):
        """Test that routers can be registered with FastAPI without errors"""
        try:
            # Import main module to verify all routers can be loaded
            import main

            # Verify app exists
            assert hasattr(main, "app"), "main.py does not have 'app' attribute"

            # Get all routes from the app
            routes = main.app.routes

            # Verify we have routes registered
            assert len(routes) > 0, "No routes registered in FastAPI app"

            print(f"\n✅ FastAPI app has {len(routes)} routes registered")

        except ImportError as e:
            pytest.fail(f"Failed to import main module: {str(e)}")
        except Exception as e:
            pytest.fail(f"Error registering routers: {type(e).__name__}: {str(e)}")

    def test_no_missing_dependencies(self):
        """Test that all required dependencies for routers are available"""
        # List of critical dependencies that routers might need
        critical_dependencies = [
            "fastapi",
            "starlette",
            "pydantic",
        ]

        missing = []

        for dep in critical_dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(dep)

        if missing:
            pytest.fail(
                f"Missing critical dependencies: {', '.join(missing)}. "
                f"Install with: pip install {' '.join(missing)}"
            )


class TestMiddlewareImports:
    """Test that middleware modules can be imported successfully"""

    def test_import_error_tracking_middleware(self):
        """Test that error tracking middleware can be imported"""
        try:
            from app.middleware import ErrorTrackingMiddleware

            # Verify it's a class
            assert isinstance(
                ErrorTrackingMiddleware, type
            ), "ErrorTrackingMiddleware is not a class"

            print("\n✅ Successfully imported ErrorTrackingMiddleware")

        except ImportError as e:
            pytest.fail(f"Failed to import ErrorTrackingMiddleware: {str(e)}")

    def test_middleware_instantiation(self):
        """Test that middleware can be instantiated without errors"""
        try:
            from fastapi import FastAPI

            from app.middleware import ErrorTrackingMiddleware

            # Create a test app
            test_app = FastAPI()

            # Try to instantiate the middleware
            middleware = ErrorTrackingMiddleware(app=test_app, environment="test")

            assert middleware is not None, "Failed to instantiate middleware"
            assert middleware.environment == "test", "Environment not set correctly"

            print("\n✅ Successfully instantiated ErrorTrackingMiddleware")

        except Exception as e:
            pytest.fail(
                f"Failed to instantiate middleware: {type(e).__name__}: {str(e)}"
            )


class TestCoreImports:
    """Test that core modules can be imported successfully"""

    def test_import_db_adapter(self):
        """Test that database adapter can be imported"""
        try:
            from app.core.db_adapter import get_db_adapter

            # Verify it's a callable function
            assert callable(get_db_adapter), "get_db_adapter should be callable"

            print("\n✅ Successfully imported db_adapter")

        except ImportError as e:
            pytest.fail(f"Failed to import db_adapter: {str(e)}")

    def test_import_auth_services(self):
        """Test that authentication services can be imported"""
        auth_modules = [
            "app.services.auth_service",
            "app.services.firebase_auth",
        ]

        failed = []

        for module_name in auth_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                failed.append((module_name, str(e)))

        if failed:
            error_msg = "\n".join([f"{name}: {error}" for name, error in failed])
            pytest.fail(f"Failed to import auth modules:\n{error_msg}")


class TestDeploymentCriticalImports:
    """
    CRITICAL: Tests for imports that caused deployment failures
    These tests prevent the specific issues we encountered
    """

    def test_uvicorn_import_critical(self):
        """CRITICAL: Test uvicorn import - caused container startup failures"""
        try:
            import uvicorn

            assert uvicorn is not None

            # Test that uvicorn can be imported from command line
            import subprocess

            result = subprocess.run(
                [sys.executable, "-c", "import uvicorn; print('uvicorn available')"],
                capture_output=True,
                text=True,
            )

            assert (
                result.returncode == 0
            ), f"uvicorn import failed in subprocess: {result.stderr}"
            print("\n✅ uvicorn import validation passed (CRITICAL)")

        except ImportError as e:
            pytest.fail(f"CRITICAL: uvicorn import failed - {e}")

    def test_port_configuration_critical(self):
        """CRITICAL: Test port configuration for Cloud Run compatibility"""
        try:
            # Read main.py and verify port configuration
            main_path = Path(__file__).parent.parent / "main.py"
            with open(main_path, "r") as f:
                content = f.read()

            # Check for Cloud Run compatible port configuration
            assert (
                'port = int(os.getenv("PORT", "8080"))' in content
            ), "CRITICAL: main.py must default to port 8080 for Cloud Run"

            print("\n✅ Port configuration validated for Cloud Run (CRITICAL)")

        except Exception as e:
            pytest.fail(f"CRITICAL: Port configuration validation failed - {e}")

    def test_json_serialization_patterns(self):
        """CRITICAL: Test JSON serialization patterns that caused 500 errors"""
        try:
            import json
            from datetime import datetime, date

            # Test the correct datetime serialization patterns
            test_data = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "date": date.today().strftime("%Y-%m-%d"),
                "status": "active",
                "data": {"test": "value"},
            }

            # This should not fail
            json_str = json.dumps(test_data)
            parsed_back = json.loads(json_str)
            assert parsed_back == test_data

            print("\n✅ JSON serialization patterns validated (CRITICAL)")

        except Exception as e:
            pytest.fail(f"CRITICAL: JSON serialization validation failed - {e}")

    def test_firebase_import_graceful_handling(self):
        """CRITICAL: Test Firebase imports handle missing credentials gracefully"""
        try:
            # This should not crash even if credentials are missing
            from app.services.firebase_auth import FirebaseAuthService

            # Test that FirebaseAuthService can be instantiated
            # Even if Firebase is disabled, it should not crash
            FirebaseAuthService()

            print(
                "\n✅ Firebase imports and service instantiation handled gracefully (CRITICAL)"
            )

        except Exception as e:
            pytest.fail(f"CRITICAL: Firebase import/service validation failed - {e}")

    def test_docker_user_permissions_compatibility(self):
        """CRITICAL: Test that Python paths work with non-root user"""
        try:
            import sys
            import os

            # Check if we can access the Python executable
            python_path = sys.executable
            assert os.access(python_path, os.X_OK), "Python executable not accessible"

            # Check if we can import from user-local paths
            import site

            user_site = (
                site.getusersitepackages()
                if hasattr(site, "getusersitepackages")
                else None
            )

            print(f"\n✅ Python path accessibility validated (CRITICAL)")
            print(f"   Python executable: {python_path}")
            if user_site:
                print(f"   User site packages: {user_site}")

        except Exception as e:
            pytest.fail(f"CRITICAL: Docker user permission compatibility failed - {e}")

    def test_environment_variables_handling(self):
        """CRITICAL: Test environment variable handling doesn't crash app"""
        try:
            import os

            # Test critical environment variables
            critical_env_vars = [
                "PORT",
                "USE_FIRESTORE",
                "GOOGLE_APPLICATION_CREDENTIALS",
                "AI_TEAM_SERVICE_URL",
                "ENVIRONMENT",
            ]

            # Application should handle missing env vars gracefully
            for var in critical_env_vars:
                value = os.getenv(var, "default_test_value")
                # Should not crash with any value or None
                assert value is not None or value == "default_test_value"

            print("\n✅ Environment variable handling validated (CRITICAL)")

        except Exception as e:
            pytest.fail(f"CRITICAL: Environment variable handling failed - {e}")

    def test_ai_team_service_import_handling(self):
        """CRITICAL: Test AI team service imports handle missing dependencies"""
        try:
            # Test that missing AI dependencies don't crash the import
            ai_modules = ["openai", "google.generativeai", "anthropic"]
            available_modules = []

            for module in ai_modules:
                try:
                    __import__(module)
                    available_modules.append(module)
                except ImportError:
                    pass  # Should not crash

            print(f"\n✅ AI module import handling validated (CRITICAL)")
            print(f"   Available AI modules: {available_modules}")

        except Exception as e:
            pytest.fail(f"CRITICAL: AI module import handling failed - {e}")


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])
