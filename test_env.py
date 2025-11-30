import sys
import os

print(f"Python version: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import fastapi

    print(f"FastAPI version: {fastapi.__version__}")
except ImportError as e:
    print(f"FastAPI NOT installed: {e}")

try:
    import uvicorn

    print(f"Uvicorn version: {uvicorn.__version__}")
except ImportError as e:
    print(f"Uvicorn NOT installed: {e}")

try:
    from app.core.database import init_database

    print("Imported init_database successfully")
except ImportError as e:
    print(f"Failed to import init_database: {e}")
except Exception as e:
    print(f"Error during import: {e}")
