---
description: Design system architecture and make high-level technical decisions
---

You are in **ARCHITECTURE DESIGN MODE**.

Use the **architect** agent to:

1. **Analyze Requirements**
   - Understand functional and non-functional requirements
   - Identify constraints (budget, timeline, team size, existing systems)
   - Clarify scale expectations (users, data volume, geographic distribution)

2. **Design System Architecture**
   - Choose architectural pattern (monolith, microservices, serverless)
   - Design system components and their interactions
   - Create architecture diagrams (component, deployment, sequence)
   - Define data flow and integration points

3. **Make Technology Decisions**
   - Select appropriate tech stack based on requirements
   - Choose database strategy (SQL vs NoSQL, single vs multiple DBs)
   - Define API architecture (REST, GraphQL, tRPC, gRPC)
   - Plan authentication and authorization strategy
   - Choose deployment platform (Vercel, AWS, GCP, Azure, on-prem)

4. **Plan for Scalability**
   - Identify scaling bottlenecks
   - Design caching strategy (client, CDN, server, database)
   - Plan for horizontal and vertical scaling
   - Design for resilience (circuit breakers, retries, fallbacks)

5. **Document Decisions**
   - Create Architecture Decision Records (ADRs)
   - Document trade-offs and rationale
   - Define success metrics
   - Plan migration path if applicable

**Output**: Comprehensive architecture design document with diagrams, technology stack, and clear rationale for decisions.

**Next Steps After Design**:

- Use `/mcp-design-nextjs` or `/mcp-design-spring` for technology-specific design
- Use `/mcp-implement-fullstack` to start implementation
- Use `/mcp-review-code` to review architecture decisions in code
