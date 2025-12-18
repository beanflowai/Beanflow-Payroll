---
name: frontend-development
description: Frontend development guide for Beanflow-Payroll - Svelte 5+ with Runes, TypeScript strict mode, TailwindCSS 4, quality checks
owner: Frontend Team
last_updated: 2025-12-18
triggers:
  - Svelte 5 Runes
  - TypeScript strict mode
  - Tailwind standards
  - component development
  - UI development
related_skills:
  - core-architecture
  - workflow-policies
  - payroll-domain
agent_hints:
  token_budget_hint: "Load with payroll-domain for payroll-specific UI logic"
  write_scope: ["writes-frontend"]
  validation_commands:
    - "cd frontend && npm run check"
    - "cd frontend && npm run lint"
  plan_shape: ["Component/page implementation", "Error/loading feedback", "Performance strategy"]
  approval_required_if: []
---

# Quick Reference Card
- When to use: Writing/reviewing Svelte components and pages, handling frontend async and type safety
- 3-step approach:
  1) Enable TypeScript strict mode; use Svelte 5 Runes ($props/$state/$derived)
  2) API access through `$lib/api/*`, follow "transparent degradation", no silent mocks
  3) Performance first: virtualization, caching, debounce; observable logging
- How to verify: `npm run check`/`lint` pass; smooth interactions (no jitter), clear error messages, stable first screen

---

## Language Usage Standards

### [Style-FE-00: Frontend Language Standards]

#### Mandatory Requirements

- **Code identifiers**: **Must** use English (variable names, function names, component names, type names)
- **Comments and docstrings**: Prefer English, but Chinese comments are allowed
- **User interface text**: **Must** use English (button text, labels, prompts, error messages)
- **Log messages**: **Must** use English (console.log, console.error outputs)

#### Example

```svelte
<!-- Correct: English identifiers + English UI text, Chinese comments allowed -->
<script lang="ts">
  import type { Employee } from '$lib/types/employee';

  // Component props with proper typing
  let { employees, onSelect, loading = false }: {
    employees: Employee[];
    onSelect: (e: Employee) => void;
    loading?: boolean;
  } = $props();

  let error = $state<string | null>(null);
  let filtered = $state<Employee[]>(employees);
  let query = $state('');

  // Handle search functionality
  function handleSearch() {
    console.log('Searching for:', query);  // English log required
  }
</script>

<!-- UI text must be in English -->
<input
  type="text"
  placeholder="Search employees..."
  bind:value={query}
  oninput={handleSearch}
/>

{#if loading}
  <p>Loading...</p>  <!-- English UI text required -->
{:else if error}
  <p class="text-red-500">{error}</p>  <!-- English error message required -->
{:else}
  <button onclick={handleSearch}>Search</button>  <!-- English button text required -->
{/if}

<!-- Wrong: UI text in Chinese -->
<script lang="ts">
  let { employeeList } = $props();  // Wrong: Chinese variable names
  function searchFunction() { ... }  // Wrong: Chinese function names
</script>

<button>Search</button>  <!-- English required -->
<p>Loading...</p>  <!-- English required -->
```

---

## Core Essentials

### Type Safety
- Component props/function returns need types; avoid `any`
- Public types centralized in `$lib/types/*`

### Svelte 5 Runes
- State: `$state()`; Computed: `$derived()`; Props: `$props()`
- Avoid legacy syntax (`export let`, `$:` repeated declarations)

### Async and Errors
- `try/catch/finally` to manage `loading/error` state; use `{#await}` block when needed
- Log error context; show English-friendly prompts to users

### API Access
- Endpoints encapsulated in `$lib/api/*.ts`
- SSR pages fetch in `load()`, components handle interactive submissions

### Performance
- Large data uses virtual lists; frequent inputs use debounce; repeated queries use TTL cache

---

## Minimal Examples

### Typed props + state

```svelte
<script lang="ts">
  import type { Employee } from '$lib/types/employee';
  import type { PayrollRun } from '$lib/types/payroll';

  let { employees, payrollRun, onUpdate, loading = false }: {
    employees: Employee[];
    payrollRun: PayrollRun;
    onUpdate: (run: PayrollRun) => void;
    loading?: boolean;
  } = $props();

  let error = $state<string | null>(null);
  let selectedEmployee = $state<Employee | null>(null);

  // Derived values
  let totalGrossPay = $derived(
    employees.reduce((sum, e) => sum + e.grossPay, 0)
  );

  let activeEmployees = $derived(
    employees.filter(e => e.isActive)
  );
</script>
```

