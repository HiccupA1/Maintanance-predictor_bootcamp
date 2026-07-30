# Entity Relationship Design

```mermaid
erDiagram
    EQUIPMENT ||--o{ PARAMETER : configures
    EQUIPMENT ||--o{ READING : receives
    PARAMETER ||--o{ READING : describes
    EQUIPMENT ||--o{ ALERT : affects
    ALERT ||--o| WORK_ORDER : becomes
    WORK_ORDER ||--o{ WORK_ORDER_PART_LINE : contains
```

Core entities include equipment, parameters, readings, alerts, work orders, and work-order part lines. A work order references one source alert, while an alert may have at most one work order. Closure stores resolution notes, root cause, closed timestamp, and actor.
