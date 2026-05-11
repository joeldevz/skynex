# Design Tree — Rate Limiter

## Resolved decisions
- D1: Algorithm = token bucket
- D2: Limit = 100 requests per minute per user
- D3: Storage = Redis
- D4: Scope = API endpoints only (not static assets)
- D5: Response on limit = HTTP 429 with Retry-After header
