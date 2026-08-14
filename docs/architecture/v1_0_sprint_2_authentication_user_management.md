# ARA v1.0 Sprint 2 Architecture Document — Authentication & User Management

## 1. Executive Summary

Sprint 2 delivers the production-grade **Authentication & User Management Platform** for the AI Research Assistant (ARA v1.0). It establishes user registration, login with login attempt throttling and account lockout protection, JWT access and refresh token lifecycle with Redis blacklist revocation, Role-Based Access Control (RBAC) with 4 standard roles (`Admin`, `Researcher`, `Developer`, `Viewer`), email verification, single-use password resets, Google/GitHub OAuth linking interfaces, and user profile management APIs.

---

## 2. Platform Component Layout

```mermaid
graph TD
    CLIENT[API Client / Web Frontend] --> ROUTER[FastAPI Routers<br>/api/v1/auth & /api/v1/users]
    ROUTER --> DEP[FastAPI Security Dependencies<br>get_current_user / require_roles]
    DEP --> SVC[AuthService & JWTManager]
    
    subgraph Security & Storage Core
        SVC --> HASH[PasswordHasher<br>Argon2 / PBKDF2]
        SVC --> JWT[JWTManager<br>HS256 Access & Refresh]
        SVC --> RBAC[RBACManager<br>Admin, Researcher, Developer, Viewer]
        SVC --> EMAIL[EmailService<br>Abstracted Verification & Reset]
        SVC --> OAUTH[OAuthManager<br>Google & GitHub Handlers]
    end

    subgraph Data Infrastructure (Sprint 1)
        SVC --> REPO[UserRepository & AuditLogRepository]
        SVC --> REDIS[(Redis Cache & Revocation List)]
        REPO --> PG[(PostgreSQL Database)]
    end
```

---

## 3. Component Breakdown

### 3.1 Password Hashing & Complexity Policy (`core/auth/password.py`)
- **`PasswordHasher`**: Uses Argon2 (`passlib.context`) with PBKDF2-HMAC-SHA256 fallback.
- **`PasswordPolicyValidator`**: Enforces enterprise password strength (min length 8, uppercase, lowercase, digit, special character).

### 3.2 JWT Token Lifecycle & Revocation (`core/auth/jwt.py`)
- **Access Tokens**: Short-lived JWTs (60 mins) carrying `sub`, `email`, `tenant_id`, `role`, `jti`.
- **Refresh Tokens**: Long-lived JWTs (7 days) with token rotation.
- **Email & Password Reset Tokens**: Single-use tokens tracked in Redis.
- **Redis Blacklist**: Revoked JTIs are stored in Redis (`jwt:blacklist:{jti}`) for instant logout & token invalidation.

### 3.3 Role-Based Access Control / RBAC (`core/auth/rbac.py`)
- **Roles**: `Admin`, `Researcher`, `Developer`, `Viewer`.
- **Permission Matrix**:
  - `Admin`: `["*"]`
  - `Developer`: `["read", "write", "execute", "workflow_manage", "dataset_manage"]`
  - `Researcher`: `["read", "write", "execute", "research:*", "workspace:*"]`
  - `Viewer`: `["read"]`

### 3.4 Email & OAuth Services (`core/auth/email_service.py` & `oauth.py`)
- **Email Providers**: `AbstractEmailProvider`, `SMTPEmailProvider`, `MockEmailProvider` (for test isolation).
- **OAuth Providers**: `GoogleOAuthHandler` and `GitHubOAuthHandler` for social account authorization & token exchange.

### 3.5 AuthService & Throttling (`core/auth/service.py`)
- **Registration**: Creates user, hashes password, assigns default role, sends verification email.
- **Login Throttling**: Tracks failed login attempts in Redis (`auth:failed_attempts:{email}`). After 5 failed attempts in 15 minutes, locks account (`auth:lockout:{email}`) for 15 minutes.
- **Audit Trail**: Records all authentication events (`USER_REGISTERED`, `LOGIN_SUCCESS`, `LOGIN_FAILED`, `PASSWORD_RESET_SUCCESS`, `ROLE_ASSIGNED`) via `AuditLogRepository`.

### 3.6 REST API Specification (`core/auth/routes.py` & `core/users/routes.py`)
- `POST /api/v1/auth/register`: User account creation
- `POST /api/v1/auth/login`: Issue JWT tokens
- `POST /api/v1/auth/refresh`: Rotate refresh token
- `POST /api/v1/auth/logout`: Revoke token and destroy session
- `POST /api/v1/auth/verify-email`: Confirm email token
- `POST /api/v1/auth/forgot-password`: Send password reset link
- `POST /api/v1/auth/reset-password`: Reset password using token
- `GET /api/v1/auth/oauth/{provider}/authorize`: OAuth redirect link
- `POST /api/v1/auth/oauth/{provider}/callback`: OAuth code exchange
- `GET /api/v1/users/me`: Current user profile
- `PATCH /api/v1/users/me`: Update profile
- `POST /api/v1/users/me/change-password`: Change password
- `GET /api/v1/users/`: Admin list all users
- `PATCH /api/v1/users/{user_id}/role`: Admin assign role

---

## 4. Verification

- **Sprint 2 Test Suite**: `tests/auth/` (**5 test suites, 16 test cases, 100% pass rate**)
- **Full Platform Test Suite**: `pytest evaluation/tests tests/decision_intelligence tests/infrastructure tests/auth` (**59/59 workspace tests passed**)
