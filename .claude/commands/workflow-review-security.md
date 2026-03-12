---
description: Comprehensive security audit focusing on OWASP Top 10 and authentication
---

You are in **SECURITY REVIEW MODE**.

Use **security** agent to perform thorough security audit.

## Security Audit Process

### 1. OWASP Top 10 Review (30 mins)

#### A01: Broken Access Control

```typescript
// ❌ CRITICAL: No authorization check
export async function deletePost(id: string) {
  await db.post.delete({ where: { id } })
}

// ✅ SECURE: Proper authorization
export async function deletePost(id: string) {
  const session = await auth()
  if (!session?.user) {
    throw new UnauthorizedError()
  }

  const post = await db.post.findUnique({
    where: { id },
    select: { authorId: true },
  })

  if (!post) {
    throw new NotFoundError()
  }

  if (post.authorId !== session.user.id && session.user.role !== 'ADMIN') {
    throw new ForbiddenError()
  }

  await db.post.delete({ where: { id } })
}
```

**Checklist:**

- [ ] All protected routes check authentication
- [ ] Resource ownership verified before operations
- [ ] Role-based access control (RBAC) implemented
- [ ] No client-side authorization only
- [ ] API endpoints protected with middleware

#### A02: Cryptographic Failures

```typescript
// ❌ CRITICAL: Storing plain text passwords
await db.user.create({
  data: { email, password }, // Plain text!
})

// ✅ SECURE: Hashed passwords
import bcrypt from 'bcrypt'

const hashedPassword = await bcrypt.hash(password, 12)
await db.user.create({
  data: { email, password: hashedPassword },
})
```

**Checklist:**

- [ ] Passwords hashed with bcrypt (12+ rounds)
- [ ] HTTPS enforced in production
- [ ] Sensitive data encrypted at rest
- [ ] Secure session storage
- [ ] Environment variables for secrets
- [ ] No secrets in code or version control

#### A03: Injection

```typescript
// ❌ CRITICAL: SQL injection risk (raw SQL)
const userId = req.query.id // User controlled!
await db.$executeRaw`SELECT * FROM users WHERE id = ${userId}`

// ✅ SECURE: Parameterized query
const userId = req.query.id
await db.user.findUnique({ where: { id: userId } })

// ✅ SECURE: Input validation
const validated = z.string().cuid().parse(userId)
await db.user.findUnique({ where: { id: validated } })
```

**Checklist:**

- [ ] Use Prisma (prevents SQL injection)
- [ ] All inputs validated with Zod
- [ ] No raw SQL with user input
- [ ] XSS prevented (no dangerouslySetInnerHTML)
- [ ] Command injection prevented

#### A04: Insecure Design

**Checklist:**

- [ ] Security requirements defined
- [ ] Threat modeling performed
- [ ] Secure authentication flow
- [ ] Proper session management
- [ ] Defense in depth implemented

#### A05: Security Misconfiguration

**Checklist:**

- [ ] Security headers configured
- [ ] Error messages don't leak info
- [ ] Default credentials changed
- [ ] Unnecessary features disabled
- [ ] CORS properly configured

#### A06: Vulnerable Components

```bash
# Check for vulnerabilities
npm audit
npm audit fix
```

**Checklist:**

- [ ] Dependencies up to date
- [ ] No known vulnerabilities (npm audit)
- [ ] Dependabot enabled
- [ ] Regular security updates

#### A07: Authentication Failures

```typescript
// ❌ CRITICAL: Weak password policy
const password = z.string().min(6) // Too weak!

// ✅ SECURE: Strong password policy
const password = z
  .string()
  .min(8)
  .regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    'Must contain uppercase, lowercase, and number'
  )

// ✅ SECURE: Rate limiting
import { Ratelimit } from '@upstash/ratelimit'

const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(5, '10 m'), // 5 attempts per 10 min
})

const { success } = await ratelimit.limit(email)
if (!success) {
  throw new TooManyRequestsError()
}
```

**Checklist:**

- [ ] Strong password requirements
- [ ] Multi-factor authentication (MFA) available
- [ ] Account lockout after failed attempts
- [ ] Session timeout implemented
- [ ] Secure session storage
- [ ] Password reset flow secure

#### A08: Software and Data Integrity

**Checklist:**

- [ ] Dependencies verified (package-lock.json)
- [ ] CI/CD pipeline secure
- [ ] Code signed/verified
- [ ] Integrity checks on updates

#### A09: Security Logging & Monitoring

```typescript
// ✅ SECURE: Log security events
import { logger } from '@/lib/logger'

// Failed login attempt
logger.warn('Failed login attempt', {
  email,
  ip: req.ip,
  timestamp: new Date(),
})

// Successful login
logger.info('User logged in', {
  userId: user.id,
  ip: req.ip,
})

// Authorization failure
logger.warn('Unauthorized access attempt', {
  userId: session?.user?.id,
  resource: 'post',
  resourceId: postId,
})
```

**Checklist:**

