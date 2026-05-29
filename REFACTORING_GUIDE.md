# TrustBridge Refactoring: Migration Guide

## Overview
The TrustBridge backend has been refactored to follow **FastAPI best practices** and **industry-standard project structure**. All functionality remains unchanged; this is a structural improvement.

## Key Changes

### 1. Directory Structure

**BEFORE (Flat Structure):**
```
Backend/
├── main.py                    # Monolithic entry point
├── engines/                   # Engine files scattered
│   ├── social_graph.py
│   ├── psychometric.py
│   ├── behavioral.py
│   └── fusion.py
├── models/                    # Models scattered
├── routers/                   # (unused)
└── data/generate_mock.py
```

**AFTER (Professional Structure):**
```
Backend/
├── app/                       # Application package
│   ├── __init__.py           # App factory: create_app()
│   ├── config.py             # Settings management
│   ├── dependencies.py       # Dependency injection
│   ├── engines/              # Scoring engines
│   ├── models/               # Pydantic schemas
│   ├── routers/              # API route groups
│   └── db/                   # Database layer
├── data/                      # Data generators (unchanged)
├── db/                        # SQL schemas (unchanged)
├── engines/                   # Legacy engines (kept for safety)
└── main.py                   # Thin entry point
```

### 2. Dependency Injection

**BEFORE:**
```python
# Global state in main.py
MERCHANTS = []
MERCHANT_MAP = {}
GRAPH = None

@app.get("/")
def root():
    return {"merchants": len(MERCHANTS)}  # Hard to test
```

**AFTER:**
```python
# app/dependencies.py
class AppState:
    merchants = []
    merchant_map = {}
    graph = None

def get_app_state() -> AppState:
    # Returns injected state
    
@app.get("/")
def root(state: AppStateDep):
    return {"merchants": len(state.merchants)}  # Easy to test
```

### 3. Configuration Management

**BEFORE:**
```python
# Scattered os.getenv() calls
gemini_key = os.getenv("GEMINI_API_KEY")
db_url = os.getenv("DATABASE_URL")
```

**AFTER:**
```python
# app/config.py - Centralized
class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DATABASE_URL: str
    # ...

settings = get_settings()  # Cached singleton
```

### 4. App Factory Pattern

**BEFORE:**
```python
# main.py created app inline
app = FastAPI()
app.add_middleware(...)
# ... lots of code ...
```

**AFTER:**
```python
# app/__init__.py
def create_app() -> FastAPI:
    app = FastAPI()
    # ... configuration ...
    return app

# main.py
from app import create_app
app = create_app()
```

**Benefit:** Can now use `create_app()` in tests, scripts, and environments.

## Migration Checklist

- ✅ Created `Backend/app/` subdirectory
- ✅ Created `app/config.py` with Settings class
- ✅ Created `app/dependencies.py` with AppState and dependency injection
- ✅ Created `app/engines/` and moved all scoring engines
- ✅ Created `app/models/` with Pydantic schemas
- ✅ Created `app/__init__.py` with create_app() factory
- ✅ Updated `Backend/main.py` to thin entry point
- ✅ All original data, db files remain unchanged
- ✅ Original engines/ folder kept for backward compatibility

## Running the Application

### Development

```bash
# Navigate to project root
cd Backend

# Method 1: Direct uvicorn
uvicorn main:app --reload --port 8000

# Method 2: Python
python main.py
```

### Docker

```bash
# Build and run
docker-compose up --build

# Backend will be at http://localhost:8000
# Frontend will be at http://localhost:8501
```

### Testing

```bash
# Verify structure
python verify_structure.py

# Expected output:
# ✓ All tests passed! Structure is correct.
```

## API Endpoints (Unchanged)

- `GET /` - Root/health
- `GET /merchants` - List all merchants
- `GET /merchants/{merchant_id}` - Get merchant details
- `GET /psychometric/questions` - Get assessment questions
- `POST /score/{merchant_id}` - Compute full trust score
- `GET /graph/stats` - Social graph statistics
- `GET /health` - Health check

## Important Notes

### For Frontend (Streamlit)

The frontend doesn't need changes—it communicates via HTTP to the API. Verify it can reach:
- Backend at `http://localhost:8000` (or configured URL)

### For Database

Database operations unchanged. Schema files remain in `Backend/db/`.

### For Mock Data

Generate mock data as usual:
```bash
python Backend/data/generate_mock.py
```

This creates `Backend/data/mock_merchants.json`.

## Future Improvements

The new structure enables:

1. **Router Organization:**
   ```python
   # Backend/app/routers/merchants.py
   router = APIRouter(prefix="/merchants")
   
   @router.get("/{merchant_id}")
   def get_merchant(merchant_id: str):
       # ...
   ```

2. **Middleware Addition:**
   ```python
   app.add_middleware(SomeMiddleware)
   ```

3. **Lifespan Context Manager:**
   ```python
   @asynccontextmanager
   async def lifespan(app: FastAPI):
       # Startup
       yield
       # Shutdown
   ```

4. **Testing:**
   ```python
   from app import create_app
   from fastapi.testclient import TestClient
   
   app = create_app()
   client = TestClient(app)
   
   def test_merchants():
       response = client.get("/merchants")
       assert response.status_code == 200
   ```

## Troubleshooting

### Import Errors

If you get import errors, ensure:
1. You're in the correct directory (`/home/aadarsh/hackathon/Hi-Tech-JunctionXKathmandu-/`)
2. Python path includes `Backend/`
3. All `__init__.py` files exist in package directories

### Module Not Found

```bash
# If python can't find Backend package
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python Backend/main.py
```

### Dockerfile Issues

The Dockerfile automatically handles paths:
```dockerfile
COPY Backend/ Backend/
# Uvicorn runs as: uvicorn Backend.main:app
```

## Migration Complete! 🎉

Your backend is now **production-ready** and follows **FastAPI best practices**. All existing functionality is preserved while maintainability is significantly improved.
