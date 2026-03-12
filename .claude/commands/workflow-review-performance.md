---
description: Performance optimization focusing on Core Web Vitals and load times
---

You are in **PERFORMANCE REVIEW MODE**.

Use **performance** agent to optimize for Core Web Vitals and fast load times.

## Performance Audit Process

### 1. Core Web Vitals Analysis (20 mins)

#### Largest Contentful Paint (LCP) - Target: < 2.5s

```typescript
// ❌ SLOW: Large unoptimized image
<img src="/hero.jpg" width="1200" height="630" />

// ✅ FAST: Optimized with next/image
import Image from 'next/image'

<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={630}
  priority // Preload above-the-fold
  quality={85}
  placeholder="blur"
  blurDataURL="data:image/..." // Or import from static
/>
```

**LCP Optimization Checklist:**

- [ ] Hero images use next/image with priority
- [ ] Above-the-fold content loads first
- [ ] Server-side rendering for initial paint
- [ ] Fonts optimized with next/font
- [ ] CSS not blocking render
- [ ] No layout shifts during load

#### First Input Delay (FID/INP) - Target: < 100ms

```typescript
// ❌ SLOW: Heavy computation on main thread
function ExpensiveComponent() {
  const data = complexCalculation(largeArray) // Blocks rendering!
  return <div>{data}</div>
}

// ✅ FAST: Memoized expensive calculation
function ExpensiveComponent() {
  const data = useMemo(
    () => complexCalculation(largeArray),
    [largeArray]
  )
  return <div>{data}</div>
}

// ✅ BETTER: Web Worker for heavy computation
function ExpensiveComponent() {
  const [data, setData] = useState(null)

  useEffect(() => {
    const worker = new Worker('/workers/calculation.js')
    worker.postMessage(largeArray)
    worker.onmessage = (e) => setData(e.data)
    return () => worker.terminate()
  }, [largeArray])

  return <div>{data}</div>
}
```

**FID/INP Optimization Checklist:**

- [ ] No long tasks blocking main thread
- [ ] Heavy computation memoized or in Web Workers
- [ ] Event handlers debounced/throttled
- [ ] Code splitting for large bundles
- [ ] Third-party scripts loaded async

#### Cumulative Layout Shift (CLS) - Target: < 0.1

```typescript
// ❌ LAYOUT SHIFT: No dimensions on image
<img src="/banner.jpg" alt="Banner" />

// ✅ NO SHIFT: Dimensions specified
<Image
  src="/banner.jpg"
  alt="Banner"
  width={1200}
  height={300} // Prevents shift
/>

// ❌ LAYOUT SHIFT: Dynamic content without placeholder
{isLoading && <Spinner />}
{data && <Content data={data} />}

// ✅ NO SHIFT: Consistent height
<div className="min-h-[400px]">
  {isLoading && <Spinner />}
  {data && <Content data={data} />}
</div>
```

**CLS Optimization Checklist:**

- [ ] All images have width/height
- [ ] Skeleton loaders for dynamic content
- [ ] No content injection above viewport
- [ ] Fonts loaded without FOUT/FOIT
- [ ] Ads/embeds have reserved space

### 2. Bundle Size Analysis (15 mins)

**Analyze Bundle**

```bash
# Build and analyze
npm run build

# Use bundle analyzer
npm install @next/bundle-analyzer
```

**next.config.js**

```typescript
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
})

module.exports = withBundleAnalyzer({
  // config
})

// Run: ANALYZE=true npm run build
```

**Bundle Optimization:**

```typescript
// ❌ LARGE: Import entire library
import _ from 'lodash' // 70kb!

// ✅ SMALL: Import only what you need
import debounce from 'lodash/debounce' // 2kb

// ❌ LARGE: Import heavy component always
import { HeavyChart } from 'chart-library'

// ✅ SMALL: Dynamic import
const HeavyChart = dynamic(() => import('chart-library'), {
  loading: () => <ChartSkeleton />,
  ssr: false, // Client-side only if not needed for SEO
})
```

**Bundle Checklist:**

- [ ] Total bundle < 200kb (gzipped)
- [ ] Tree shaking enabled
- [ ] Unused dependencies removed
- [ ] Heavy libraries code-split
- [ ] Moment.js replaced with date-fns or dayjs
- [ ] Icons optimized (use lucide-react, not all of FontAwesome)

### 3. Database Query Optimization (20 mins)

**N+1 Query Prevention**

```typescript
// ❌ SLOW: N+1 query problem
const posts = await db.post.findMany()
for (const post of posts) {
  post.author = await db.user.findUnique({
    where: { id: post.authorId },
  }) // N queries!
}

// ✅ FAST: Single query with include
const posts = await db.post.findMany({
  include: {
    author: {
      select: { id: true, name: true, image: true },
    },
  },
})

// ✅ FASTER: Pagination for large datasets
const posts = await db.post.findMany({
  take: 20,
  skip: (page - 1) * 20,
  include: { author: true },
  orderBy: { createdAt: 'desc' },
})
```

**Indexing**

```prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  slug      String   @unique
  authorId  String
  published Boolean  @default(false)
  createdAt DateTime @default(now())

  // Indexes for common queries
  @@index([authorId]) // Filter by author
  @@index([published]) // Filter by published
  @@index([createdAt]) // Sort by date
  @@index([authorId, published]) // Composite for both
}
```

**Query Optimization Checklist:**