### Async with UI feedback

```svelte
<script lang="ts">
  import { payrollApi } from '$lib/api/payroll';

  let loading = $state(false);
  let error = $state<string | null>(null);

  async function submitPayroll() {
    error = null;
    loading = true;
    try {
      const result = await payrollApi.runPayroll({
        companyId: company.id,
        payGroupId: selectedPayGroup.id,
        payDate: payDate
      });
      // Handle success
    } catch (e) {
      error = e instanceof Error ? e.message : 'Unknown error occurred';
      console.error('Payroll submission failed:', e);
    } finally {
      loading = false;
    }
  }
</script>

{#if loading}
  <div class="flex items-center gap-2">
    <span class="loading loading-spinner"></span>
    <span>Processing payroll...</span>
  </div>
{:else if error}
  <div class="alert alert-error">
    <span>{error}</span>
  </div>
{:else}
  <button onclick={submitPayroll} class="btn btn-primary">
    Run Payroll
  </button>
{/if}
```

### Form handling with validation

```svelte
<script lang="ts">
  import type { EmployeeInput } from '$lib/types/employee';

  let formData = $state<EmployeeInput>({
    firstName: '',
    lastName: '',
    email: '',
    payRate: 0,
    payGroupId: ''
  });

  let errors = $state<Record<string, string>>({});

  function validateForm(): boolean {
    const newErrors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'First name is required';
    }
    if (!formData.email.includes('@')) {
      newErrors.email = 'Valid email is required';
    }
    if (formData.payRate <= 0) {
      newErrors.payRate = 'Pay rate must be greater than 0';
    }

    errors = newErrors;
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit() {
    if (!validateForm()) return;
    // Submit logic
  }
</script>

<form onsubmit|preventDefault={handleSubmit}>
  <div class="form-control">
    <label class="label">
      <span class="label-text">First Name</span>
    </label>
    <input
      type="text"
      bind:value={formData.firstName}
      class="input input-bordered"
      class:input-error={errors.firstName}
    />
    {#if errors.firstName}
      <span class="text-error text-sm">{errors.firstName}</span>
    {/if}
  </div>

  <button type="submit" class="btn btn-primary">
    Save Employee
  </button>
</form>
```

---

## Component Patterns

### Props with defaults

```svelte
<script lang="ts">
  let {
    title,
    variant = 'primary',
    disabled = false,
    onclick
  }: {
    title: string;
    variant?: 'primary' | 'secondary' | 'danger';
    disabled?: boolean;
    onclick?: () => void;
  } = $props();
</script>
```

### Event handlers

```svelte
<script lang="ts">
  let { onEmployeeSelect }: {
    onEmployeeSelect: (employeeId: string) => void;
  } = $props();

  function handleClick(id: string) {
    onEmployeeSelect(id);
  }
</script>

<button onclick={() => handleClick(employee.id)}>
  Select
</button>
```

### Reactive effects

```svelte
<script lang="ts">
  let searchQuery = $state('');
  let employees = $state<Employee[]>([]);

  // Effect runs when searchQuery changes
  $effect(() => {
    if (searchQuery.length >= 2) {
      fetchEmployees(searchQuery);
    }
  });

  async function fetchEmployees(query: string) {
    // Debounced fetch logic
  }
</script>
```

---

## Quality Check Commands

```bash
cd frontend

# Type checking
npm run check

# Linting
npm run lint

# Format code
npm run format

# Build for production
npm run build
```

**Requirement**: `npm run check` and `npm run lint` must pass without errors.

---

## Validation Checklist

- [ ] Component props/function returns have types; no `any`
- [ ] Using Runes ($props/$state/$derived); no legacy `export let`
- [ ] Async interactions have loading/error UI and logging
- [ ] API access through `$lib/api/*`, errors follow "transparent degradation"
- [ ] Large tables/long lists use virtualization; frequent inputs have debounce; repeated queries have cache
- [ ] All UI text in English
- [ ] All console logs in English

---

## Related Resources

- **Core Architecture**: See `core-architecture` skill
- **Workflow Policies**: See `workflow-policies` skill
- **Backend Development**: See `backend-development` skill
- **Payroll Domain**: See `payroll-domain` skill
