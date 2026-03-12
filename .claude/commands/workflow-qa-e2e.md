---
description: Write comprehensive end-to-end tests with Playwright
---

You are in **E2E TESTING MODE**.

Use **qa-tester** agent to write Playwright end-to-end tests.

## E2E Testing Workflow

### 1. Test Planning (10 mins)

**Identify Critical User Flows**

- [ ] User authentication (signup, login, logout)
- [ ] Core feature usage (create, read, update, delete)
- [ ] Payment/checkout flows
- [ ] Form submissions
- [ ] Navigation and routing
- [ ] Error scenarios

**Define Test Scenarios**

```typescript
// User Story: User can create and publish a blog post

Scenarios:
1. Happy path: Create and publish post successfully
2. Validation: Form validation prevents invalid input
3. Authorization: Only authenticated users can create posts
4. Error handling: Network error shows appropriate message
5. Edge case: Very long title/content
```

### 2. Playwright Setup (5 mins)

**Install Playwright**

```bash
npm install -D @playwright/test
npx playwright install
```

**playwright.config.ts**

```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'mobile',
      use: { ...devices['iPhone 13'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

### 3. Page Object Model (15 mins)

**Create Page Objects for Reusability**

```typescript
// e2e/pages/login.page.ts
import { Page, Locator } from '@playwright/test'

export class LoginPage {
  readonly page: Page
  readonly emailInput: Locator
  readonly passwordInput: Locator
  readonly submitButton: Locator
  readonly errorMessage: Locator

  constructor(page: Page) {
    this.page = page
    this.emailInput = page.getByLabel('Email')
    this.passwordInput = page.getByLabel('Password')
    this.submitButton = page.getByRole('button', { name: 'Sign in' })
    this.errorMessage = page.getByRole('alert')
  }

  async goto() {
    await this.page.goto('/login')
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email)
    await this.passwordInput.fill(password)
    await this.submitButton.click()
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message)
  }
}

// e2e/pages/posts.page.ts
export class PostsPage {
  readonly page: Page
  readonly createButton: Locator
  readonly titleInput: Locator
  readonly contentInput: Locator
  readonly publishButton: Locator

  constructor(page: Page) {
    this.page = page
    this.createButton = page.getByRole('button', { name: 'New Post' })
    this.titleInput = page.getByLabel('Title')
    this.contentInput = page.getByLabel('Content')
    this.publishButton = page.getByRole('button', { name: 'Publish' })
  }

  async goto() {
    await this.page.goto('/posts')
  }

  async createPost(title: string, content: string) {
    await this.createButton.click()
    await this.titleInput.fill(title)
    await this.contentInput.fill(content)
    await this.publishButton.click()
  }

  async getPostByTitle(title: string) {
    return this.page.getByRole('article', { name: title })
  }
}
```

### 4. Authentication Helper (10 mins)

```typescript
// e2e/helpers/auth.ts
import { Page } from '@playwright/test'

export async function loginAsUser(page: Page, email: string, password: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: 'Sign in' }).click()
  await page.waitForURL('/dashboard')
}

export async function loginAsAdmin(page: Page) {
  await loginAsUser(page, 'admin@example.com', 'AdminPassword123')
}

