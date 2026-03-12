---
description: Design Next.js application architecture with modern patterns
---

You are in **NEXT.JS DESIGN MODE**.

Use the **fullstack-js-savant** agent to design a modern Next.js application architecture.

## Design Workflow

### 1. Application Structure Design

- **App Router Layout**: Design layout hierarchy and nested routes
- **Server vs Client Components**: Plan which components should be Server/Client
- **Data Fetching Strategy**: Determine where to fetch data (Server Components, Route Handlers, Server Actions)
- **Streaming Strategy**: Plan Suspense boundaries and loading states

### 2. Routing Architecture

```
app/
├── (auth)/
│   ├── login/
│   └── signup/
├── (dashboard)/
│   ├── layout.tsx (protected layout)
│   ├── page.tsx
│   └── [features]/
└── api/
    ├── trpc/
    └── webhooks/
```

### 3. State Management Design

- **Server State**: React Query/TanStack Query configuration
- **Client State**: Zustand, Jotai, or Context API
- **Form State**: react-hook-form with Zod schemas
- **URL State**: searchParams for filters and pagination

### 4. API Layer Design

- **tRPC Setup**: Define routers and procedures
- **Route Handlers**: REST endpoints for webhooks, third-party integrations
- **Server Actions**: Form submissions, mutations
- **Middleware**: Authentication, rate limiting, logging

### 5. Database Integration

- **Prisma Schema**: Design entities and relationships
- **Query Patterns**: Plan data fetching patterns to avoid N+1 queries
- **Caching**: Redis for session, query results, rate limiting

### 6. Authentication Flow

- **NextAuth.js v5**: Configure providers, callbacks, session strategy
- **Protected Routes**: Middleware vs layout-based protection
- **Authorization**: Role-based access control (RBAC)

### 7. UI Component Strategy

- **shadcn/ui Components**: Which components to install
- **Custom Components**: Shared UI components structure
- **Theme System**: Dark mode, color schemes, typography

### 8. Performance Planning

- **Bundle Optimization**: Code splitting strategy, dynamic imports
- **Image Optimization**: next/image usage patterns
- **Font Optimization**: next/font configuration
- **Caching Headers**: ISR, SSG, dynamic rendering decisions

## Design Deliverables

1. **Project Structure Document**
   - Directory structure with rationale
   - File naming conventions
   - Module organization

2. **Data Flow Diagrams**
   - User authentication flow
   - Data fetching patterns
   - Form submission flows

3. **API Contract**
   - tRPC router definitions
   - Zod schemas for validation
   - Error handling patterns

4. **Component Hierarchy**
   - Layout components
   - Page components
   - Shared UI components

**After Design, Proceed To**:

- `/workflow-implement-fullstack` - Implement full-stack features
- `/workflow-implement-frontend` - Build UI components
- `/workflow-implement-backend` - Create API layer
