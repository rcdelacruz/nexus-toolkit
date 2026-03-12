---
description: Implement full-stack feature end-to-end with Next.js
---

You are in **FULL-STACK IMPLEMENTATION MODE**.

Use **fullstack-js-savant** to orchestrate implementation across frontend, backend, and database.

## Implementation Workflow

### Phase 1: Database Schema (5-10 mins)

Use **database** agent to:

- Create/update Prisma schema
- Write migration
- Add indexes for performance
- Define relationships and constraints

```bash
# Example tasks:
- Add new Post model with User relation
- Create migration: npx prisma migrate dev --name add_posts
- Add indexes on frequently queried fields
```

### Phase 2: Backend API (15-20 mins)

Use **backend-api** agent to:

- Create tRPC router or Route Handlers
- Define Zod schemas for input validation
- Implement business logic in service layer
- Add authentication/authorization checks
- Write API tests

```typescript
// Example tasks:
- Create app/server/routers/post.ts
- Define createPost, updatePost, deletePost procedures
- Add protection middleware
- Validate inputs with Zod
```

### Phase 3: Server Components & Actions (10-15 mins)

Use **fullstack-nextjs** agent to:

- Create Server Components for data fetching
- Implement Server Actions for mutations
- Set up Suspense boundaries for streaming
- Handle loading and error states

```typescript
// Example tasks:
- Create app/(dashboard)/posts/page.tsx (Server Component)
- Implement createPostAction server action
- Add Suspense with loading.tsx
- Create error.tsx for error boundaries
```

### Phase 4: UI Components (15-20 mins)

Use **frontend-ui** agent to:

- Build forms with react-hook-form + Zod
- Create UI components with shadcn/ui
- Implement client-side interactions
- Add optimistic updates

```typescript
// Example tasks:
- Create PostForm with form validation
- Build PostCard component
- Add delete confirmation dialog
- Implement optimistic UI updates
```

### Phase 5: Integration & Testing (10-15 mins)

- Connect all layers (DB → API → Server Components → UI)
- Test user flows end-to-end
- Verify error handling
- Check loading states

### Phase 6: Security Review (5 mins)

Use **security** agent to:

- Verify input validation
- Check authorization on all endpoints
- Ensure CSRF protection
- Validate error messages don't leak sensitive info

## Implementation Checklist

**Database Layer**

- [ ] Prisma schema updated
- [ ] Migration created and applied
- [ ] Indexes added for performance
- [ ] Seed data if needed

**API Layer**

- [ ] tRPC routers/Route Handlers created
- [ ] Input validation with Zod
- [ ] Authorization checks implemented
- [ ] Error handling added
- [ ] API tests written

**Server Layer**

- [ ] Server Components for data fetching
- [ ] Server Actions for mutations
- [ ] Suspense boundaries added
- [ ] Loading states implemented
- [ ] Error boundaries created

**UI Layer**

- [ ] Forms with validation
- [ ] UI components with shadcn/ui
- [ ] Client-side interactions
- [ ] Optimistic updates
- [ ] Accessibility (ARIA labels, keyboard navigation)

**Security**

- [ ] Authentication required where needed
- [ ] Authorization enforced
- [ ] Input sanitization
- [ ] Rate limiting (if public endpoint)

**Testing**

- [ ] API integration tests
- [ ] Component tests
- [ ] E2E test for critical path

## After Implementation

- Use `/workflow-review-code` to review implementation quality
- Use `/workflow-review-security` to audit security
- Use `/workflow-review-performance` to optimize performance
- Use `/workflow-qa-e2e` to write comprehensive E2E tests
