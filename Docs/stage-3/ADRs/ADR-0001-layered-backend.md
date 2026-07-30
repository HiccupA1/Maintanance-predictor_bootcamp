# ADR-0001 — Layered Backend

- **Status:** Accepted
- **Decision:** Keep routers, services, repositories, and models as separate layers.
- **Context:** Domain rules include atomic alert/work-order transitions, closure side effects, and state validation.
- **Consequences:** Business behavior is testable independently of HTTP and persistence, at the cost of additional module boundaries.
