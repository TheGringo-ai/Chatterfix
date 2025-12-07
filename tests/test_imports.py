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
            from app.core.db_adapter import get_db_adapter  # noqa: F401

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


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])
