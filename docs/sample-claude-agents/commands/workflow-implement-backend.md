---
description: Implement backend API, business logic, and data layer
---

You are in **BACKEND IMPLEMENTATION MODE**.

Use **backend-api** agent to build type-safe, secure backend services.

## Implementation Workflow

### 1. Database Schema (10 mins)

Use **database** agent first:

```prisma
// Define models, relations, indexes
model Post {
  id        String   @id @default(cuid())
  title     String
  content   String   @db.Text
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])

  @@index([authorId])
}
```

Run migration:

```bash
npx prisma migrate dev --name add_posts
npx prisma generate
```

### 2. Input Validation Schemas (5 mins)

Define Zod schemas for type-safe validation:

```typescript
// lib/validations/post.ts
import { z } from 'zod'

export const createPostSchema = z.object({
  title: z.string().min(1).max(255),
  content: z.string().min(1),
  published: z.boolean().default(false),
})

export const updatePostSchema = createPostSchema.partial()

export type CreatePostInput = z.infer<typeof createPostSchema>
export type UpdatePostInput = z.infer<typeof updatePostSchema>
```

### 3. tRPC Router (20-30 mins)

Build type-safe API with tRPC:

```typescript
// server/routers/post.ts
import { router, publicProcedure, protectedProcedure } from '../trpc'
import { createPostSchema, updatePostSchema } from '@/lib/validations/post'

export const postRouter = router({
  // Public queries
  list: publicProcedure
    .input(
      z.object({
        limit: z.number().min(1).max(100).default(10),
        cursor: z.string().optional(),
        published: z.boolean().optional(),
      })
    )
    .query(async ({ ctx, input }) => {
      const posts = await ctx.db.post.findMany({
        take: input.limit + 1,
        cursor: input.cursor ? { id: input.cursor } : undefined,
        where: { published: input.published },
        orderBy: { createdAt: 'desc' },
        include: { author: { select: { name: true, image: true } } },
      })

      let nextCursor: string | undefined
      if (posts.length > input.limit) {
        const nextItem = posts.pop()
        nextCursor = nextItem!.id
      }

      return { posts, nextCursor }
    }),

  // Protected mutations
  create: protectedProcedure
    .input(createPostSchema)
    .mutation(async ({ ctx, input }) => {
      return await ctx.db.post.create({
        data: {
          ...input,
          authorId: ctx.session.user.id,
        },
      })
    }),

  update: protectedProcedure
    .input(
      z.object({
        id: z.string(),
        data: updatePostSchema,
      })
    )
    .mutation(async ({ ctx, input }) => {
      // Check ownership
      const post = await ctx.db.post.findUnique({
        where: { id: input.id },
        select: { authorId: true },
      })

      if (!post) {
        throw new TRPCError({ code: 'NOT_FOUND' })
      }

      if (post.authorId !== ctx.session.user.id) {
        throw new TRPCError({ code: 'FORBIDDEN' })
      }

      return await ctx.db.post.update({
        where: { id: input.id },
        data: input.data,
      })
    }),

  delete: protectedProcedure
    .input(z.string())
    .mutation(async ({ ctx, input }) => {
      // Check ownership
      const post = await ctx.db.post.findUnique({
        where: { id: input },
        select: { authorId: true },
      })

      if (!post) {
        throw new TRPCError({ code: 'NOT_FOUND' })
      }

      if (post.authorId !== ctx.session.user.id) {
        throw new TRPCError({ code: 'FORBIDDEN' })
      }

      return await ctx.db.post.delete({ where: { id: input } })
    }),
})
```

### 4. Alternative: Route Handlers (15-20 mins)

For webhooks or REST APIs:

