---
description: Comprehensive code quality review with best practices enforcement
---

You are in **CODE REVIEW MODE**.

Use **code-reviewer** agent to perform thorough code quality analysis.

## Review Process

### 1. Initial Assessment (5 mins)

- Review overall code structure
- Check file organization
- Assess naming conventions
- Verify TypeScript usage

### 2. Architecture Review (10 mins)

**Component Architecture**

- [ ] Server vs Client Components used correctly
- [ ] Props properly typed with interfaces
- [ ] Components are focused and single-purpose
- [ ] Proper separation of concerns

**Data Flow**

- [ ] Data fetching in Server Components
- [ ] Mutations via Server Actions or tRPC
- [ ] State management appropriate for use case
- [ ] No prop drilling (use Context or state management)

**Code Organization**

- [ ] Files in correct directories
- [ ] Consistent naming (camelCase, PascalCase, kebab-case)
- [ ] Imports organized (React, libraries, local)
- [ ] No circular dependencies

### 3. TypeScript Review (10 mins)

**Type Safety**

```typescript
// ❌ BAD: Any types
function processData(data: any) {}

// ✅ GOOD: Proper types
function processData(data: User) {}

// ❌ BAD: Type assertions
const user = data as User

// ✅ GOOD: Type guards
if (isUser(data)) {
  // data is User
}
```

**Type Coverage**

- [ ] No `any` types (except unavoidable cases)
- [ ] Functions have return type annotations
- [ ] Interfaces defined for complex objects
- [ ] Generics used where appropriate
- [ ] Type guards for runtime checks

### 4. React Best Practices (15 mins)

**Hooks Usage**

```typescript
// ❌ BAD: Conditional hooks
if (condition) {
  useEffect(() => {})
}

// ✅ GOOD: Hooks at top level
useEffect(() => {
  if (condition) {
  }
}, [condition])

// ❌ BAD: Missing dependencies
useEffect(() => {
  fetchData(userId)
}, []) // userId missing!

// ✅ GOOD: All dependencies
useEffect(() => {
  fetchData(userId)
}, [userId])
```

**Component Patterns**

- [ ] Hooks only in components/custom hooks
- [ ] Proper dependency arrays in useEffect
- [ ] Memoization used appropriately (useMemo, useCallback)
- [ ] No inline function definitions in JSX (if used in deps)

### 5. Next.js Patterns Review (15 mins)

**Server Components**

```typescript
// ✅ GOOD: Server Component fetches data
export default async function PostsPage() {
  const posts = await db.post.findMany()
  return <PostsList posts={posts} />
}

// ❌ BAD: Using client hooks in Server Component
export default async function PostsPage() {
  const [posts, setPosts] = useState([]) // Error!
}
```

**Server Actions**

```typescript
// ✅ GOOD: Proper error handling
'use server'
export async function createPost(formData: FormData) {
  try {
    const validated = schema.safeParse(/* ... */)
    if (!validated.success) {
      return { errors: validated.error.flatten().fieldErrors }
    }
    // Create post
    revalidatePath('/posts')
  } catch (error) {
    return { error: 'Failed to create post' }
  }
}
```

**Patterns to Check**

- [ ] Server Components for data fetching
- [ ] Client Components only when needed
- [ ] Server Actions for mutations
- [ ] Proper revalidation after mutations
- [ ] Loading states with Suspense
- [ ] Error boundaries for error handling

### 6. Security Review (10 mins)

**Authentication & Authorization**

```typescript
// ❌ BAD: No auth check
export async function deletePost(id: string) {
  await db.post.delete({ where: { id } })
}

// ✅ GOOD: Auth + ownership check
export async function deletePost(id: string) {
  const session = await auth()
  if (!session?.user) throw new UnauthorizedError()

  const post = await db.post.findUnique({ where: { id } })
  if (post?.authorId !== session.user.id) {
    throw new ForbiddenError()
  }

  await db.post.delete({ where: { id } })
}
```

**Input Validation**

```typescript
// ❌ BAD: No validation
export async function createPost(data: any) {
  await db.post.create({ data })
}

// ✅ GOOD: Zod validation
export async function createPost(data: unknown) {
  const validated = createPostSchema.parse(data)
  await db.post.create({ data: validated })
}
```

