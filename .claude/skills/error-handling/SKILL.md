---
name: error-handling
description: Error handling and transparent fallback strategies for Beanflow-Payroll - prohibit hiding errors with mock data, allow transparent degradation with clear user notification, graceful failure patterns
owner: Core Team
last_updated: 2025-12-18
triggers:
  - error handling
  - fallback strategy
  - transparent degradation
  - hiding errors
  - graceful degradation
  - mock data
  - error messages
related_skills:
  - backend-development
  - frontend-development
  - core-architecture
agent_hints:
  token_budget_hint: "Focus on error handling strategies; combine with implementation skills when needed"
  write_scope: ["writes-backend", "writes-frontend"]
  plan_shape: ["Determine if fallback strategy is transparent", "Design error messages", "Implement graceful degradation"]
  approval_required_if: []
---

# Quick Reference Card
- When to use: Handling API failures, implementing fallback logic, designing error handling
- 3-step approach:
  1) Confirm if error is transparent to user (transparent vs hidden)
  2) Design clear error messages or warning notifications
  3) Implement degradation logic (if necessary), ensure user is informed
- How to verify: User clearly knows what happened, errors are not concealed

---

# Error Handling Transparency Principles

## [Rule-08: Prohibit Error-Hiding Fallback Logic]

### Core Principle

**Prohibit hiding errors, allow transparent degradation**

- Strictly prohibited: Silent failures and hidden errors
- Allowed: Transparent degradation strategies (clearly inform user)

---

## Strictly Prohibited (Hiding Errors)

### 1. Silently Using Mock Data

```typescript
// Wrong: API fails, automatically return fake data, user unaware
async function fetchEmployees() {
  try {
    return await api.getEmployees();
  } catch (error) {
    // Bug completely hidden!
    return [{ id: '1', name: 'Sample Employee', payRate: 25.00 }];
  }
}
```

**Problem**: User cannot detect data is fake, real bug is hidden.

---

### 2. Auto-Filling Business Data Defaults

```python
# Wrong: Fill defaults when data is missing
def process_payroll_input(data: dict) -> PayrollInput:
    return PayrollInput(
        hoursWorked=data.get("hoursWorked", 40.0),  # Conceals data source issue
        payRate=data.get("payRate", 15.0),          # Hides missing field
        employeeId=data.get("employeeId", "unknown")
    )
```

**Problem**: Conceals missing data or validation failures.

---

### 3. Ignoring Validation Errors

```typescript
// Wrong: Continue execution when validation fails
function savePayrollRun(run: PayrollRun) {
  if (!validate(run)) {
    // Ignore validation errors, fill with defaults
    run = fillDefaults(run);
  }
  return api.save(run);
}
```

**Problem**: Data validation failed but still saved, causes data inconsistency.

---

### 4. Hiding Error State

```typescript
// Wrong: Operation failed but pretend success
async function submitPayroll(runId: string) {
  try {
    await api.submitPayroll(runId);
  } catch (error) {
    // Silent failure, don't tell user
    console.log('Submit failed, but user won\'t know');
  }
  // Pretend success
  showSuccess('Payroll submitted successfully');
}
```

**Problem**: User thinks operation succeeded, but it actually failed.

---

## Allowed (Transparent Degradation)

### 1. Offline Cache Degradation (With Clear Notice)

```typescript
// Correct: Use cache but clearly inform user
async function fetchPayGroups() {
  try {
    const payGroups = await api.getPayGroups();
    localStorage.setItem('payGroups_cache', JSON.stringify({
      data: payGroups,
      timestamp: new Date().toISOString()
    }));
    return { data: payGroups, source: 'api', fresh: true };
  } catch (error) {
    const cached = localStorage.getItem('payGroups_cache');
    if (cached) {
      const { data, timestamp } = JSON.parse(cached);
      // Clearly inform user of data source and freshness
      showWarning(`Network connection failed. Showing cached data (updated ${formatTime(timestamp)})`);
      return { data, source: 'cache', fresh: false };
    }
    // No cache, show error
    throw new Error('Unable to load pay groups. Please check your network connection.');
  }
}
```

**Key**: User knows data source, can judge if data is trustworthy.

---

### 2. Configuration Defaults

```python
# Correct: Use reasonable defaults when system config missing
class PayrollConfig:
    defaultCurrency: str = "CAD"           # Doesn't affect business logic correctness
    defaultVacationRate: float = 0.04      # System configuration
    defaultOvertimeMultiplier: float = 1.5 # Display configuration
```

**Key**: These are system behavior configurations, not business data.

---

### 3. Form Initial Values

```typescript
// Correct: Initial values for new form
const newEmployee = {
  firstName: '',              // User will fill
  lastName: '',               // User will fill
  email: '',                  // User will fill
  payRate: 0,                 // User must fill
  startDate: new Date(),      // User will modify
  province: 'ON',             // User will confirm
};
```

**Key**: User knows this is a new form, will actively modify and confirm.

---

### 4. Graceful Degradation (Functional)

```typescript
// Correct: Chart rendering fails, degrade to table
function renderPayrollSummary(data: PayrollData) {
  try {
    return <PayrollChart data={data} />;
  } catch (error) {
    // Clearly inform user of degradation reason
    logger.error('Chart rendering failed', { error });
    return (
      <div>
        <Alert type="warning">Chart rendering failed. Switched to table view.</Alert>
        <PayrollTable data={data} />
      </div>
    );
  }
}
```

**Key**: User knows what happened, feature degraded but information complete.

