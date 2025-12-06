# Training Module Tests

This directory contains tests for the ChatterFix training module.

## Test Structure

- `test_training.py` - Main training endpoint tests
- `conftest.py` - pytest configuration and fixtures

## Running Tests

### Option 1: Using pytest (if installed)
```bash
pip install pytest pytest-asyncio
pytest tests/test_training.py -v
```

### Option 2: Manual Testing (no dependencies)
```bash
# Test basic training functionality
python3 -c "
import sys
sys.path.append('.')
from app.routers.training import get_current_user_from_session
user = get_current_user_from_session('valid_session_token_12345')
print('Session validation works:', user is not None)
"

# Test complete training flow
python3 -c "
import asyncio, sys
sys.path.append('.')
from app.core.db_adapter import get_db_adapter

async def test():
    db = get_db_adapter()
    modules = await db.get_training_modules()
    print('Training modules loaded:', len(modules))
    
asyncio.run(test())
"
```

## Test Coverage

The tests cover:

1. **Training Endpoints**
   - Get training modules (with filtering)
   - Module details 
   - Start training
   - Complete training
   - Assign training
   - Get user training

2. **Authentication**
   - Valid session access
   - Invalid session redirects
   - Unauthenticated redirects

3. **Firestore Integration**
   - Module CRUD operations
   - User training assignments
   - Training statistics

4. **Helper Functions**
   - User training with modules
   - Training statistics calculation
   - Performance metrics updates

## Mock Data

Tests use mocked Firestore data including:
- Sample training modules (Safety, Pump Maintenance)
- User training assignments
- Module content with quizzes
- Training completion scores

## Expected Results

All tests should pass with proper Firestore integration. The training module is fully converted from SQLite to Firestore and includes proper authentication.