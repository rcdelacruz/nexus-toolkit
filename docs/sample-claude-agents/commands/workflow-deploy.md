---
description: Deploy application to production with CI/CD pipeline
---

You are in **DEPLOYMENT MODE**.

Use **deployment** agent to set up production deployment and CI/CD.

## Deployment Workflow

### 1. Pre-Deployment Checklist (10 mins)

**Code Quality**

- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] No console.logs or debugging code
- [ ] No TODOs for critical features
- [ ] TypeScript builds without errors

**Security**

- [ ] Environment variables configured
- [ ] Secrets not in code
- [ ] API keys rotated for production
- [ ] Security audit passed
- [ ] Dependencies updated (npm audit)

**Performance**

- [ ] Bundle size optimized
- [ ] Images optimized
- [ ] Core Web Vitals targets met
- [ ] Database indexes added

**Configuration**

- [ ] Production environment variables set
- [ ] Database connection configured
- [ ] CDN configured
- [ ] Domain/DNS configured
- [ ] SSL certificate configured

### 2. Database Migration (15 mins)

**Prepare Migration**

```bash
# Review pending migrations
npx prisma migrate status

# Create migration if needed
npx prisma migrate dev --name deployment_prep

# Generate Prisma Client
npx prisma generate
```

**Production Migration Strategy**

```bash
# Option 1: Run migration during deployment (small changes)
npx prisma migrate deploy

# Option 2: Run migration separately (breaking changes)
# 1. Add new columns (nullable)
# 2. Deploy code that works with both old/new schema
# 3. Backfill data
# 4. Deploy code that requires new schema
# 5. Remove old columns
```

**Migration Checklist**

- [ ] Migrations tested in staging
- [ ] Backup database before migration
- [ ] Migration is backwards compatible (if zero-downtime)
- [ ] Rollback plan documented
- [ ] Data migration scripts tested

### 3. Vercel Deployment (Recommended) (10 mins)

**Setup Vercel**

```bash
# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Link project
vercel link
```

**Configure Environment Variables**

```bash
# Add via CLI
vercel env add DATABASE_URL production
vercel env add NEXTAUTH_SECRET production
vercel env add NEXTAUTH_URL production

# Or via dashboard: vercel.com/[team]/[project]/settings/environment-variables
```

**vercel.json Configuration**

```json
{
  "framework": "nextjs",
  "buildCommand": "npm run build",
  "installCommand": "npm ci",
  "regions": ["iad1"],
  "env": {
    "DATABASE_URL": "@database-url",
    "NEXTAUTH_SECRET": "@nextauth-secret",
    "NEXTAUTH_URL": "@nextauth-url"
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Frame-Options",
          "value": "SAMEORIGIN"
        },
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=31536000; includeSubDomains"
        }
      ]
    }
  ]
}
```

**Deploy**

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod

# Promote preview to production
vercel promote [preview-url]
```

**Vercel Deployment Checklist**

- [ ] Environment variables configured
- [ ] Custom domain configured
- [ ] SSL certificate active
- [ ] Database migrations run
- [ ] Deployment successful
- [ ] Health check passing

### 4. GitHub Actions CI/CD (20 mins)

**Continuous Integration**

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npm run type-check

      - name: Setup test database
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Run unit tests
        run: npm run test
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Run E2E tests
        run: npx playwright test
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/

      - name: Build
        run: npm run build
        env:
          SKIP_ENV_VALIDATION: true
```

**Continuous Deployment to Vercel**

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Vercel CLI
        run: npm install --global vercel@latest

      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Run Database Migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}

      - name: Build Artifacts
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel
        run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Run Smoke Tests
        run: npm run test:smoke
        env:
          BASE_URL: https://your-app.vercel.app
```

### 5. Docker Deployment (Alternative) (20 mins)

**Dockerfile**

```dockerfile
# Multi-stage build
FROM node:20-alpine AS base

# Dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Generate Prisma Client
RUN npx prisma generate

# Build Next.js
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

**next.config.js**

```javascript
module.exports = {
  output: 'standalone', // Required for Docker
}
```

**docker-compose.yml**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - '3000:3000'
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=${NEXTAUTH_URL}
    depends_on:
      - db
    restart: unless-stopped

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - '5432:5432'
    restart: unless-stopped

volumes:
  postgres_data:
```

**Deploy with Docker**

```bash
# Build
docker build -t myapp:latest .

# Run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### 6. Post-Deployment Verification (10 mins)

**Smoke Tests**

```bash
# Health check
curl https://your-app.com/api/health

# Test authentication
curl -X POST https://your-app.com/api/auth/signin \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Test main endpoints
curl https://your-app.com/api/posts
```

**Manual Verification**

- [ ] Homepage loads correctly
- [ ] Login works
- [ ] Create/update operations work
- [ ] Images load correctly
- [ ] API responses are correct
- [ ] Database migrations applied
- [ ] No console errors
- [ ] Monitoring/logging active

### 7. Rollback Plan (5 mins)

**Vercel Rollback**

```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

**Docker Rollback**

```bash
# Keep previous images tagged
docker tag myapp:latest myapp:previous

# Rollback
docker stop myapp
docker rm myapp
docker run -d --name myapp myapp:previous
```

**Database Rollback**

```bash
# Restore from backup
pg_restore -d mydb backup.dump

# Or revert migration (careful!)
npx prisma migrate resolve --rolled-back [migration-name]
```

### 8. Monitoring Setup (10 mins)

**Configure Sentry**

```typescript
// sentry.server.config.ts
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
})
```

**Configure Vercel Analytics**

```typescript
// app/layout.tsx
import { Analytics } from '@vercel/analytics/react'
import { SpeedInsights } from '@vercel/speed-insights/next'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  )
}
```

**Set Up Alerts**

- [ ] Error rate alerts (Sentry)
- [ ] Uptime monitoring (UptimeRobot, Better Uptime)
- [ ] Performance alerts (Vercel Analytics)
- [ ] Database alerts (connection pool, slow queries)

## Deployment Checklist

**Pre-Deployment**

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Security audit passed
- [ ] Performance targets met
- [ ] Database backup created

**Configuration**

- [ ] Environment variables set
- [ ] Database connection configured
- [ ] Domain/SSL configured
- [ ] CDN configured
- [ ] Monitoring configured

**Deployment**

- [ ] Database migrations run
- [ ] Application deployed
- [ ] Health check passing
- [ ] Smoke tests passing
- [ ] No errors in logs

**Post-Deployment**

- [ ] Manual verification complete
- [ ] Monitoring active
- [ ] Alerts configured
- [ ] Rollback plan documented
- [ ] Team notified

## Deployment Commands Reference

**Vercel**

```bash
vercel                    # Deploy to preview
vercel --prod             # Deploy to production
vercel env ls             # List environment variables
vercel logs               # View deployment logs
vercel rollback [url]     # Rollback deployment
```

**Docker**

```bash
docker build -t myapp .   # Build image
docker-compose up -d      # Start containers
docker-compose logs -f    # View logs
docker-compose down       # Stop containers
```

**Prisma**

```bash
npx prisma migrate deploy # Run migrations
npx prisma db push        # Push schema changes
npx prisma generate       # Generate Prisma Client
```

## After Deployment

- Monitor application health
- Check error rates in Sentry
- Review performance metrics
- Verify user feedback
- Update documentation
- Plan next release