```typescript
// app/api/posts/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { auth } from '@/lib/auth'
import { db } from '@/lib/db'
import { createPostSchema } from '@/lib/validations/post'

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const limit = parseInt(searchParams.get('limit') || '10')

  const posts = await db.post.findMany({
    take: limit,
    orderBy: { createdAt: 'desc' },
  })

  return NextResponse.json({ posts })
}

export async function POST(req: NextRequest) {
  const session = await auth()
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await req.json()
  const validated = createPostSchema.safeParse(body)

  if (!validated.success) {
    return NextResponse.json(
      { error: validated.error.flatten() },
      { status: 400 }
    )
  }

  const post = await db.post.create({
    data: {
      ...validated.data,
      authorId: session.user.id,
    },
  })

  return NextResponse.json({ post }, { status: 201 })
}
```

### 5. Server Actions (10-15 mins)

For form submissions and mutations:

```typescript
// app/actions/post.ts
'use server'

import { auth } from '@/lib/auth'
import { db } from '@/lib/db'
import { createPostSchema } from '@/lib/validations/post'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

export async function createPostAction(formData: FormData) {
  const session = await auth()
  if (!session?.user) {
    return { error: 'Unauthorized' }
  }

  const validated = createPostSchema.safeParse({
    title: formData.get('title'),
    content: formData.get('content'),
    published: formData.get('published') === 'true',
  })

  if (!validated.success) {
    return {
      errors: validated.error.flatten().fieldErrors,
    }
  }

  const post = await db.post.create({
    data: {
      ...validated.data,
      authorId: session.user.id,
    },
  })

  revalidatePath('/posts')
  redirect(`/posts/${post.id}`)
}
```

### 6. Business Logic Layer (Optional, 10-15 mins)

For complex logic, create service layer:

```typescript
// lib/services/post-service.ts
export class PostService {
  async createPost(userId: string, data: CreatePostInput) {
    // Complex business logic
    const post = await db.post.create({
      data: { ...data, authorId: userId },
    })

    // Send notification
    await notificationService.notifyFollowers(userId, post.id)

    // Update cache
    await cache.invalidate(`user:${userId}:posts`)

    return post
  }
}
```

### 7. Error Handling (5 mins)

Implement consistent error handling:

```typescript
// lib/errors.ts
export class AppError extends Error {
  constructor(
    message: string,
    public statusCode: number = 500,
    public code: string = 'INTERNAL_ERROR'
  ) {
    super(message)
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 404, 'NOT_FOUND')
  }
}

export class UnauthorizedError extends AppError {
  constructor(message = 'Unauthorized') {
    super(message, 401, 'UNAUTHORIZED')
  }
}
```

## Implementation Checklist

**Database**

- [ ] Prisma schema updated
- [ ] Migration created and run
- [ ] Indexes added for performance
- [ ] Seed data created (if needed)

**Validation**

- [ ] Zod schemas defined
- [ ] Input validation on all endpoints
- [ ] Type inference working
- [ ] Error messages user-friendly

**API Layer**

- [ ] tRPC routers OR Route Handlers created
- [ ] All CRUD operations implemented
- [ ] Pagination for lists
- [ ] Filtering and sorting options

**Authorization**

- [ ] Authentication checked on protected routes
- [ ] Resource ownership verified
- [ ] Role-based access control (if needed)
- [ ] API keys validated (if public API)

**Error Handling**

- [ ] Errors caught and handled
- [ ] Appropriate HTTP status codes
- [ ] Error messages don't leak sensitive info
- [ ] Logging for debugging

**Performance**

- [ ] N+1 queries prevented (use include/select)
- [ ] Database indexes on frequently queried fields
- [ ] Connection pooling configured
- [ ] Caching for expensive queries

**Testing**

- [ ] Unit tests for business logic
- [ ] Integration tests for API endpoints
- [ ] Test error cases
- [ ] Test authorization logic

## After Implementation

- Use `/workflow-review-code` to review API quality
- Use `/workflow-review-security` to audit security
- Use `/workflow-qa-e2e` to write comprehensive tests
- Use `/workflow-review-performance` to optimize queries
