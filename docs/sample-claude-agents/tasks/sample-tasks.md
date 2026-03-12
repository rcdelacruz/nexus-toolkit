# Authentication & SSO - Development Tasks

## 📊 Project Overview

- **Total Tasks**: 45
- **Estimated Effort**: 225 hours
- **Priority Distribution**: 32 High, 11 Medium, 2 Low
- **Roles**: Backend (15), Frontend (4), Fullstack (8), DevOps (3), QA (5), Security (10)

## 📋 Task Summary Table

| Task ID  | Summary                                         | Priority | Effort | Role      | Dependencies                                                                                                                                                                                                                                                                                                                                                                                       |
| -------- | ----------------------------------------------- | -------- | ------ | --------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TASK-001 | Configure Google Cloud OAuth Credentials        | High     | 3h     | DevOps    | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-002 | Setup JWT Key Pair (RS256)                      | High     | 2h     | Security  | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-003 | Setup PostgreSQL Custom Tables Connection       | High     | 4h     | Backend   | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-004 | Install Required npm Packages                   | High     | 3h     | DevOps    | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-005 | Create refresh_tokens Table                     | High     | 3h     | Backend   | TASK-003                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-006 | Create activity_logs Table                      | High     | 3h     | Backend   | TASK-003                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-007 | Create Database Migration Runner                | High     | 2h     | Backend   | TASK-005,TASK-006                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-008 | Implement Google OAuth Callback Handler         | High     | 8h     | Backend   | TASK-001,TASK-002,TASK-004                                                                                                                                                                                                                                                                                                                                                                         |
| TASK-009 | Implement JWT Access Token Generation           | High     | 4h     | Backend   | TASK-002,TASK-004                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-010 | Implement JWT Refresh Token Generation          | High     | 5h     | Backend   | TASK-002,TASK-005                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-011 | Implement Token Refresh Endpoint                | High     | 6h     | Backend   | TASK-009,TASK-010                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-012 | Implement Logout Endpoint                       | High     | 3h     | Backend   | TASK-010                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-013 | Implement Activity Logger                       | High     | 4h     | Backend   | TASK-006                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-014 | Implement Domain Validation Middleware          | High     | 3h     | Backend   | TASK-001                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-015 | Implement Token Verification Middleware         | High     | 3h     | Backend   | TASK-009                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-016 | Setup Expo AuthSession for Google OAuth         | High     | 5h     | Frontend  | TASK-001,TASK-004                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-017 | Implement Mobile Sign-In Screen UI              | High     | 4h     | Frontend  | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-018 | Implement Native Secure Token Storage           | High     | 5h     | Frontend  | TASK-004                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-019 | Implement Mobile OAuth Callback Handler         | High     | 5h     | Frontend  | TASK-008,TASK-016,TASK-018                                                                                                                                                                                                                                                                                                                                                                         |
| TASK-020 | Implement Automatic Token Refresh (Mobile)      | High     | 5h     | Frontend  | TASK-011,TASK-018                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-021 | Implement Mobile Logout Functionality           | High     | 4h     | Frontend  | TASK-012,TASK-018                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-022 | Implement Web Sign-In Page UI                   | High     | 3h     | Fullstack | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-023 | Implement Web OAuth Initiation                  | High     | 3h     | Fullstack | TASK-001                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-024 | Implement Web OAuth Callback & Cookie Storage   | High     | 4h     | Fullstack | TASK-008,TASK-023                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-025 | Implement Web Automatic Token Refresh           | High     | 4h     | Fullstack | TASK-011                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-026 | Implement Web Logout Functionality              | High     | 2h     | Fullstack | TASK-012                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-027 | Implement Role-Based Access Control Middleware  | High     | 4h     | Backend   | TASK-015                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-028 | Implement Rate Limiting                         | High     | 4h     | Backend   | TASK-003                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-029 | Implement Security Headers                      | High     | 2h     | Security  | None                                                                                                                                                                                                                                                                                                                                                                                               |
| TASK-030 | Implement Password/Secret Rotation Script       | Medium   | 2h     | DevOps    | TASK-002                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-031 | Write Unit Tests for Authentication Functions   | High     | 6h     | QA        | TASK-008,TASK-009,TASK-010,TASK-011,TASK-012,TASK-013,TASK-014,TASK-015                                                                                                                                                                                                                                                                                                                            |
| TASK-032 | Write Integration Tests for Authentication Flow | Medium   | 8h     | QA        | TASK-008,TASK-009,TASK-010,TASK-011,TASK-012,TASK-013,TASK-014,TASK-015,TASK-016,TASK-017,TASK-018,TASK-019,TASK-020,TASK-021,TASK-022,TASK-023,TASK-024,TASK-025,TASK-026                                                                                                                                                                                                                         |
| TASK-033 | Create Admin Portal Login Page                  | Medium   | 3h     | Fullstack | TASK-022                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-034 | Implement Moderator Role Check                  | Medium   | 4h     | Backend   | TASK-008,TASK-027                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-035 | Implement Admin Portal RBAC Middleware          | Medium   | 3h     | Backend   | TASK-027,TASK-034                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-036 | Implement Moderator Activity Logging            | Medium   | 4h     | Backend   | TASK-013,TASK-034                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-037 | Implement Session Timeout for Moderators        | Low      | 6h     | Backend   | TASK-011                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-038 | Implement Granular Permissions System           | Low      | 8h     | Backend   | TASK-027                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-039 | Implement Multi-Organization Support            | Low      | 16h    | Backend   | TASK-008,TASK-014                                                                                                                                                                                                                                                                                                                                                                                  |
| TASK-040 | Implement Google Workspace Group Sync           | Low      | 8h     | Backend   | TASK-034                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-041 | Implement Device Fingerprinting                 | Low      | 12h    | Security  | TASK-010                                                                                                                                                                                                                                                                                                                                                                                           |
| TASK-042 | Write Security Tests for RBAC                   | Medium   | 4h     | QA        | TASK-027,TASK-034,TASK-035                                                                                                                                                                                                                                                                                                                                                                         |
| TASK-043 | Write Load Tests for Authentication Endpoints   | Medium   | 4h     | QA        | TASK-008,TASK-009,TASK-010,TASK-011,TASK-012                                                                                                                                                                                                                                                                                                                                                       |
| TASK-044 | Conduct Security Audit                          | High     | 16h    | Security  | TASK-001,TASK-002,TASK-003,TASK-004,TASK-005,TASK-006,TASK-007,TASK-008,TASK-009,TASK-010,TASK-011,TASK-012,TASK-013,TASK-014,TASK-015,TASK-016,TASK-017,TASK-018,TASK-019,TASK-020,TASK-021,TASK-022,TASK-023,TASK-024,TASK-025,TASK-026,TASK-027,TASK-028,TASK-029,TASK-030,TASK-031,TASK-032,TASK-033,TASK-034,TASK-035,TASK-036,TASK-037,TASK-038,TASK-039,TASK-040,TASK-041,TASK-042,TASK-043 |
| TASK-045 | Write End-to-End Tests (Cypress/Playwright)     | Medium   | 8h     | QA        | TASK-016,TASK-017,TASK-018,TASK-019,TASK-020,TASK-021,TASK-022,TASK-023,TASK-024,TASK-025,TASK-026                                                                                                                                                                                                                                                                                                 |