- [ ] No N+1 queries (use include/select)
- [ ] Indexes on frequently queried fields
- [ ] Pagination for large datasets
- [ ] Select only needed fields
- [ ] Connection pooling configured
- [ ] Query explain plan reviewed

### 4. Caching Strategy Review (15 mins)

**Multi-Layer Caching**

```typescript
// 1. Client-Side Caching (React Query)
const { data } = useQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  staleTime: 5 * 60 * 1000, // 5 minutes
})

// 2. Server-Side Caching (Next.js)
export const revalidate = 60 // ISR - revalidate every 60s

// 3. Database Query Caching (Redis)
async function getCachedPosts() {
  const cached = await redis.get('posts')
  if (cached) return JSON.parse(cached)

  const posts = await db.post.findMany()
  await redis.set('posts', JSON.stringify(posts), { ex: 300 }) // 5 min TTL
  return posts
}

// 4. CDN Caching (Headers)
export async function GET() {
  const data = await fetchData()

  return NextResponse.json(data, {
    headers: {
      'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=120',
    },
  })
}
```

**Caching Checklist:**

- [ ] Static pages use SSG
- [ ] Dynamic pages use ISR where appropriate
- [ ] API responses cached with appropriate TTL
- [ ] Redis for session and query caching
- [ ] CDN caching configured
- [ ] Cache invalidation strategy

### 5. Image Optimization (10 mins)

**Image Best Practices**

```typescript
// ✅ OPTIMIZED: Modern image with next/image
<Image
  src="/product.jpg"
  alt="Product"
  width={800}
  height={600}
  quality={85} // 75-85 is good balance
  sizes="(max-width: 768px) 100vw, 50vw" // Responsive
  loading="lazy" // Lazy load below fold
/>

// ✅ OPTIMIZED: Use WebP/AVIF with fallback
const imageFormats = {
  avif: '/image.avif',
  webp: '/image.webp',
  jpg: '/image.jpg',
}
```

**Image Optimization Checklist:**

- [ ] All images use next/image
- [ ] Priority flag on hero images
- [ ] Lazy loading on below-fold images
- [ ] Responsive images with sizes
- [ ] Modern formats (WebP/AVIF)
- [ ] Images compressed (quality 75-85)
- [ ] No images larger than displayed size

### 6. Font Optimization (5 mins)

```typescript
// app/layout.tsx
import { Inter, JetBrains_Mono } from 'next/font/google'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap', // Prevent FOIT
  variable: '--font-inter',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
})

export default function RootLayout({ children }) {
  return (
    <html className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  )
}
```

**Font Checklist:**

- [ ] Fonts loaded via next/font
- [ ] Subset to needed characters
- [ ] display: 'swap' to prevent FOIT
- [ ] Preload critical fonts
- [ ] Variable fonts for size savings

### 7. Code Splitting & Lazy Loading (10 mins)

```typescript
// ❌ SLOW: Load everything upfront
import HeavyComponent from './HeavyComponent'
import RarelyUsedFeature from './RarelyUsedFeature'

// ✅ FAST: Dynamic import
const HeavyComponent = dynamic(() => import('./HeavyComponent'), {
  loading: () => <Skeleton />,
})

const RarelyUsedFeature = dynamic(() => import('./RarelyUsedFeature'), {
  ssr: false, // Client-only
})

// ✅ FAST: Route-based code splitting (automatic in Next.js)
// Each page in app/ directory is automatically code-split
```

**Code Splitting Checklist:**

- [ ] Heavy libraries dynamically imported
- [ ] Third-party components lazy loaded
- [ ] Modals/dialogs lazy loaded
- [ ] Route-based splitting (automatic)
- [ ] Client-only components marked (ssr: false)

### 8. Runtime Performance (10 mins)

**React Rendering Optimization**

```typescript
// ❌ SLOW: Unnecessary re-renders
function Parent() {
  const [count, setCount] = useState(0)
  return <ExpensiveChild data={heavyData} /> // Re-renders on every count change!
}

// ✅ FAST: Memoized component
const ExpensiveChild = memo(function ExpensiveChild({ data }) {
  return <div>{/* expensive render */}</div>
})

// ✅ FAST: Memoized callback
function Parent() {
  const handleClick = useCallback(() => {
    // handler
  }, []) // Stable reference

  return <Child onClick={handleClick} />
}
```

**Runtime Checklist:**

- [ ] Expensive components memoized
- [ ] Callbacks wrapped in useCallback
- [ ] Expensive calculations in useMemo
- [ ] Large lists virtualized
- [ ] No inline function definitions in render
- [ ] Debounced/throttled event handlers

## Performance Audit Output

### Core Web Vitals

- LCP: \_\_\_\_ (Target: < 2.5s)
- FID/INP: \_\_\_\_ (Target: < 100ms)
- CLS: \_\_\_\_ (Target: < 0.1)

### Bundle Analysis

- Total Size: \_\_\_\_ (Target: < 200kb gzipped)
- First Load JS: \_\_\_\_
- Largest Bundles: \_\_\_\_

### Database Performance

- Query Count per Page: \_\_\_\_
- Slowest Queries: \_\_\_\_
- Missing Indexes: \_\_\_\_

### Optimization Recommendations

**Critical (Fix Now)**

- [ ] Issue 1
- [ ] Issue 2

**High Priority**

- [ ] Improvement 1
- [ ] Improvement 2

**Nice to Have**

- [ ] Enhancement 1
- [ ] Enhancement 2

## After Performance Review

- Fix critical performance issues
- Implement caching strategy
- Set up performance monitoring
- Create performance budget
- Regular performance audits
