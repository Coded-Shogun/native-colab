# Authentication Overview

Authentication in Native Colab uses JWT (JSON Web Tokens) for secure API access.

## Authentication Flow

1. User logs in with credentials
2. Server validates credentials
3. Server generates access + refresh tokens
4. Client stores tokens securely
5. Client includes access token in API requests

## Token Types

- **Access Token**: Short-lived (15 min), used for API requests
- **Refresh Token**: Long-lived (7 days), used to get new access tokens

## Next Steps

- [Login →](./login)
- [Register →](./register)
- [Token Refresh →](./tokens)