- [ ] Security events logged
- [ ] Failed login attempts tracked
- [ ] Suspicious activity monitored
- [ ] Alerts configured
- [ ] Logs reviewed regularly

#### A10: Server-Side Request Forgery (SSRF)

```typescript
// ❌ CRITICAL: SSRF vulnerability
const url = req.body.url // User controlled!
const response = await fetch(url)

// ✅ SECURE: Whitelist allowed domains
const allowedDomains = ['api.example.com', 'cdn.example.com']
const urlObj = new URL(url)

if (!allowedDomains.includes(urlObj.hostname)) {
  throw new Error('Invalid domain')
}

const response = await fetch(url)
```

**Checklist:**

- [ ] URL validation before fetching
- [ ] Whitelist allowed domains
- [ ] No user-controlled URLs
- [ ] Internal endpoints not exposed

### 2. Authentication Flow Review (20 mins)

**NextAuth.js Configuration**

```typescript
// Check auth.ts configuration
export const authOptions: NextAuthOptions = {
  providers: [
    // OAuth providers configured correctly
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  callbacks: {
    async jwt({ token, user }) {
      // Token enrichment
      if (user) {
        token.id = user.id
        token.role = user.role
      }
      return token
    },
  },
  secret: process.env.NEXTAUTH_SECRET!, // Required
}
```

**Authentication Checklist:**

- [ ] NEXTAUTH_SECRET set and strong
- [ ] NEXTAUTH_URL configured correctly
- [ ] OAuth redirect URIs whitelisted
- [ ] Session strategy appropriate (JWT vs database)
- [ ] Session expiry configured
- [ ] Refresh token rotation (if using)

### 3. Authorization Review (15 mins)

**Middleware Protection**

```typescript
// middleware.ts
export default function middleware(req: NextRequest) {
  const token = await getToken({ req })

  // Protect dashboard routes
  if (req.nextUrl.pathname.startsWith('/dashboard')) {
    if (!token) {
      return NextResponse.redirect(new URL('/login', req.url))
    }
  }

  // Admin-only routes
  if (req.nextUrl.pathname.startsWith('/admin')) {
    if (!token || token.role !== 'ADMIN') {
      return NextResponse.redirect(new URL('/', req.url))
    }
  }
}
```

**Authorization Checklist:**

- [ ] Middleware protects routes
- [ ] Role-based access control
- [ ] Resource-level authorization
- [ ] API endpoints protected
- [ ] No client-side only auth

### 4. Input Validation Review (15 mins)

**Zod Validation**

```typescript
// ✅ SECURE: Comprehensive validation
export const createUserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(2).max(100),
  password: z
    .string()
    .min(8)
    .regex(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/),
  age: z.number().int().min(18).max(120),
  website: z.string().url().optional(),
})

// Validate in API
const validated = createUserSchema.parse(data)
```

**Validation Checklist:**

- [ ] All inputs validated with Zod
- [ ] String lengths limited
- [ ] Numbers have min/max
- [ ] Emails validated
- [ ] URLs validated
- [ ] File uploads validated (type, size)
- [ ] Sanitization for HTML content

### 5. API Security Review (10 mins)

**Rate Limiting**

```typescript
// ✅ SECURE: Rate limiting on API
import { Ratelimit } from '@upstash/ratelimit'

const ratelimit = new Ratelimit({
  redis,
  limiter: Ratelimit.slidingWindow(10, '10 s'),
})

export async function POST(req: Request) {
  const ip = req.headers.get('x-forwarded-for') || 'anonymous'
  const { success } = await ratelimit.limit(ip)

  if (!success) {
    return NextResponse.json({ error: 'Too many requests' }, { status: 429 })
  }

  // Handle request
}
```

**API Security Checklist:**

- [ ] Rate limiting implemented
- [ ] CORS configured correctly
- [ ] API keys validated
- [ ] Request size limits
- [ ] Timeout configured

### 6. Data Protection Review (10 mins)

**Checklist:**

- [ ] PII encrypted at rest
- [ ] Sensitive data not logged
- [ ] Data retention policy
- [ ] GDPR compliance (if applicable)
- [ ] User data export available
- [ ] User data deletion available

## Security Audit Output

### Critical Issues (Fix Immediately)

- [ ] Missing authentication checks
- [ ] SQL injection vulnerabilities
- [ ] XSS vulnerabilities
- [ ] Secrets in code
- [ ] Broken access control

### High Priority

- [ ] Weak password policy
- [ ] Missing rate limiting
- [ ] Insecure session management
- [ ] Missing input validation
- [ ] Outdated dependencies

### Medium Priority

- [ ] Missing security headers
- [ ] Insufficient logging
- [ ] CORS misconfiguration
- [ ] Error information leakage

### Recommendations

- [ ] Enable MFA
- [ ] Implement CSP headers
- [ ] Add security monitoring
- [ ] Regular security audits
- [ ] Penetration testing

## After Security Review

- Fix all critical issues before deployment
- Plan remediation for high priority issues
- Schedule regular security audits
- Enable security monitoring
- Train team on secure coding