---

## 🔧 Phase 1: Project Setup

### TASK-001: Configure Google Cloud OAuth Credentials

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: DevOps
- **Dependencies**: None

**Description:**
Set up Google Cloud Console project and configure OAuth 2.0 credentials for Bili-bili marketplace. Create OAuth client IDs for mobile (iOS/Android) and web applications with proper redirect URIs and scopes.

**Acceptance Criteria:**

- [ ] Google Cloud project created: "bili-bili-marketplace"
- [ ] OAuth consent screen configured (Internal app, @stratpoint.com domain)
- [ ] Web OAuth client ID created with redirect URI
- [ ] iOS OAuth client ID created with bundle ID
- [ ] Android OAuth client ID created with package name
- [ ] OAuth scopes configured: openid, email, profile
- [ ] Client credentials stored in environment variables

**Technical Notes:**

- Use Google Cloud Console: https://console.cloud.google.com
- Enable Google+ API for profile data
- Configure authorized domains

---

### TASK-002: Setup JWT Key Pair (RS256)

- **Priority**: High ⚡
- **Effort**: 2 hours
- **Role**: Security
- **Dependencies**: None

**Description:**
Generate RSA key pair for JWT signing using RS256 algorithm. Store private key securely in AWS Secrets Manager (production) and local .env (development).

**Acceptance Criteria:**

- [ ] RSA key pair generated (2048-bit minimum)
- [ ] Private key stored in AWS Secrets Manager
- [ ] Public key stored in environment variables
- [ ] Key rotation script created
- [ ] Documentation added for key rotation process

**Technical Notes:**

- Use openssl to generate keys
- Private key NEVER exposed in code or environment variables
- Public key can be in .env (needed for token verification)

---

### TASK-003: Setup PostgreSQL Custom Tables Connection

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: None

**Description:**
Configure PostgreSQL connection for custom authentication tables (separate from Saleor database). Set up connection pooling and environment configuration for refresh_tokens and activity_logs tables.

**Acceptance Criteria:**

- [ ] PostgreSQL database created or Supabase project configured
- [ ] Database connection string configured in .env
- [ ] Connection pooling configured (max 10 connections)
- [ ] SSL/TLS enabled for database connections
- [ ] Database user created with minimal privileges
- [ ] Connection tested from Next.js API route

**Technical Notes:**

- Use pg (node-postgres) library for connection
- Consider using Supabase for managed PostgreSQL
- Enable SSL mode: ?sslmode=require

---

### TASK-004: Install Required npm Packages

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: DevOps
- **Dependencies**: None

**Description:**
Install and configure all required npm packages for authentication: OAuth libraries, JWT libraries, secure storage (mobile), and testing utilities.

**Acceptance Criteria:**

- [ ] Backend packages installed (google-auth-library, jsonwebtoken, pg, bcryptjs)
- [ ] Mobile packages installed (expo-auth-session, expo-secure-store, @apollo/client)
- [ ] TypeScript types installed for all packages
- [ ] Package versions locked in package-lock.json
- [ ] Security audit completed with npm audit

**Technical Notes:**

- Pin major versions to avoid breaking changes
- Review security advisories
- Document why each package is needed

---

## ⚙️ Phase 2: Database Schema

### TASK-005: Create refresh_tokens Table

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-003

**Description:**
Create refresh_tokens table to store hashed refresh tokens with family ID for rotation detection. Includes indexes for performance and security.

**Acceptance Criteria:**

- [ ] Migration file created with table structure
- [ ] Table includes all required fields (id, user_id, token_hash, family_id, expires_at, etc.)
- [ ] Indexes created on user_id, token_hash, family_id, expires_at
- [ ] Foreign key constraint to Saleor users.id with CASCADE delete
- [ ] Rollback migration created
- [ ] Migration tested on development database

**Technical Notes:**

- Token hash uses SHA-256 (not bcrypt)
- Family ID enables detection of token reuse attacks
- Expires_at index for efficient cleanup queries

---

### TASK-006: Create activity_logs Table

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-003

**Description:**
Create activity_logs table to track all authentication and user actions for audit trail. Supports security monitoring and compliance.

**Acceptance Criteria:**

