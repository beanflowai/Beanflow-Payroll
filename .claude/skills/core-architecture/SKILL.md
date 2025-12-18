---
name: core-architecture
description: Beanflow-Payroll core architecture principles - frontend-backend separation, stateless backend design, explicit parameters, multi-tab support
owner: Core Team
last_updated: 2025-12-18
triggers:
  - API design
  - architecture decisions
  - frontend-backend separation
  - data flow design
  - state management
related_skills:
  - workflow-policies
  - backend-development
  - frontend-development
agent_hints:
  token_budget_hint: "Load this skill first; for API/architecture changes, also load workflow-policies"
  write_scope: ["reads", "writes-docs"]
  plan_shape: ["Define user confirmation points", "List interface contracts"]
  approval_required_if: ["New features/architecture/interface changes (Rule-09)"]
---

# Quick Reference Card
- When to use: API contract decisions, architecture design, state management discussions
- 3-step approach:
  1) Ensure "frontend-backend separation" is respected
  2) Verify explicit parameter passing (no implicit session state)
  3) Check multi-tab support compatibility
- How to verify: Draw data flow diagram, point out user confirmation and data sources

---

# Core Architecture Principles

When making API design, data flow changes, or architecture decisions, you must follow these core principles.

## [Rule-01: Frontend-Backend Separation]

- **Frontend responsibility**: User interface, form handling, data visualization, API consumption
- **Backend responsibility**: Business logic, payroll calculations, data validation
- **Communication**: Standard HTTP/REST API, JSON payloads
- **No shared state**: Each layer maintains its own state management

**Key point**: Strict separation of responsibilities, communication through API contracts.

---

## [Rule-05: Modern Web Standards]

- **Frontend**: SvelteKit + TypeScript + TailwindCSS 4
- **Backend**: FastAPI + Pydantic + async/await
- **Database**: Supabase (PostgreSQL)
- **Testing**: Vitest (Frontend), Pytest (Backend)

**Tech selection principle**: Prioritize mature, active modern tech stack.

---

## [Rule-06: Supabase as Primary Storage]

- **Primary storage**: Supabase PostgreSQL (single source of truth)
- **Local storage**: User preferences, temporary cache
- **Auth**: Supabase Auth for user authentication
- **Privacy**: Minimize data retention, secure handling

**Data principles**:
- Supabase is the single source of truth for all payroll data
- Avoid duplicate data storage
- Clean up temporary data promptly

---

## [Rule-14: Session Responsibility Separation]

- **Session responsibility**: Only for authentication (who is logged in)
- **Business state**: Managed by frontend state management
- **Strictly prohibited**: Storing business-related state in session

**Core concept**: Session is authentication state, not a business state container.

**Example**:
```python
# Correct: Session only contains auth info
session_data = {
    "user_id": "...",
    "access_token": "...",
    "expires_at": datetime,
}

# Wrong: Session contains business state
session_data = {
    "user_id": "...",
    "current_company_id": "...",  # Business state should not be here
    "selected_pay_group": "..."    # Business state should not be here
}
```

---

## [Rule-15: Stateless Backend + Explicit Parameters]

- **All APIs**: Must explicitly receive all required business parameters
- **Strictly prohibited**: Implicitly reading business state from session
- **Frontend responsibility**: Maintain business state, explicitly pass on each API call
- **Backend responsibility**: Provide stateless services, execute based on request parameters

**Benefits**:
- Multi-tab/multi-device without conflicts
- Strong API testability (no implicit dependencies)
- Simple state sync (frontend is single source of truth)
- Easy horizontal scaling (no server-side session state)

**Example**:
```python
# Correct: Explicit parameters
@router.get("/payroll/run")
async def get_payroll_run(
    company_id: str,      # Required, explicitly passed
    pay_group_id: str,    # Required, explicitly passed
    pay_date: str,
    current_user: str = Depends(get_current_user)
) -> dict[str, Any]:
    """Get payroll run with explicit parameters."""
    service = PayrollService()
    return await service.get_payroll_run(company_id, pay_group_id, pay_date)

# Wrong: Implicit session dependency
@router.get("/payroll/run")
async def get_payroll_run(
    pay_date: str,
    session: Session = Depends(get_session)  # Reading company_id from session
) -> dict[str, Any]:
    company_id = session.current_company_id  # Implicit state
    # ...
```

```typescript
// Correct: Frontend explicitly passes parameters
const response = await payrollAPI.getPayrollRun({
  company_id: currentCompany.id,  // Explicit
  pay_group_id: selectedPayGroup.id,
  pay_date: '2025-01-15'
});

// Wrong: Relying on backend reading from session
const response = await payrollAPI.getPayrollRun({
  pay_date: '2025-01-15'  // Missing company_id and pay_group_id
});
```

---

## [Rule-16: Multi-Tab/Multi-Device Support]

Through explicit parameter passing and frontend state management, naturally supports multi-tab independent work.

**How it works**:
```
Tab A: Displaying Company A's payroll -> API call passes company_id=A
Tab B: Displaying Company B's payroll -> API call passes company_id=B
Both work independently without interference
```

**Design points**:
- Each frontend tab maintains independent state (currentCompany, selectedPayGroup)
- Backend receives explicit parameters for each request
- No shared server-side business state
- Avoid using server-side sessions for business logic state

**Anti-pattern (causes conflicts)**:
```
Wrong design: Business state stored in session
Tab A: Select Company A -> session.current_company = A
Tab B: Select Company B -> session.current_company = B
Tab A: Refresh -> Now shows Company B data!
```
