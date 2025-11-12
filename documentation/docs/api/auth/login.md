# Login

Authenticate a user and receive access tokens.

## Endpoint

```
POST /api/v1/auth/login
```

## Request Body

```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

## Response

```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 900
}
```

## Error Responses

- `401 Unauthorized`: Invalid credentials
- `429 Too Many Requests`: Rate limit exceeded