**Security Checklist**

- [ ] All inputs validated with Zod
- [ ] Authentication checked on protected routes
- [ ] Authorization enforced (user owns resource)
- [ ] SQL injection prevented (using Prisma)
- [ ] XSS prevented (no dangerouslySetInnerHTML)
- [ ] Secrets in environment variables, not code
- [ ] Rate limiting on public endpoints

### 7. Performance Review (10 mins)

**Database Queries**

```typescript
// ❌ BAD: N+1 query problem
const posts = await db.post.findMany()
for (const post of posts) {
  post.author = await db.user.findUnique({ where: { id: post.authorId } })
}

// ✅ GOOD: Include relation
const posts = await db.post.findMany({
  include: { author: true },
})
```

**React Performance**

```typescript
// ❌ BAD: Unnecessary re-renders
const value = { user, setUser } // New object every render!
<UserContext.Provider value={value}>

// ✅ GOOD: Memoized value
const value = useMemo(() => ({ user, setUser }), [user])
<UserContext.Provider value={value}>
```

**Performance Checklist**

- [ ] No N+1 database queries
- [ ] Images use next/image
- [ ] Fonts use next/font
- [ ] Code splitting with dynamic imports
- [ ] Expensive calculations memoized
- [ ] Large lists virtualized

### 8. Error Handling Review (5 mins)

**Consistent Error Handling**

```typescript
// ✅ GOOD: Proper error handling
try {
  const result = await riskyOperation()
  return { success: true, data: result }
} catch (error) {
  logger.error('Operation failed', { error, context })

  if (error instanceof ValidationError) {
    return { success: false, error: error.message }
  }

  // Don't leak internal errors to client
  return { success: false, error: 'Operation failed' }
}
```

**Error Handling Checklist**

- [ ] Try-catch blocks around async operations
- [ ] Errors logged for debugging
- [ ] User-friendly error messages
- [ ] No sensitive info in error messages
- [ ] Error boundaries for UI errors

### 9. Code Quality (10 mins)

**Clean Code Principles**

- [ ] Functions are small and focused
- [ ] Descriptive variable and function names
- [ ] No magic numbers (use constants)
- [ ] No commented-out code
- [ ] No console.logs (use proper logging)
- [ ] Consistent formatting (Prettier)

**DRY Principle**

- [ ] No duplicated code
- [ ] Common logic extracted to utilities
- [ ] Reusable components created

**Testing**

- [ ] Critical paths have tests
- [ ] Edge cases covered
- [ ] Error scenarios tested

## Review Checklist

**Architecture**

- [ ] Component architecture is sound
- [ ] Data flow is clear and unidirectional
- [ ] Code organization follows conventions
- [ ] No circular dependencies

**TypeScript**

- [ ] No `any` types (justified exceptions only)
- [ ] Proper type annotations
- [ ] Type guards for runtime checks
- [ ] Interfaces defined for complex objects

**React/Next.js**

- [ ] Hooks used correctly
- [ ] Server/Client Components used appropriately
- [ ] Server Actions for mutations
- [ ] Proper Suspense boundaries

**Security**

- [ ] Input validation with Zod
- [ ] Authentication on protected routes
- [ ] Authorization checks (ownership)
- [ ] No security vulnerabilities

**Performance**

- [ ] No N+1 queries
- [ ] Proper memoization
- [ ] Code splitting
- [ ] Optimized images/fonts

**Error Handling**

- [ ] Errors caught and handled
- [ ] Proper logging
- [ ] User-friendly messages
- [ ] Error boundaries

**Code Quality**

- [ ] Clean, readable code
- [ ] No code smells
- [ ] DRY principle followed
- [ ] Tests written

## Review Output

Provide:

1. **Summary**: Overall code quality assessment
2. **Critical Issues**: Must-fix issues (security, bugs)
3. **Improvements**: Suggestions for better code quality
4. **Best Practices**: Violations of best practices
5. **Refactoring**: Opportunities for refactoring
6. **Approval Status**: Approved / Needs Changes

## After Review

- Fix critical issues immediately
- Plan refactoring for improvements
- Use `/workflow-review-security` for deeper security audit
- Use `/workflow-review-performance` for performance optimization
