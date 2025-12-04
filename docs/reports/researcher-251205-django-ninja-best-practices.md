# Django Ninja Best Practices - Research Report (Phase 04 Backend API Development)

## Project Structure

### Recommended Architecture
```
project/
├── api.py           # Main API configuration
├── urls.py          # Django URL routing
└── apps/
    ├── users/
    │   ├── models.py
    │   ├── schemas.py
    │   └── api.py    # App-specific API routes
    └── accounts/
        ├── models.py
        ├── schemas.py
        └── api.py
```

## Authentication: JWT Implementation

### Recommended Approach
1. Use `django-ninja-jwt` library
2. Implement async authenticator
3. Configure authentication at router level

```python
from ninja_jwt.authentication import JWTAuthentication

class JWTAuthenticator(JWTAuthentication):
    async def authenticate(self, request):
        # Custom async authentication logic
        ...

# Router-level authentication
api.add_router("/protected/", protected_router, auth=JWTAuthenticator())
```

## Pydantic Schemas: Best Practices

### Schema Design
- Use "In" and "Out" postfixes for input/output schemas
- Leverage model validation
- Configure schema behavior

```python
from ninja import Schema
from pydantic import field_validator

class UserIn(Schema):
    username: str
    email: str

    @field_validator('email')
    def validate_email(cls, v):
        # Custom email validation
        ...

class UserOut(Schema):
    id: int
    username: str

    class Config:
        from_attributes = True  # ORM integration
```

## Error Handling

### Custom Exception Handling
```python
from ninja import NinjaAPI
from ninja.errors import HttpError

api = NinjaAPI()

@api.exception_handler(ValidationError)
def custom_validation_error(request, exc):
    return api.create_response(
        request,
        {"detail": exc.errors()},
        status=422
    )
```

## Pagination Strategy

### Cursor-Based Pagination
```python
class PaginatedResponse(Schema):
    items: List[ItemOut]
    next_cursor: Optional[str] = None
    total_count: int

@api.get("/items", response=PaginatedResponse)
def list_items(request, cursor: Optional[str] = None, limit: int = 10):
    # Implement cursor-based pagination
    ...
```

## Security Considerations
- Always use HTTPS
- Implement rate limiting
- Use Django's built-in CSRF protection
- Validate and sanitize all input

## Performance Optimization
- Use async views for I/O-bound operations
- Implement database query optimization
- Use efficient serialization
- Cache frequently accessed data

## Unresolved Questions
- Best practices for handling large file uploads (>100MB)
- Optimal caching strategies for multi-user scenarios

## References
- Django Ninja Documentation: https://django-ninja.dev
- Pydantic Documentation: https://docs.pydantic.dev

**Generated on**: 2025-12-05
**Version**: Django Ninja 1.0+