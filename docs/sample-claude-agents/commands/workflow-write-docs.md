---
description: Create comprehensive technical documentation with MkDocs Material
---

You are in **DOCUMENTATION MODE**.

Use **tech-writer** agent to create professional, comprehensive documentation.

## Documentation Workflow

### 1. Documentation Planning (10 mins)

**Identify Documentation Needs**

- [ ] README.md (project overview, quick start)
- [ ] API Reference (endpoints, schemas, examples)
- [ ] User Guides (how-to guides, tutorials)
- [ ] Architecture Documentation (system design, diagrams)
- [ ] Deployment Documentation (setup, configuration)
- [ ] Contributing Guidelines
- [ ] Changelog

**Define Target Audience**

- Developers (API docs, architecture)
- End Users (user guides, tutorials)
- DevOps (deployment, monitoring)
- Contributors (setup, conventions)

**Choose Documentation Format**

- README.md for quick start
- MkDocs Material for comprehensive docs site
- JSDoc/TSDoc for code documentation
- OpenAPI/Swagger for API docs

### 2. README.md Creation (15 mins)

**Essential Sections**

````markdown
# Project Name

Brief, compelling description (1-2 sentences)

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Quick Start

```bash
# Install
npm install

# Run
npm run dev
```
````

## Installation

Detailed setup instructions...

## Usage

Basic usage examples...

## API Reference

Link to full API docs...

## Configuration

Environment variables and configuration...

## Contributing

How to contribute...

## License

MIT License

````

**README Checklist**
- [ ] Clear project description
- [ ] Quick start (< 5 minutes)
- [ ] Installation instructions
- [ ] Basic usage examples
- [ ] Links to full documentation
- [ ] Badges (build status, coverage, version)
- [ ] Screenshots or demos
- [ ] License information

### 3. MkDocs Material Setup (20 mins)

**Install MkDocs Material**
```bash
pip install mkdocs-material
pip install mkdocs-material[imaging]  # For social cards
````

**Create mkdocs.yml**

```yaml
site_name: Your Project
site_description: Comprehensive documentation
site_author: Your Name
site_url: https://yourusername.github.io/project

repo_name: username/project
repo_url: https://github.com/username/project
edit_uri: edit/main/docs/

theme:
  name: material
  custom_dir: docs/overrides
  language: en
  palette:
    # Light mode
    - scheme: default
      primary: indigo
      accent: blue
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Dark mode
    - scheme: slate
      primary: black
      accent: light blue
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Work Sans
    code: JetBrains Mono
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.sections
    - navigation.expand
    - navigation.indexes
    - navigation.top
    - toc.follow
    - search.suggest
    - search.highlight
    - search.share
    - content.code.copy
    - content.code.annotate

extra_css:
  - stylesheets/extra.css

extra_javascript:
  - https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js
  - javascripts/mermaid-init.js

markdown_extensions:
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - meta
  - md_in_html
  - toc:
      permalink: true
      toc_depth: 3
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:pymdownx.superfences.fence_code_format
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde

nav:
  - Home: index.md
  - Getting Started:
      - Overview: getting-started/overview.md
      - Installation: getting-started/installation.md
      - Quick Start: getting-started/quick-start.md
  - User Guide:
      - Introduction: guide/introduction.md
      - Configuration: guide/configuration.md
      - Usage: guide/usage.md
  - API Reference:
      - Overview: api/overview.md
      - Authentication: api/authentication.md
      - Endpoints: api/endpoints.md
  - Architecture:
      - System Design: architecture/system-design.md
      - Database Schema: architecture/database.md
      - Security: architecture/security.md
  - Deployment:
      - Production: deployment/production.md
      - CI/CD: deployment/cicd.md
  - Contributing:
      - Guidelines: contributing/guidelines.md
      - Development: contributing/development.md

plugins:
  - search

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/username/project
```

**Create Directory Structure**

```bash
mkdir -p docs/{stylesheets,javascripts,getting-started,guide,api,architecture,deployment,contributing}
```

**MkDocs Setup Checklist**

- [ ] mkdocs.yml configured
- [ ] Theme customized (colors, fonts)
- [ ] Navigation structure defined
- [ ] Custom CSS created
- [ ] Mermaid diagrams enabled
- [ ] Search configured

### 4. API Documentation (30 mins)

**REST API Documentation**

````markdown
# API Reference

## Authentication

All API requests require authentication using JWT tokens.

### Get Access Token

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```
````

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

## Endpoints

### Posts

#### List Posts

```http
GET /api/posts?page=1&limit=10
Authorization: Bearer {token}
```

**Query Parameters:**

| Parameter | Type    | Required | Description                            |
| --------- | ------- | -------- | -------------------------------------- |
| page      | integer | No       | Page number (default: 1)               |
| limit     | integer | No       | Items per page (default: 10, max: 100) |
| published | boolean | No       | Filter by published status             |
| authorId  | string  | No       | Filter by author                       |

**Response:**

```json
{
  "posts": [
    {
      "id": "1",
      "title": "Post Title",
      "content": "Post content...",
      "published": true,
      "author": {
        "id": "123",
        "name": "John Doe"
      },
      "createdAt": "2024-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "totalPages": 10
  }
}
```