- [ ] Migration file created with table structure
- [ ] Table includes all required fields (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at)
- [ ] Indexes created on user_id, created_at, action
- [ ] Composite index on (resource_type, resource_id)
- [ ] Foreign key constraint to Saleor users.id
- [ ] Rollback migration created
- [ ] Partitioning strategy documented

**Technical Notes:**

- JSONB column for flexible metadata storage
- IP address field supports both IPv4 and IPv6
- Retention policy: 1 year minimum

---

### TASK-007: Create Database Migration Runner

- **Priority**: High ⚡
- **Effort**: 2 hours
- **Role**: Backend
- **Dependencies**: TASK-005,TASK-006

**Description:**
Create migration script to apply database schema changes consistently across environments (local, staging, production).

**Acceptance Criteria:**

- [ ] Migration runner script created
- [ ] Supports dry-run mode
- [ ] Tracks applied migrations in schema_migrations table
- [ ] Prevents duplicate migration execution
- [ ] Rollback support for failed migrations
- [ ] Logging of all migration activity
- [ ] Environment-specific configuration

**Technical Notes:**

- Use node-pg-migrate or custom script
- Store migration history in database
- Validate migration checksums

---

## 💻 Phase 3: Backend OAuth & Token Management

### TASK-008: Implement Google OAuth Callback Handler

- **Priority**: High ⚡
- **Effort**: 8 hours
- **Role**: Backend
- **Dependencies**: TASK-001,TASK-002,TASK-004

**Description:**
Create Next.js API route to handle Google OAuth callback, exchange authorization code for ID token, verify email domain, and create/authenticate user in Saleor.

**Acceptance Criteria:**

- [ ] API route created for OAuth callback
- [ ] Accepts OAuth authorization code from query params
- [ ] Exchanges code for Google ID token (server-side)
- [ ] Verifies ID token signature using google-auth-library
- [ ] Validates email domain is @stratpoint.com
- [ ] Rejects non-organizational Google accounts
- [ ] Queries Saleor GraphQL for existing user by email
- [ ] Creates new user in Saleor if first login with default role Employee
- [ ] Extracts metadata: name, email, profile photo
- [ ] Issues JWT access token and refresh token
- [ ] Returns tokens to client (web: cookies, mobile: JSON)
- [ ] Error handling for OAuth failures, domain mismatch, Saleor errors
- [ ] Logs authentication event to activity_logs

**Technical Notes:**

- Use OAuth2Client from google-auth-library
- Verify ID token audience matches client ID
- Handle both web and mobile callback flows
- Set appropriate cookie flags for web

---

### TASK-009: Implement JWT Access Token Generation

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-002,TASK-004

**Description:**
Create function to generate JWT access tokens with RS256 signing, custom claims (user_id, email, role), and 1-hour expiry.

**Acceptance Criteria:**

- [ ] Function created: generateAccessToken(user)
- [ ] Uses RS256 algorithm (asymmetric signing)
- [ ] Private key loaded from AWS Secrets Manager (production) or .env (dev)
- [ ] Token payload includes userId, email, role, iat, exp
- [ ] Token expiry configurable via environment variable (default: 3600 seconds)
- [ ] Error handling for key loading failures
- [ ] Unit tests for token generation and verification

**Technical Notes:**

- Use jsonwebtoken library
- Load private key asynchronously
- Cache private key in memory
- Token size should be < 1KB

---

### TASK-010: Implement JWT Refresh Token Generation

- **Priority**: High ⚡
- **Effort**: 5 hours
- **Role**: Backend
- **Dependencies**: TASK-002,TASK-005

**Description:**
Create function to generate refresh tokens, hash them with SHA-256, store in database with family ID for rotation tracking.

**Acceptance Criteria:**

- [ ] Function created: generateRefreshToken(userId)
- [ ] Generates cryptographically secure random token (32 bytes, base64 encoded)
- [ ] Hashes token with SHA-256 before database storage
- [ ] Creates new family ID (UUID) for token family tracking
- [ ] Stores in refresh_tokens table with user_id, token_hash, family_id, expires_at
- [ ] Returns unhashed token to caller
- [ ] Token expiry configurable (default: 2592000 seconds / 30 days)
- [ ] Cleanup function to delete expired tokens

**Technical Notes:**

- Use crypto.randomBytes(32) for token generation
- Hash with crypto.createHash('sha256')
- Never log unhashed tokens
- Family ID is crucial for detecting token reuse attacks

---

### TASK-011: Implement Token Refresh Endpoint

- **Priority**: High ⚡
- **Effort**: 6 hours
- **Role**: Backend
- **Dependencies**: TASK-009,TASK-010

**Description:**
Create API endpoint to refresh expired access tokens using valid refresh token. Implements token rotation to prevent reuse attacks.

**Acceptance Criteria:**

- [ ] API route created for token refresh
- [ ] Accepts refresh token from request body (mobile) or cookies (web)
- [ ] Hashes incoming token and looks up in database
- [ ] Validates token exists, not expired, not revoked
- [ ] Detects token reuse and revokes entire family if detected
- [ ] Issues new access token
- [ ] Rotates refresh token (generate new, revoke old)
- [ ] Rate limiting: max 10 refreshes/minute per user
- [ ] Updates last_used_at timestamp
- [ ] Logs token refresh event to activity_logs

**Technical Notes:**

- Token rotation is critical security feature
- Reuse detection prevents replay attacks
- Use database transaction for atomicity

---

### TASK-012: Implement Logout Endpoint

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-010

**Description:**
Create API endpoint to invalidate user session by revoking refresh token. Supports single-device and all-device logout.

**Acceptance Criteria:**

- [ ] API route created for logout
- [ ] Accepts refresh token from request body or cookies
- [ ] Revokes specific refresh token (set revoked = TRUE, revoked_at = NOW())
- [ ] Supports "logout all devices" mode (revokes all tokens for user_id)
- [ ] Clears HttpOnly cookies (web clients)
- [ ] Returns success response
- [ ] Logs logout event to activity_logs
- [ ] Handles case where token already revoked (idempotent)

