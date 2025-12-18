---
name: workflow-policies
description: Development workflow policies for Beanflow-Payroll - plan approval requirements, single-task focus, breaking changes policy during development stage, Git commit policies
owner: Core Team
last_updated: 2025-12-18
triggers:
  - plan approval
  - single-task focus
  - task management
  - backward compatibility
  - breaking changes
  - development workflow
  - git commit
  - auto-commit
  - create commit
related_skills:
  - core-architecture
  - backend-development
  - frontend-development
agent_hints:
  token_budget_hint: "For workflow requirement checks; lightweight policy check"
  write_scope: ["reads", "writes-docs"]
  plan_shape: ["Determine if approval needed", "Confirm task scope", "Check compatibility requirements"]
  approval_required_if: ["New features, API changes, architecture modifications (Rule-09)"]
  commit_policy: ["Only create Git commits when user explicitly requests (Rule-12)"]
---

# Quick Reference Card
- When to use: Before starting new tasks, determining approval needs, managing task scope, before Git commits
- 4-step approach:
  1) Determine if task requires plan approval (Rule-09)
  2) Confirm focusing only on current task, record other findings (Rule-10)
  3) Development stage allows direct breaking changes (Rule-11)
  4) Only create Git commits when user explicitly requests (Rule-12)
- How to verify: Get approval (if needed), single task complete, no leftover tech debt, user controls commits

---

# Workflow Policies

## [Rule-09: Plan Approval Requirements]

For any changes involving the following, **must** present plan and explicitly request approval before implementation:

### Requires Plan Approval

- **New user interface features** (new pages, components, workflows)
- **API contract changes** (new endpoints, modified request/response formats)
- **Architecture modifications** (new services, changed data flow)
- **External integrations** (third-party services, payment providers)
- **Database schema changes** (new tables, column modifications)

### No Plan Approval Needed

- **Bug fixes** (correcting existing functionality)
- **Code quality improvements** (refactoring, optimization)
- **Documentation updates** (README, code comments)
- **Test additions** (unit tests, integration tests)
- **UI/UX improvements** (styling, accessibility, responsive design)

**Process**: Must receive explicit positive confirmation from human developer.

---

### Plan Presentation Format

```markdown
## Task: [Feature Name]

### Objective
Brief description of the feature and why it's needed

### Impact Scope
- Backend: Adding X API endpoints, modifying Y services
- Frontend: Adding X pages/components
- Database: New/modified tables or fields

### Implementation Plan
1. **Phase 1**: Backend API implementation
   - Create `/api/v1/feature` endpoint
   - Add data validation logic
   - Write unit tests

2. **Phase 2**: Frontend integration
   - Create Feature component
   - Integrate API calls
   - Add error handling

3. **Phase 3**: Testing and validation
   - Run quality checks
   - Manual testing of key flows

### Risk Assessment
- [ ] Does this affect existing functionality?
- [ ] Does this require data migration?
- [ ] Are there external dependencies?

### Request Approval
Please confirm if the above plan is reasonable, I will begin implementation.
```

---

### Decision Flowchart

```
Start new task
    |
Creating new UI feature? ---------> Yes -> Requires approval
    | No
Modifying API contract? ----------> Yes -> Requires approval
    | No
Modifying architecture? ----------> Yes -> Requires approval
    | No
Adding external integration? -----> Yes -> Requires approval
    | No
Modifying database schema? -------> Yes -> Requires approval
    | No
No approval needed, proceed directly
```

---

## [Rule-10: Single-Task Focus]

### Core Principle

- **Strictly follow** single-task principle
- Only focus on the currently approved core task

### When Discovering Unrelated Issues

If during execution you find unrelated bugs or optimization opportunities:

1. **Strictly prohibited** to fix them immediately
2. **Must** propose recording them in project TODO list
3. Only request new task after current task is **fully completed**

**Philosophy**: Stay focused, avoid task creep, ensure each task is fully delivered.

---

### Example Scenario

#### Correct Approach

```
Task: Fix date format issue in payroll run

During execution, discovered:
- Pay period calculation also has issues
- Tax rate calculation seems inaccurate

Correct approach:
1. Only fix the date format issue
2. Report to user:
   "During the fix, I discovered the following issues:
   - Pay period calculation logic may have issues
   - Tax rate calculation needs verification

   Recommend recording these issues to TODO list, process after current task completes."
3. After completing current task, wait for new instructions
```

---

#### Wrong Approach

```
Task: Fix date format issue in payroll run

Wrong approach:
1. Fix date format
2. Also fix pay period calculation logic
3. Also refactor tax rate calculation
4. Also optimize performance

Problems:
- Task scope out of control
- May introduce new bugs
- Hard to track changes
- Cannot rollback independently
```

---

### Task Completion Criteria

Current task is only complete when meeting all:

- [ ] Core functionality implemented
- [ ] Related tests added/updated
- [ ] Quality checks passed
- [ ] Documentation updated (if needed)
- [ ] User confirmed completion

**Only start new task after completion**

---

## [Rule-11: No Backward Compatibility in Development Stage]

### Core Principle

