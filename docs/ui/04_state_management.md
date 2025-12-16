# State Management (Svelte Stores)

> **Last Updated**: 2025-12-07
> **Location**: `payroll-frontend/src/lib/stores/`

---

## Store Architecture

### Core Stores

```typescript
// stores/payroll.ts
import { writable, derived } from 'svelte/store';
import type { PayPeriod, Employee, PayrollRecord, PayrollRun } from '$lib/types';

// ============================================
// Pay Period State
// ============================================

// Current pay period being viewed
export const currentPayPeriod = writable<PayPeriod | null>(null);

// All payroll runs for current year
export const payrollRuns = writable<PayrollRun[]>([]);

// ============================================
// Employee State
// ============================================

// All employees for this company
export const employeesList = writable<Employee[]>([]);

// Employee currently being edited
export const editingEmployee = writable<Employee | null>(null);

// ============================================
// Payroll Records State
// ============================================

// Payroll records for current pay period (Map for O(1) lookup)
export const payrollRecords = writable<Map<string, PayrollRecord>>(new Map());

// Set of employee IDs currently being calculated
export const isCalculating = writable<Set<string>>(new Set());

// ============================================
// UI State
// ============================================

export const showEmployeeForm = writable<boolean>(false);
export const showEmployeeDetail = writable<boolean>(false);
export const showPaystubModal = writable<boolean>(false);
export const showHolidayModal = writable<boolean>(false);
export const selectedEmployeeId = writable<string | null>(null);

// ============================================
// Derived Stores
// ============================================

// Active employees only
export const activeEmployees = derived(
  employeesList,
  ($employees) => $employees.filter(emp => !emp.terminationDate)
);

// Terminated employees only
export const terminatedEmployees = derived(
  employeesList,
  ($employees) => $employees.filter(emp => emp.terminationDate)
);

// Employee counts by type
export const employeeCounts = derived(
  employeesList,
  ($employees) => ({
    total: $employees.length,
    active: $employees.filter(e => !e.terminationDate).length,
    salaried: $employees.filter(e => e.salaryType === 'annual').length,
    hourly: $employees.filter(e => e.salaryType === 'hourly').length,
  })
);

// Payroll totals for current period
export const payrollTotals = derived(
  payrollRecords,
  ($records) => {
    let totalGross = 0;
    let totalDeductions = 0;
    let totalNetPay = 0;
    let employerCpp = 0;
    let employerEi = 0;

    $records.forEach(record => {
      totalGross += record.grossTotal;
      totalDeductions += record.totalDeductions;
      totalNetPay += record.netPay;
      employerCpp += record.cppEmployer;
      employerEi += record.eiEmployer;
    });

    return {
      totalGross,
      totalDeductions,
      totalNetPay,
      employerCpp,
      employerEi,
      totalEmployerCost: employerCpp + employerEi,
    };
  }
);

// Selected employee details
export const selectedEmployee = derived(
  [employeesList, selectedEmployeeId],
  ([$employees, $id]) => $employees.find(e => e.id === $id) ?? null
);
```

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    User Interaction                       │
│  (Edit Gross Pay, Change Pay Period, Add Employee)       │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   Svelte Component                        │
│       (PayrollTable.svelte, EmployeeForm.svelte)         │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   Update Store                            │
│       payrollRecords.update(), isCalculating.update()    │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│                 Backend API Call                          │
│     POST /api/payroll/calculate                          │
│     GET /api/payroll/runs/{id}/records                   │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Receive API Response                         │
│     { grossPay, cppEmployee, eiEmployee, ... }           │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Update Store with Result                     │
│          payrollRecords.set(newRecords)                  │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│              Save to Supabase                             │
│    payroll_runs / payroll_records tables                 │
└───────────────────────┬──────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────┐
│           UI Auto-refresh (Reactivity)                    │
│      Svelte components re-render with new data           │
└──────────────────────────────────────────────────────────┘
```

---

## Store Actions Pattern

For complex operations, use action functions:

```typescript
// stores/actions/payroll.ts
import { payrollRecords, isCalculating, currentPayPeriod } from '../payroll';
import { api } from '$lib/api';

