# Project Guidelines

## Documentation Requirements

-   Update relevant documentation in /docs when modifying features
-   Keep README.md in sync with new capabilities
-   Maintain changelog entries in CHANGELOG.md

## Architecture Decision Records

Create ADRs in /docs/adr for:

-   Major dependency changes
-   Architectural pattern changes
-   New integration patterns
-   Database schema changes
-   Follow template in /docs/adr/template.md

### Best Practices for Writing ADRs

-   Keep them concise but complete
-   Use clear, simple language
-   Focus on the decision and its rationale
-   Document alternatives that were considered
-   Update the status as the decision evolves
-   Link related ADRs to show the decision history
-   Include mermaid diagrams when they help clarify the decision

## Code Style & Patterns

-   Generate API clients using OpenAPI Generator
-   Place generated code in /src/generated
-   Prefer composition over inheritance
-   Use repository pattern for data access

## Testing Standards

-   Unit tests required for business logic
-   Integration tests for API endpoints
-   E2E tests for critical user flows