---

## Key Judgment Criteria

**Does the user know what happened?**

| Scenario | Hiding Error? | Allowed? |
|----------|---------------|----------|
| Show warning + use cached data | No (Transparent) | Yes |
| Silently return fake data | Yes (Hidden) | No |
| Show error message + degrade to table | No (Transparent) | Yes |
| Ignore render error, show blank | Yes (Hidden) | No |
| Form defaults (user will modify) | No (Transparent) | Yes |
| Auto-fill business data | Yes (Hidden) | No |

---

## Implementation Checklist

Before implementing any degradation logic, ask yourself:

- [ ] Can user detect the data source?
- [ ] Is the error clearly displayed?
- [ ] Could this make user think operation succeeded?
- [ ] Could this conceal real system problems?

**If any answer is "would hide", that degradation logic is prohibited.**

---

## Error Message Design Best Practices

### Good Error Messages

```typescript
// Clear, actionable, contextual
throw new Error(
  'Unable to process payroll. Please check:\n' +
  '1. All employees have valid pay rates\n' +
  '2. Pay period dates are correctly set\n' +
  '3. No pending deductions need review'
);
```

**Characteristics**:
- Explains what the problem is
- Provides possible causes
- Gives resolution suggestions

---

### Bad Error Messages

```typescript
// Vague, useless, technical
throw new Error('Error 500');
throw new Error('Something went wrong');
throw new Error('NullPointerException at line 42');
```

**Problems**:
- User doesn't know what happened
- Doesn't know how to resolve
- Technical details meaningless to user

---

## Frontend Error Display Patterns

### Alert Component

```svelte
<script lang="ts">
  let { errorMessage }: { errorMessage: string | null } = $props();
</script>

{#if errorMessage}
  <div class="alert alert-error">
    <svg><!-- error icon --></svg>
    <span>{errorMessage}</span>
    <button onclick={() => errorMessage = null}>Dismiss</button>
  </div>
{/if}
```

---

### Toast Notifications

```typescript
// Temporary error notification
toast.error('Save failed. Please try again.', { duration: 3000 });

// Success notification
toast.success('Payroll submitted successfully');

// Warning notification
toast.warning('Using cached data. May not be current.');
```

---

### Inline Errors

```svelte
<!-- Error message next to form field -->
<input bind:value={payRate} class:error={payRateError} />
{#if payRateError}
  <span class="text-error text-sm">{payRateError}</span>
{/if}
```

---

## Backend Error Handling Patterns

### HTTP Status Code Usage

```python
from fastapi import HTTPException

# 400 - Client error (validation failed)
if not validate_input(data):
    raise HTTPException(
        status_code=400,
        detail="Hours worked must be greater than 0"
    )

# 404 - Resource not found
if not employee:
    raise HTTPException(
        status_code=404,
        detail=f"Employee {employee_id} not found"
    )

# 422 - Unprocessable entity (business logic error)
if payroll_already_submitted:
    raise HTTPException(
        status_code=422,
        detail="Payroll has already been submitted for this period"
    )

# 500 - Server error (unexpected exception)
try:
    process_payroll()
except Exception as e:
    logger.error("Unexpected error", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Server error. Please try again later."
    )
```

---

### Structured Error Response

```python
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    errorCode: str | None = None
    details: dict | None = None

# API return
return ErrorResponse(
    error="Unable to calculate payroll",
    errorCode="PAYROLL_CALC_ERROR",
    details={"employeeId": employee_id, "reason": "Missing pay rate"}
)
```

---

## Common Scenario Patterns

### Scenario 1: API Call Failed

```typescript
// Correct approach
try {
  const data = await payrollApi.getEmployees(companyId);
  return data;
} catch (error) {
  // Log error
  logger.error('API call failed', { error, companyId });

  // Show error notification
  showError('Failed to load employees. Please check your connection.');

  // Throw error, let upper layer decide how to handle
  throw error;
}
```

---

### Scenario 2: Data Validation Failed

```python
# Correct approach
def process_payroll_input(data: dict) -> PayrollInput:
    # Validate required fields
    required_fields = ["employeeId", "hoursWorked", "payRate"]
    missing = [f for f in required_fields if f not in data]

    if missing:
        raise ValueError(
            f"Missing required fields: {', '.join(missing)}"
        )

    # Validate data types and ranges
    hours = data["hoursWorked"]
    if not isinstance(hours, (int, float)) or hours < 0:
        raise ValueError("Hours worked must be a non-negative number")

    if hours > 168:
        raise ValueError("Hours worked cannot exceed 168 per period")

    return PayrollInput(**data)
```

---

### Scenario 3: Payroll Calculation Error

```typescript
// Correct approach
async function calculatePayroll(employeeId: string, payPeriod: PayPeriod) {
  try {
    const result = await payrollApi.calculate({
      employeeId,
      payPeriodStart: payPeriod.start,
      payPeriodEnd: payPeriod.end
    });
    return result;
  } catch (error) {
    // Distinguish different error types
    if (error.status === 400) {
      showError(`Invalid payroll data for employee: ${error.detail}`);
    } else if (error.status === 422) {
      showError(`Cannot calculate: ${error.detail}`);
    } else {
      showError('Payroll calculation failed. Please try again.');
    }
    throw error;
  }
}
```

---

**Philosophy**: Transparency first. Users should always know the real state of the system, even if that means showing error messages. Hiding errors causes bugs to be concealed, eventually causing bigger problems. Clear error messages help users understand problems and take action.