// Create test user fixture
export async function createTestUser() {
  // Call API to create test user
  const response = await fetch('http://localhost:3000/api/test/users', {
    method: 'POST',
    body: JSON.stringify({
      email: `test-${Date.now()}@example.com`,
      password: 'TestPassword123',
    }),
  })
  return response.json()
}
```

### 5. Write E2E Tests (30-60 mins)

**Authentication Flow Tests**

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test'
import { LoginPage } from './pages/login.page'

test.describe('Authentication', () => {
  let loginPage: LoginPage

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page)
    await loginPage.goto()
  })

  test('user can sign up with valid credentials', async ({ page }) => {
    await page.goto('/signup')
    await page.getByLabel('Email').fill('newuser@example.com')
    await page.getByLabel('Name').fill('New User')
    await page.getByLabel('Password').fill('Password123!')
    await page.getByRole('button', { name: 'Sign up' }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByText('Welcome, New User')).toBeVisible()
  })

  test('user can login with valid credentials', async ({ page }) => {
    await loginPage.login('user@example.com', 'Password123!')

    await expect(page).toHaveURL('/dashboard')
    await expect(page.getByRole('button', { name: 'Logout' })).toBeVisible()
  })

  test('login fails with invalid credentials', async () => {
    await loginPage.login('user@example.com', 'WrongPassword')

    await loginPage.expectError('Invalid email or password')
    await expect(loginPage.page).toHaveURL('/login')
  })

  test('user can logout', async ({ page }) => {
    await loginPage.login('user@example.com', 'Password123!')
    await page.getByRole('button', { name: 'Logout' }).click()

    await expect(page).toHaveURL('/login')
  })
})
```

**CRUD Operations Tests**

```typescript
// e2e/posts.spec.ts
import { test, expect } from '@playwright/test'
import { PostsPage } from './pages/posts.page'
import { loginAsUser } from './helpers/auth'

test.describe('Posts', () => {
  let postsPage: PostsPage

  test.beforeEach(async ({ page }) => {
    await loginAsUser(page, 'user@example.com', 'Password123!')
    postsPage = new PostsPage(page)
    await postsPage.goto()
  })

  test('user can create a new post', async ({ page }) => {
    const title = `Test Post ${Date.now()}`
    const content = 'This is test content'

    await postsPage.createPost(title, content)

    // Verify post appears in list
    const post = await postsPage.getPostByTitle(title)
    await expect(post).toBeVisible()
    await expect(post).toContainText(content)
  })

  test('form validation prevents invalid post', async ({ page }) => {
    await postsPage.createButton.click()

    // Try to submit without title
    await postsPage.publishButton.click()

    await expect(page.getByText('Title is required')).toBeVisible()
  })

  test('user can edit their own post', async ({ page }) => {
    const newTitle = `Updated Post ${Date.now()}`

    // Find existing post
    const post = await page.getByRole('article').first()
    await post.getByRole('button', { name: 'Edit' }).click()

    // Edit title
    await page.getByLabel('Title').fill(newTitle)
    await page.getByRole('button', { name: 'Save' }).click()

    // Verify update
    await expect(page.getByRole('article', { name: newTitle })).toBeVisible()
  })

  test('user can delete their own post', async ({ page }) => {
    const post = await page.getByRole('article').first()
    const postTitle = await post.getByRole('heading').textContent()

    // Delete post
    await post.getByRole('button', { name: 'Delete' }).click()
    await page.getByRole('button', { name: 'Confirm' }).click()

    // Verify deletion
    await expect(
      page.getByRole('article', { name: postTitle! })
    ).not.toBeVisible()
  })

  test("user cannot edit another user's post", async ({ page }) => {
    // Navigate to another user's post
    await page.goto('/posts/another-user-post-id')

    // Edit button should not exist
    await expect(page.getByRole('button', { name: 'Edit' })).not.toBeVisible()
  })
})
```

**Form Validation Tests**

```typescript
// e2e/forms.spec.ts
test.describe('Form Validation', () => {
  test('validates email format', async ({ page }) => {
    await page.goto('/signup')
    await page.getByLabel('Email').fill('invalid-email')
    await page.getByLabel('Email').blur()

    await expect(page.getByText('Invalid email format')).toBeVisible()
  })

  test('validates password strength', async ({ page }) => {
    await page.goto('/signup')
    await page.getByLabel('Password').fill('weak')
    await page.getByLabel('Password').blur()

    await expect(
      page.getByText('Password must be at least 8 characters')
    ).toBeVisible()
  })

  test('shows real-time validation', async ({ page }) => {
    await page.goto('/signup')
    const emailInput = page.getByLabel('Email')

    // Type invalid email
    await emailInput.fill('test@')
    await expect(page.getByText('Invalid email')).toBeVisible()

    // Fix email
    await emailInput.fill('test@example.com')
    await expect(page.getByText('Invalid email')).not.toBeVisible()
  })
})
```