- Project is in **development stage**, not in production
- Can make **breaking changes** directly
- No need to consider API backward compatibility
- When refactoring, modify directly, no optional parameter transitions needed

### Allowed Breaking Changes

#### 1. Direct API Signature Modifications

```python
# Development stage: Directly change optional to required
# Old code
@router.get("/payroll/summary")
async def get_payroll_summary(pay_date: str):
    # Read company_id from session
    ...

# New code: Direct breaking change
@router.get("/payroll/summary")
async def get_payroll_summary(
    company_id: str,  # <- Directly required, no optional transition
    pay_group_id: str,
    pay_date: str
):
    ...
```

---

#### 2. Direct Data Structure Modifications

```typescript
// Development stage: Directly modify interface definition
// Old code
interface Employee {
  id: string;
  name: string;
}

// New code: Direct breaking change
interface Employee {
  id: string;
  name: string;
  email: string;  // <- Directly add required field
  payGroupId: string;
}
```

---

#### 3. Direct Removal of Deprecated Fields

```python
# Development stage: Directly remove unneeded fields
# Old code
employee_data = {
    "id": employee_id,
    "name": name,
    "legacy_tax_code": None,  # <- Will be removed
}

# New code: Directly remove
employee_data = {
    "id": employee_id,
    "name": name,
    # legacy_tax_code removed
}
```

---

### Not Allowed (Only needed in production)

**Development stage does NOT need these**:

```python
# NOT needed: Optional parameter transition period
@router.get("/payroll/summary")
async def get_payroll_summary(
    company_id: str | None = None,  # <- Not needed in dev stage
    pay_date: str
):
    if company_id:
        # New logic
    else:
        # Old logic fallback
```

```python
# NOT needed: Deprecation warnings
if not company_id:
    logger.warning("[DEPRECATED] Please pass company_id")
```

---

### When Is Backward Compatibility Needed?

**Only in these situations**:

- Project is in production
- External systems depend on your API
- Multiple teams developing in parallel
- Zero-downtime deployment required

**Current project status**: Development stage, none of the above apply.

---

### Best Practices

1. **Modify directly, no transition needed**
   - Found design issue, refactor immediately
   - No need for optional parameters
   - No need to keep old code paths

2. **Update all callers synchronously**
   - Backend modifies API signature
   - Frontend updates all calls simultaneously
   - Complete at once, no tech debt

3. **Clean up completely**
   - Delete deprecated code
   - Delete deprecated fields
   - Delete deprecated comments

**Philosophy**: Development stage prioritizes code quality and architecture clarity, don't sacrifice design for backward compatibility. Iterate quickly, refactor boldly.

---

## [Rule-12: Git Commit Policy]

### Core Principle

**Auto-commit is strictly prohibited**: AI assistant must not create Git commits without user's explicit request.

### Commit Timing

#### Allowed to Create Commits

**Only when user explicitly requests**:

- User explicitly says "please commit these changes"
- User says "create a commit"
- User says "commit these changes"
- User says "commit to git"

#### Prohibited Auto-Commit Situations

Even after completing a task, **strictly prohibited** to auto-create commits:

- After fixing bugs
- After implementing new features
- After completing code review
- After passing quality checks
- After completing any development task

### Correct Workflow

```
1. Implement changes
2. Run tests
3. Quality checks
4. Show change summary to user
5. Wait for user's explicit instruction
   |- User says "commit" -> Create commit
   |- User doesn't say "commit" -> Don't create commit
```

### Example Scenarios

#### Correct Approach

```
Task: Fix payroll calculation bug

AI Assistant:
1. Fix bug
2. Run tests
3. Report to user:
   "Bug fixed! Change summary:
   - Modified calculateGrossPay() function
   - Fixed overtime calculation logic
   - All tests passed

   Changed files:
   - backend/app/services/payroll_service.py
   - backend/tests/test_payroll.py

   Do you want me to create a commit?"

4. Wait for user instruction
```

#### Wrong Approach

```
Task: Fix payroll calculation bug

AI Assistant:
1. Fix bug
2. Run tests
3. Auto-create commit
4. Report to user: "Done and committed to git"

Problems:
- User didn't request commit
- Deprived user of chance to review changes
- User might want to continue modifying
- Violates user control principle
```

### Exceptions

**No exceptions**. Even in these cases, do not auto-commit:

- "This is a small change" - Still needs user confirmation
- "All tests passed" - Still needs user confirmation
- "Just a bug fix" - Still needs user confirmation
- "Plan was approved" - Approved the changes, not the commit

### Commit Message Format

When user explicitly requests commit, follow this format:

```
<type>(<scope>): <subject>

<body>

Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Refactoring
- `docs`: Documentation
- `style`: Code formatting
- `test`: Tests
- `chore`: Build/tooling

### Philosophy

Respect user's control. User should have the opportunity to:
- Review all changes
- Decide when to create commits
- Decide commit message content
- Possibly want to continue modifying

**Never make commit decisions for the user.**

---

**Philosophy**: Clear workflow ensures quality delivery. Approval mechanism prevents blind implementation, single-task focus improves completion rate, development stage flexibility accelerates iteration. User control is paramount, AI assistant only operates Git when explicitly instructed.