**Error Responses:**

| Code | Description                             |
| ---- | --------------------------------------- |
| 400  | Bad Request - Invalid parameters        |
| 401  | Unauthorized - Invalid or missing token |
| 403  | Forbidden - Insufficient permissions    |
| 404  | Not Found - Resource doesn't exist      |
| 500  | Internal Server Error                   |

#### Create Post

```http
POST /api/posts
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "My New Post",
  "content": "Post content here...",
  "published": false
}
```

**Request Body:**

| Field     | Type    | Required | Description                          |
| --------- | ------- | -------- | ------------------------------------ |
| title     | string  | Yes      | Post title (max 255 chars)           |
| content   | string  | Yes      | Post content (markdown supported)    |
| published | boolean | No       | Publish immediately (default: false) |

**Response:**

```json
{
  "id": "2",
  "title": "My New Post",
  "content": "Post content here...",
  "published": false,
  "authorId": "123",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

````

**tRPC Documentation**
```markdown
# tRPC API Reference

## Post Router

### Query: List Posts

```typescript
const { data } = trpc.post.list.useQuery({
  limit: 10,
  cursor: undefined,
  published: true,
})
````

**Input Schema:**

```typescript
{
  limit: number // 1-100, default: 10
  cursor?: string // For pagination
  published?: boolean // Filter by status
}
```

**Output:**

```typescript
{
  posts: Post[]
  nextCursor?: string
}
```

### Mutation: Create Post

```typescript
const createPost = trpc.post.create.useMutation()

await createPost.mutateAsync({
  title: 'My Post',
  content: 'Content here...',
  published: false,
})
```

**Input Schema:**

```typescript
{
  title: string // Min 1, max 255
  content: string // Min 1
  published?: boolean // Default: false
}
```

**Output:**

```typescript
{
  id: string
  title: string
  content: string
  published: boolean
  authorId: string
  createdAt: Date
}
```

````

**API Documentation Checklist**
- [ ] All endpoints documented
- [ ] Request/response examples
- [ ] Parameter descriptions
- [ ] Error responses
- [ ] Authentication explained
- [ ] Code examples in multiple languages
- [ ] Rate limiting information

### 5. User Guides & Tutorials (30 mins)

**Getting Started Guide**
```markdown
# Getting Started

This guide will help you get up and running with [Project Name].

## Prerequisites

Before you begin, ensure you have:

1. Node.js 20 or higher installed
2. PostgreSQL database running
3. Basic knowledge of Next.js and React
4. Git installed

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/username/project.git
cd project
````

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

Create a `.env.local` file in the root directory:

```env
DATABASE_URL="postgresql://user:password@localhost:5432/db"
NEXTAUTH_SECRET="your-secret-key"
NEXTAUTH_URL="http://localhost:3000"
```

!!! warning "Security"
Never commit `.env` files to version control. Add them to `.gitignore`.

### 4. Run Database Migrations

```bash
npx prisma migrate dev
npx prisma generate
```

### 5. Start Development Server

```bash
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) to see your app.

!!! success "Success!"
You should see the application running at http://localhost:3000

## Next Steps

- [Configuration Guide](../guide/configuration.md) - Configure the application
- [API Reference](../api/overview.md) - Explore the API
- [Deployment](../deployment/production.md) - Deploy to production

````

**Tutorial Example**
```markdown
# Tutorial: Building Your First Blog Post

In this tutorial, you'll learn how to create a blog post feature.

## What You'll Build

By the end of this tutorial, you'll have:

- A form to create blog posts
- A list view to display posts
- Edit and delete functionality
- Authentication protection

**Estimated time:** 30 minutes

## Step 1: Create the Database Schema

First, let's define the Post model in your Prisma schema:

```prisma
// prisma/schema.prisma
model Post {
  id        String   @id @default(cuid())
  title     String
  content   String   @db.Text
  published Boolean  @default(false)
  authorId  String
  author    User     @relation(fields: [authorId], references: [id])
  createdAt DateTime @default(now())

  @@index([authorId])
}
````

Run the migration:

```bash
npx prisma migrate dev --name add_posts
```

## Step 2: Create the tRPC Router

[Continue with detailed steps...]

## Conclusion

You've successfully built a blog post feature! You learned:

- How to design a database schema with Prisma
- How to create type-safe APIs with tRPC
- How to build forms with react-hook-form
- How to implement authentication

## Next Steps

- Add comments to posts
- Implement rich text editing
- Add image uploads

````

**User Guide Checklist**
- [ ] Prerequisites listed
- [ ] Step-by-step instructions
- [ ] Code examples
- [ ] Screenshots/visuals
- [ ] Common errors explained
- [ ] Next steps provided

### 6. Architecture Documentation (20 mins)

**System Architecture Document**
```markdown
# System Architecture

## Overview

[Project Name] is a modern full-stack application built with Next.js 15, featuring real-time capabilities, type-safe APIs, and enterprise-grade security.

## Architecture Diagram