**Technical Notes:**

- Access tokens cannot be revoked (short-lived by design)
- Client must delete access token from storage immediately

---

### TASK-013: Implement Activity Logger

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-006

**Description:**
Create reusable utility to log all authentication events and user actions to activity_logs table. Supports audit trail and security monitoring.

**Acceptance Criteria:**

- [ ] Function created: logActivity(userId, action, metadata)
- [ ] Inserts record into activity_logs table
- [ ] Extracts IP from X-Forwarded-For header (supports proxies)
- [ ] Handles both IPv4 and IPv6 addresses
- [ ] Non-blocking (async, doesn't slow down requests)
- [ ] Error handling (log failures don't break main flow)
- [ ] Middleware integration for automatic logging

**Technical Notes:**

- Use for all authentication endpoints
- Consider using message queue for high volume (Phase 2)

---

### TASK-014: Implement Domain Validation Middleware

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-001

**Description:**
Create middleware to validate that Google Workspace email belongs to organization domain (@stratpoint.com). Prevents unauthorized access from personal Gmail accounts.

**Acceptance Criteria:**

- [ ] Function created: validateEmailDomain(email)
- [ ] Checks if email ends with @stratpoint.com
- [ ] Configurable domain via environment variable
- [ ] Returns boolean: true if valid, false if invalid
- [ ] Case-insensitive comparison
- [ ] Logs rejected domain attempts to activity_logs
- [ ] Unit tests for various email formats

**Technical Notes:**

- Simple string suffix check is sufficient for MVP
- Phase 2: Consider Google Workspace Admin SDK

---

### TASK-015: Implement Token Verification Middleware

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-009

**Description:**
Create middleware to verify JWT access token on protected API routes. Extracts user info from token and attaches to request object.

**Acceptance Criteria:**

- [ ] Middleware created: verifyAccessToken(req)
- [ ] Extracts token from Authorization: Bearer header (mobile) or cookies (web)
- [ ] Verifies token signature using public key (RS256)
- [ ] Validates token expiry (exp claim)
- [ ] Extracts user info from payload: userId, email, role
- [ ] Attaches user info to request object: req.user
- [ ] Returns 401 Unauthorized if token invalid, expired, or missing
- [ ] Returns 403 Forbidden if token valid but user lacks required role
- [ ] Handles malformed tokens gracefully
- [ ] Logs failed verification attempts

**Technical Notes:**

- Use jwt.verify(token, publicKey, { algorithms: ['RS256'] })
- Public key can be cached
- Middleware should be applied to all protected routes

---

## 📱 Phase 4: Mobile Integration

### TASK-016: Setup Expo AuthSession for Google OAuth

- **Priority**: High ⚡
- **Effort**: 5 hours
- **Role**: Frontend
- **Dependencies**: TASK-001,TASK-004

**Description:**
Configure Expo AuthSession to handle Google OAuth flow in React Native app. Supports deep linking for OAuth callback.

**Acceptance Criteria:**

- [ ] expo-auth-session package installed
- [ ] Deep link scheme configured
- [ ] OAuth configuration created with clientId, redirectUri, scopes
- [ ] app.json updated with deep link scheme
- [ ] iOS: URL scheme added to Info.plist
- [ ] Android: Intent filter added to AndroidManifest.xml
- [ ] Deep link tested on physical device
- [ ] Handles OAuth consent screen redirection
- [ ] Handles OAuth callback with authorization code

**Technical Notes:**

- Use AuthSession.useAuthRequest() hook
- Discovery document: Google's OpenID configuration
- Test deep linking with npx uri-scheme

---

### TASK-017: Implement Mobile Sign-In Screen UI

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Frontend
- **Dependencies**: None

**Description:**
Create sign-in screen with "Sign in with Google" button following Google Brand Guidelines. Accessible and responsive design.

**Acceptance Criteria:**

- [ ] Screen created with Sign in with Google button
- [ ] Google logo icon on button
- [ ] Colors follow Google Brand Guidelines (#4285F4 background, white text)
- [ ] Minimum touch target: 44x44 pts (iOS), 48x48 dp (Android)
- [ ] Welcome message and subtitle displayed
- [ ] Terms & Privacy links below button
- [ ] Loading state while OAuth in progress
- [ ] Error state for OAuth failures (alert dialog)
- [ ] Accessibility labels for screen readers
- [ ] Responsive layout (works on small and large screens)

**Technical Notes:**

- Use React Native Paper or NativeWind for styling
- Test with VoiceOver (iOS) and TalkBack (Android)

---

### TASK-018: Implement Native Secure Token Storage

- **Priority**: High ⚡
- **Effort**: 5 hours
- **Role**: Frontend
- **Dependencies**: TASK-004

**Description:**
Integrate iOS Keychain and Android Keystore for secure token storage. Never store tokens in plain AsyncStorage.

**Acceptance Criteria:**

- [ ] expo-secure-store package installed and configured
- [ ] Functions created: storeTokens, getAccessToken, getRefreshToken, clearTokens
- [ ] iOS: Tokens stored in Keychain
- [ ] Android: Tokens stored in Android Keystore
- [ ] Tokens NEVER stored in AsyncStorage or any plain text storage
- [ ] Error handling for storage failures
- [ ] Biometric protection option (optional for MVP)

**Technical Notes:**

- Use SecureStore.setItemAsync() and SecureStore.getItemAsync()
- iOS Keychain is encrypted by default
- Android Keystore requires device PIN/pattern/fingerprint
- Test on physical devices

---

### TASK-019: Implement Mobile OAuth Callback Handler

- **Priority**: High ⚡
- **Effort**: 5 hours
- **Role**: Frontend
- **Dependencies**: TASK-008,TASK-016,TASK-018

**Description:**
Handle deep link callback from Google OAuth, exchange authorization code for tokens via Next.js API, store tokens securely, and navigate to home screen.

**Acceptance Criteria:**

- [ ] Deep link listener registered
- [ ] Extracts authorization code from deep link URL
- [ ] Calls Next.js API with code
- [ ] Receives access token and refresh token from API
- [ ] Stores tokens using secure storage
- [ ] Navigates to Home screen on success
- [ ] Shows error alert for wrong email domain, OAuth failure, network error, API error
- [ ] Logs authentication event
- [ ] Cleans up deep link listener on unmount

**Technical Notes:**

- Handle both success and error callbacks
- Parse deep link URL format
- Test with manual deep link triggering

---

### TASK-020: Implement Automatic Token Refresh (Mobile)

- **Priority**: High ⚡
- **Effort**: 5 hours
- **Role**: Frontend
- **Dependencies**: TASK-011,TASK-018

**Description:**
Automatically refresh access token when API returns 401 Unauthorized. Transparent to user - no re-login required.

**Acceptance Criteria:**

- [ ] Axios/Fetch interceptor created to detect 401 responses
- [ ] On 401: pause failed request, retrieve refresh token, call refresh API
- [ ] Receive new tokens and update secure storage
- [ ] Retry original request with new access token
- [ ] If refresh fails: clear tokens, navigate to login, show session expired message
- [ ] Handles concurrent requests (only one refresh at a time)
- [ ] Rate limiting: respects API rate limits
- [ ] Logs token refresh events

**Technical Notes:**

- Use Axios interceptors or custom Fetch wrapper
- Queue concurrent requests during token refresh

---

### TASK-021: Implement Mobile Logout Functionality

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Frontend
- **Dependencies**: TASK-012,TASK-018

**Description:**
Allow user to log out from profile screen. Clears tokens, calls logout API, and navigates to login screen.

**Acceptance Criteria:**

- [ ] Logout button added to Profile screen
- [ ] Confirmation dialog: "Are you sure you want to log out?"
- [ ] On confirm: retrieve refresh token, call logout API, clear tokens, clear Apollo Client cache, clear AsyncStorage, navigate to Login
- [ ] Handles network errors gracefully (still logs out locally)
- [ ] Shows success toast: "You have been logged out"
- [ ] Prevents back navigation to protected screens after logout

**Technical Notes:**

- Always clear local tokens even if API call fails
- Reset navigation stack to prevent back button issues

---

## 🌐 Phase 5: Web Integration

### TASK-022: Implement Web Sign-In Page UI

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Fullstack
- **Dependencies**: None

**Description:**
Create sign-in page for web application with "Sign in with Google" button. Responsive design for desktop and tablet.

**Acceptance Criteria:**

- [ ] Page created with centered card layout
- [ ] Bili-bili logo displayed
- [ ] Title: "Welcome to Bili-bili Marketplace"
- [ ] Subtitle: "Sign in with your company Google account"
- [ ] Sign in with Google button (Google Brand Guidelines)
- [ ] Terms & Privacy links in footer
- [ ] Button click initiates OAuth flow
- [ ] Loading state during redirect
- [ ] Error message display from URL params
- [ ] Responsive design (mobile, tablet, desktop)
- [ ] Accessibility: keyboard navigation, ARIA labels

**Technical Notes:**

- Use Tailwind CSS and Shadcn/ui components
- Server-side redirect to Google OAuth URL

---

### TASK-023: Implement Web OAuth Initiation

- **Priority**: High ⚡
- **Effort**: 3 hours
- **Role**: Fullstack
- **Dependencies**: TASK-001

**Description:**
Create server action or API route to initiate Google OAuth flow from web app. Generates OAuth URL and redirects user to Google consent screen.

**Acceptance Criteria:**

- [ ] Server action created to initiate OAuth
- [ ] Generates Google OAuth URL with client_id, redirect_uri, response_type, scope, state
- [ ] Redirects user to generated OAuth URL
- [ ] State parameter stored in secure cookie (HttpOnly)
- [ ] Validates state parameter on callback (prevents CSRF)

**Technical Notes:**

- Use google-auth-library to generate URL
- State token prevents CSRF attacks
- Store state in session or encrypted cookie

---

### TASK-024: Implement Web OAuth Callback & Cookie Storage

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Fullstack
- **Dependencies**: TASK-008,TASK-023

**Description:**
Handle OAuth callback on web app, receive tokens from backend API, store in HttpOnly cookies, and redirect to dashboard.

**Acceptance Criteria:**

- [ ] OAuth callback reuses backend API route
- [ ] Validates state parameter (CSRF protection)
- [ ] Receives access token and refresh token from callback handler
- [ ] Sets HttpOnly cookies with proper flags (Secure, SameSite=Lax)
- [ ] Cookies NOT accessible to JavaScript (XSS protection)
- [ ] Redirects to /dashboard on success
- [ ] Redirects to /login?error=<error_code> on failure
- [ ] Handles domain mismatch error specifically

**Technical Notes:**

- HttpOnly cookies prevent XSS attacks
- Secure flag requires HTTPS (production)
- SameSite=Lax prevents CSRF while allowing navigation

---

### TASK-025: Implement Web Automatic Token Refresh

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Fullstack
- **Dependencies**: TASK-011

**Description:**
Automatically refresh access token when it expires during user session. Server-side middleware detects expiry and refreshes transparently.

**Acceptance Criteria:**

- [ ] Middleware created (Next.js middleware)
- [ ] On protected route request: read access token from cookies, verify token
- [ ] If expired: read refresh token, call refresh endpoint internally, update cookies, continue to protected route
- [ ] If refresh token expired: clear cookies, redirect to /login?session_expired=true
- [ ] Middleware applied to protected routes
- [ ] No client-side JavaScript required (fully server-side)

**Technical Notes:**

- Next.js middleware runs on Edge Runtime (fast)
- Use NextResponse.next() to continue request
- Use NextResponse.redirect() for login redirect

---

### TASK-026: Implement Web Logout Functionality

- **Priority**: High ⚡
- **Effort**: 2 hours
- **Role**: Fullstack
- **Dependencies**: TASK-012

**Description:**
Allow user to log out from web app. Clears HttpOnly cookies, calls logout API, and redirects to login page.

**Acceptance Criteria:**

- [ ] Logout button added to header/navigation
- [ ] Server action created for logout
- [ ] On logout: read refresh token from cookies, call logout API, clear cookies, redirect to /login
- [ ] Success message: "You have been logged out successfully"
- [ ] Handles API errors gracefully (always clears cookies)

**Technical Notes:**

- Use server action for logout (no client-side API call needed)
- Clear cookies with response.cookies.delete()

---

## 🔒 Phase 6: Security & RBAC

### TASK-027: Implement Role-Based Access Control Middleware

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-015

**Description:**
Create middleware to enforce role-based permissions on API routes. Employees can only access marketplace endpoints, moderators can access admin endpoints.

**Acceptance Criteria:**

- [ ] Middleware created: requireRole(allowedRoles)
- [ ] Extracts user role from JWT token
- [ ] Checks if user role is in allowed roles array
- [ ] Returns 403 Forbidden if role not allowed
- [ ] Applied to protected routes (Employee and Moderator routes)
- [ ] Logs unauthorized access attempts
- [ ] Unit tests for role enforcement

**Technical Notes:**

- Composable middleware
- Role claim is in JWT payload (no database lookup needed)
- Default role for all users: Employee

---

### TASK-028: Implement Rate Limiting

- **Priority**: High ⚡
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-003

**Description:**
Implement rate limiting on authentication endpoints to prevent brute force attacks and token abuse.

**Acceptance Criteria:**

- [ ] Rate limiter middleware created using rate-limiter-flexible library
- [ ] Redis or in-memory store for rate limit tracking
- [ ] Limits configured for OAuth callback, refresh, logout, and all API routes
- [ ] Returns 429 Too Many Requests when limit exceeded
- [ ] Response headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
- [ ] Configurable via environment variables
- [ ] Logs rate limit violations

**Technical Notes:**

- Use rate-limiter-flexible with Redis backend (production) or in-memory (dev)
- Track by IP address for auth endpoints
- Track by user ID for refresh/logout

---

### TASK-029: Implement Security Headers

- **Priority**: High ⚡
- **Effort**: 2 hours
- **Role**: Security
- **Dependencies**: None

**Description:**
Configure security headers on all Next.js responses to protect against common web vulnerabilities (XSS, clickjacking, etc.).

**Acceptance Criteria:**

- [ ] Security headers configured (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, CSP)
- [ ] Headers applied to all routes (API and pages)
- [ ] Verified with security scan tool

**Technical Notes:**

- Use Next.js headers() configuration in next.config.js
- CSP policy should allow Google OAuth domains
- Test in production environment

---

### TASK-030: Implement Password/Secret Rotation Script

- **Priority**: Medium ⚙️
- **Effort**: 2 hours
- **Role**: DevOps
- **Dependencies**: TASK-002

**Description:**
Create script to rotate JWT signing keys and other secrets quarterly. Ensures old keys are phased out gracefully without downtime.

**Acceptance Criteria:**

- [ ] Script created for key rotation
- [ ] Supports graceful rotation workflow
- [ ] Updates AWS Secrets Manager with new private key
- [ ] Documentation for manual rotation process
- [ ] Tested in staging environment

**Technical Notes:**

- Graceful rotation: verify with both old and new keys during transition
- Schedule: Quarterly (every 3 months)

---

## 🧪 Phase 7: Testing (MVP)

### TASK-031: Write Unit Tests for Authentication Functions

- **Priority**: High ⚡
- **Effort**: 6 hours
- **Role**: QA
- **Dependencies**: TASK-008,TASK-009,TASK-010,TASK-011,TASK-012,TASK-013,TASK-014,TASK-015

**Description:**
Comprehensive unit tests for all authentication functions: token generation, verification, domain validation, OAuth callback logic.

**Acceptance Criteria:**

- [ ] Test files created for all auth modules
- [ ] Test coverage > 90% for auth modules
- [ ] Tests cover successful token generation, token expiry, invalid tokens, domain validation, OAuth callbacks, RBAC
- [ ] Mock external dependencies (Google OAuth, Saleor GraphQL)
- [ ] Run in CI/CD pipeline

**Technical Notes:**

- Use Jest for testing framework
- Mock google-auth-library with jest.mock()
- Test edge cases

---

### TASK-032: Write Integration Tests for Authentication Flow

- **Priority**: Medium ⚙️
- **Effort**: 8 hours
- **Role**: QA
- **Dependencies**: TASK-008,TASK-009,TASK-010,TASK-011,TASK-012,TASK-013,TASK-014,TASK-015,TASK-016,TASK-017,TASK-018,TASK-019,TASK-020,TASK-021,TASK-022,TASK-023,TASK-024,TASK-025,TASK-026

**Description:**
End-to-end integration tests for complete authentication flows: sign-in, token refresh, logout. Tests entire flow from OAuth to token storage.

**Acceptance Criteria:**

- [ ] Integration test suite created
- [ ] Tests cover Web Sign-In Flow, Mobile Sign-In Flow, Token Refresh Flow, Logout Flow
- [ ] Uses test database (not production)
- [ ] Cleans up test data after each test
- [ ] Run in CI/CD pipeline

**Technical Notes:**

- Use Supertest for API testing
- Mock Google OAuth responses
- Use test Saleor instance or mock GraphQL

---

## 👑 Phase 8: Admin Portal (Phase 2)

### TASK-033: Create Admin Portal Login Page

- **Priority**: Medium ⚙️
- **Effort**: 3 hours
- **Role**: Fullstack
- **Dependencies**: TASK-022

**Description:**
Create dedicated login page for admin portal with clear messaging that it's for moderators/HR only.

**Acceptance Criteria:**

- [ ] Page created for admin login
- [ ] Title: "Bili-bili Moderator Portal"
- [ ] Subtitle: "For HR and Admin use only"
- [ ] Sign in with Google button
- [ ] Warning: "Unauthorized access is prohibited"
- [ ] Link to marketplace for regular employees
- [ ] Same OAuth flow as employee login
- [ ] Responsive design

**Technical Notes:**

- Reuse OAuth callback handler
- Add branding to differentiate from employee login

---

### TASK-034: Implement Moderator Role Check

- **Priority**: Medium ⚙️
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-008,TASK-027

**Description:**
After OAuth callback, check if user has 'Moderator' role in Saleor metadata. Grant access to admin portal only if moderator.

**Acceptance Criteria:**

- [ ] OAuth callback checks user role after authentication
- [ ] If role is Moderator: issue admin JWT token, set cookies, redirect to admin dashboard
- [ ] If role is Employee: deny access, redirect to access denied page, log attempt
- [ ] Access denied page shows appropriate message and link to return to marketplace
- [ ] Logs all moderator authentication events

**Technical Notes:**

- Role stored in Saleor user metadata
- Manual role assignment via Saleor admin dashboard (Phase 1)

---

### TASK-035: Implement Admin Portal RBAC Middleware

- **Priority**: Medium ⚙️
- **Effort**: 3 hours
- **Role**: Backend
- **Dependencies**: TASK-027,TASK-034

**Description:**
Apply RBAC middleware to all admin portal API routes. Ensure only moderators can access moderation endpoints.

**Acceptance Criteria:**

- [ ] Middleware applied to admin routes (moderation, reports, analytics)
- [ ] Returns 403 Forbidden if user role is not Moderator
- [ ] Logs unauthorized access attempts
- [ ] Unit tests for admin route protection

**Technical Notes:**

- Reuse requireRole() middleware
- Apply to all admin API routes consistently

---

### TASK-036: Implement Moderator Activity Logging

- **Priority**: Medium ⚙️
- **Effort**: 4 hours
- **Role**: Backend
- **Dependencies**: TASK-013,TASK-034

**Description:**
Enhanced activity logging for all moderator actions. Logs include action type, resource affected, moderator ID, timestamp, IP address.

**Acceptance Criteria:**

- [ ] All moderator actions logged to activity_logs
- [ ] Logs include user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at
- [ ] Activity logs viewable in admin portal (Phase 2 feature)
- [ ] Retention: 1 year minimum (compliance)

**Technical Notes:**

- Extend logActivity() function
- Consider separate table for moderator actions (Phase 2+)

---

### TASK-037: Implement Session Timeout for Moderators

- **Priority**: Low 📝
- **Effort**: 6 hours
- **Role**: Backend
- **Dependencies**: TASK-011

**Description:**
Optional: Shorter session timeout for moderators (e.g., 1 day instead of 30 days) for enhanced security.

**Acceptance Criteria:**

- [ ] Configurable session timeout per role (Employee: 30 days, Moderator: 1 day)
- [ ] Refresh token expiry based on user role
- [ ] Moderator warned before session expires
- [ ] Automatic logout after timeout
- [ ] Re-authentication required after timeout

**Technical Notes:**

- Decision needed: Same timeout vs. different timeout
- Recommendation: Same timeout for Phase 1

---

## 🔐 Phase 9: Advanced Security (Phase 2)

### TASK-038: Implement Granular Permissions System

- **Priority**: Low 📝
- **Effort**: 8 hours
- **Role**: Backend
- **Dependencies**: TASK-027

**Description:**
Phase 2+: Implement granular permissions beyond basic Employee/Moderator roles. Allows fine-grained control.

**Acceptance Criteria:**

- [ ] Permissions table created
- [ ] Role-permissions junction table created
- [ ] Predefined permissions defined
- [ ] Middleware updated to check permissions (not just roles)
- [ ] Admin UI to assign permissions to roles

**Technical Notes:**

- Significant enhancement (Phase 2+)
- Requires database schema changes

---

### TASK-039: Implement Multi-Organization Support

- **Priority**: Low 📝
- **Effort**: 16 hours
- **Role**: Backend
- **Dependencies**: TASK-008,TASK-014

**Description:**
Phase 2+: Support multiple organizations (multi-tenancy). Each organization has its own Google Workspace domain and isolated data.

**Acceptance Criteria:**

- [ ] Organizations table created
- [ ] User-organization relationship established
- [ ] Domain validation updated for multiple domains
- [ ] Data isolation enforced
- [ ] Organization-specific branding and configuration
- [ ] Tenant-aware authentication flow

**Technical Notes:**

- Major architectural change (not recommended for MVP)
- Requires row-level security across all tables

---

### TASK-040: Implement Google Workspace Group Sync

- **Priority**: Low 📝
- **Effort**: 8 hours
- **Role**: Backend
- **Dependencies**: TASK-034

**Description:**
Phase 2+: Automatically assign moderator role based on Google Workspace group membership.

**Acceptance Criteria:**

- [ ] Google Workspace Admin SDK integrated
- [ ] Cron job to sync group membership daily
- [ ] Users in Moderators group automatically get Moderator role
- [ ] Users removed from group automatically lose Moderator role
- [ ] Manual override option
- [ ] Audit log of role changes

**Technical Notes:**

- Requires Google Workspace Admin API access
- Requires domain-wide delegation

---

### TASK-041: Implement Device Fingerprinting

- **Priority**: Low 📝
- **Effort**: 12 hours
- **Role**: Security
- **Dependencies**: TASK-010

**Description:**
Phase 2+: Track device fingerprints for each refresh token. Detect suspicious login activity.

**Acceptance Criteria:**

- [ ] Device fingerprint captured on login
- [ ] Stored with refresh token in database
- [ ] Alert user when new device detected
- [ ] User can view active sessions and revoke devices
- [ ] Suspicious activity detection

**Technical Notes:**

- Use library like FingerprintJS
- Privacy consideration: Inform users about device tracking
- GDPR compliance required

---

## ✅ Phase 10: Final Testing & Audit

### TASK-042: Write Security Tests for RBAC

- **Priority**: Medium ⚙️
- **Effort**: 4 hours
- **Role**: QA
- **Dependencies**: TASK-027,TASK-034,TASK-035

**Description:**
Security-focused tests to ensure RBAC is properly enforced. Tests attempt to bypass role checks and access restricted resources.

**Acceptance Criteria:**

- [ ] Test suite created for RBAC security
- [ ] Tests cover unauthorized access attempts, expired tokens, tampered tokens, missing role claims, role escalation
- [ ] All tests pass (no security vulnerabilities)

**Technical Notes:**

- Test negative cases
- Simulate common attack vectors

---

### TASK-043: Write Load Tests for Authentication Endpoints

- **Priority**: Medium ⚙️
- **Effort**: 4 hours
- **Role**: QA
- **Dependencies**: TASK-008,TASK-009,TASK-010,TASK-011,TASK-012

**Description:**
Load testing to ensure authentication endpoints can handle high concurrency (1,000 concurrent logins). Validates rate limiting effectiveness.

**Acceptance Criteria:**

- [ ] Load test script created using k6 or Artillery
- [ ] Test scenarios: 1,000 concurrent logins, token refresh storm, rate limit validation
- [ ] Performance targets met: OAuth callback < 3s (P95), Token refresh < 200ms (P95), Login success rate > 95%
- [ ] Database connection pool not exhausted
- [ ] No server crashes under load

**Technical Notes:**

- Run against staging environment
- Use test Google OAuth credentials

---

### TASK-044: Conduct Security Audit

- **Priority**: High ⚡
- **Effort**: 16 hours
- **Role**: Security
- **Dependencies**: All tasks

**Description:**
Comprehensive security audit of authentication system before production launch. External or internal security review.

**Acceptance Criteria:**

- [ ] Security checklist completed
- [ ] Code review by security expert
- [ ] Penetration testing completed
- [ ] Vulnerability scan with automated tools
- [ ] All critical vulnerabilities fixed before production
- [ ] Security audit report documented

**Technical Notes:**

- Schedule before production deployment
- Consider hiring external security firm

---

### TASK-045: Write End-to-End Tests (Cypress/Playwright)

- **Priority**: Medium ⚙️
- **Effort**: 8 hours
- **Role**: QA
- **Dependencies**: TASK-016,TASK-017,TASK-018,TASK-019,TASK-020,TASK-021,TASK-022,TASK-023,TASK-024,TASK-025,TASK-026

**Description:**
End-to-end tests using Cypress or Playwright to simulate real user authentication flows in browser and mobile app.

**Acceptance Criteria:**

- [ ] E2E test suite created for web (Cypress)
- [ ] E2E test suite created for mobile (Detox)
- [ ] Tests cover web and mobile authentication flows
- [ ] All tests pass on CI/CD pipeline
- [ ] Screenshots captured for failures

**Technical Notes:**

- Mock Google OAuth responses
- Use test user accounts
- Run in headless mode for CI/CD

---

## 📈 Progress Tracking

- [ ] Phase 1: Project Setup (0/4 tasks)
- [ ] Phase 2: Database Schema (0/3 tasks)
- [ ] Phase 3: Backend OAuth & Token Management (0/8 tasks)
- [ ] Phase 4: Mobile Integration (0/6 tasks)
- [ ] Phase 5: Web Integration (0/5 tasks)
- [ ] Phase 6: Security & RBAC (0/4 tasks)
- [ ] Phase 7: Testing (MVP) (0/2 tasks)
- [ ] Phase 8: Admin Portal (Phase 2) (0/5 tasks)
- [ ] Phase 9: Advanced Security (Phase 2) (0/4 tasks)
- [ ] Phase 10: Final Testing & Audit (0/4 tasks)

---

## 🗓️ Dependency Graph

```
Project Setup:
TASK-001 → TASK-008, TASK-014, TASK-016, TASK-023
TASK-002 → TASK-008, TASK-009, TASK-010, TASK-030
TASK-003 → TASK-005, TASK-006, TASK-028
TASK-004 → TASK-008, TASK-009, TASK-016, TASK-018

Database:
TASK-005 → TASK-007, TASK-010
TASK-006 → TASK-007, TASK-013

Backend OAuth:
TASK-008 → TASK-019, TASK-024, TASK-034
TASK-009 → TASK-011, TASK-015
TASK-010 → TASK-011, TASK-012, TASK-041
TASK-011 → TASK-020, TASK-025, TASK-037
TASK-015 → TASK-027

Mobile:
TASK-016 → TASK-019
TASK-018 → TASK-019, TASK-020, TASK-021

Web:
TASK-023 → TASK-024
TASK-024 → TASK-033

Security & RBAC:
TASK-027 → TASK-034, TASK-035, TASK-038

Testing:
All auth tasks → TASK-031, TASK-032, TASK-042, TASK-043, TASK-044, TASK-045
```

---

_Generated by task-planner agent | 2026-01-11_
