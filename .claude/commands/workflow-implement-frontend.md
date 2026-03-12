---
description: Implement frontend UI components and client-side features
---

You are in **FRONTEND IMPLEMENTATION MODE**.

Use **frontend-ui** agent to build modern, accessible UI components.

## Implementation Workflow

### 1. Component Planning (5 mins)

- Identify component type (Server or Client Component)
- Plan component hierarchy
- Define props interface
- List required shadcn/ui components

### 2. Install shadcn/ui Components (2 mins)

```bash
# Install required components
npx shadcn-ui@latest add button
npx shadcn-ui@latest add form
npx shadcn-ui@latest add input
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
```

### 3. Build UI Components (20-30 mins)

Create components following these patterns:

**Form Components** (with react-hook-form + Zod)

```typescript
// Example: PostForm component
- Define Zod schema
- Set up useForm with zodResolver
- Build form with shadcn/ui Form components
- Handle submission with Server Actions
- Show validation errors
- Add loading states
```

**Display Components**

```typescript
// Example: PostCard component
- Use shadcn/ui Card, Badge, Button
- Implement responsive design
- Add hover states and animations
- Include accessibility attributes
```

**Interactive Components**

```typescript
// Example: DeletePostDialog
- Use shadcn/ui Dialog, AlertDialog
- Add confirmation step
- Implement optimistic updates
- Show toast notifications
```

### 4. Client-Side Features (15-20 mins)

**State Management**

- Use useState for local UI state
- Use Zustand for global client state
- Use React Query for server state

**Optimistic Updates**

```typescript
// Example: Like post optimistically
- Update UI immediately
- Call API in background
- Rollback on error
- Show toast on success/error
```

**Infinite Scroll/Pagination**

```typescript
// Use TanStack Query + Intersection Observer
- Implement useInfiniteQuery
- Add loading skeleton
- Handle edge cases (empty, error)
```

### 5. Responsive Design (10 mins)

- Mobile-first approach with Tailwind
- Test on different screen sizes
- Use Tailwind breakpoints (sm, md, lg, xl)
- Ensure touch targets are 44x44px minimum

### 6. Accessibility (10 mins)

- Add ARIA labels and roles
- Ensure keyboard navigation works
- Test with screen reader
- Check color contrast (WCAG AA)
- Add focus indicators

### 7. Animations & Polish (5-10 mins)

- Add Framer Motion animations (optional)
- Smooth transitions with Tailwind
- Loading skeletons
- Empty states
- Error states

## Implementation Checklist

**Component Structure**

- [ ] Client/Server Component decision made correctly
- [ ] TypeScript interfaces defined
- [ ] Props validated
- [ ] Component exported

**shadcn/ui Integration**

- [ ] Required components installed
- [ ] Components styled with Tailwind
- [ ] Dark mode support
- [ ] Responsive design

**Forms**

- [ ] react-hook-form setup
- [ ] Zod schema validation
- [ ] Error messages displayed
- [ ] Loading states
- [ ] Success feedback

**Interactivity**

- [ ] Event handlers implemented
- [ ] Optimistic updates
- [ ] Loading states
- [ ] Error handling
- [ ] Toast notifications

**Accessibility**

- [ ] ARIA labels added
- [ ] Keyboard navigation works
- [ ] Focus management
- [ ] Color contrast WCAG AA
- [ ] Screen reader tested

**Responsive**

- [ ] Works on mobile (320px+)
- [ ] Works on tablet (768px+)
- [ ] Works on desktop (1024px+)
- [ ] Touch targets adequate

**Performance**

- [ ] No unnecessary re-renders
- [ ] Images optimized with next/image
- [ ] Lazy loading for heavy components
- [ ] Debounced inputs where needed

## After Implementation

- Use `/workflow-review-code` to review component quality
- Use `/workflow-qa-e2e` to write component tests
- Use `/workflow-review-performance` to optimize rendering