**Responsive/Mobile Tests**

```typescript
// e2e/mobile.spec.ts
import { test, expect, devices } from '@playwright/test'

test.use({ ...devices['iPhone 13'] })

test.describe('Mobile Experience', () => {
  test('mobile menu works', async ({ page }) => {
    await page.goto('/')

    // Open mobile menu
    await page.getByLabel('Menu').click()
    await expect(page.getByRole('navigation')).toBeVisible()

    // Navigate to posts
    await page.getByRole('link', { name: 'Posts' }).click()
    await expect(page).toHaveURL('/posts')
  })

  test('form works on mobile', async ({ page }) => {
    await page.goto('/login')

    // Fill form
    await page.getByLabel('Email').fill('user@example.com')
    await page.getByLabel('Password').fill('Password123!')

    // Keyboard should not obscure submit button
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page).toHaveURL('/dashboard')
  })
})
```

**Error Scenarios Tests**

```typescript
// e2e/errors.spec.ts
test.describe('Error Handling', () => {
  test('shows error when API fails', async ({ page, context }) => {
    // Simulate network failure
    await context.route('**/api/posts', (route) => {
      route.abort('failed')
    })

    await page.goto('/posts')

    await expect(page.getByText('Failed to load posts')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible()
  })

  test('shows 404 page for invalid route', async ({ page }) => {
    await page.goto('/invalid-page-that-does-not-exist')

    await expect(page.getByRole('heading', { name: '404' })).toBeVisible()
    await expect(page.getByText('Page not found')).toBeVisible()
  })
})
```

### 6. Test Data Management (10 mins)

```typescript
// e2e/fixtures/test-data.ts
import { test as base } from '@playwright/test'

type TestData = {
  testUser: { email: string; password: string }
  testPost: { title: string; content: string }
}

export const test = base.extend<TestData>({
  testUser: async ({ page }, use) => {
    // Create test user before test
    const user = await createTestUser()

    // Provide to test
    await use(user)

    // Cleanup after test
    await deleteTestUser(user.id)
  },

  testPost: async ({ page }, use) => {
    const post = {
      title: `Test Post ${Date.now()}`,
      content: 'Test content for E2E testing',
    }

    await use(post)
  },
})
```

## E2E Testing Checklist

**Test Coverage**

- [ ] Authentication flows (signup, login, logout)
- [ ] CRUD operations for main entities
- [ ] Form validation (client and server)
- [ ] Authorization checks
- [ ] Error scenarios (API failures, 404s)
- [ ] Responsive/mobile experience
- [ ] Navigation and routing

**Test Quality**

- [ ] Page Object Model used
- [ ] Tests are independent (can run in parallel)
- [ ] Test data cleanup after tests
- [ ] Meaningful test names
- [ ] Waiting strategies (not arbitrary waits)
- [ ] Screenshot on failure
- [ ] Retry on flaky tests (in CI)

**Coverage Metrics**

- [ ] Critical user flows: 100%
- [ ] Important features: 80%+
- [ ] Edge cases: 60%+

## Running Tests

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test e2e/auth.spec.ts

# Run in headed mode (see browser)
npx playwright test --headed

# Run specific browser
npx playwright test --project=chromium

# Debug mode
npx playwright test --debug

# UI mode (interactive)
npx playwright test --ui

# Generate code (record interactions)
npx playwright codegen http://localhost:3000
```

## After E2E Testing

- Run tests in CI/CD pipeline
- Set up test reports
- Monitor flaky tests
- Update tests when features change
- Expand coverage for new features
