# CORS Configuration Guide

## What is CORS?

**CORS (Cross-Origin Resource Sharing)** is a security mechanism that controls which websites can access your API from browsers.

### The Same-Origin Policy Problem

Browsers block requests between different origins by default:

```
❌ Blocked by default:
Frontend: http://localhost:3000  →  Backend: http://localhost:8000
(different ports = different origins)

✅ Allowed:
Frontend: http://localhost:8000  →  Backend: http://localhost:8000
(same origin)
```

### How CORS Works

1. **Browser** sends preflight request (OPTIONS):
   ```
   Origin: http://localhost:3000
   ```

2. **Backend** responds with headers:
   ```
   Access-Control-Allow-Origin: http://localhost:3000
   Access-Control-Allow-Credentials: true
   Access-Control-Allow-Methods: GET, POST, PUT, DELETE
   ```

3. If origin is in whitelist - browser allows the request, otherwise - blocks it.

## Configuration in This Project

### Environment Variables

CORS origins are configured in `.env` file:

```env
# CORS Configuration
# Format: JSON array for List[str] fields in Pydantic Settings
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
CORS_ALLOW_CREDENTIALS=true
```

### Pydantic Settings

The configuration is loaded in `app/core/config.py`:

```python
cors_origins: Annotated[
    List[str],
    BeforeValidator(parse_string_list)
] = Field(
    default=["http://localhost:3000", "http://localhost:8000"],
    description="Allowed CORS origins"
)
```

### Middleware Setup

CORS middleware is configured in `app/api/middleware.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Best Practices

### 1. Development vs Production

```python
# ❌ BAD - allow all (insecure)
CORS_ORIGINS=["*"]

# ✅ GOOD - explicit whitelist
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]  # Development
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]  # Production
```

### 2. Environment-Specific Configuration

Create separate `.env` files:

**`.env.development`:**
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

**`.env.production`:**
```env
CORS_ORIGINS=["https://yourdomain.com","https://app.yourdomain.com"]
```

### 3. Format Options

Pydantic Settings 2.x supports multiple formats for list fields:

**A) JSON Array (Recommended):**
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```
- ✅ Works out-of-the-box with Pydantic Settings
- ✅ Type-safe
- ❌ Less readable for simple cases

**B) Comma-Separated String (with custom parser):**
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```
- ✅ More readable
- ✅ Easier to edit manually
- ❌ Requires custom parser

Our implementation supports both formats through the `parse_string_list` validator.

### 4. Security Considerations

#### Never use wildcard in production:
```python
# ❌ NEVER DO THIS IN PRODUCTION
CORS_ORIGINS=["*"]
```

#### Be explicit about allowed origins:
```python
# ✅ GOOD - explicit whitelist
CORS_ORIGINS=[
    "https://yourdomain.com",
    "https://app.yourdomain.com",
    "https://admin.yourdomain.com"
]
```

#### Consider subdomain patterns:
If you need to allow all subdomains, implement custom logic:
```python
def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed (including subdomains)."""
    allowed_domains = ["yourdomain.com"]
    return any(origin.endswith(f".{domain}") or origin.endswith(domain)
               for domain in allowed_domains)
```

### 5. Credentials and Cookies

When using cookies or authentication:

```env
CORS_ALLOW_CREDENTIALS=true
```

**Important:** When `allow_credentials=true`, you CANNOT use `allow_origins=["*"]`. You must specify exact origins.

## Troubleshooting

### Issue: "No 'Access-Control-Allow-Origin' header"

**Cause:** Origin not in whitelist or CORS middleware not configured.

**Solution:**
1. Check `.env` file has correct `CORS_ORIGINS`
2. Verify middleware is added in `app/main.py`
3. Check origin matches exactly (including protocol and port)

### Issue: "SettingsError: error parsing value for field cors_origins"

**Cause:** Invalid format in `.env` file.

**Solution:** Use JSON array format:
```env
CORS_ORIGINS=["http://localhost:3000","http://localhost:8000"]
```

### Issue: CORS works in development but not production

**Cause:** Different origins between environments.

**Solution:**
1. Create environment-specific `.env` files
2. Update `CORS_ORIGINS` for production domains
3. Ensure HTTPS in production

## Testing CORS

### Using curl:
```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/v1/deals
```

### Using JavaScript:
```javascript
fetch('http://localhost:8000/api/v1/deals', {
    method: 'GET',
    credentials: 'include',
    headers: {
        'Content-Type': 'application/json'
    }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('CORS error:', error));
```

## References

- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [FastAPI CORS Middleware](https://fastapi.tiangolo.com/tutorial/cors/)
- [Pydantic Settings Documentation](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