export async function calculateEmployeePayroll(
  employeeId: string,
  grossPay: number
): Promise<void> {
  // 1. Mark as calculating
  isCalculating.update(set => {
    set.add(employeeId);
    return new Set(set);
  });

  try {
    // 2. Call API
    const result = await api.payroll.calculate({
      employeeId,
      grossPay,
      // ... other params from stores
    });

    // 3. Update store
    payrollRecords.update(map => {
      map.set(employeeId, result);
      return new Map(map);
    });

  } catch (error) {
    console.error('Calculation failed:', error);
    throw error;
  } finally {
    // 4. Clear calculating state
    isCalculating.update(set => {
      set.delete(employeeId);
      return new Set(set);
    });
  }
}

export async function loadPayrollRun(runId: string): Promise<void> {
  const run = await api.payroll.getRun(runId);
  currentPayPeriod.set({
    id: run.id,
    start: run.periodStart,
    end: run.periodEnd,
    payDate: run.payDate,
  });

  const records = await api.payroll.getRecords(runId);
  const recordMap = new Map(records.map(r => [r.employeeId, r]));
  payrollRecords.set(recordMap);
}

export async function approvePayroll(runId: string): Promise<void> {
  await api.payroll.approve(runId);
  // Update local state or refetch
}
```

---

## Example: Inline Editing Flow

```svelte
<script lang="ts">
  import { payrollRecords, isCalculating } from '$lib/stores/payroll';
  import { calculateEmployeePayroll } from '$lib/stores/actions/payroll';
  import type { Employee, PayrollRecord } from '$lib/types';

  interface Props {
    employee: Employee;
    record: PayrollRecord;
  }

  let { employee, record }: Props = $props();

  let editedGrossPay = $state(record.grossRegular / 100);
  let isEditing = $state(false);

  const calculating = $derived($isCalculating.has(employee.id));

  async function handleSave() {
    const newGrossPayCents = Math.round(editedGrossPay * 100);

    if (newGrossPayCents === record.grossRegular) {
      isEditing = false;
      return;
    }

    try {
      await calculateEmployeePayroll(employee.id, newGrossPayCents);
      isEditing = false;
    } catch (error) {
      // Revert on error
      editedGrossPay = record.grossRegular / 100;
      alert('Failed to calculate payroll. Please try again.');
    }
  }

  function handleCancel() {
    editedGrossPay = record.grossRegular / 100;
    isEditing = false;
  }
</script>

{#if isEditing}
  <input
    type="number"
    bind:value={editedGrossPay}
    step="0.01"
    min="0"
    class="w-24 px-2 py-1 border rounded"
    onkeydown={(e) => {
      if (e.key === 'Enter') handleSave();
      if (e.key === 'Escape') handleCancel();
    }}
    disabled={calculating}
  />
  {#if calculating}
    <span class="ml-2 animate-spin">⟳</span>
  {/if}
{:else}
  <button
    onclick={() => isEditing = true}
    class="text-left hover:bg-gray-100 px-2 py-1 rounded"
  >
    ${(record.grossRegular / 100).toFixed(2)}
  </button>
{/if}
```

---

## Store File Structure

```
payroll-frontend/src/lib/stores/
├── payroll.ts           # Core payroll stores
├── employees.ts         # Employee-specific stores
├── ui.ts                # UI state stores
├── actions/
│   ├── payroll.ts       # Payroll action functions
│   ├── employees.ts     # Employee action functions
│   └── index.ts         # Re-exports
└── index.ts             # Re-exports all stores
```

---

## Best Practices

### 1. Use Maps for O(1) Lookup

```typescript
// ✅ Good: O(1) lookup by employee ID
export const payrollRecords = writable<Map<string, PayrollRecord>>(new Map());

// ❌ Avoid: O(n) lookup
export const payrollRecords = writable<PayrollRecord[]>([]);
```

### 2. Immutable Updates

```typescript
// ✅ Good: Create new Map/Set
payrollRecords.update(map => {
  const newMap = new Map(map);
  newMap.set(id, record);
  return newMap;
});

// ❌ Avoid: Mutating existing
payrollRecords.update(map => {
  map.set(id, record);  // Mutation!
  return map;           // Same reference, may not trigger updates
});
```

### 3. Derived for Computed Values

```typescript
// ✅ Good: Auto-updates when source changes
export const activeCount = derived(
  employeesList,
  ($list) => $list.filter(e => !e.terminationDate).length
);

// ❌ Avoid: Manual computation in components
let activeCount = $employees.filter(e => !e.terminationDate).length;
```

### 4. Actions for Side Effects

```typescript
// ✅ Good: Centralized side effect handling
await calculateEmployeePayroll(id, grossPay);

// ❌ Avoid: Scattered API calls in components
await fetch('/api/calculate', { ... });
payrollRecords.update(...);
```
