"""Import verification and project structure documentation."""

# New Industry-Standard Structure:
#
# Backend/
# ├── app/                          # Application package
# │   ├── __init__.py              # App factory: create_app()
# │   ├── config.py                # Settings management
# │   ├── dependencies.py          # Dependency injection
# │   ├── engines/                 # Scoring engines
# │   │   ├── __init__.py
# │   │   ├── social_graph.py      # Layer 1: Social trust
# │   │   ├── psychometric.py      # Layer 2: Gemini API
# │   │   ├── behavioral.py        # Layer 3: Patterns
# │   │   └── fusion.py            # Score fusion
# │   ├── models/                  # Pydantic schemas
# │   │   ├── __init__.py          # Contains all models
# │   │   └── merchant.py          # (legacy, models in __init__)
# │   ├── routers/                 # API route groups
# │   │   ├── __init__.py
# │   │   ├── merchants.py         # (future: merchant routes)
# │   │   └── scores.py            # (future: scoring routes)
# │   ├── db/                      # Database
# │   │   ├── __init__.py
# │   │   └── schema.sql
# │   └── data/                    # Data generators
# │       ├── __init__.py
# │       └── generate_mock.py
# ├── main.py                      # Entry point (uvicorn Backend.main:app)
# ├── pyproject.toml
# └── requirements.txt (optional)

# Key Benefits:
# ✅ Scalable: Easy to add more routers, middleware, lifespan handlers
# ✅ Testable: Can import create_app() for testing
# ✅ Professional: Matches FastAPI best practices
# ✅ Dependency Injection: Using Depends() for state management
# ✅ Configuration: Centralized settings via pydantic

# Usage Examples:
# 1. Development:
#    $ cd Backend
#    $ uvicorn main:app --reload --port 8000
#
# 2. Docker:
#    $ docker-compose up --build
#    # Uses: docker.entrypoint: uvicorn Backend.main:app --host 0.0.0.0 --port 8000
#
# 3. Testing (future):
#    from app import create_app
#    app = create_app()
#    client = TestClient(app)
#    response = client.get("/health")