```mermaid
graph TB
    Client[Client Browser]
    NextJS[Next.js App Router]
    API[tRPC API Layer]
    Auth[NextAuth.js]
    DB[(PostgreSQL)]
    Cache[(Redis Cache)]

    Client -->|HTTPS| NextJS
    NextJS -->|SSR/SSG| Client
    NextJS --> API
    API --> Auth
    API --> DB
    API --> Cache
    Auth --> DB

    style Client fill:#E0E0E0,stroke:#616161,stroke-width:2px,color:#000
    style NextJS fill:#F5F5F5,stroke:#757575,stroke-width:2px,color:#000
    style API fill:#EEEEEE,stroke:#9E9E9E,stroke-width:2px,color:#000
    style Auth fill:#BDBDBD,stroke:#616161,stroke-width:2px,color:#000
    style DB fill:#FAFAFA,stroke:#424242,stroke-width:2px,color:#000
    style Cache fill:#F5F5F5,stroke:#757575,stroke-width:2px,color:#000
````

## Technology Stack

### Frontend

- **Next.js 15** - React framework with App Router
- **React 18** - UI library with Server Components
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Component library built on Radix UI

### Backend

- **Next.js API Routes** - Serverless API endpoints
- **tRPC** - End-to-end type-safe API layer
- **NextAuth.js v5** - Authentication framework
- **Prisma** - Type-safe database ORM

### Database

- **PostgreSQL** - Primary relational database
- **Redis** - Caching and session storage

### Infrastructure

- **Vercel** - Hosting and deployment platform
- **GitHub Actions** - CI/CD pipeline
- **Sentry** - Error tracking and monitoring

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant Next.js
    participant tRPC
    participant Prisma
    participant PostgreSQL

    User->>Next.js: Request /posts
    Next.js->>tRPC: post.list()
    tRPC->>Prisma: findMany()
    Prisma->>PostgreSQL: SELECT * FROM posts
    PostgreSQL-->>Prisma: Results
    Prisma-->>tRPC: Post[]
    tRPC-->>Next.js: Typed data
    Next.js-->>User: Rendered page

    box rgba(224,224,224,0.2) Browser
    participant User
    end
    box rgba(245,245,245,0.2) Application
    participant Next.js
    participant tRPC
    participant Prisma
    end
    box rgba(250,250,250,0.2) Database
    participant PostgreSQL
    end
```

## Security Architecture

- **Authentication**: NextAuth.js with JWT tokens
- **Authorization**: Role-based access control (RBAC)
- **Input Validation**: Zod schemas at API boundaries
- **SQL Injection Prevention**: Prisma ORM with parameterized queries
- **XSS Prevention**: React automatic escaping + CSP headers
- **CSRF Protection**: Built-in Next.js CSRF tokens
- **Rate Limiting**: Redis-based rate limiter
- **Security Headers**: Helmet.js configuration

## Scalability Considerations

- **Horizontal Scaling**: Stateless Next.js instances
- **Database Optimization**: Indexes on frequently queried columns
- **Caching Strategy**: Multi-layer caching (browser, CDN, Redis)
- **CDN**: Static assets served via Vercel Edge Network
- **Connection Pooling**: PgBouncer for database connections

````

**Architecture Documentation Checklist**
- [ ] System overview
- [ ] Architecture diagrams (Mermaid)
- [ ] Technology stack explained
- [ ] Data flow documented
- [ ] Security architecture
- [ ] Scalability considerations
- [ ] Integration points

### 7. Build and Deploy Documentation Site (10 mins)

**Build Documentation**
```bash
# Serve locally
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
````

**Add to package.json**

```json
{
  "scripts": {
    "docs:dev": "mkdocs serve",
    "docs:build": "mkdocs build",
    "docs:deploy": "mkdocs gh-deploy"
  }
}
```

**GitHub Pages Setup**

1. Go to repository Settings → Pages
2. Source: Deploy from a branch
3. Branch: gh-pages
4. Folder: / (root)

**Documentation Deployment Checklist**

- [ ] MkDocs builds successfully
- [ ] All links work
- [ ] Images display correctly
- [ ] Search works
- [ ] Navigation is intuitive
- [ ] Mobile responsive
- [ ] Deployed to hosting

## Documentation Checklist

### Essential Documentation

- [ ] README.md with quick start
- [ ] Installation guide
- [ ] API reference
- [ ] User guides/tutorials
- [ ] Architecture documentation
- [ ] Deployment guide
- [ ] Contributing guidelines

### Quality Standards

- [ ] Clear, concise writing
- [ ] No jargon (or explained)
- [ ] Code examples work
- [ ] Screenshots current
- [ ] Links not broken
- [ ] Mobile-friendly
- [ ] Searchable
- [ ] Accessibility (WCAG AA)

### Maintenance

- [ ] Version documentation
- [ ] Changelog maintained
- [ ] Deprecated features marked
- [ ] Regular updates scheduled

## After Documentation

- Share documentation URL with team
- Add documentation link to README
- Set up documentation CI/CD
- Schedule regular reviews
- Gather user feedback
- Update as features change
